"""CRUD tools for the conversational CRUD agent.

Provides tool categories:
1. surreal_query — dynamic SurrealQL generation from natural language with guardrails
2. preview_write / execute_pending_write — HITL write protocol
3. preview_bulk_write — bulk HITL write protocol
4. undo_last_write — undo the most recent write operation
5. get_schema_info — returns allowed fields and enum values for ACM tables
6. ask_user_choice — present a multiple-choice question to the user

All tools are async — they run in the same async context as the LangGraph
graph nodes, ensuring contextvars (source_id scoping) propagate correctly.

All operations are scoped to a specific source_id to prevent cross-job data modification.
Security: all generated SurrealQL MUST include WHERE source_id = $sid.
"""

import json
import os
import re
import time
import uuid
from typing import Optional

from jinja2 import Environment, FileSystemLoader
from langchain_core.tools import tool
from loguru import logger

from open_notebook.database.repository import ensure_record_id, repo_query
from open_notebook.graphs.guardrails import (
    ALLOWED_ACM_FIELDS,
    ALLOWED_BUILDING_FIELDS,
    DB_SCHEMA_CONTEXT,
    MAX_RESULT_ROWS,
    cap_results,
    validate_read_query,
    validate_write_operation,
)

# --- Jinja2 prompt environment ---
_prompts_dir = os.path.join(os.path.dirname(__file__), "..", "..", "prompts")
_jinja_env = Environment(
    loader=FileSystemLoader(os.path.abspath(_prompts_dir)),
    autoescape=False,
)

# --- Pending write store ---
_pending_writes: dict = {}
_PENDING_WRITE_TTL = 600  # 10 minutes — stale writes are auto-cleaned

# --- Tool context (delegates to unified tool_context module) ---
from open_notebook.graphs.tool_context import get_source_id, set_tool_scope


def _cleanup_stale_writes() -> None:
    """Remove pending writes older than TTL. Called before creating new ones."""
    now = time.time()
    stale = [k for k, v in _pending_writes.items() if now - v.get("_created_at", 0) > _PENDING_WRITE_TTL]
    for k in stale:
        del _pending_writes[k]


def set_crud_context(source_id: str) -> None:
    """Set the source_id scope for CRUD operations. Called by the agent graph."""
    set_tool_scope(source_id=source_id)


def get_crud_context() -> str:
    """Get the current source_id scope."""
    return get_source_id() or ""


async def _generate_surrealql(user_question: str, source_id: str) -> str:
    """Use an LLM to generate a SurrealQL query from natural language.

    Falls back to a simple keyword-based query if the LLM is unavailable.
    """
    from open_notebook.graphs.guardrails import ALLOWED_READ_TABLES

    template = _jinja_env.get_template("crud/surrealql_query.jinja")
    prompt_text = template.render(
        schema_context=DB_SCHEMA_CONTEXT,
        max_rows=MAX_RESULT_ROWS,
        allowed_tables=", ".join(sorted(ALLOWED_READ_TABLES)),
        user_question=user_question,
    )

    try:
        from open_notebook.graphs.utils import provision_langchain_model

        model = await provision_langchain_model(
            prompt_text,
            None,  # use default model
            "chat",
            max_tokens=512,
        )

        from langchain_core.messages import HumanMessage

        response = await model.ainvoke([HumanMessage(content=prompt_text)])
        raw_query = response.content.strip()

        # Strip markdown code fences if present
        raw_query = re.sub(r"^```(?:sql|surrealql)?\s*", "", raw_query)
        raw_query = re.sub(r"\s*```$", "", raw_query)
        raw_query = raw_query.strip()

        return raw_query

    except Exception as e:
        logger.warning(f"LLM SurrealQL generation failed, using fallback: {e}")
        return _fallback_query(user_question)


