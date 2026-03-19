# MCS13: Fix Schema Inference DocumentMeta Bug + Format Profile Cache
# Generated from MCS7 validation audit — 2026-03-19

**SP: 3 | Priority: P1 | Dependencies: MCS8 (ghost save fix)**
**Audit ref: MCS7 validation — schema inference failed with AttributeError**
**Related commits: 167f0c43 (schema inference node), 881f04f1 (format profile registry), fa1ff9a4 (validation)**

## Skills to Load

/systematic-debugging — root cause the DocumentMeta attribute error
/langgraph-fundamentals — graph state typing for Pydantic models
/planning-with-files — persistent markdown plan
/test-driven-development — write test for schema inference with DocumentMeta
/e2e-test — verify schema inference triggers on new format
/acm-observability — trace schema inference decisions
/verification-before-completion — verify cache hit/miss behavior

---

## Problem Statement

During MCS7 validation, the `schema_inference_node` failed with:
```
AttributeError: 'DocumentMeta' object has no attribute 'get'
```

The node at lines 463-465 calls:
```python
state.get("document_metadata", {}).get("format_name")
```

But `state["document_metadata"]` is a `DocumentMeta` Pydantic model, not a dict. `.get()` doesn't exist on Pydantic models — should use `getattr()` or access attributes directly.

### Impact
- Schema inference never runs → no new format profiles created
- Only 1 format profile exists in DB (from a prior manual test)
- New consultant formats fall back to COLUMN_ALIASES instead of LLM inference
- MCS7 cache hit verification was impossible (no new profiles created)

---

## Key Files

**Read:**
- `open_notebook/extractors/schema_inference.py` — lines 344-674, the full node
- `open_notebook/extractors/metadata_and_structure.py` — DocumentMeta model definition
- `open_notebook/graphs/acm_extraction.py` — graph state schema
- `open_notebook/extractors/format_profile_repository.py` — cache hit/miss logic

**Modify:**
- `open_notebook/extractors/schema_inference.py` — fix all `.get()` calls on DocumentMeta (lines 463, 464, 487, 488, 547, 548)
- Replace `state.get("document_metadata", {}).get("format_name")` with proper attribute access

**Test:**
- `tests/test_schema_inference.py` (create or update) — test with DocumentMeta Pydantic model in state

---

## Plan

### Phase 1: Fix DocumentMeta Access Pattern
- [ ] Find all 6 occurrences of `.get()` on `document_metadata` in schema_inference.py
- [ ] Replace with `getattr(state.get("document_metadata"), "format_name", None)` or equivalent
- [ ] Handle both dict and Pydantic model cases (defensive)

### Phase 2: Test Schema Inference
- [ ] Write unit test with mock state containing DocumentMeta Pydantic model
- [ ] Verify schema inference produces InferredSchema with column_mapping
- [ ] Test cache hit path (existing format profile)
- [ ] Test cache miss path (new format → LLM inference → profile saved)

### Phase 3: Verify Cache Behavior
- [ ] Upload new consultant format PDF (e.g., Clutch_Broadmeadows.pdf)
- [ ] Verify schema inference triggers (confidence score in logs)
- [ ] Verify new format profile saved to SurrealDB
- [ ] Re-upload same format → verify cache hit (no LLM call)
- [ ] Verify `sample_count` incremented

### Phase 4: Verification
- [ ] Run /e2e-test for schema inference flow
- [ ] Run /acm-observability to trace inference decisions
- [ ] Verify format profiles in DB match expected consultant patterns

---

## Agent Strategy: Agent Team (Opus)

Create team `mcs13-schema-inference` with 3 agents:

| Agent | Role | Model | Tasks |
|-------|------|-------|-------|
| `inference-fixer` | Fix DocumentMeta access + schema inference logic | opus | Phase 1-2 |
| `cache-tester` | Test cache hit/miss behavior with real PDFs | opus | Phase 3 |
| `verifier` | E2E tests + observability traces | opus | Phase 4 |

---

## Verification Checklist

- [ ] `schema_inference_node` runs without AttributeError
- [ ] New format profile created in `consultant_format_profile` table
- [ ] Cache hit works: second upload of same format skips LLM
- [ ] `sample_count` increments on cache hit
- [ ] Column mapping contains correct SF field mappings
- [ ] `/e2e-test` passes for schema inference flow
- [ ] No `.get()` calls on Pydantic models in schema_inference.py

---

## Commit Template

```
fix(extraction): fix schema inference DocumentMeta attribute access and verify cache

- Replace .get() calls on Pydantic DocumentMeta with getattr()
- Schema inference now triggers correctly for new consultant formats
- Format profile cache hit/miss verified end-to-end
- MCS13 — from MCS7 validation finding

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>
```
