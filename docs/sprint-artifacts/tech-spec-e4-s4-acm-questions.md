# Tech Spec: E4-S4 - Support ACM-Specific Questions

> **Story:** E4-S4
> **Epic:** Chat with ACM Context
> **Status:** Done
> **Created:** 2025-12-08

---

## Overview

Enhance the chat system prompt to help the AI correctly interpret and answer ACM-specific questions about buildings, rooms, risk levels, and asbestos terminology.

---

## User Story

**As a** user
**I want** to ask natural questions like "What's the risk level in Building A?"
**So that** I get useful answers without complex queries

---

## Acceptance Criteria

- [x] AI correctly interprets building/room references
- [x] AI summarizes risk status when asked
- [x] AI explains ACM terminology when asked
- [x] AI references policy sections when relevant

---

## Technical Design

### 1. Enhanced System Prompt

Location: `api/routers/source_chat.py`

```python
ACM_SYSTEM_PROMPT = """You are an AI assistant helping users understand ACM (Asbestos Containing Material) Register data.

## ACM Domain Knowledge

### Key Terms
- **ACM**: Asbestos Containing Material
- **SAMP**: Site Asbestos Management Plan
- **Friable**: Asbestos that can be crumbled by hand, releasing fibers (higher risk)
- **Non-Friable**: Asbestos that is bonded and less likely to release fibers
- **Risk Status**: Low (safe, no action), Medium (monitor), High (immediate action required)

### Risk Assessment Factors
- Material condition (Good, Fair, Poor)
- Friability (Friable materials are higher risk)
- Location (accessible areas are higher risk)
- Likelihood of disturbance

### Common Questions and How to Answer

1. **Building/Room queries**: "What's in Building A?" or "Show me Room 101"
   - Filter the ACM data to match the location
   - List all ACM items found there
   - Highlight any high-risk items

2. **Risk summaries**: "What are the high-risk items?" or "Is the school safe?"
   - Group and count by risk status
   - Highlight any High risk items with their locations
   - Provide context about what the risk levels mean

3. **Terminology questions**: "What is friable asbestos?"
   - Explain the term in plain language
   - Relate to the data if applicable

4. **Compliance questions**: "Do we need to remove anything?"
   - High risk items typically require remediation
   - Medium risk items need monitoring
   - Recommend consulting a licensed assessor for specific advice

## Response Guidelines

- Always cite specific records using [acm:record_id:field_name] format
- When summarizing, include counts and locations
- If asked about safety, be cautious and recommend professional assessment
- Use tables for multi-item responses when appropriate

## Example Responses

User: "What's in Building A1?"
Assistant: "Building A1 contains 3 ACM items:
| Room | Product | Risk |
|------|---------|------|
| A101 | Floor Tiles [acm:rec123:product] | Low |
| A102 | Ceiling Tiles [acm:rec124:product] | Medium |
| A103 | Pipe Lagging [acm:rec125:product] | High |

The pipe lagging in A103 is High risk due to its friable condition."

User: "Is the school safe?"
Assistant: "Based on the ACM Register:
- 15 Low risk items (no action needed)
- 5 Medium risk items (monitoring required)
- 2 High risk items (action recommended)

The two High risk items in Building B2 should be assessed by a licensed professional. For specific safety determinations, consult your occupational health advisor."
"""
```

### 2. Question Pattern Detection

Optional: Detect question types for better routing:

```python
import re

def detect_question_type(message: str) -> str:
    """Detect the type of ACM question being asked."""
    message_lower = message.lower()

    # Location queries
    if re.search(r'\b(building|room|area|floor|wing)\b', message_lower):
        return 'location_query'

    # Risk queries
    if re.search(r'\b(risk|danger|safe|hazard|high risk)\b', message_lower):
        return 'risk_query'

    # Terminology queries
    if re.search(r'\b(what is|what are|define|explain|meaning)\b', message_lower):
        return 'terminology_query'

    # Action queries
    if re.search(r'\b(remove|action|do we need|should we|remediat)\b', message_lower):
        return 'action_query'

    # Summary queries
    if re.search(r'\b(summary|overview|total|count|how many)\b', message_lower):
        return 'summary_query'

    return 'general'
```

### 3. Context Formatting for Question Types

