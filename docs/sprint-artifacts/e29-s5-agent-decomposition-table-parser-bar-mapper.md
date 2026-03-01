# E29-S5: Agent Decomposition I — Table Parser + BAR Mapper

> **Epic**: E29 — Pipeline Unification
> **Story Points**: 3 | **Phase**: 3 | **Owner**: Backend Dev
> **Requires**: Gate 2 PASS
> **Source of Truth**: [Execution Contract](../../V3/epic-29-execution-contract.md) | [Architecture Delta](../../docs/architecture/e29-architecture-delta.md)

---

## Story Status

| Field | Value |
|-------|-------|
| Status | `drafted` |
| Sprint | E29 Phase 3 |
| Assigned To | — |
| Started | — |
| Completed | — |
| PR | — |
| Blocked By | Gate 2 (after S4) |

---

## User Story

> As a **pipeline developer**, I want ACM table rows parsed into raw record candidates without LLM dependency (table_parser), and BAR field mapping driven by `field_schema` (bar_mapper), so that extraction is faster, cheaper, and more deterministic.

---

## Dependencies

| Type | Item | Status |
|------|------|--------|
| Story | E29-S4 (registry + fallback) | Must be merged |
| Gate | Gate 2 — Unified Path Parity | Must PASS |

---

## Acceptance Criteria

| # | Criterion | Measurable Check |
|---|-----------|------------------|
| AC-1 | DataFrame rows produce raw record candidates without LLM dependency | `table_parser.parse(df)` returns list of dicts; zero LLM calls in trace |
| AC-2 | BAR mapping is schema-driven from `field_schema` | `bar_mapper.map(raw_record)` uses field_schema definitions, not hardcoded mapping |
| AC-3 | Regex normalization handles known consultant field variants | Test: "Cement Sheet" / "cement sheet" / "CEMENT SHEET" normalize to same value |
| AC-4 | Per-agent metrics logged: row recall for table_parser | Log contains `agent.table_parser.row_recall` metric |
| AC-5 | Per-agent metrics logged: mapping accuracy for bar_mapper | Log contains `agent.bar_mapper.mapping_accuracy` metric |
| AC-6 | No benchmark regression from Gate 2 baseline | **Broadmeadows >=31/31**, **Alexander >=36/43** |

---

## Tasks / Subtasks

| # | Task | File(s) | Est |
|---|------|---------|-----|
| T1 | Implement `table_parser.py` | `open_notebook/extractors/table_parser.py` (new) | 90m |
| T1.1 | — `parse_dataframe(df: pd.DataFrame) -> list[RawRecordCandidate]` | | |
| T1.2 | — Header detection: find ACM-relevant columns in DataFrame | | |
| T1.3 | — Row extraction: iterate rows, produce raw candidates | | |
| T1.4 | — Emit `agent.table_parser.row_recall` metric | | |
| T2 | Implement `bar_mapper.py` | `open_notebook/extractors/bar_mapper.py` (new) | 60m |
| T2.1 | — `map_to_bar(raw: RawRecordCandidate, schema: FieldSchema) -> ACMExtractionRecord` | | |
| T2.2 | — Schema-driven field mapping: iterate `field_schema` definitions | | |
| T2.3 | — Regex normalization for known consultant variants | | |
| T2.4 | — Emit `agent.bar_mapper.mapping_accuracy` metric | | |
| T3 | Wire agents into orchestrator extraction loop | `open_notebook/extractors/orchestrator.py` | 30m |
| T4 | Write table_parser tests | `tests/test_table_parser.py` (new) | 60m |
| T5 | Write bar_mapper tests | `tests/test_bar_mapper.py` (new) | 45m |
| T6 | Run benchmark: no regression | Benchmark harness | 15m |
| T7 | Lint + full test suite pass | `ruff check . --fix && pytest tests/ -x` | 10m |

**Within-story parallelism**: T1 (table_parser) and T2 (bar_mapper) can be developed in parallel.

---

## Test Strategy

- **Unit tests** (`tests/test_table_parser.py`):
  - Parse well-formed DataFrame with standard columns
  - Parse DataFrame with missing/extra columns (graceful degradation)
  - Parse DataFrame with merged cells (from Docling HTML tables)
  - Empty DataFrame returns empty list
  - Row recall metric calculation is correct
- **Unit tests** (`tests/test_bar_mapper.py`):
  - Map raw candidate to ACMExtractionRecord using field_schema
  - Regex normalization: case variants, abbreviations, consultant-specific names
  - Missing fields: mapped as None, not error
  - Mapping accuracy metric calculation is correct
- **Benchmark validation**: No regression from Gate 2 baseline

---

## Touched Files

| File | Action | Lines (est) |
|------|--------|-------------|
| `open_notebook/extractors/table_parser.py` | Add (new) | ~200 |
| `open_notebook/extractors/bar_mapper.py` | Add (new) | ~150 |
| `open_notebook/extractors/orchestrator.py` | Modify | ~30 |
| `tests/test_table_parser.py` | Add (new) | ~180 |
| `tests/test_bar_mapper.py` | Add (new) | ~120 |

---

## Risks

| Risk | Mitigation |
|------|------------|
| Table parser misses non-standard column layouts | Fallback F2 (text-only) still works; parser is additive |
| BAR mapper normalization incomplete | Start with known Broadmeadows + Alexander variants; extensible regex list |

---

## QA Checklist

- [ ] AC-1: Zero LLM calls in table_parser trace
- [ ] AC-2: BAR mapping uses field_schema, not hardcoded
- [ ] AC-3: Case-variant normalization verified
- [ ] AC-4: table_parser row recall metric logged
- [ ] AC-5: bar_mapper mapping accuracy metric logged
- [ ] AC-6: No benchmark regression
- [ ] `ruff check .` clean
- [ ] `pytest tests/ -x` green

---

## Post-Dev Notes

_To be filled by the developer after implementation._

---

## Post-QA Notes

_To be filled by QA after verification._
