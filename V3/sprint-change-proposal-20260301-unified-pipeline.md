# Sprint Change Proposal: Unified Extraction Pipeline

> **SCP ID**: SCP-20260301-unified-pipeline
> **Date**: 2026-03-01
> **Author**: Demi (PM) + Claude Opus 4.6 (Architect analysis)
> **Status**: PROPOSED
> **Priority**: P0 — Architectural alignment + Alexander extraction blocker
> **Approach**: Surgical (Approach A) — 4 stories, ~1 sprint
> **Epic**: E29 (New) — Unified Extraction Pipeline

---

## 1. Problem Statement

### The Dual-Path Fork

ACM-AI's extraction pipeline has a conditional fork in `acm_extraction.py` that routes documents through two completely separate code paths:

```
tag_pages → should_use_orchestrator()?
  YES → orchestrate_extraction (per-building, parallel, Docling injection)
  NO  → prepare_context → extract_records (monolithic loop, no Docling injection)
```

**This violates Design Principle #1: "Unified Pipeline"** — stated in the architecture document as: *"Every document — regardless of format, consultant, or building count — flows through the same orchestrated pipeline."*

### Evidence of the Problem

| Document | Buildings | Path Taken | Accuracy | Docling Tables Injected? |
|----------|-----------|------------|----------|--------------------------|
| Broadmeadows | 1 | Legacy (`extract_records`) | 31/31 (100%) | **No** — orchestrator skipped |
| Alexander | 6 | Orchestrator (`orchestrate_extraction`) | 0/43 → 29/43 (post E27) | Yes |

**Key findings from project artifacts:**

1. **E26-S4 validation report** (2026-02-28): *"Docling table injection via `_get_docling_tables()` did NOT fire because the orchestrator was skipped."* Broadmeadows achieved 100% through content normalization + prompt improvements alone — it never benefits from the structured DataFrame context that powers the orchestrator.

2. **Alexander error log** (2026-02-28): Alexander extraction hits `extract_records:1408` (the **legacy** path), not the orchestrator. The JSON parser fails with `No JSON object found` because `claude-sonnet-4.6` wraps responses in markdown code fences (`` ```json ... ``` ``). The `parse_json_response()` brace-depth extractor cannot handle this.

3. **E1-S20 design doc**: The conditional fork was deliberately designed as "ADDITIONAL path, not replacement" for backward compatibility during the orchestrator rollout. This was the right decision at the time. But now that the orchestrator is proven (29/43 on Alexander post-E27, 100% on Broadmeadows when it does fire), the legacy path is tech debt.

### What the Dual-Path Causes

1. **Fixes don't propagate** — Docling injection only works on orchestrator path; JSON parser fixes only help legacy path
2. **Testing complexity** — Two paths to validate for every change
3. **Inconsistent building metadata** — Orchestrator tags records with building context; legacy path doesn't
4. **Dead code** — `prepare_context()`, `extract_records()` loop, chunking logic all become unnecessary
5. **Per-building export inconsistency** — Records from the legacy path lack consistent building_id for per-building/ACM exports

### Blocking Issue: JSON Parser Bug

The Alexander extraction (2026-02-28 final run) shows:

