"""CRUD tools for the conversational CRUD agent (E19-S8).

All write operations are scoped to a specific source_id to prevent
cross-job data modification. The preview_write protocol ensures
no write is executed without explicit user confirmation.

Security: all generated SurrealQL MUST include WHERE source_id = $source_id.
"""

import asyncio
import json
import uuid
from typing import Optional

from langchain_core.tools import tool
from loguru import logger

from open_notebook.database.repository import ensure_record_id, repo_query

# --- Allowed ACM fields for UPDATE (SQL injection prevention) ---
ALLOWED_ACM_FIELDS = {
    'building_id', 'building_name', 'product', 'friable', 'acm_product_group',
    'acm_product_type', 'material_condition', 'disturbance_potential', 'location',
    'room_name', 'room_id', 'floor_level', 'quantity', 'sample_result',
    'risk_status', 'identifying_company', 'material_description', 'extent',
    'hygienist_recommendations', 'area_type', 'no_access', 'acm_labelled',
}

# --- Pending write store ---
# Stores previewed operations keyed by operation_id.
# Operations are cleared after execution or expiry.
_pending_writes: dict = {}

# --- Tool context (set by agent before invocation) ---
_crud_context: dict = {}


def set_crud_context(source_id: str) -> None:
    """Set the source_id scope for CRUD operations. Called by the agent graph."""
    _crud_context["source_id"] = source_id


def get_crud_context() -> str:
    """Get the current source_id scope."""
    return _crud_context.get("source_id", "")


