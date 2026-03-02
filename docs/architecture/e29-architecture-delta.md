# Epic 29 Architecture Delta: Pipeline Unification

| Field | Value |
|-------|-------|
| **Version** | 1.0 |
| **Date** | 2026-03-01 |
| **Author** | Winston (Architect) |
| **Status** | Proposed |
| **Epic** | E29 — Pipeline Unification |
| **Supersedes** | Sections 5.5, 5.6, 5.7 of 04-architecture.md (placeholder stubs) |
| **Depends On** | E26 Docling Direct API (merged), E27 Pipeline Observability (merged), E28 ARA Recovery (merged) |

---

## Table of Contents

1. [Current-State vs Target-State Architecture](#1-current-state-vs-target-state-architecture)
2. [Unified Routing Contract](#2-unified-routing-contract)
3. [Fallback Contract Matrix](#3-fallback-contract-matrix)
4. [Component/File Impact Map (S1-S8)](#4-componentfile-impact-map-s1-s8)
5. [Migration and Rollback Plan](#5-migration-and-rollback-plan)
6. [Telemetry Plan](#6-telemetry-plan)
7. [Architecture Delta Table](#7-architecture-delta-table)
8. [Risk Register](#8-risk-register)

---

## 1. Current-State vs Target-State Architecture

### Current State (Post-E28, Pre-E29)

```
                        ACM Extraction Pipeline — CURRENT
 =========================================================================

 START
  │
  ▼
 extract_metadata ──► structure ──► inventory ──► tag_pages
                                                     │
                                          ┌──────────┴──────────┐
                                          │ should_use_         │
                                          │ orchestrator(state)  │
                                          └──────────┬──────────┘
                                     TRUE │                │ FALSE
                                          ▼                ▼
                                    orchestrate      prepare_context
                                          │                │
                                          │           ┌────┴────┐
                                          │           ▼         ▼
                                          │      extract     (error→END)
                                          │      records
                                          │        │ ◄──── (loop chunks)
                                          │        │
                                          ▼        ▼
                                       validate_records ◄──────────┐
                                          │                        │
                                    ┌─────┴─────┐                 │
                                    ▼            ▼                 │
                              deduplicate    correct ───────────────┘
                                    │         (max 3 retries)
                                    ▼
                            recover_no_access
                                    │
                                    ▼
                               save_records
                                    │
                                    ▼
                                   END
```

**Key problems with current state:**

- `should_use_orchestrator()` returns `False` when `building_inventory` is empty, routing to legacy `prepare_context → extract_records` path
- Two parallel extraction codepaths must be maintained and tested
- `prepare_context` duplicates some orchestrator logic (Docling table injection, content trimming)
- No benchmark harness — quality regressions are detected manually
- Monolithic orchestrator: extraction + classification + validation + enrichment all in one LLM call
- JSON parser silently swallows some fence/preamble/truncation issues
- No strategy registry — routing logic is implicit in conditionals
- Export is hard-coded to current column set

### Target State (Post-E29)

```
                        ACM Extraction Pipeline — TARGET (E29)
 =========================================================================

 START
  │
  ▼
 extract_metadata ──► structure ──► inventory ──► tag_pages
                                                     │
                                                     │  (ALWAYS)
                                                     ▼
                                              orchestrate_extraction
                                                     │
                                    ┌────────────────┼────────────────┐
                                    ▼                ▼                ▼
                              table_parser    context_enricher  classifier
                              (DataFrame→     (LLM-targeted     (regex-first
                               raw rows)       enrichment)      product type)
                                    │                │                │
                                    ▼                ▼                ▼
                               bar_mapper ────► merge_candidates ◄────┘
                              (schema-driven        │
                               field mapping)       ▼
                                              validator
                                              (deterministic
                                               retry ≤3)
                                                     │
                                                     ▼
                                            deduplicate_records
                                                     │
                                                     ▼
                                           recover_no_access
                                                     │
                                                     ▼
                                              save_records
                                                     │
                                                     ▼
                                                    END

 ┌─────────────────────────────────────────────────────────────────────┐
 │  REMOVED (after Gate 3):                                           │
 │    - should_use_orchestrator() conditional                         │
 │    - prepare_context node                                          │
 │    - extract_records node                                          │
 │    - Legacy chunk-loop extraction                                  │
 │                                                                    │
 │  ADDED:                                                            │
 │    - strategy_registry.py (capability routing)                     │
 │    - table_parser.py (DataFrame → raw candidates)                  │
 │    - bar_mapper.py (schema-driven field mapping)                   │
 │    - context_enricher.py (targeted LLM enrichment)                 │
 │    - classifier.py (regex-first product classification)            │
 │    - Benchmark harness (benchmarks/, CI gate)                      │
 │                                                                    │
 │  PRESERVED (unchanged):                                            │
 │    - extract_metadata, structure, inventory, tag_pages             │
 │    - validate → correct loop (max 3)                               │
 │    - deduplicate_records                                           │
 │    - recover_no_access                                             │
 │    - save_records                                                  │
 │    - PipelineLogger / AGUIEventEmitter (SSE observability)         │
 │    - Docling Direct API table injection                            │
 └─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Unified Routing Contract

### Authoritative Rule

```
tag_pages → orchestrate_extraction (ALWAYS, unconditionally)
```

The `should_use_orchestrator()` function is eliminated. There is no conditional fork after `tag_pages`.

### Routing Invariants

| # | Invariant | Enforcement |
|---|-----------|-------------|
| R1 | `tag_pages` MUST always route to `orchestrate_extraction` | `add_edge("tag_pages", "orchestrate")` — unconditional edge, no `add_conditional_edges` |
| R2 | Documents with missing `building_inventory` use synthetic whole-document plan | `orchestrator.py` creates `SyntheticExtractionPlan(page_range=(1, total_pages))` |
| R3 | Documents with zero buildings use single-pass extraction on full content | Same as R2 — no building loop needed, content treated as one extraction unit |
| R4 | Docling table injection operates within unified path | `_get_docling_tables()` and `_inject_docling_tables()` called inside `orchestrate_extraction()` for every building (and for synthetic plans) |
| R5 | Post-extraction stages receive identical input format regardless of document type | `orchestrate_extraction` returns `{"raw_records": list[ACMExtractionRecord]}` — same as today |

### Synthetic Whole-Document Plan

When `building_inventory` is `None` or empty:

```python
# In orchestrate_extraction():
if not inventory or not inventory.buildings:
    plan = SyntheticExtractionPlan(
        building_name="Whole Document",
        page_start=1,
        page_end=state.get("total_pages", 999),
        source="synthetic_no_inventory"
    )
    buildings_to_process = [plan]
else:
    buildings_to_process = inventory.buildings
```

This keeps all documents on the same code path. The orchestrator's per-building loop runs exactly once for synthetic plans.

---

## 3. Fallback Contract Matrix

### 3.1 Primary Fallback Matrix

| # | Condition | Detection | Behavior | Output | Severity | Telemetry Tag |
|---|-----------|-----------|----------|--------|----------|---------------|
| F1 | **No building inventory** | `inventory is None or len(inventory.buildings) == 0` | Create synthetic whole-document extraction plan | Extraction proceeds on full content; no per-building segmentation | Non-fatal (degraded) | `fallback.no_inventory` |
| F2 | **No Docling tables in page range** | `_get_docling_tables()` returns empty list | Continue text-only extraction using `full_text` content | LLM receives markdown only — no DataFrame injection | Non-fatal (degraded) | `fallback.no_docling_tables` |
| F3 | **LLM JSON formatting error** | `parse_json_response()` raises `JSONDecodeError` or `TruncationError` | Resilient parser: strip fences → scan brace depth → select largest valid object → Pydantic validate | Records from largest parseable JSON block | Non-fatal (retry-eligible) | `fallback.json_parse` |
| F4 | **LLM returns no records** | Parsed response has `len(records) == 0` | Log warning + continue (building may legitimately have no ACM) | Empty record set for building | Non-fatal | `fallback.empty_extraction` |
| F5 | **Pydantic validation failure** | `ACMExtractionResult.model_validate()` raises `ValidationError` | Targeted correction: send failed records + validation errors to LLM for fix (max 3 retries) | Corrected records or terminal failure with error log | Retry-bounded | `fallback.validation_failure` |
| F6 | **Correction retries exhausted** | `correction_count >= 3` | Accept records that passed validation; drop records that still fail | Partial record set with `extraction_notes` documenting failures | Non-fatal (degraded) | `fallback.correction_exhausted` |
| F7 | **LLM provider error (5xx/timeout)** | HTTP 5xx or `asyncio.TimeoutError` from LLM call | Retry once after 5s backoff; if second failure, skip building and log | Building skipped with error annotation | Non-fatal (degraded) | `fallback.llm_error` |
| F8 | **Docling extraction failure** | Exception during `DocumentConverter.convert()` | Continue with PyMuPDF `full_text` only (Docling tables unavailable) | Text-only extraction for all buildings | Non-fatal (degraded) | `fallback.docling_failure` |

### 3.2 Fallback Decision Tree

```
tag_pages
    │
    ▼
orchestrate_extraction
    │
    ├── inventory present? ──NO──► F1: synthetic whole-doc plan
    │                                    │
    │                                    ▼
    │                               (continue below)
    │
    ├── For each building (or synthetic plan):
    │   │
    │   ├── get Docling tables
    │   │   └── empty? ──YES──► F2: text-only extraction
    │   │
    │   ├── call LLM
    │   │   ├── 5xx/timeout? ──YES──► F7: retry once → skip building
    │   │   ├── JSON parse fail? ──YES──► F3: resilient parser
    │   │   └── zero records? ──YES──► F4: log + continue
    │   │
    │   └── validate records
    │       ├── validation fail? ──YES──► F5: correction retry (≤3)
    │       │                                  │
    │       │                        exhausted? ──YES──► F6: accept partials
    │       │
    │       └── pass → merge into final set
    │
    ▼
deduplicate → recover_no_access → save
```

### 3.3 Determinism Guarantees

- **Retry cap**: Correction retries are hard-capped at 3. No unbounded loops.
- **Backoff**: LLM provider retries use a fixed 5s backoff (not exponential), limited to 1 retry.
- **Idempotency**: Running the same document twice with the same model produces the same graph traversal path (deterministic routing).
- **Logging**: Every fallback activation emits a structured log with the telemetry tag, building name, and reason.

---

## 4. Component/File Impact Map (S1-S8)

### 4.1 File Change Matrix

| File | S1 | S2 | S3 | S4 | S5 | S6 | S7 | S8 | Change Type |
|------|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|-------------|
| `open_notebook/graphs/utils.py` | **M** | | | | | | | | Fix: fence stripping, preamble handling, truncation error |
| `tests/test_json_parser.py` | **A** | | | | | | | | New: resilient parser test suite |
| `benchmarks/` (directory) | | **A** | | | | | | | New: ground-truth data, harness config |
| `scripts/research/e29_benchmark_harness.py` | | **A** | | | | | | | New: benchmark runner with metrics |
| `tests/integration/test_benchmark_harness.py` | | **A** | | | | | | | New: harness integration tests |
| `docs/reviews/e29-baseline-benchmark-report.md` | | **A** | | | | | | | New: baseline metrics report |
| `open_notebook/graphs/acm_extraction.py` | | | **M** | | | **M** | **M** | | Modify: remove conditional edge, remove legacy nodes (S7) |
| `open_notebook/extractors/orchestrator.py` | | | **M** | **M** | | | **M** | | Modify: synthetic plan, strategy registry integration, dead code removal |
| `open_notebook/extractors/acm_schemas.py` | | | **M** | **M** | | | | | Modify: schema updates for strategy metadata |
| `tests/test_orchestrator.py` | | | **M** | | | | **M** | | Modify: test unified path, remove legacy tests |
| `tests/test_acm_ai_extraction.py` | | | **M** | | | | | | Modify: update for always-orchestrator routing |
| `open_notebook/extractors/strategy_registry.py` | | | | **A** | | | | | New: capability registry and route selection |
| `tests/test_strategy_registry.py` | | | | **A** | | | | | New: registry tests |
| `open_notebook/extractors/table_parser.py` | | | | | **A** | | | | New: DataFrame → raw record candidates |
| `open_notebook/extractors/bar_mapper.py` | | | | | **A** | | | | New: schema-driven BAR field mapping |
| `tests/test_table_parser.py` | | | | | **A** | | | | New: table parser tests |
| `tests/test_bar_mapper.py` | | | | | **A** | | | | New: BAR mapper tests |
| `open_notebook/extractors/context_enricher.py` | | | | | | **A** | | | New: targeted LLM enrichment agent |
| `open_notebook/extractors/classifier.py` | | | | | | **A** | | | New: regex-first product classifier |
| `open_notebook/extractors/validator.py` | | | | | | **A** | | | New: deterministic validation agent |
| `tests/test_context_enricher.py` | | | | | | **A** | | | New: enricher tests |
| `tests/test_classifier.py` | | | | | | **A** | | | New: classifier tests |
| `tests/test_validator.py` | | | | | | **A** | | | New: validator tests |
| `scripts/research/e29_validation_gate.py` | | | | | | | **A** | | New: dual-benchmark validation runner |
| `docs/reviews/e29-validation-gate-results.md` | | | | | | | **A** | | New: gate results report |
| `commands/source_commands.py` | | | | | | | **M** | | Modify: remove legacy extraction references |
| `api/routers/acm.py` | | | | | | | | **M** | Modify: schema-driven export |
| `frontend/src/components/ExportDialog.tsx` | | | | | | | | **M** | Modify: per-building and ACM-type export |
| `tests/test_export.py` | | | | | | | | **A** | New: export integration tests |
| `tests/test_unified_pipeline.py` | | | | | | | | **A** | New: E2E unified pipeline tests |
| BMAD docs (PRD, arch, epics, sprint) | | | | | | | | **M** | Modify: align to E29 final state |

**Legend**: **A** = Add (new file), **M** = Modify (existing file)

### 4.2 Dependency Graph Across Stories

```
S1 (JSON Parser) ─────────┐
                           ▼
S2 (Benchmark Harness) ──► GATE 1 (baseline captured)
                           │
                           ▼
S3 (Unified Path) ─────┐
                        ▼
S4 (Strategy Registry) ► GATE 2 (parity confirmed)
                           │
                           ▼
S5 (Table Parser + BAR) ──┐
                           ▼
S6 (Enricher/Classifier) ► GATE 3 (no regression)
                           │
                           ▼
S7 (Validation + Cleanup) ─┐
                            ▼
S8 (Export + Docs) ────────► GATE 4 (release ready)
```

---

## 5. Migration and Rollback Plan

### 5.1 Per-Gate Migration Steps

#### Gate 1: Baseline Harness (after S2)

| Step | Action | Rollback |
|------|--------|----------|
| 1 | Deploy resilient JSON parser (S1) | Revert `utils.py` to prior commit — old parser is backward-compatible |
| 2 | Run benchmark harness on 3+ documents | No rollback needed — read-only measurement |
| 3 | Publish baseline report | Archive report if inaccurate |
| **Gate criteria** | Harness runs, baselines captured | **If blocked**: parser fix is independent; debug harness in isolation |

#### Gate 2: Unified Path Parity (after S4)

| Step | Action | Rollback |
|------|--------|----------|
| 4 | Remove `should_use_orchestrator()` conditional | Restore conditional edge in `acm_extraction.py` — legacy path is still present (not yet deleted) |
| 5 | Add synthetic whole-document plan for no-inventory docs | Revert orchestrator changes — conditional edge still routes to prepare_context |
| 6 | Deploy strategy registry | Registry is additive — removing it restores prior behavior |
| 7 | Run benchmark: Broadmeadows 31/31, Alexander >=36/43 | **If regression**: revert S3-S4 changes; legacy path is still intact and reachable by restoring the conditional edge |
| **Gate criteria** | Parity confirmed | **If blocked**: legacy path is still present. Restore conditional routing, investigate. |

#### Gate 3: Cleanup Permission (after S6)

| Step | Action | Rollback |
|------|--------|----------|
| 8 | Deploy decomposed agents (table_parser, bar_mapper, enricher, classifier, validator) | Each agent is a new file — delete files to revert to monolithic orchestrator |
| 9 | Wire agents into orchestrator loop | Revert orchestrator.py to pre-decomposition state |
| 10 | Run benchmark: no regression from baseline | **If regression**: revert agent wiring; monolithic orchestrator still works |
| **Gate criteria** | Benchmark pass, latency/cost acceptable | **If blocked**: agents are additive. Revert wiring, keep monolithic path. |

#### Gate 4: Release Readiness (after S8)

| Step | Action | Rollback |
|------|--------|----------|
| 11 | Delete legacy nodes: `prepare_context`, `extract_records`, `should_use_orchestrator` | Git revert — code is in history |
| 12 | Remove legacy feature flags and dead branches | Git revert |
| 13 | Deploy export hardening | Revert `acm.py` and `ExportDialog.tsx` |
| 14 | Update BMAD documentation | Re-run docs update |
| **Gate criteria** | E2E tests pass, CI benchmark pass, docs aligned | **If blocked**: delay doc updates; export changes are isolated |

### 5.2 Rollback Safety Principle

**Legacy path deletion (S7) is the only irreversible step**, and it is gated behind Gate 3 — which requires:
1. Benchmark parity confirmed
2. Latency/cost within thresholds
3. All fallback behaviors tested deterministically

Before Gate 3, the legacy path (`prepare_context → extract_records`) remains in the codebase, unreachable but restorable by adding back the conditional edge. This is the "safety net" that makes S1-S6 fully rollback-safe.

---

## 6. Telemetry Plan

### 6.1 Benchmark Metrics (captured by harness, per document)

| Metric | Type | Capture Point | Threshold |
|--------|------|---------------|-----------|
| `benchmark.recall` | float (0-1) | Ground-truth comparison | >= baseline |
| `benchmark.precision` | float (0-1) | Ground-truth comparison | >= baseline |
| `benchmark.field_accuracy` | float (0-1) | Per-field match rate | >= baseline |
| `benchmark.record_count` | int | Post-dedup record count | Exact match to ground truth |
| `benchmark.latency_s` | float | Wall-clock extraction time | <= baseline * 1.2 (20% tolerance) |
| `benchmark.token_usage` | int | LLM token counter (prompt + completion) | <= baseline * 1.3 (30% tolerance) |
| `benchmark.cost_usd` | float | Calculated from token usage + model pricing | Informational |

### 6.2 Stage Metrics (emitted per extraction run via PipelineLogger)

| Metric | Type | Capture Point | Used By |
|--------|------|---------------|---------|
| `stage.duration_s` | float | Each PipelineLogger `stage_enter`/`stage_exit` pair | Performance regression detection |
| `stage.llm_calls` | int | Counter in orchestrator per-building loop | Cost tracking |
| `stage.records_extracted` | int | Post-extraction, pre-validation | Quality gate |
| `stage.records_validated` | int | Post-validation, pre-dedup | Quality gate |
| `stage.records_saved` | int | Post-save | Final accuracy |
| `stage.fallback_activated` | string[] | List of `fallback.*` tags triggered | Debugging, drift detection |
| `stage.buildings_processed` | int | Orchestrator loop counter | Coverage tracking |
| `stage.buildings_skipped` | int | F7 (LLM error) skip counter | Reliability tracking |

### 6.3 Correction Metrics (emitted per correction cycle)

| Metric | Type | Capture Point | Used By |
|--------|------|---------------|---------|
| `correction.retry_count` | int | `should_correct()` → `correct()` loop | Retry budget tracking |
| `correction.records_fixed` | int | Delta between pre/post-correction valid count | Correction effectiveness |
| `correction.records_dropped` | int | Records that failed all 3 retries | Quality gap analysis |
| `correction.failure_reasons` | string[] | Pydantic `ValidationError` field paths | Schema/prompt improvement signals |
| `correction.total_correction_time_s` | float | Sum of correction LLM calls | Cost tracking |

### 6.4 Agent Decomposition Metrics (S5-S6, per decomposed agent)

| Metric | Type | Capture Point | Used By |
|--------|------|---------------|---------|
| `agent.table_parser.row_recall` | float | Rows extracted vs DataFrame rows input | Table parser effectiveness |
| `agent.bar_mapper.mapping_accuracy` | float | Fields successfully mapped vs total fields | Mapper quality |
| `agent.classifier.regex_hit_rate` | float | Classifications resolved by regex (no LLM) | LLM call reduction tracking |
| `agent.enricher.records_enriched` | int | Records that received LLM enrichment | Targeted enrichment scope |
| `agent.validator.pass_rate` | float | Records passing validation on first attempt | Upstream quality signal |

### 6.5 Gate Pass/Fail Evidence

Each gate decision is recorded as a JSON artifact:

```json
{
  "gate": "gate_2_unified_path_parity",
  "timestamp": "2026-03-XX",
  "status": "PASS",
  "criteria": [
    {"name": "broadmeadows_31_31", "expected": 31, "actual": 31, "pass": true},
    {"name": "alexander_gte_36_43", "expected": ">=36", "actual": 38, "pass": true},
    {"name": "docling_injection_confirmed", "expected": true, "actual": true, "pass": true}
  ],
  "benchmark_report": "docs/reviews/e29-baseline-benchmark-report.md",
  "commit": "abc123"
}
```

---

## 7. Architecture Delta Table

| # | Component | Current State | Target State (E29) | Story | Breaking? |
|---|-----------|---------------|-------------------|-------|-----------|
| D1 | **Graph routing (tag_pages →)** | Conditional: `should_use_orchestrator()` forks to orchestrate or prepare_context | Unconditional: `add_edge("tag_pages", "orchestrate")` | S3 | No (legacy path retained until S7) |
| D2 | **No-inventory handling** | Falls to legacy `prepare_context → extract_records` | Synthetic whole-document plan within orchestrator | S3 | No |
| D3 | **JSON parser** | Silent failures on fenced JSON, preambles, truncation | Resilient parser: fence strip → brace scan → largest object → truncation error | S1 | No (backward-compatible) |
| D4 | **Benchmark harness** | None | Automated harness, 3+ ground-truth documents, CI entrypoint | S2 | No (additive) |
| D5 | **Strategy registry** | Implicit routing via conditionals in orchestrator | Explicit `strategy_registry.py` with centralized selection rules | S4 | No (additive) |
| D6 | **Fallback contract** | Ad-hoc, per-function exception handling | Codified matrix (F1-F8), deterministic retry caps, telemetry tags | S4 | No |
| D7 | **Table parsing** | Monolithic: LLM does everything (parse + map + classify) | Decomposed: `table_parser.py` extracts raw rows from DataFrames without LLM | S5 | No (additive agent) |
| D8 | **BAR field mapping** | Embedded in LLM prompt and Pydantic validation | Decomposed: `bar_mapper.py` with schema-driven mapping from `field_schema` | S5 | No (additive agent) |
| D9 | **Product classification** | LLM classifies all products | Regex-first `classifier.py`; LLM only for ambiguous cases | S6 | No (additive agent) |
| D10 | **Context enrichment** | Full-document LLM context per building | Targeted `context_enricher.py`; LLM enrichment only where needed | S6 | No (additive agent) |
| D11 | **Validation** | Inline in corrective RAG loop | Decomposed: `validator.py` with deterministic retry contract | S6 | No (replaces inline logic) |
| D12 | **Legacy path deletion** | `prepare_context`, `extract_records` present but reachable | Deleted: nodes, edges, feature flags removed | S7 | Yes (after Gate 3) |
| D13 | **Export** | Hard-coded column set | Schema-driven per-building and ACM-type exports | S8 | No (additive) |
| D14 | **Documentation** | Stubs in 04-architecture.md sections 5.5-5.7 | Full specification aligned to implementation reality | S8 | No |

---

## 8. Risk Register

| # | Risk | Likelihood | Impact | Mitigation | Owner | Gate |
|---|------|-----------|--------|------------|-------|------|
| R1 | **Broadmeadows regression on unified path** — synthetic plan or routing change causes record loss | Medium | High | Gate 2 blocks further work until 31/31 confirmed; legacy path is restorable until S7 | Dev | Gate 2 |
| R2 | **Alexander regression during decomposition** — agent decomposition changes extraction quality for ARA format | Medium | High | Gate 2 requires >=36/43; Gate 3 requires no regression from baseline; ground-truth captures ARA-specific patterns | Dev | Gate 2, 3 |
| R3 | **Benchmark harness flaky or unreliable** — non-deterministic LLM outputs make benchmark results inconsistent | Medium | Medium | Run each benchmark 3x, report median; pin model version and temperature=0; document variance | Dev | Gate 1 |
| R4 | **JSON parser change breaks edge case** — resilient parser handles new cases but regresses on existing ones | Low | High | S1 includes backward-compatibility tests for all existing unfenced patterns; parser is first story specifically so any issues surface before benchmarking | Dev | Gate 1 |
| R5 | **Agent decomposition increases latency** — more LLM calls from decomposed agents increase total extraction time | Medium | Medium | Gate 3 enforces latency <= baseline * 1.2; regex-first classifier reduces LLM calls; table_parser has zero LLM dependency | Dev | Gate 3 |
| R6 | **Agent decomposition increases cost** — more fine-grained LLM calls increase token usage | Medium | Low | Gate 3 enforces token usage <= baseline * 1.3; batched enrichment and targeted correction reduce total tokens vs monolithic approach | Dev | Gate 3 |
| R7 | **Legacy cleanup breaks post-extraction stages** — removing `prepare_context`/`extract_records` breaks assumptions in downstream code | Low | High | S7 runs full `ruff` + `pytest` after cleanup; downstream stages (validate, dedup, recover, save) only depend on `raw_records` output shape, not on which node produced them | Dev | Gate 3, 4 |
| R8 | **Export hardening breaks existing downloads** — schema-driven export produces different column ordering | Low | Medium | S8 includes backward-compatibility tests for current export format; new export options are additive (per-building, per-type) | Dev | Gate 4 |
| R9 | **Docling table injection fails in synthetic plan** — synthetic whole-document plan may not correctly query `acm_table_section` by page range | Medium | Medium | S3 acceptance criteria explicitly requires Docling table injection for single-building documents; integration test covers no-inventory + Docling tables scenario | Dev | Gate 2 |
| R10 | **Ground-truth creation effort underestimated** — creating accurate ground-truth for 3+ documents takes longer than budgeted | Medium | Low | Start with existing Broadmeadows (31 records) and Alexander (43 records) ground truths; third document can be smaller scope | Dev | Gate 1 |

---

## Appendix A: Compatibility with Existing Post-Extraction Stages

The post-extraction pipeline stages are **not modified by E29** and receive identical input:

| Stage | Input Contract | Provided By (Current) | Provided By (E29) | Compatible? |
|-------|---------------|----------------------|-------------------|-------------|
| `validate_records` | `state["raw_records"]: list[ACMExtractionRecord]` | `orchestrate_extraction` or `extract_records` | `orchestrate_extraction` only | Yes |
| `correct_records` | `state["validation_errors"]: list[dict]` | `validate_records` | `validate_records` (unchanged) | Yes |
| `deduplicate_records` | `state["raw_records"]: list[ACMExtractionRecord]` | `validate_records` pass-through | `validate_records` pass-through (unchanged) | Yes |
| `recover_no_access` | `state["raw_records"]: list[ACMExtractionRecord]`, `state["source"]: Source` | `deduplicate_records` | `deduplicate_records` (unchanged) | Yes |
| `save_records` | `state["raw_records"]: list[ACMExtractionRecord]`, `state["source"]: Source` | `recover_no_access` | `recover_no_access` (unchanged) | Yes |

The key compatibility invariant is that `orchestrate_extraction` produces `raw_records` in the same `list[ACMExtractionRecord]` shape. This is already true today — S3 does not change the output format.

## Appendix B: SSE/Observability Compatibility

| Component | Current Integration | E29 Impact |
|-----------|-------------------|------------|
| `PipelineLogger` | Wraps `stage_enter`/`stage_exit` for StageId enum stages | No change to existing stages. New decomposed agents emit sub-stage metrics via the same logger instance. |
| `AGUIEventEmitter` | Emits `step_started`/`step_finished` for AG-UI SSE | No change. `orchestrate` step name remains. Decomposed agents are internal to the orchestrator node — they do not surface as separate AG-UI steps. |
| `extraction_progress` table | Stores `PipelineRunState` JSON per command_id | No schema change. State JSON grows slightly with new metrics fields (backward-compatible). |
| Frontend `pipeline.ts` types | Mirrors `StageId` enum | No change. Decomposed agents are not new stages — they run within the existing `ORCHESTRATOR` stage. |