```
WARNING  | extract_records:1408 - Structured output extraction failed: provider error 524
INFO     | extract_records:1438 - Attempting fallback: direct model invocation
WARNING  | extract_records:1506 - Fallback JSON parsing failed: No JSON object found
         | Response preview: 'I'll systematically extract all ACM records...```json\n{\n "status"...'
```

**Root cause**: `claude-sonnet-4.6` (note: model upgraded from `claude-sonnet-4`) prefixes its response with conversational preamble and wraps JSON in markdown `` ```json `` fences. The `parse_json_response()` brace-depth extractor finds the opening `{` but doesn't strip the code fence context, causing the extracted text to include fence markers as part of the JSON string, or the fence closing to truncate before the JSON closes.

This is **separate from the pipeline unification** but must be fixed as a prerequisite.

---

## 2. Proposed Solution

### Target State: Single Path for All Documents

```
tag_pages → orchestrate_extraction (ALWAYS) → validate → correct → dedup → recover → save
```

The orchestrator handles every scenario:

| Scenario | Current Behavior | Proposed Behavior |
|----------|-----------------|-------------------|
| Multi-building + inventory | Orchestrator (per-building plans) | Same — unchanged |
| Single-building + inventory | Orchestrator (1-building plan) | Same — unchanged |
| No inventory (pre-extraction failed) | **Legacy path** | **Synthetic 1-building plan** → orchestrator |
| Single-building, no inventory | **Legacy path** | **Synthetic 1-building plan** → orchestrator |

**Synthetic single-building fallback:**

When `building_inventory` is `None` or empty (pre-extraction stages failed), the orchestrator creates:

```python
BuildingExtractionPlan(
    building_id="default",
    building_name=source.title or "Entire Document",
    strategy=ExtractionStrategy.FULL_LLM,
    page_range=(register_start_page or 1, total_pages),
    complexity="complex"
)
```

This routes the full document through the orchestrator's `extract_building()` function, which:
- Calls `_inject_docling_tables()` for DataFrame context (currently missing on legacy path)
- Uses the per-building prompt template (`building_extraction.jinja`)
- Produces records with consistent `building_id` metadata
- Benefits from all post-extraction quality stages identically

### Why This Is Low Risk

The orchestrator's `extract_building()` already does exactly what the legacy `extract_records()` does for a single chunk:
1. Assemble context (text + optional Docling DataFrames)
2. Call the LLM with extraction prompt
3. Parse JSON response
4. Validate with Pydantic

The only difference: the orchestrator scopes context to a building's page range. For a single-building document with a synthetic plan, the page range IS the entire register — functionally identical to the legacy path, but with Docling injection added.

---

## 3. Stories

### E29-S1: JSON Parser Resilience — Markdown Fence Handling

**Priority**: P0 (Blocker — must fix before unification)
**Size**: S (1 SP)
**Depends on**: Nothing
**Files**: `open_notebook/graphs/utils.py`, `tests/test_json_parser.py`

**Story**: As a system processing LLM responses, I want `parse_json_response()` to handle markdown code fence wrapping (`` ```json ... ``` ``), conversational preamble, and truncated responses, so that JSON extraction succeeds regardless of model response formatting.

**Acceptance Criteria**:

1. **AC-1**: `parse_json_response()` strips markdown code fences (`` ```json``, `` ``` ``) before brace-depth extraction
2. **AC-2**: Conversational preamble before JSON (e.g., "I'll extract all records...") does not affect JSON extraction
3. **AC-3**: Multiple JSON blocks in a single response: the largest complete JSON object is returned
4. **AC-4**: Truncated JSON (unclosed braces after fence stripping) raises a clear error, not "No JSON object found"
5. **AC-5**: Existing `parse_json_response()` behavior unchanged for responses without fences (backward compatible)
6. **AC-6**: Unit tests cover: fenced JSON, fenced with preamble, unfenced (pass-through), truncated, multiple blocks, nested fences

**Tasks**:

- [ ] 1.1 Add markdown fence stripping to `parse_json_response()` in `utils.py` (before brace-depth scan)
- [ ] 1.2 Handle multiple `` ```json `` blocks — extract content from each, return largest valid JSON
- [ ] 1.3 Improve error message for truncated JSON (include character position of unclosed brace)
- [ ] 1.4 Unit tests for all 6 ACs
- [ ] 1.5 Run `uv run pytest tests/ -x` — zero regression
- [ ] 1.6 Run `uv run ruff check .` — clean

**Claude Code Prompt**:

```
I need to fix the JSON parser in open_notebook/graphs/utils.py.

CONTEXT: The parse_json_response() function uses a brace-depth JSON extractor to find JSON
in LLM text responses. It's failing on claude-sonnet-4.6 responses because the model wraps
JSON in markdown code fences:

  I'll systematically extract all ACM records...
  ```json
  {
    "status": "valid",
    "records": [...]
  }
  ```

The brace-depth extractor can't handle the fence markers.

FIX NEEDED in parse_json_response() (utils.py, around line 213-252):
1. Before the brace-depth scan, strip markdown code fences:
   - Find all ```json ... ``` blocks using regex
   - Extract the content between fences
   - If multiple fence blocks exist, try each one (largest valid JSON wins)
   - If no fence blocks, fall back to current brace-depth behavior (backward compat)
2. Improve error for truncated JSON — instead of "No JSON object found", say
   "JSON appears truncated at position N (unclosed braces: M)"
3. Handle conversational preamble — the fence stripping naturally handles this

TESTS: Create/update tests/test_json_parser.py with:
- test_fenced_json: ```json { "key": "value" } ``` → parses correctly
- test_fenced_with_preamble: "Here are the results:\n```json\n{...}\n```" → parses correctly
- test_unfenced_passthrough: existing behavior unchanged
- test_truncated_json: clear error message
- test_multiple_fence_blocks: returns largest valid JSON
- test_nested_fences: handles edge case

VALIDATION:
- uv run pytest tests/test_json_parser.py -v
- uv run pytest tests/ -x --ignore=tests/test_broadmeadows_e2e.py
- uv run ruff check .

COMMIT: "fix: parse_json_response handles markdown code fences

claude-sonnet-4.6 wraps JSON in ```json fences with conversational preamble.
Brace-depth extractor now strips fences before scanning. Backward compatible.

Fixes: Alexander extraction JSON parse failure (2026-02-28)"
```

---

### E29-S2: Unified Orchestrator Path — Remove Legacy Fork

**Priority**: P0 (Core architectural fix)
**Size**: M (3 SP)
**Depends on**: E29-S1 (JSON parser must work for both paths during transition)
**Files**: `open_notebook/graphs/acm_extraction.py`, `open_notebook/extractors/orchestrator.py`, `tests/test_orchestrator.py`, `tests/test_acm_ai_extraction.py`

**Story**: As a system architect, I want every document to flow through the orchestrator path regardless of building count or pre-extraction results, so that the pipeline is truly unified and all documents benefit from Docling DataFrame injection, per-building context, and consistent building metadata.

**Acceptance Criteria**:

1. **AC-1**: The conditional edge `should_use_orchestrator()` is removed from the LangGraph state machine
2. **AC-2**: The `tag_pages` node always routes to `orchestrate_extraction` (no conditional)
3. **AC-3**: When `building_inventory` is `None` or empty, the orchestrator creates a synthetic single-building plan:
   - `building_id="default"`
   - `building_name=source.title or "Entire Document"`
   - `strategy=ExtractionStrategy.FULL_LLM`
   - `page_range=(register_start_page or 1, total_pages)`
4. **AC-4**: `_inject_docling_tables()` fires for all documents (including single-building)
5. **AC-5**: Existing `extract_building()` function handles synthetic plan identically to real plans
6. **AC-6**: The legacy `prepare_context → extract_records` loop path is unreachable (no edge routes to it)
7. **AC-7**: All existing orchestrator tests pass without modification
8. **AC-8**: Broadmeadows extraction via unified path produces ≥ 31 records (may get more from Docling injection)

**Tasks**:

- [ ] 2.1 In `orchestrate_extraction()` (orchestrator.py): add synthetic single-building fallback when `building_inventory` is None/empty
- [ ] 2.2 In `acm_extraction.py`: remove `should_use_orchestrator()` conditional edge
- [ ] 2.3 In `acm_extraction.py`: change graph wiring from conditional edge to direct edge: `tag_pages → orchestrate_extraction`
- [ ] 2.4 Ensure `_inject_docling_tables()` receives correct page range for synthetic plans (full document range)
- [ ] 2.5 Ensure `_get_docling_tables()` handles documents with no Docling tables gracefully (returns empty, non-fatal)
- [ ] 2.6 Update `ExtractionState` typing — remove `should_orchestrate` field if it exists
- [ ] 2.7 Unit tests: synthetic single-building plan creation, Docling injection with full range
- [ ] 2.8 Integration test: graph compiles with only orchestrator path (no legacy edge)
- [ ] 2.9 `uv run pytest tests/ -x` — zero regression
- [ ] 2.10 `uv run ruff check .` — clean

**Claude Code Prompt**:

```
I need to unify the ACM extraction pipeline by removing the legacy fork and making ALL
documents flow through the orchestrator.

CONTEXT:
The LangGraph state machine in open_notebook/graphs/acm_extraction.py has a conditional
edge after tag_pages:
  - should_use_orchestrator() → True → orchestrate_extraction
  - should_use_orchestrator() → False → prepare_context → extract_records (legacy loop)

This means single-building documents (like Broadmeadows) never go through the orchestrator,
never get Docling DataFrame injection, and use a completely separate code path.

TARGET STATE:
  tag_pages → orchestrate_extraction (ALWAYS) → validate → correct → dedup → recover → save

CHANGES NEEDED:

1. In orchestrator.py — orchestrate_extraction() function:
   Add a synthetic single-building fallback at the TOP of the function. If building_inventory
   is None or empty or has 0 buildings:
   ```python
   if not building_inventory or not building_inventory.buildings:
       # Create synthetic single-building plan for the entire document
       register_start = state.get("register_start_page", 1)
       total_pages = state.get("total_pages", 999)
       synthetic_plan = BuildingExtractionPlan(
           building_id="default",
           building_name=state.get("source_title", "Entire Document"),
           strategy=ExtractionStrategy.FULL_LLM,
           page_range=(register_start, total_pages),
           complexity="complex"
       )
       # Continue with normal orchestrator flow using [synthetic_plan]
   ```
   This MUST integrate with the existing plan_strategy() → parallel_extract flow.

2. In acm_extraction.py — graph wiring (look for add_conditional_edges or should_use_orchestrator):
   - Remove the conditional edge after tag_pages
   - Replace with: agent_state.add_edge("tag_page_sections", "orchestrate_extraction")
   - Remove the edges from tag_pages → prepare_context (legacy path)
   - Keep the prepare_context and extract_records NODES in the graph for now (dead code removal is S4)

3. In orchestrator.py — _inject_docling_tables():
   - Ensure it handles full-document page ranges (not just per-building ranges)
   - Ensure it returns gracefully when no Docling tables exist (return empty string, no error)

4. In orchestrator.py — _get_docling_tables():
   - Ensure page_range of (1, total_pages) fetches ALL Docling tables for the source

5. Update ExtractionState if it has a should_orchestrate or use_orchestrator boolean — remove it.

KEY FILES TO STUDY FIRST:
- open_notebook/graphs/acm_extraction.py — graph wiring, ~line 1268-1309
- open_notebook/extractors/orchestrator.py — orchestrate_extraction(), ~line 700+
- open_notebook/extractors/orchestrator.py — _invoke(), _inject_docling_tables(), _get_docling_tables()
- open_notebook/extractors/acm_schemas.py — ExtractionState TypedDict

TESTS:
- tests/test_orchestrator.py — add test for synthetic single-building plan
- tests/test_orchestrator.py — add test for Docling injection with full page range
- tests/test_acm_ai_extraction.py — verify graph compiles without conditional edge
- uv run pytest tests/ -x --ignore=tests/test_broadmeadows_e2e.py
- uv run ruff check .

COMMIT: "refactor: unify extraction pipeline — remove legacy fork

All documents now flow through orchestrate_extraction() regardless of
building count. Single-building and failed-inventory documents get a
synthetic single-building plan. Docling DataFrame injection fires for
all documents. Legacy prepare_context → extract_records path unreachable.

Design Principle #1: Unified Pipeline — every document, same path.
Ref: SCP-20260301-unified-pipeline"
```

---

### E29-S3: Broadmeadows + Alexander Validation Gate

**Priority**: P0 (Decision gate — confirms unification didn't regress)
**Size**: S (1 SP)
**Depends on**: E29-S1, E29-S2
**Files**: `scripts/research/e29_s3_unified_validation.py`, `docs/reviews/e29-s3-validation-results.md`

**Story**: As a compliance officer, I want the unified pipeline to maintain 100% accuracy on Broadmeadows and establish a baseline for Alexander, so that the architectural change is validated before dead code removal.

**Acceptance Criteria**:

1. **AC-1**: Broadmeadows extraction via unified orchestrator path: **31/31 (100%)** — zero regression
2. **AC-2**: Broadmeadows extraction uses orchestrator (not legacy path) — confirmed via pipeline logs showing `[ORCHESTRATOR]` stage
3. **AC-3**: Broadmeadows extraction includes Docling DataFrame injection — confirmed via logs showing `_inject_docling_tables()` fired
4. **AC-4**: Alexander extraction via unified orchestrator path: establishes baseline (target ≥ 35/43)
5. **AC-5**: Alexander extraction produces records for ALL 6 buildings (0 buildings with 0 records)
6. **AC-6**: Validation report documents: per-building record counts, extraction duration, Docling injection status, comparison to previous baselines
7. **AC-7**: If Broadmeadows < 31/31: **STOP — do not proceed to S4**, file bug

**Tasks**:

- [ ] 3.1 Create `scripts/research/e29_s3_unified_validation.py` (based on `e26_s4_accuracy_validation.py`)
- [ ] 3.2 Run Broadmeadows extraction with pipeline logging enabled
- [ ] 3.3 Verify orchestrator path taken (not legacy) via `[PIPELINE] [ORCHESTRATOR]` log entries
- [ ] 3.4 Verify Docling injection fired via `_inject_docling_tables` log entries
- [ ] 3.5 Compare Broadmeadows results against `docs/samplePDF/Clutch_Broadmeadows.csv` ground truth
- [ ] 3.6 Run Alexander extraction
- [ ] 3.7 Verify all 6 Alexander buildings produce records
- [ ] 3.8 Document results in `docs/reviews/e29-s3-validation-results.md`

**Claude Code Prompt**:

```
I need to validate the unified pipeline on both benchmark documents.

CONTEXT:
E29-S2 unified the extraction pipeline — all documents now flow through the orchestrator.
I need to confirm:
1. Broadmeadows (1 building) still achieves 31/31 (100%) via the unified path
2. Alexander (6 buildings) establishes a baseline (target ≥35/43)
3. Both documents show orchestrator path taken (not legacy)
4. Both documents show Docling injection fired

VALIDATION SCRIPT: Create scripts/research/e29_s3_unified_validation.py
Base it on the existing scripts/research/e26_s4_accuracy_validation.py pattern.

The script should:
1. Extract Broadmeadows (source already in DB, or re-upload)
2. Compare against docs/samplePDF/Clutch_Broadmeadows.csv ground truth
3. Extract Alexander (source already in DB, or re-upload)
4. Compare against docs/samplePDF/Alexander_GroundTruth.csv (if exists, else count records per building)
5. For both: verify pipeline logs contain "[ORCHESTRATOR]" (not legacy path)
6. For both: verify logs show Docling table injection
7. Print summary table with: document, accuracy, path_used, docling_injected, duration

REPORT: Write results to docs/reviews/e29-s3-validation-results.md in the same format as
docs/reviews/e26-s4-validation-results.md but with a "Unified Pipeline" header and
comparison columns showing E26-S4 baseline vs E29-S3 unified.

DECISION GATE:
- Broadmeadows 31/31 → PROCEED to S4
- Broadmeadows < 31/31 → STOP, file bug, investigate
- Alexander ≥35/43 → Good baseline, continue
- Alexander <35/43 → Flag as known gap, don't block S4

COMMIT: "test: E29-S3 unified pipeline validation

Broadmeadows: [X]/31 via unified orchestrator path
Alexander: [Y]/43 via unified orchestrator path
Both documents confirmed using orchestrator (not legacy).
Docling injection confirmed for both.

Ref: SCP-20260301-unified-pipeline"
```

---

### E29-S4: Dead Code Removal — Legacy Extraction Path

**Priority**: P1 (Cleanup — only after S3 validation passes)
**Size**: S (1 SP)
**Depends on**: E29-S3 (must pass validation gate)
**Files**: `open_notebook/graphs/acm_extraction.py`, `tests/test_acm_ai_extraction.py`

**Story**: As a developer, I want the unused legacy extraction path removed from the codebase, so that there is only one code path to maintain, test, and debug.

**Acceptance Criteria**:

1. **AC-1**: `prepare_context()` function removed from `acm_extraction.py`
2. **AC-2**: `extract_records()` monolithic loop function removed from `acm_extraction.py`
3. **AC-3**: `should_use_orchestrator()` routing function removed
4. **AC-4**: All chunking logic specific to legacy path removed (chunk boundary calculation, overlap logic)
5. **AC-5**: Graph nodes for legacy path removed from LangGraph wiring
6. **AC-6**: Tests referencing legacy path updated or removed (no test failures)
7. **AC-7**: `uv run pytest tests/ -x` passes with zero test failures
8. **AC-8**: `uv run ruff check .` clean (no unused imports from removed code)
9. **AC-9**: Lines removed documented (for commit message and sprint tracking)
10. **AC-10**: `npm run build` passes (no frontend dependency on removed backend code)

**Tasks**:

- [ ] 4.1 Identify all functions only used by legacy path (grep for `prepare_context`, `extract_records`, `should_use_orchestrator`)
- [ ] 4.2 Remove `prepare_context()` and its helper functions
- [ ] 4.3 Remove `extract_records()` monolithic loop and chunking helpers
- [ ] 4.4 Remove `should_use_orchestrator()` conditional routing
- [ ] 4.5 Remove legacy graph nodes and edges from LangGraph wiring
- [ ] 4.6 Update/remove tests that reference legacy functions
- [ ] 4.7 Run `uv run ruff check .` — fix unused imports
- [ ] 4.8 Run `uv run pytest tests/ -x` — all pass
- [ ] 4.9 Run `cd frontend && npm run build` — verify no frontend breaks
- [ ] 4.10 Count lines removed, document in commit message

**Claude Code Prompt**:

```
I need to remove the dead legacy extraction path from acm_extraction.py.

CONTEXT:
E29-S2 unified the pipeline — all documents now flow through orchestrate_extraction().
E29-S3 validated both Broadmeadows (31/31) and Alexander on the unified path.
The legacy path is now dead code.

WHAT TO REMOVE from open_notebook/graphs/acm_extraction.py:

1. prepare_context() function — was the legacy context assembly
   - And any helper functions it calls that aren't used by the orchestrator
   
2. extract_records() function — was the monolithic extraction loop
   - This is the chunk-based loop that processes the entire document
   - IMPORTANT: The orchestrator's extract_building() is DIFFERENT — keep that!
   - Look carefully at line numbers — extract_records is around line 1200-1520
   - extract_building() is in orchestrator.py — completely separate
   
3. should_use_orchestrator() function — was the conditional routing logic

4. Legacy graph node registrations and edges:
   - The nodes for prepare_context, extract_records in the StateGraph
   - The conditional edge that called should_use_orchestrator()
   - Any edges from tag_pages → prepare_context
   
5. Any chunking logic ONLY used by legacy path:
   - Chunk boundary calculation
   - Overlap/sliding window logic
   - If any of these are shared with orchestrator, KEEP them

WHAT TO KEEP:
- ALL orchestrator code (orchestrate_extraction, extract_building, etc.)
- ALL post-extraction stages (validate, correct, dedup, recover, save)
- ALL pre-extraction stages (structure, inventory, tag_pages, metadata)
- parse_json_response() and _unwrap_completion_state() — used by orchestrator
- _normalize_extraction_json() — used by orchestrator
- _recover_no_access_records() — post-extraction stage

APPROACH:
1. First, grep to find all callers of prepare_context, extract_records, should_use_orchestrator
2. Confirm they're only called from graph wiring (not from orchestrator or other live code)
3. Remove functions
4. Remove graph nodes/edges
5. Fix imports (ruff will catch unused)
6. Fix tests (remove or update tests for removed functions)

VALIDATION:
- uv run ruff check . (clean)
- uv run pytest tests/ -x --ignore=tests/test_broadmeadows_e2e.py (all pass)
- cd frontend && npm run build (pass)
- Count total lines removed

COMMIT: "refactor: remove legacy extraction path (N lines)

Removed: prepare_context(), extract_records() loop, should_use_orchestrator(),
legacy graph nodes/edges, and chunking logic. All documents now use the
unified orchestrate_extraction() path exclusively.

Dead code since E29-S2 (unified pipeline). Validated in E29-S3:
Broadmeadows 31/31, Alexander [baseline].

Ref: SCP-20260301-unified-pipeline"
```

---

## 4. Implementation Order & Dependencies

```
E29-S1 (JSON Parser Fix) ─────────┐
                                   ├──→ E29-S3 (Validation Gate) ──→ E29-S4 (Dead Code Removal)
E29-S2 (Unified Orchestrator) ────┘
```

- **S1 and S2 can be developed in parallel** (different files)
- **S3 requires both S1 and S2** (validation needs both fixes)
- **S4 requires S3 pass** (don't remove code until validated)
- **S1 is the highest urgency** — it's blocking Alexander extraction RIGHT NOW

---

## 5. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Broadmeadows regresses below 31/31 | Low | High | S3 validation gate; rollback to S2 if fails |
| Synthetic single-building plan misses content | Low | Medium | Use same page range as legacy path (register_start → total_pages) |
| Docling injection changes Broadmeadows output | Medium | Low | More records = good (validate against ground truth, extras are acceptable) |
| Alexander still below 35/43 | Medium | Medium | Separate concern — prompt engineering for ARA format, not a unification issue |
| JSON parser fix doesn't cover all fence variants | Low | Low | Unit tests cover 6 variants; add more as discovered |

---

## 6. Artifact Impacts

| Artifact | Change Needed | Priority |
|----------|--------------|----------|
| `acm_extraction.py` | Remove conditional edge, remove legacy functions | S2 + S4 |
| `orchestrator.py` | Add synthetic plan fallback, verify Docling injection | S2 |
| `utils.py` | Fix `parse_json_response()` markdown fence handling | S1 |
| Architecture doc (HTML) | Update pipeline diagrams to remove dual-path | Post-S4 |
| `sprint-status.yaml` | Add E29 with 4 stories | Immediate |
| `05-epics-and-stories.md` | Add E29 epic definition | Immediate |

---

## 7. Success Metrics

| Metric | Current | Target | Measured At |
|--------|---------|--------|-------------|
| Code paths through pipeline | 2 (legacy + orchestrator) | **1 (orchestrator only)** | S4 complete |
| Broadmeadows accuracy | 31/31 (100%) | **31/31 (100%)** — no regression | S3 |
| Alexander accuracy | ~29/43 (67%) or 0/43 (error) | **≥35/43 (81%)** baseline | S3 |
| Docling injection for single-building | Never fires | **Always fires** | S3 |
| Legacy dead code | ~400 lines | **0 lines** | S4 |
| `parse_json_response()` fence handling | Fails | **Handles all variants** | S1 |

---

## 8. Estimated Effort

| Story | Size | SP | Effort | Notes |
|-------|------|----|--------|-------|
| E29-S1 | S | 1 | 1-2 hours | Regex + unit tests, isolated change |
| E29-S2 | M | 3 | 3-4 hours | Core graph wiring + fallback logic |
| E29-S3 | S | 1 | 1-2 hours | Run scripts, document results |
| E29-S4 | S | 1 | 1-2 hours | Delete code, fix tests |
| **Total** | | **6 SP** | **~8 hours** | Single sprint |

---

## 9. Appendix: Architectural Alignment Check

### Design Principle Compliance (from Architecture Doc Section 17)

| Principle | Current Status | After E29 |
|-----------|---------------|-----------|
| 1. Unified Pipeline | ❌ Dual-path fork | ✅ Single orchestrator path |
| 2. Hybrid Extraction | ✅ PyMuPDF + Docling | ✅ Unchanged (now benefits ALL docs) |
| 3. AI Interprets, Rules Validate | ✅ Working | ✅ Unchanged |
| 4. Graceful Degradation | ⚠️ Legacy = fallback | ✅ Synthetic plan = graceful fallback |
| 5. Measure Before Fixing | ✅ Benchmarks exist | ✅ S3 validation gate |
| 6. Design for the Officer | ✅ UI unchanged | ✅ UI unchanged |

### BMAD Compliance

- **SCP format**: This document ✅
- **Sprint tracking**: E29 to be added to `sprint-status.yaml` ✅
- **Story artifacts**: Each story has ACs, tasks, Claude Code prompts ✅
- **Validation gate**: S3 is an explicit go/no-go decision point ✅
- **Retrospective**: To be conducted after S4 completion ✅

---

*SCP generated 2026-03-01. Approved by: [pending]*
