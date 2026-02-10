# Tech-Spec: E4-S3 ACM-Aware Chat Responses

**Created:** 2025-12-07
**Status:** Done
**Epic:** E4 - Chat with ACM Context
**Story:** S3 - Generate ACM-Aware Chat Responses

---

## Overview

### Problem Statement

When ACM data is in context, the AI needs to understand ACM terminology and cite specific records using `[acm:...]` format. Currently, the system prompt doesn't include ACM-specific guidance.

### Solution

Update the system prompt in the chat handler to:
- Explain ACM domain concepts
- Instruct use of `[acm:record_id:field]` citation format
- Provide examples of how to answer ACM questions

### Scope

**In Scope:**
- Update system prompt with ACM guidance
- Citation format instructions
- Domain terminology explanations

**Out of Scope:**
- Fine-tuning models
- Complex multi-turn reasoning

---

## Implementation Plan

### Tasks

- [x] **Task 1: Analyze existing system prompt**
  - Read chat handler code
  - Understand prompt structure

- [x] **Task 2: Create ACM prompt section**
  - Explain ACM/asbestos concepts
  - Define risk levels (Low/Medium/High)
  - Explain friable vs non-friable

- [x] **Task 3: Add citation format instructions**
  - Format: `[acm:record_id:field]`
  - When to use citations
  - Examples

- [x] **Task 4: Test with sample questions**
  - "What's the risk level in Building A?"
  - "Are there friable materials?"
  - "Summarize high-risk items"

### Acceptance Criteria

- [x] **AC1**: AI responses include `[acm:...]` citations (prompt instructs to use format)
- [ ] **AC2**: Citations are clickable in chat (requires E3-S3 citation parser - separate story)
- [x] **AC3**: AI answers domain questions accurately (prompt includes domain knowledge)
- [x] **AC4**: System prompt includes ACM guidance

---

## Code Specification

### ACM System Prompt Addition

```python
ACM_SYSTEM_PROMPT = """
## ACM (Asbestos Containing Material) Context

When ACM Register data is included in context, you are helping analyze asbestos survey data. Key concepts:

**Risk Levels:**
- High: Friable materials in poor condition, immediate action needed
- Medium: Non-friable materials or good condition friable, monitor and plan
- Low: Stable materials, routine monitoring only

**Material Types:**
- Friable: Can crumble by hand, higher risk of fiber release
- Non-Friable: Bonded materials, lower risk when undisturbed

**Citation Format:**
When referencing specific ACM data, use: [acm:record_id:field_name]
Example: "The floor tiles in Room B00A-R001 are [acm:acm_record:abc123:result]"

**Response Guidelines:**
1. Cite specific records when stating facts about materials
2. Summarize risk distribution when asked about safety
3. Group findings by building/room when relevant
4. Explain technical terms if user seems unfamiliar
"""
```

### Integration Point

```python
# In chat context builder
if include_acm_context and acm_records_exist:
    system_prompt += ACM_SYSTEM_PROMPT
```

---

## Dependencies

| Dependency | Type | Notes |
|------------|------|-------|
| E4-S1 (ACM in Context) | Story | ACM data available |
| E3-S3 (Citation Parser) | Story | Parse citations |

---

## Dev Agent Record

### Implementation Notes

The implementation uses a Jinja2 template approach with conditional ACM sections that are only rendered when `context_indicators.acm_records_included` is populated. This is more flexible than the simple string concatenation shown in the spec.

Key implementation details:
- ACM guidance is conditionally included via Jinja2 `{% if %}` blocks
- Frontend provides a toggle switch to enable/disable ACM context per-source
- Toggle state is persisted in sessionStorage per source
- New `@radix-ui/react-switch` dependency added for toggle component

### File List

| File | Change Type | Description |
|------|-------------|-------------|
| `prompts/source_chat.jinja` | Modified | Added conditional ACM guidance sections (Risk Levels, Material Types, Key Terms, Citation Format, Response Guidelines, Examples) |
| `open_notebook/graphs/source_chat.py` | Modified | Added `include_acm_context` to state, integrated ACM context fetching |
| `api/routers/source_chat.py` | Modified | Added `include_acm_context` field to `SendMessageRequest`, passed through to streaming handler |
| `frontend/src/components/source/ChatPanel.tsx` | Modified | Added ACM context toggle switch with sessionStorage persistence, status indicators |
| `frontend/src/components/ui/switch.tsx` | Added | New Radix UI Switch component for ACM toggle |
| `frontend/src/lib/hooks/useSourceChat.ts` | Modified | Added `includeAcmContext` parameter to `sendMessage` function |
| `frontend/src/lib/types/api.ts` | Modified | Added `include_acm_context` to request types |
| `frontend/src/lib/api/acm.ts` | Modified | Updated API types for ACM context |
| `frontend/src/app/(dashboard)/sources/[id]/page.tsx` | Modified | Pass `hasAcmData` and `sourceId` props to ChatPanel |
| `frontend/package.json` | Modified | Added `@radix-ui/react-switch: ^1.2.6` dependency |
| `frontend/package-lock.json` | Modified | Lock file updated with new dependency |
| `tests/test_acm_chat_context.py` | Added | 19 unit tests for ACM context integration and prompt template |

### Change Log

| Date | Author | Change |
|------|--------|--------|
| 2026-01-09 | Dev Agent | Initial implementation of ACM-aware system prompt |
| 2026-01-09 | Dev Agent | Added frontend toggle for ACM context |
| 2026-01-09 | Dev Agent | Added 19 unit tests for ACM prompt template |
| 2026-01-11 | Code Review | Added Dev Agent Record, fixed SSE media type, fixed sessionStorage error handling |

### Test Evidence

```
tests/test_acm_chat_context.py: 19 passed
- TestFormatACMContext: 5 tests (context formatting, truncation, missing fields)
- TestSourceChatStateWithACM: 1 test (state includes flag)
- TestFormatSourceContextWithACM: 1 test (ACM section included)
- TestACMContextIntegration: 2 tests (integration behavior)
- TestSendMessageRequestWithACM: 2 tests (API request model)
- TestACMPromptTemplate: 8 tests (prompt template rendering)
```

---

*Tech-Spec generated by create-tech-spec workflow*