def _fallback_query(user_question: str) -> str:
    """Keyword-based fallback when LLM is unavailable."""
    q = user_question.lower()

    if "count" in q or "how many" in q:
        return (
            "SELECT count() as total FROM acm_record WHERE source_id = $sid GROUP ALL;"
        )

    if ("list" in q and "building" in q) or "buildings" in q:
        return "SELECT DISTINCT building_id, building_name FROM acm_record WHERE source_id = $sid;"

    if "no_access" in q or "no access" in q:
        return (
            "SELECT building_name, room_name, product, location FROM acm_record "
            "WHERE source_id = $sid AND no_access = true;"
        )

    if "friable" in q:
        return (
            "SELECT building_name, room_name, product, friable, sample_result FROM acm_record "
            "WHERE source_id = $sid AND friable = 'Friable' LIMIT 50;"
        )

    if "high risk" in q or "positive" in q:
        return (
            "SELECT building_name, room_name, product, sample_result, friable, "
            "material_condition, disturbance_potential FROM acm_record "
            "WHERE source_id = $sid AND (sample_result = 'Positive' "
            "OR sample_result = 'Assumed Positive') LIMIT 50;"
        )

    if "risk" in q and (
        "breakdown" in q or "summary" in q or "count" in q or "by" in q
    ):
        return (
            "SELECT sample_result, count() as total FROM acm_record "
            "WHERE source_id = $sid GROUP BY sample_result;"
        )

    # Generic fallback
    return (
        "SELECT building_name, room_name, product, sample_result, friable "
        "FROM acm_record WHERE source_id = $sid LIMIT 20;"
    )


@tool
async def surreal_query(question: str) -> str:
    """Query ACM records for the current job using natural language.

    Automatically generates and executes a SurrealQL query scoped to this job.
    Use this for any read operation: counting, listing, filtering, aggregating.

    Args:
        question: Natural language description of what you want to find.
            Examples: "how many friable records?", "list buildings",
            "show high risk records in Building A", "count by risk status"
    """
    source_id = get_crud_context()
    if not source_id:
        return json.dumps(
            {
                "type": "surreal_query",
                "error": "No job context set. Cannot query records.",
                "results": [],
            }
        )

    # Generate SurrealQL from natural language
    generated_sql = await _generate_surrealql(question, source_id)
    logger.info(f"Generated SurrealQL: {generated_sql}")

    # Validate through guardrails
    check = validate_read_query(generated_sql)
    if not check.allowed:
        logger.warning(f"Guardrail blocked query: {check.reason}")
        return json.dumps(
            {
                "type": "surreal_query",
                "error": f"Query blocked: {check.reason}",
                "generated_sql": generated_sql,
                "results": [],
            }
        )

    # Execute the validated query
    try:
        sid = ensure_record_id(source_id)
        # Build vars — always include $sid, optionally $val for search terms
        query_vars: dict = {"sid": sid}

        # Extract search value if the query uses $val or other common param names
        sanitized = check.sanitized_query
        if "$val" in sanitized:
            val = _extract_search_value(question)
            query_vars["val"] = val
        # Also handle LLM-generated queries that use alternate variable names
        for param_name in re.findall(r"\$(\w+)", sanitized):
            if param_name not in query_vars:
                # Bind unmatched params to the extracted search value
                query_vars[param_name] = _extract_search_value(question)

        result = await repo_query(sanitized, query_vars)

        # Flatten nested list results from SurrealDB
        if (
            result
            and isinstance(result, list)
            and len(result) == 1
            and isinstance(result[0], list)
        ):
            result = result[0]

        # Apply output guardrails
        capped = cap_results(result) if result else []

        return json.dumps(
            {
                "type": "surreal_query",
                "question": question,
                "generated_sql": check.sanitized_query,
                "total_results": len(result) if result else 0,
                "results": capped,
                "warnings": check.warnings,
            }
        )
    except Exception as e:
        logger.error(f"Error in surreal_query: {e}")
        return json.dumps(
            {
                "type": "surreal_query",
                "error": f"Query execution error: {str(e)}",
                "generated_sql": generated_sql,
                "results": [],
            }
        )


def _extract_search_value(question: str) -> str:
    """Extract the most likely search term from a natural language question."""
    # Check for quoted strings
    quoted = re.findall(r'"([^"]+)"', question) or re.findall(r"'([^']+)'", question)
    if quoted:
        return quoted[0]

    # Check for building references like "Building A", "BLD#001"
    bld = re.search(r"(?:building|bld)\s*#?\s*(\S+)", question, re.IGNORECASE)
    if bld:
        return bld.group(0)

    # Check for "in <something>" pattern
    in_match = re.search(
        r"\bin\s+(.+?)(?:\s+with|\s+that|\s*$)", question, re.IGNORECASE
    )
    if in_match:
        return in_match.group(1).strip()

    # Fallback: return the question itself (the LLM query will handle it)
    return question