```python
def format_acm_context_for_question(
    records: List[ACMRecord],
    question_type: str
) -> str:
    """Format ACM context based on question type."""

    if question_type == 'risk_query':
        # Group by risk status
        by_risk = {}
        for r in records:
            risk = r.risk_status or 'Unknown'
            by_risk.setdefault(risk, []).append(r)

        lines = ["## ACM Risk Summary"]
        for risk in ['High', 'Medium', 'Low', 'Unknown']:
            if risk in by_risk:
                lines.append(f"\n### {risk} Risk ({len(by_risk[risk])} items)")
                for r in by_risk[risk][:5]:  # Limit per category
                    lines.append(f"- {r.building_id}/{r.room_id}: {r.product}")
        return "\n".join(lines)

    elif question_type == 'location_query':
        # Group by location
        by_building = {}
        for r in records:
            by_building.setdefault(r.building_id, []).append(r)

        lines = ["## ACM by Location"]
        for building, items in by_building.items():
            lines.append(f"\n### {building}")
            for r in items:
                lines.append(f"- {r.room_id}: {r.product} ({r.risk_status})")
        return "\n".join(lines)

    else:
        # Default: table format
        return format_acm_as_table(records)
```

---

## File Changes

| File | Change |
|------|--------|
| `api/routers/source_chat.py` | Add ACM system prompt |
| `api/utils/acm_context.py` | New - context formatting utils |

---

## Dependencies

- E4-S1: ACM records in chat context
- E4-S3: ACM-aware responses with citations

---

## Testing

### Test Questions

1. **Location query**: "What asbestos is in Building A?"
   - Verify response lists items in Building A
   - Verify citations included

2. **Risk query**: "What are the high-risk items?"
   - Verify High risk items highlighted
   - Verify locations included

3. **Terminology**: "What does friable mean?"
   - Verify definition provided
   - Verify related data shown if applicable

4. **Safety query**: "Is this building safe?"
   - Verify cautious response
   - Verify professional assessment recommended

5. **Summary query**: "Give me an overview"
   - Verify counts by risk
   - Verify building summary

---

## Estimated Complexity

**Medium** - Primarily prompt engineering with optional pattern detection

---

## Dev Agent Record

### Implementation Date: 2026-01-11

### Implementation Notes

1. **Enhanced System Prompt** (`prompts/source_chat.jinja`):
   - Added comprehensive "Common ACM Question Types and How to Answer" section
   - Included 5 question type patterns: Location, Risk, Terminology, Action/Compliance, Summary
   - Added 4 detailed example responses showing proper formatting for different query types
   - Enhanced Response Guidelines with tables and professional assessment recommendations

2. **New Utility Module** (`api/utils/acm_context.py`):
   - Created `detect_question_type()` function to classify ACM questions
   - Created `format_acm_context_for_question()` to format context based on question type
   - Implemented formatting functions: `_format_risk_summary()`, `_format_by_location()`, `_format_summary()`, `_format_as_table()`

3. **Test Coverage** (`tests/test_acm_chat_context.py`):
   - Added `TestQuestionPatternDetection` class with 6 test methods
   - Added `TestACMContextFormatting` class with 5 test methods
   - Added `TestACMQuestionExamples` class with 6 test methods
   - All 36 tests pass (17 new + 19 existing)

### File List

| File | Status |
|------|--------|
| `prompts/source_chat.jinja` | Modified |
| `api/utils/__init__.py` | New |
| `api/utils/acm_context.py` | New |
| `tests/test_acm_chat_context.py` | Modified |

### Change Log

- 2026-01-11: Implemented E4-S4 - Enhanced system prompt with ACM question handling patterns and examples. Created utility module with question detection and context formatting. Added comprehensive test coverage.
- 2026-01-11: Code Review Fixes Applied:
  - **HIGH**: Integrated utility module (`detect_question_type`, `format_acm_context_for_question`) into actual chat flow in `source_chat.py`
  - **MEDIUM**: Added policy reference guidance section to prompt template
  - **MEDIUM**: Replaced duplicate ACMRecord class with Protocol for flexibility with domain model
  - **MEDIUM**: Added proper exports to `api/utils/__init__.py`
  - **LOW**: Fixed grammar "1 items" → "1 item" with proper pluralization
  - **LOW**: Updated test file docstring to reference all related stories

### Updated File List

| File | Status |
|------|--------|
| `prompts/source_chat.jinja` | Modified (prompt + policy guidance) |
| `open_notebook/graphs/source_chat.py` | Modified (integration) |
| `api/utils/__init__.py` | Modified (exports) |
| `api/utils/acm_context.py` | Modified (Protocol type) |
| `tests/test_acm_chat_context.py` | Modified (docstring + tests) |

---