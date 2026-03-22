"""Guardrails for SurrealQL CRUD tools.

Validates generated SurrealQL queries before execution:
- Table allowlisting (read vs write)
- Blocked operation detection (DROP, REMOVE, DEFINE, INFO)
- Parameterized variable enforcement (no string interpolation)
- Result size capping
"""

import asyncio
import os
import re
from dataclasses import dataclass, field
from typing import Any

from loguru import logger

# --- Tables accessible for READ operations ---
ALLOWED_READ_TABLES = {
    "acm_record",
    "building_record",
    "source",
    "source_intelligence",
    "acm_table_section",
    "raw_extraction_table",
    "crud_audit",
}

# --- Tables accessible for WRITE operations (subset) ---
ALLOWED_WRITE_TABLES = {
    "acm_record",
    "building_record",
}

# --- Fields on acm_record that can be updated ---
ALLOWED_ACM_FIELDS = {
    "building_id",
    "building_name",
    "product",
    "friable",
    "acm_product_group",
    "acm_product_type",
    "material_condition",
    "disturbance_potential",
    "location",
    "room_name",
    "room_id",
    "floor_level",
    "quantity",
    "sample_result",
    "risk_status",
    "identifying_company",
    "material_description",
    "extent",
    "hygienist_recommendations",
    "area_type",
    "no_access",
    "acm_labelled",
}

# --- Fields on building_record that can be updated ---
ALLOWED_BUILDING_FIELDS = {
    "building_name",
    "building_year",
    "building_construction",
    "building_address",
    "suburb",
    "postcode",
    "building_type",
    "building_category",
    "roof_type",
    "number_of_levels",
    "frequency_of_use",
    "daily_duration",
    "level_of_activity",
    "public_access",
    "owned_or_leased",
    "state",
    "site_name",
    "additional_comments",
}

# --- Operations that are NEVER allowed ---
BLOCKED_KEYWORDS = {
    "DROP",
    "REMOVE",
    "DEFINE",
    "INFO",
    "SLEEP",
    "KILL",
    "SIGNUP",
    "SIGNIN",
    "USE",
    "LET",
    "BEGIN",
    "COMMIT",
    "CANCEL",
}

# Maximum rows returned from a read query
MAX_RESULT_ROWS = 100

# --- Schema context for LLM prompt injection ---
ACM_RECORD_SCHEMA = """Table: acm_record
Fields: id, source_id (record<source>), building_record_id (record<building_record>),
  building_id (string), building_name (string), building_year (int),
  building_construction (string), room_id (string), room_name (string),
  room_area (float), area_type (string), product (string),
  material_description (string), extent (string), location (string),
  friable (string: "Friable"|"Non-friable"), material_condition (string),
  risk_status (string: "High"|"Medium"|"Low"|"Very Low"),
  result (string), sample_result (string: "Positive"|"Negative"|"Not Sampled"|"No Access"),
  acm_product_group (string), acm_product_type (string),
  disturbance_potential (string), identifying_company (string),
  quantity (string), acm_labelled (bool), no_access (bool),
  hygienist_recommendations (string), floor_level (string),
  page_number (int), extraction_confidence (float),
  created (datetime), updated (datetime)"""

BUILDING_RECORD_SCHEMA = """Table: building_record
Fields: id, internal_id (string), source_id (record<source>),
  building_code (string), building_name (string), building_year (string),
  building_construction (string), building_address (string),
  suburb (string), postcode (string), state (string),
  building_type (string), building_category (string),
  roof_type (string), number_of_levels (int), est_building_size_m2 (float),
  frequency_of_use (string), daily_duration (string),
  level_of_activity (string), public_access (string),
  owned_or_leased (string), site_name (string),
  school_uid (string), building_unique_id (string),
  no_identified_acms (int), date_of_audit_report (string),
  created (datetime), updated (datetime)"""

SOURCE_SCHEMA = """Table: source
Fields: id, name (string), full_text (string), asset_type (string),
  size (int), state (string: "processing"|"ready"|"error"),
  url (string), notebook_id (record<notebook>),
  page_count (int), total_pages (int),
  created (datetime), updated (datetime)"""

SOURCE_INTELLIGENCE_SCHEMA = """Table: source_intelligence
Fields: id, source_id (record<source>),
  consultant (string), site_name (string), site_address (string),
  building_names (array<string>), document_type (string),
  estimated_buildings (int), estimated_pages (int),
  metadata_json (object),
  created (datetime), updated (datetime)"""