@tool
async def preview_write(
    operation: str,
    record_id: Optional[str],
    field: Optional[str],
    new_value: Optional[str],
    reason: str,
) -> str:
    """Preview a write operation before executing it. ALWAYS call this before any write.

    The user must confirm before the write is executed.

    Args:
        operation: The operation type — one of: "UPDATE", "DELETE", "INSERT"
        record_id: The ACM record ID to update or delete (for UPDATE/DELETE). Use None for INSERT.
        field: The field name to update (for UPDATE only)
        new_value: The new value as a string (for UPDATE only)
        reason: Brief explanation of why this change is being made

    Returns a JSON preview with an operation_id. The user must approve via the UI dialog.
    """
    source_id = get_crud_context()
    if not source_id:
        return json.dumps({"type": "preview_write", "error": "No job context set."})

    # Determine target table from record_id
    table = "acm_record"
    if record_id and record_id.startswith("building_record:"):
        table = "building_record"

    # Validate through guardrails
    check = validate_write_operation(table, operation, field)
    if not check.allowed:
        return json.dumps(
            {
                "type": "preview_write",
                "error": f"Write blocked: {check.reason}",
            }
        )

    _cleanup_stale_writes()
    operation_id = str(uuid.uuid4())[:8]

    _pending_writes[operation_id] = {
        "operation_id": operation_id,
        "operation": operation,
        "source_id": source_id,
        "record_id": record_id,
        "table": table,
        "field": field,
        "new_value": new_value,
        "reason": reason,
        "status": "pending",
        "_created_at": time.time(),
    }

    preview = {
        "type": "preview_write",
        "operation_id": operation_id,
        "operation": operation,
        "record_id": record_id or "new",
        "field": field,
        "new_value": new_value,
        "reason": reason,
    }

    return json.dumps(preview)


@tool
async def preview_bulk_write(
    operation: str,
    filter_description: str,
    field: str,
    new_value: str,
    reason: str,
    record_ids: Optional[list] = None,
) -> str:
    """Preview a bulk write operation affecting multiple records.

    Args:
        operation: "UPDATE" or "DELETE"
        filter_description: Natural language description of which records to affect
        field: The field to update (for UPDATE)
        new_value: The new value (for UPDATE)
        reason: Why this change is being made
        record_ids: Optional explicit list of record IDs. If not provided, generates
            filter from description.
    """
    source_id = get_crud_context()
    if not source_id:
        return json.dumps(
            {"type": "preview_bulk_write", "error": "No job context set."}
        )

    # Determine target table
    table = "acm_record"
    if record_ids and len(record_ids) > 0:
        if str(record_ids[0]).startswith("building_record:"):
            table = "building_record"

    # Validate through guardrails
    check = validate_write_operation(
        table, operation, field if operation.upper() == "UPDATE" else None
    )
    if not check.allowed:
        return json.dumps(
            {
                "type": "preview_bulk_write",
                "error": f"Write blocked: {check.reason}",
            }
        )

    # Resolve record IDs
    resolved_ids: list = []
    if record_ids is not None:
        resolved_ids = [str(rid) for rid in record_ids]
    else:
        # Generate SurrealQL from filter description to collect IDs
        generated_sql = await _generate_surrealql(filter_description, source_id)
        check_read = validate_read_query(generated_sql)
        if check_read.allowed:
            try:
                sid = ensure_record_id(source_id)
                result = await repo_query(check_read.sanitized_query, {"sid": sid})
                if (
                    result
                    and isinstance(result, list)
                    and len(result) == 1
                    and isinstance(result[0], list)
                ):
                    result = result[0]
                if result:
                    for row in result:
                        if isinstance(row, dict) and "id" in row:
                            resolved_ids.append(str(row["id"]))
            except Exception as e:
                logger.warning(f"preview_bulk_write: failed to resolve record IDs: {e}")

    _cleanup_stale_writes()
    operation_id = str(uuid.uuid4())[:8]

    _pending_writes[operation_id] = {
        "operation_id": operation_id,
        "type": "bulk",
        "operation": operation,
        "source_id": source_id,
        "table": table,
        "field": field,
        "new_value": new_value,
        "filter_description": filter_description,
        "reason": reason,
        "record_ids": resolved_ids,
        "status": "pending",
        "_created_at": time.time(),
    }

    return json.dumps(
        {
            "type": "preview_bulk_write",
            "operation_id": operation_id,
            "operation": operation,
            "affected_count": len(resolved_ids),
            "field": field,
            "new_value": new_value,
            "reason": reason,
            "record_ids": resolved_ids,
        }
    )


def _fetch_old_value(rows, field: Optional[str] = None):
    """Extract old value from a SurrealDB query result."""
    if not rows or not isinstance(rows, list):
        return None
    first = rows[0]
    if isinstance(first, list) and first:
        first = first[0]
    if isinstance(first, dict):
        return first.get(field) if field else first
    return None