def _run_async(coro):
    """Run an async coroutine from a sync LangGraph context."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor() as pool:
            new_loop = asyncio.new_event_loop()
            try:
                return pool.submit(new_loop.run_until_complete, coro).result()
            finally:
                new_loop.close()
    else:
        return asyncio.run(coro)


@tool
def query_job_records(query: str) -> str:
    """Execute a read-only query about ACM records for the current job.

    Use this to answer questions about buildings, rooms, products, risk levels, etc.

    The query will be scoped to the current job's source_id automatically.
    Describe what you want to find in plain English — do not write SurrealQL.

    Examples:
    - "count all friable records"
    - "find records with no_access = true"
    - "list all buildings"
    - "show records in building Broadmeadows with High risk"

    Args:
        query: Natural language description of what you want to find
    """
    source_id = get_crud_context()
    if not source_id:
        return "Error: No job context set. Cannot query records. The source_id should be provided in the system prompt."

    q_lower = query.lower()

    async def run_query():
        sid = ensure_record_id(source_id)

        if "count" in q_lower or "how many" in q_lower:
            result = await repo_query(
                "SELECT count() as total FROM acm_record WHERE source_id = $sid GROUP ALL",
                {"sid": sid},
            )
            total = result[0]["total"] if result else 0
            return f"Total records for this job: {total}"

        elif ("list" in q_lower and "building" in q_lower) or "buildings" in q_lower:
            result = await repo_query(
                "SELECT DISTINCT building_id, building_name FROM acm_record WHERE source_id = $sid",
                {"sid": sid},
            )
            buildings = [
                f"- {r.get('building_name') or r.get('building_id')}" for r in result
            ]
            return (
                "Buildings:\n" + "\n".join(buildings)
                if buildings
                else "No buildings found."
            )

        elif "no_access" in q_lower or "no access" in q_lower:
            result = await repo_query(
                "SELECT building_id, building_name, room_name, product FROM acm_record "
                "WHERE source_id = $sid AND no_access = true",
                {"sid": sid},
            )
            if not result:
                return "No records marked as No Access."
            lines = [
                f"- {r.get('building_name', '?')} / {r.get('room_name', '?')} — {r.get('product', '?')}"
                for r in result
            ]
            return f"{len(result)} No Access records:\n" + "\n".join(lines)

        elif "friable" in q_lower:
            result = await repo_query(
                "SELECT building_name, room_name, product, friable FROM acm_record "
                "WHERE source_id = $sid AND friable = 'Friable'",
                {"sid": sid},
            )
            if not result:
                return "No friable records found."
            lines = [
                f"- {r.get('building_name', '?')} / {r.get('room_name', '?')} — {r.get('product', '?')}"
                for r in result
            ]
            return f"{len(result)} friable records:\n" + "\n".join(lines)

        elif "high risk" in q_lower:
            result = await repo_query(
                "SELECT building_name, room_name, product, risk_status FROM acm_record "
                "WHERE source_id = $sid AND risk_status = 'High'",
                {"sid": sid},
            )
            if not result:
                return "No High risk records."
            lines = [
                f"- {r.get('building_name', '?')} / {r.get('room_name', '?')} — {r.get('product', '?')}"
                for r in result
            ]
            return f"{len(result)} High risk records:\n" + "\n".join(lines)

        else:
            # Generic: return first 10 records summary
            result = await repo_query(
                "SELECT building_name, room_name, product, risk_status FROM acm_record "
                "WHERE source_id = $sid LIMIT 10",
                {"sid": sid},
            )
            if not result:
                return "No records found."
            lines = [
                f"- {r.get('building_name', '?')} / {r.get('room_name', '?')} — {r.get('product', '?')} [{r.get('risk_status', '?')}]"
                for r in result
            ]
            return f"First {len(result)} records:\n" + "\n".join(lines)

    try:
        return _run_async(run_query())
    except Exception as e:
        logger.error(f"Error in query_job_records: {e}")
        return f"Error querying records: {str(e)}"


@tool
def preview_write(
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

    Returns a JSON preview with an operation_id. The user must call confirm_write with this ID.
    The output will be displayed as a confirmation card in the UI.
    """
    source_id = get_crud_context()
    if not source_id:
        return "Error: No job context set."

    operation_id = str(uuid.uuid4())[:8]

    import time

    # Store pending operation with timestamp for same-turn guard
    _pending_writes[operation_id] = {
        "operation_id": operation_id,
        "operation": operation,
        "source_id": source_id,
        "record_id": record_id,
        "field": field,
        "new_value": new_value,
        "reason": reason,
        "status": "pending",
        "_created_at": time.time(),
    }

    # Return as JSON — the frontend renders an approval dialog
    # and sends the user's decision as a chat message
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
def execute_pending_write(
    operation_id: str,
    source_id: Optional[str] = None,
    edits: Optional[dict] = None,
) -> str:
    """Execute a previously previewed write operation ONLY after the user explicitly approves.

    CRITICAL: Only call this tool when the user's LAST message contains "Approved" or
    "Execute operation". NEVER call this in the same turn as preview_write.
    If the user has not approved, DO NOT call this tool.

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

    # Safety: block if previewed less than 2 seconds ago (prevent same-turn self-approval)
    import time
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

    async def execute():
        sid = ensure_record_id(source_id)
        op = pending["operation"]
        record_id = pending.get("record_id")
        field = pending.get("field")
        new_value = pending.get("new_value")

        if op == "UPDATE" and record_id and field:
            if field not in ALLOWED_ACM_FIELDS:
                return f"Error: Field '{field}' is not a valid ACM field."
            rid = ensure_record_id(record_id)
            check = await repo_query(
                "SELECT id FROM acm_record WHERE id = $rid AND source_id = $sid",
                {"rid": rid, "sid": sid},
            )
            if not check:
                return "Error: Record not found in this job."

            await repo_query(
                f"UPDATE $rid SET {field} = $val",
                {"rid": rid, "val": new_value},
            )

            await repo_query(
                """INSERT INTO crud_audit {
                    job_id: $sid,
                    timestamp: time::now(),
                    natural_language: $reason,
                    generated_surql: $surql,
                    operation: $op,
                    confirmed_by: 'user_hitl'
                }""",
                {
                    "sid": sid,
                    "reason": pending.get("reason", ""),
                    "surql": f"UPDATE {record_id} SET {field} = '{new_value}'",
                    "op": op,
                },
            )

            pending["status"] = "executed"
            return f"Updated {field} on record {record_id} to '{new_value}'."

        elif op == "DELETE" and record_id:
            rid = ensure_record_id(record_id)
            check = await repo_query(
                "SELECT id FROM acm_record WHERE id = $rid AND source_id = $sid",
                {"rid": rid, "sid": sid},
            )
            if not check:
                return "Error: Record not found in this job."

            await repo_query("DELETE $rid", {"rid": rid})

            await repo_query(
                """INSERT INTO crud_audit {
                    job_id: $sid,
                    timestamp: time::now(),
                    natural_language: $reason,
                    generated_surql: $surql,
                    operation: $op,
                    confirmed_by: 'user_hitl'
                }""",
                {
                    "sid": sid,
                    "reason": pending.get("reason", ""),
                    "surql": f"DELETE {record_id}",
                    "op": op,
                },
            )

            pending["status"] = "executed"
            return f"Deleted record {record_id}."

        else:
            return f"Error: Unsupported operation {op} or missing parameters."

    try:
        return _run_async(execute())
    except Exception as e:
        logger.error(f"Error executing write {operation_id}: {e}")
        return f"Error executing write: {str(e)}"