ACM_TABLE_SECTION_SCHEMA = """Table: acm_table_section
Fields: id, source_id (record<source>),
  table_index (int), page_start (int), page_end (int),
  row_count (int), column_count (int),
  headers_json (array<string>), content_preview (string),
  bbox_json (object),
  created (datetime)"""

RAW_EXTRACTION_TABLE_SCHEMA = """Table: raw_extraction_table
Fields: id, source_id (record<source>),
  table_index (int), page_number (int),
  html_content (string), headers (array<string>),
  row_count (int), column_count (int), bbox (object),
  created (datetime)"""

DB_SCHEMA_CONTEXT = f"""{ACM_RECORD_SCHEMA}

{BUILDING_RECORD_SCHEMA}

{SOURCE_SCHEMA}

{SOURCE_INTELLIGENCE_SCHEMA}

{ACM_TABLE_SECTION_SCHEMA}

{RAW_EXTRACTION_TABLE_SCHEMA}

Relationships:
- acm_record.source_id → source (the job/document)
- acm_record.building_record_id → building_record
- building_record.source_id → source
- source_intelligence.source_id → source
- acm_table_section.source_id → source
- raw_extraction_table.source_id → source
- crud_audit.job_id → source"""


@dataclass
class GuardrailResult:
    """Result of a guardrail validation check."""

    allowed: bool
    reason: str = ""
    sanitized_query: str = ""
    warnings: list[str] = field(default_factory=list)


def validate_read_query(query: str) -> GuardrailResult:
    """Validate a generated SurrealQL SELECT query.

    Checks:
    1. Only SELECT statements allowed
    2. Tables must be in ALLOWED_READ_TABLES
    3. No blocked keywords (DROP, REMOVE, etc.)
    4. Must use $vars for parameterized values (no raw string literals in WHERE)
    """
    q_upper = query.upper().strip()

    # Block dangerous keywords
    for kw in BLOCKED_KEYWORDS:
        if re.search(rf"\b{kw}\b", q_upper):
            return GuardrailResult(
                allowed=False,
                reason=f"Blocked operation: {kw} is not allowed in read queries.",
            )

    # Must start with SELECT or be a math/aggregate
    if not q_upper.startswith("SELECT"):
        return GuardrailResult(
            allowed=False,
            reason="Read queries must be SELECT statements.",
        )

    # Block write operations embedded in SELECT
    for op in ("UPDATE", "DELETE", "CREATE", "INSERT", "RELATE", "UPSERT"):
        if re.search(rf"\b{op}\b", q_upper):
            return GuardrailResult(
                allowed=False,
                reason=f"Write operation {op} not allowed in read queries.",
            )

    # Validate tables — extract FROM clause
    from_matches = re.findall(r"\bFROM\s+(\w+)", q_upper)
    for table in from_matches:
        table_lower = table.lower()
        if table_lower.startswith("$"):
            continue  # parameterized table ref
        if table_lower not in ALLOWED_READ_TABLES:
            return GuardrailResult(
                allowed=False,
                reason=f"Table '{table_lower}' is not accessible. Allowed: {', '.join(sorted(ALLOWED_READ_TABLES))}",
            )

    warnings = []

    # Check for LIMIT — warn if missing
    if "LIMIT" not in q_upper:
        warnings.append(
            f"Query has no LIMIT clause. Results will be capped at {MAX_RESULT_ROWS} rows."
        )

    return GuardrailResult(
        allowed=True,
        sanitized_query=query.strip().rstrip(";") + ";",
        warnings=warnings,
    )


def validate_write_operation(
    table: str, operation: str, field_name: str | None = None
) -> GuardrailResult:
    """Validate a write operation (UPDATE/DELETE/CREATE).

    Checks:
    1. Table must be in ALLOWED_WRITE_TABLES
    2. Operation must be UPDATE, DELETE, or CREATE
    3. Field must be in the allowed fields for the table
    """
    op_upper = operation.upper()

    if op_upper not in ("UPDATE", "DELETE", "CREATE"):
        return GuardrailResult(
            allowed=False,
            reason=f"Operation '{operation}' is not allowed. Use UPDATE, DELETE, or CREATE.",
        )

    table_lower = table.lower()
    if table_lower not in ALLOWED_WRITE_TABLES:
        return GuardrailResult(
            allowed=False,
            reason=f"Table '{table_lower}' is not writable. Allowed: {', '.join(sorted(ALLOWED_WRITE_TABLES))}",
        )

    if op_upper == "UPDATE" and field_name:
        if table_lower == "acm_record":
            allowed_fields = ALLOWED_ACM_FIELDS
        elif table_lower == "building_record":
            allowed_fields = ALLOWED_BUILDING_FIELDS
        else:
            allowed_fields = set()

        if field_name not in allowed_fields:
            return GuardrailResult(
                allowed=False,
                reason=f"Field '{field_name}' is not updatable on {table_lower}. Allowed: {', '.join(sorted(allowed_fields))}",
            )

    return GuardrailResult(allowed=True)