@tool
async def execute_pending_write(
    operation_id: str,
    source_id: Optional[str] = None,
    edits: Optional[dict] = None,
) -> str:
    """Execute a previously previewed write operation ONLY after the user explicitly approves.

    CRITICAL: Only call this tool when the user's LAST message contains "Approved" or
    "Execute operation". NEVER call this in the same turn as preview_write.

    Args:
        operation_id: The operation_id from the preview_write result
        source_id: Optional source_id override. Falls back to context.
        edits: Optional field edits from the user
    """
    source_id = source_id or get_crud_context()
    pending = _pending_writes.get(operation_id)

    if not pending:
        return f"Error: No pending operation found with ID {operation_id}. The user must approve before execution."

    if pending.get("status") == "executed":
        return f"Operation {operation_id} was already executed."

    # Safety: block if previewed less than 2 seconds ago
    created_at = pending.get("_created_at", 0)
    if time.time() - created_at < 2.0:
        return f"Error: Operation {operation_id} was just previewed. Wait for user approval before executing."

    if pending.get("source_id") != source_id:
        return "Error: Operation source_id mismatch — security violation."

    # Apply any user edits from the approval dialog
    if edits:
        if "new_value" in edits:
            pending["new_value"] = edits["new_value"]
        if "field" in edits:
            pending["field"] = edits["field"]

    try:
        sid = ensure_record_id(source_id)
        op = pending["operation"]
        record_id = pending.get("record_id")
        field = pending.get("field")
        new_value = pending.get("new_value")
        table = pending.get("table", "acm_record")

        # --- Bulk branch ---
        if pending.get("type") == "bulk":
            record_ids = pending.get("record_ids", [])
            updated_count = 0
            for rid_str in record_ids:
                rid = ensure_record_id(rid_str)
                try:
                    if op == "UPDATE" and field:
                        old_rows = await repo_query(
                            f"SELECT {field} FROM $rid", {"rid": rid}
                        )
                        old_value = _fetch_old_value(old_rows, field)

                        await repo_query(
                            f"UPDATE $rid SET {field} = $val",
                            {"rid": rid, "val": new_value},
                        )

                        await repo_query(
                            """INSERT INTO crud_audit {
                                job_id: $sid, timestamp: time::now(),
                                natural_language: $reason, generated_surql: $surql,
                                operation: $op, confirmed_by: 'user_hitl',
                                record_id: $record_id, field_name: $field_name,
                                old_value: $old_value, new_value: $new_value
                            }""",
                            {
                                "sid": sid,
                                "reason": pending.get("reason", ""),
                                "surql": f"UPDATE {rid_str} SET {field} = '{new_value}'",
                                "op": op,
                                "record_id": rid_str,
                                "field_name": field,
                                "old_value": str(old_value)
                                if old_value is not None
                                else None,
                                "new_value": str(new_value)
                                if new_value is not None
                                else None,
                            },
                        )
                        updated_count += 1

                    elif op == "DELETE":
                        old_rows = await repo_query("SELECT * FROM $rid", {"rid": rid})
                        old_value = _fetch_old_value(old_rows)

                        await repo_query("DELETE $rid", {"rid": rid})

                        await repo_query(
                            """INSERT INTO crud_audit {
                                job_id: $sid, timestamp: time::now(),
                                natural_language: $reason, generated_surql: $surql,
                                operation: $op, confirmed_by: 'user_hitl',
                                record_id: $record_id, old_value: $old_value
                            }""",
                            {
                                "sid": sid,
                                "reason": pending.get("reason", ""),
                                "surql": f"DELETE {rid_str}",
                                "op": op,
                                "record_id": rid_str,
                                "old_value": json.dumps(old_value)
                                if old_value is not None
                                else None,
                            },
                        )
                        updated_count += 1
                except Exception as e:
                    logger.error(f"execute_pending_write bulk: error on {rid_str}: {e}")

            pending["status"] = "executed"
            label = field if op == "UPDATE" else "records"
            return json.dumps(
                {
                    "type": "write_result",
                    "success": True,
                    "message": f"Updated {label} on {updated_count} records.",
                    "operation_id": operation_id,
                }
            )

        # --- Single-record UPDATE branch ---
        if op == "UPDATE" and record_id and field:
            if table == "acm_record" and field not in ALLOWED_ACM_FIELDS:
                return f"Error: Field '{field}' is not a valid ACM field."
            if table == "building_record" and field not in ALLOWED_BUILDING_FIELDS:
                return f"Error: Field '{field}' is not a valid building field."

            rid = ensure_record_id(record_id)
            check = await repo_query(
                f"SELECT id FROM {table} WHERE id = $rid AND source_id = $sid",
                {"rid": rid, "sid": sid},
            )
            if not check:
                return "Error: Record not found in this job."

            # Fetch old value before UPDATE
            old_rows = await repo_query(f"SELECT {field} FROM $rid", {"rid": rid})
            old_value = _fetch_old_value(old_rows, field)

            await repo_query(
                f"UPDATE $rid SET {field} = $val", {"rid": rid, "val": new_value}
            )

            await repo_query(
                """INSERT INTO crud_audit {
                    job_id: $sid, timestamp: time::now(),
                    natural_language: $reason, generated_surql: $surql,
                    operation: $op, confirmed_by: 'user_hitl',
                    record_id: $record_id, field_name: $field_name,
                    old_value: $old_value, new_value: $new_value
                }""",
                {
                    "sid": sid,
                    "reason": pending.get("reason", ""),
                    "surql": f"UPDATE {record_id} SET {field} = '{new_value}'",
                    "op": op,
                    "record_id": record_id,
                    "field_name": field,
                    "old_value": str(old_value) if old_value is not None else None,
                    "new_value": str(new_value) if new_value is not None else None,
                },
            )

            pending["status"] = "executed"
            return json.dumps(
                {
                    "type": "write_result",
                    "success": True,
                    "message": f"Updated {field} on record {record_id} to '{new_value}'.",
                    "operation_id": operation_id,
                }
            )

        # --- Single-record DELETE branch ---
        elif op == "DELETE" and record_id:
            rid = ensure_record_id(record_id)
            check = await repo_query(
                f"SELECT id FROM {table} WHERE id = $rid AND source_id = $sid",
                {"rid": rid, "sid": sid},
            )
            if not check:
                return "Error: Record not found in this job."

            # Fetch full record before DELETE
            old_rows = await repo_query("SELECT * FROM $rid", {"rid": rid})
            old_value = _fetch_old_value(old_rows)

            await repo_query("DELETE $rid", {"rid": rid})

            await repo_query(
                """INSERT INTO crud_audit {
                    job_id: $sid, timestamp: time::now(),
                    natural_language: $reason, generated_surql: $surql,
                    operation: $op, confirmed_by: 'user_hitl',
                    record_id: $record_id, old_value: $old_value
                }""",
                {
                    "sid": sid,
                    "reason": pending.get("reason", ""),
                    "surql": f"DELETE {record_id}",
                    "op": op,
                    "record_id": record_id,
                    "old_value": json.dumps(old_value)
                    if old_value is not None
                    else None,
                },
            )

            pending["status"] = "executed"
            return json.dumps(
                {
                    "type": "write_result",
                    "success": True,
                    "message": f"Deleted record {record_id}.",
                    "operation_id": operation_id,
                }
            )

        else:
            return f"Error: Unsupported operation {op} or missing parameters."

    except Exception as e:
        logger.error(f"Error executing write {operation_id}: {e}")
        return f"Error executing write: {str(e)}"


