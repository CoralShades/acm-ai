"""LLM-based intent classification with entity extraction.

Enhances the rule-based classify_intent() from guardrails.py by adding:
1. Entity extraction (building names, room names, risk levels, materials, record IDs)
2. More granular intent classification
3. LLM fallback for ambiguous queries with structured JSON output

The router result is used to:
- Pre-filter tool candidates (reduce tool calls)
- Inject extracted entities as hints in the system prompt
- Speed up tool execution by providing pre-parsed parameters
"""

import asyncio
import json
import os
from dataclasses import dataclass, field
from typing import Optional

from loguru import logger

from open_notebook.graphs.guardrails import classify_intent


@dataclass
class RouterResult:
    """Result of intent classification + entity extraction."""

    intent: str  # read, write, analytics, search, meta, general
    entities: dict = field(default_factory=dict)
    confidence: float = 0.0
    source: str = "rule"  # "rule" or "llm"


# --- Entity extraction patterns (rule-based, fast) ---

_BUILDING_PATTERNS = [
    r"building\s+([A-Z][a-zA-Z0-9\s-]*?)(?:\s+(?:has|with|in|and|$))",
    r"(?:BLD|bld)\s*#?\s*([A-Z0-9_-]+)",
    r"in\s+(?:building\s+)?([A-Z][a-zA-Z0-9\s]*?)(?:\s+(?:has|with|and|$))",
]

_RISK_LEVELS = {"high", "medium", "low", "very low"}
_MATERIAL_KEYWORDS = {
    "vinyl",
    "cement",
    "asbestos",
    "insulation",
    "lagging",
    "tile",
    "pipe",
    "ceiling",
    "floor",
    "sheeting",
    "board",
    "fibro",
    "chrysotile",
    "amosite",
    "crocidolite",
}


def _extract_entities_rule(message: str) -> dict:
    """Extract entities from a message using regex patterns."""
    import re

    entities: dict = {
        "buildings": [],
        "rooms": [],
        "risk_levels": [],
        "materials": [],
        "record_ids": [],
    }

    m = message.lower()

    # Risk levels
    for level in _RISK_LEVELS:
        if level in m:
            entities["risk_levels"].append(level.title())

    # Materials
    for kw in _MATERIAL_KEYWORDS:
        if kw in m:
            entities["materials"].append(kw)

    # Record IDs (acm_record:xxx, building_record:xxx)
    for match in re.finditer(r"((?:acm_record|building_record):[a-z0-9]+)", m):
        entities["record_ids"].append(match.group(1))

    # Buildings
    for pattern in _BUILDING_PATTERNS:
        for match in re.finditer(pattern, message, re.IGNORECASE):
            name = match.group(1).strip()
            if name and len(name) > 1 and name not in entities["buildings"]:
                entities["buildings"].append(name)

    # Rooms (basic patterns)
    room_match = re.search(
        r"(?:room|office|classroom|lab|hall)\s+([A-Z0-9][A-Za-z0-9\s.-]*?)(?:\s|$|,|\.|;)",
        message,
        re.IGNORECASE,
    )
    if room_match:
        entities["rooms"].append(room_match.group(1).strip())

    # Filter empty lists
    return {k: v for k, v in entities.items() if v}


def classify_with_entities(message: str) -> RouterResult:
    """Fast rule-based classification with entity extraction.

    This is the primary path — called synchronously from the agent node.
    No LLM calls, no async, no latency.
    """
    intent = classify_intent(message)
    entities = _extract_entities_rule(message)

    # Boost confidence for clear intents
    confidence = 0.9 if intent != "general" else 0.5

    # Additional meta intent detection
    m = message.lower()
    if any(kw in m for kw in ["schema", "fields", "what can i edit", "valid values"]):
        intent = "meta"
        confidence = 0.95
    elif any(kw in m for kw in ["undo", "revert", "rollback", "undo last"]):
        intent = "write"
        confidence = 0.95
    elif any(kw in m for kw in ["search", "find", "look for", "where is"]):
        intent = "search"
        confidence = 0.85
    elif any(kw in m for kw in ["document", "report", "pdf", "what does the report"]):
        intent = "search"
        confidence = 0.8

    return RouterResult(
        intent=intent,
        entities=entities,
        confidence=confidence,
        source="rule",
    )


async def classify_with_llm(
    message: str, timeout: float = 3.0
) -> RouterResult:
    """LLM-based classification with entity extraction.

    Uses Claude Haiku for structured JSON output when the rule-based
    classifier returns low confidence. Falls back to rule-based on error.

    Args:
        message: The user message to classify.
        timeout: Maximum seconds for the LLM call.
    """
    # Always start with rules
    rule_result = classify_with_entities(message)

    # If rules are confident, skip LLM
    if rule_result.confidence >= 0.8:
        return rule_result

    # Try LLM for ambiguous queries
    api_key = os.environ.get("ACM_ANTHROPIC_API_KEY")
    if not api_key:
        return rule_result

    try:
        import anthropic
    except ImportError:
        return rule_result

    async def _call_llm() -> RouterResult:
        client = anthropic.AsyncAnthropic(api_key=api_key)
        response = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            system=(
                "You classify ACM (Asbestos Containing Material) database queries.\n"
                "Return ONLY a JSON object with:\n"
                '- "intent": one of "read", "write", "analytics", "search", "meta", "general"\n'
                '- "entities": {"buildings": [...], "rooms": [...], "risk_levels": [...], '
                '"materials": [...], "record_ids": [...]}\n'
                "Only include non-empty entity arrays.\n"
                "Example: user says 'show high risk records in Building A'\n"
                '→ {"intent": "read", "entities": {"buildings": ["Building A"], "risk_levels": ["High"]}}'
            ),
            messages=[{"role": "user", "content": message}],
        )
        text = response.content[0].text.strip()

        # Parse JSON response
        try:
            data = json.loads(text)
            return RouterResult(
                intent=data.get("intent", rule_result.intent),
                entities=data.get("entities", rule_result.entities),
                confidence=0.9,
                source="llm",
            )
        except json.JSONDecodeError:
            # If LLM returns plain text intent
            if text.lower() in ("read", "write", "analytics", "search", "meta", "general"):
                return RouterResult(
                    intent=text.lower(),
                    entities=rule_result.entities,
                    confidence=0.8,
                    source="llm",
                )
            return rule_result

    try:
        return await asyncio.wait_for(_call_llm(), timeout=timeout)
    except (asyncio.TimeoutError, Exception) as e:
        logger.debug(f"LLM router fallback to rules: {e}")
        return rule_result


def build_entity_hint(result: RouterResult) -> str:
    """Build a natural language hint from extracted entities for the system prompt."""
    parts = []
    entities = result.entities

    if entities.get("buildings"):
        parts.append(f"Buildings mentioned: {', '.join(entities['buildings'])}")
    if entities.get("rooms"):
        parts.append(f"Rooms mentioned: {', '.join(entities['rooms'])}")
    if entities.get("risk_levels"):
        parts.append(f"Risk levels: {', '.join(entities['risk_levels'])}")
    if entities.get("materials"):
        parts.append(f"Materials: {', '.join(entities['materials'])}")
    if entities.get("record_ids"):
        parts.append(f"Record IDs: {', '.join(entities['record_ids'])}")

    if not parts:
        return ""

    return "\n\nExtracted context from user message:\n" + "\n".join(f"- {p}" for p in parts)