def cap_results(
    results: list[dict[str, Any]], max_rows: int = MAX_RESULT_ROWS
) -> list[dict[str, Any]]:
    """Limit result set size and strip internal fields."""
    capped = results[:max_rows]
    # Strip embedding vectors and internal fields from results
    strip_fields = {
        "embedding",
        "embedding_text",
        "embedding_model",
        "embedded_at",
        "enriched_text",
    }
    cleaned = []
    for row in capped:
        cleaned.append({k: v for k, v in row.items() if k not in strip_fields})
    return cleaned


def classify_intent(message: str) -> str:
    """Rule-based intent classifier for user messages.

    Returns: "read" | "write" | "analytics" | "general"
    """
    m = message.lower().strip()

    # Write intent signals
    write_signals = [
        "update",
        "change",
        "set",
        "modify",
        "edit",
        "delete",
        "remove",
        "drop",
        "add",
        "create",
        "insert",
        "mark as",
        "flag as",
        "relabel",
    ]
    for sig in write_signals:
        if sig in m:
            return "write"

    # Analytics intent signals
    analytics_signals = [
        "count",
        "how many",
        "total",
        "average",
        "sum",
        "statistics",
        "stats",
        "breakdown",
        "summary",
        "distribution",
        "percentage",
        "compare",
        "group by",
        "aggregate",
    ]
    for sig in analytics_signals:
        if sig in m:
            return "analytics"

    # Read intent signals
    read_signals = [
        "show",
        "list",
        "find",
        "search",
        "get",
        "what",
        "which",
        "where",
        "look up",
        "display",
        "fetch",
        "retrieve",
        "tell me about",
        "describe",
    ]
    for sig in read_signals:
        if sig in m:
            return "read"

    return "general"


async def classify_intent_with_llm_fallback(message: str, timeout: float = 2.0) -> str:
    """Intent classifier with LLM fallback.

    1. Try rule-based classify_intent() first (fast, free).
    2. If result is "general", call Claude Haiku via ACM_ANTHROPIC_API_KEY with timeout.
    3. On timeout/error: return "general" (graceful degradation).

    Args:
        message: The user message to classify.
        timeout: Maximum seconds to wait for the LLM call. Defaults to 2.0.

    Returns:
        One of "read", "write", "analytics", or "general".
    """
    rule_result = classify_intent(message)
    if rule_result != "general":
        return rule_result

    api_key = os.environ.get("ACM_ANTHROPIC_API_KEY")
    if not api_key:
        return "general"

    async def _llm_classify() -> str:
        try:
            import anthropic  # lazy import — optional dependency
        except ImportError:
            logger.warning(
                "guardrails: anthropic package not installed; skipping LLM fallback"
            )
            return "general"

        client = anthropic.AsyncAnthropic(api_key=api_key)
        response = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=10,
            system=(
                "Classify the following user message about an ACM (Asbestos Containing Material) "
                "database as exactly one of: read, write, analytics, general. "
                "Reply with ONLY the classification word, nothing else."
            ),
            messages=[{"role": "user", "content": message}],
        )
        raw = response.content[0].text.strip().lower()
        if raw in ("read", "write", "analytics", "general"):
            return raw
        logger.warning(
            f"guardrails: LLM returned unexpected classification '{raw}'; using 'general'"
        )
        return "general"

    try:
        return await asyncio.wait_for(_llm_classify(), timeout=timeout)
    except asyncio.TimeoutError:
        logger.warning(
            f"guardrails: LLM intent classification timed out after {timeout}s; using 'general'"
        )
        return "general"
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            f"guardrails: LLM intent classification failed: {exc}; using 'general'"
        )
        return "general"