@tool
async def undo_last_write(record_id: Optional[str] = None) -> str:
    """Undo the most recent write operation for this job.

    Args:
        record_id: Optional specific record to undo. If not provided, undoes the
            last write for the job.
    """
    source_id = get_crud_context()
    if not source_id:
        return json.dumps({"type": "undo_error", "error": "No job context set."})

    try:
        sid = ensure_record_id(source_id)
        if record_id:
            audit_rows = await repo_query(
                "SELECT * FROM crud_audit WHERE job_id = $sid AND record_id = $rid "
                "ORDER BY timestamp DESC LIMIT 1",
                {"sid": sid, "rid": str(record_id)},
            )
        else:
            audit_rows = await repo_query(
                "SELECT * FROM crud_audit WHERE job_id = $sid "
                "ORDER BY timestamp DESC LIMIT 1",
                {"sid": sid},
            )
        if (
            audit_rows
            and isinstance(audit_rows, list)
            and len(audit_rows) == 1
            and isinstance(audit_rows[0], list)
        ):
            audit_rows = audit_rows[0]
    except Exception as e:
        logger.error(f"undo_last_write: failed to query audit log: {e}")
        return json.dumps(
            {"type": "undo_error", "error": f"Failed to query audit log: {str(e)}"}
        )

    if not audit_rows:
        return json.dumps(
            {
                "type": "undo_error",
                "error": "No audit records found for this job."
                + (f" Record: {record_id}" if record_id else ""),
            }
        )

    audit = audit_rows[0] if isinstance(audit_rows, list) else audit_rows

    op = audit.get("operation", "").upper()
    audited_record_id = audit.get("record_id")
    old_value = audit.get("old_value")
    field_name = audit.get("field_name")

    if op == "UPDATE":
        if not audited_record_id or old_value is None or not field_name:
            return json.dumps(
                {
                    "type": "undo_error",
                    "error": "Audit row is missing record_id, field_name, or old_value — cannot undo.",
                }
            )
        return await preview_write.ainvoke(
            {
                "operation": "UPDATE",
                "record_id": audited_record_id,
                "field": field_name,
                "new_value": str(old_value),
                "reason": f"Undo: restoring {field_name} to previous value '{old_value}'",
            }
        )

    elif op == "DELETE":
        return json.dumps(
            {
                "type": "undo_error",
                "error": "Undo of DELETE is not supported — the record has been permanently removed.",
            }
        )

    else:
        return json.dumps(
            {
                "type": "undo_error",
                "error": f"Cannot undo operation type '{op}'.",
            }
        )


@tool
async def get_schema_info(table: Optional[str] = None) -> str:
    """Get schema information about ACM database tables.

    Args:
        table: Optional table name ("acm_record" or "building_record"). If not
            provided, returns both.
    """
    _enum_values: dict = {
        "friable": ["Friable", "Non-friable"],
        "risk_status": ["High", "Medium", "Low", "Very Low"],
        "sample_result": ["Positive", "Negative", "Not Sampled", "No Access"],
        "material_condition": ["Good", "Fair", "Poor", "Very Poor"],
    }

    acm_schema = {
        "updatable_fields": sorted(ALLOWED_ACM_FIELDS),
        "enum_values": {
            k: v for k, v in _enum_values.items() if k in ALLOWED_ACM_FIELDS
        },
    }

    building_schema = {
        "updatable_fields": sorted(ALLOWED_BUILDING_FIELDS),
        "enum_values": {},
    }

    if table is None:
        tables = {"acm_record": acm_schema, "building_record": building_schema}
    elif table.lower() == "acm_record":
        tables = {"acm_record": acm_schema}
    elif table.lower() == "building_record":
        tables = {"building_record": building_schema}
    else:
        return json.dumps(
            {
                "type": "schema_info",
                "error": f"Unknown table '{table}'. Use 'acm_record' or 'building_record'.",
                "tables": {},
            }
        )

    return json.dumps({"type": "schema_info", "tables": tables})


@tool
async def ask_user_choice(
    question: str,
    options_query: Optional[str] = None,
    static_options: Optional[list] = None,
) -> str:
    """Present a multiple-choice question to the user.

    Args:
        question: The question to ask
        options_query: Optional SurrealQL SELECT query to generate options dynamically
        static_options: Optional list of static option strings
    """
    source_id = get_crud_context()
    options: list = []

    if options_query:
        check = validate_read_query(options_query)
        if not check.allowed:
            return json.dumps(
                {
                    "type": "ask_user_choice",
                    "error": f"Options query blocked: {check.reason}",
                }
            )

        try:
            query_vars: dict = {}
            if source_id:
                query_vars["sid"] = ensure_record_id(source_id)
            rows = await repo_query(check.sanitized_query, query_vars)
            if (
                rows
                and isinstance(rows, list)
                and len(rows) == 1
                and isinstance(rows[0], list)
            ):
                rows = rows[0]
            rows = rows or []
        except Exception as e:
            logger.error(f"ask_user_choice: failed to execute options_query: {e}")
            return json.dumps(
                {
                    "type": "ask_user_choice",
                    "error": f"Options query failed: {str(e)}",
                }
            )

        for row in rows[:20]:
            if isinstance(row, dict):
                first_val = next(
                    (str(v) for v in row.values() if v is not None), str(row)
                )
                options.append({"label": first_val, "value": first_val})
            else:
                options.append({"label": str(row), "value": str(row)})

    elif static_options is not None:
        options = [{"label": str(opt), "value": str(opt)} for opt in static_options]

    choice_id = str(uuid.uuid4())[:8]

    return json.dumps(
        {
            "type": "ask_user_choice",
            "question": question,
            "options": options,
            "choice_id": choice_id,
        }
    )
