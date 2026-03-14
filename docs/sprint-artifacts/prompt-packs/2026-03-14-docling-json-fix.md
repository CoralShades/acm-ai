# Session: Fix docling_document_json empty dict bug — trace data flow from Docling to SurrealDB, restore per-row extraction

## Skills to Load

/systematic-debugging — structured diagnosis before proposing fixes
/acm-observability — query traces, inspect graph state, debug extraction failures
/planning-with-files — persistent markdown plan for session continuity
/verification-before-completion — verify findings before claiming audit complete

---

## Prerequisites

Before starting this session, verify:

- SurrealDB running: `docker ps | grep acm-ai-db`
- API running: `curl http://localhost:5055/health`
- Branch: ACMV3
- Docling installed: `uv run python -c "import docling; print(docling.__version__)"`
- Sample PDF exists: `D:/ailocal/acm-ai/docs/samplePDF/Clutch_Broadmeadows.pdf`
- Ground truth file exists: `D:/ailocal/acm-ai/benchmarks/ground_truth/broadmeadows.json`
- Worker running: `uv run python run_worker.py --import-modules commands`

---

## Project Glossary

Key terms for this session. Refer to these definitions when interpreting code or instructions.

| Term | Definition |
|------|-----------|
| `docling_document_json` | Lossless cell-level JSON from Docling's `table.data.model_dump(mode="json")`. Contains `table_cells` array with `text`, `row_span`, `col_span`, `start_row_offset_idx`, etc. Stored in `acm_table_section` table. Primary input for per-row extraction. |
| `NormalizedTable` | Provider-agnostic dataclass in `providers/base.py`. Carries `docling_json: Optional[Dict]` alongside `html`, `markdown`, `csv`. |
| `DoclingAdapter` | Extraction provider in `providers/docling_adapter.py`. Calls `table.data.model_dump(mode="json")` at line 151 to populate `docling_json`. |
| `_store_docling_tables()` | Function in `source_commands.py:181` that persists merged table dicts to `acm_table_section` via `repo_create()`. Maps `docling_json` key → `docling_document_json` column. |
| `repo_create()` | Generic SurrealDB insert wrapper in `repository.py:85`. Uses `connection.insert(table, data)` from the Python SurrealDB client. |
| `_get_docling_tables()` | Function in `orchestrator.py:37` that retrieves `acm_table_section` rows via `SELECT *`. Returns dicts with `docling_document_json` key. |
| `extract_items_node` | LangGraph node in `acm_extraction.py:~980` that routes between per-row and bulk extraction. Checks `dj = t.get("docling_document_json"); if dj:` — empty dict `{}` is falsy, so per-row never triggers. |
| `RawTableRow` | Pydantic model in `row_segmenter.py` — one parsed row from Docling JSON. Contains `cells` dict, `column_mapping`, `raw_text`. Created by `segment_multiple_tables()`. |
| `per_row` vs `bulk` | Two extraction modes. Per-row = one LLM call per table row (requires `docling_document_json`). Bulk = one LLM call per building chunk (fallback when no Docling JSON). |
| ExtractionState | LangGraph TypedDict carrying all pipeline data between nodes: source metadata, docling tables, building cache, extracted records. |
| `parse_record_ids()` | Post-processing function in `repository.py` that converts SurrealDB RecordID objects to strings. Could potentially mangle nested data. |
| Skill | Markdown instruction set for Claude Code activated via `/skill-name`. |
| Subagent | Claude Code session spawned via Task tool for parallel work. Model: `sonnet` for complex, `haiku` for simple. |
| Plan mode | Session starts by reading/writing `task_plan.md` to prevent scope creep. |

---

## Current State

- Branch: ACMV3 (recent commits: `feat(frontend): complete frontend audit`, pipeline debug fixes)
- GitHub Issues: #104 (docling_document_json empty), #105 (per-row blocked by #104), #106 (model mismatch)
- Pipeline debug session (2026-03-14): 8 fixes applied, 0→29 records (93.5% of 31 ground truth)
- Per-row extraction has NEVER triggered successfully — always falls back to bulk
- `docling_document_json` stores as `{}` even after fresh Docling re-extraction
- `mode="json"` fix was applied in Bug Fix 11 (was `mode="python"`)
- Stale detection fix applied: `IS NULL OR = {}` catches empty dicts
- BUT re-extraction ALSO produces `{}` → infinite stale loop risk
- The `_store_docling_tables()` function maps `table.get("docling_json")` → `docling_document_json`
- The adapter calls `table.data.model_dump(mode="json")` which should return valid data
- SurrealDB migration 48 defines field as `TYPE option<object>`

### Key Discovery from Test File

`test_docling_json_storage.py` uses `export_to_dict()` — but the actual adapter code uses `table.data.model_dump(mode="json")`. These are DIFFERENT methods. The test may not reflect reality.

### Suspected Root Causes (ordered by likelihood)

1. **SurrealDB `TYPE option<object>` rejects nested arrays** — `table_cells` is an array, `object` type may coerce it to `{}`
2. **Python SurrealDB client `insert()` truncates large nested dicts** — docling JSON can be 50-200KB per table
3. **`parse_record_ids()` clobbers non-ID dict values** during response parsing
4. **`model_dump(mode="json")` returns empty dict** for certain Docling table types (unlikely given adapter logs show tables extracted)

---

## Key Files

Files this session will read or modify. Verify all paths exist before starting.

**Read (data flow audit — CRITICAL):**
- `D:/ailocal/acm-ai/open_notebook/extractors/providers/docling_adapter.py` — `model_dump()` call at line 151
- `D:/ailocal/acm-ai/open_notebook/extractors/providers/base.py` — `NormalizedTable` dataclass, `docling_json` field
- `D:/ailocal/acm-ai/commands/source_commands.py` — `_store_docling_tables()` at line 181, `_merge_provider_tables()` ~line 430
- `D:/ailocal/acm-ai/open_notebook/database/repository.py` — `repo_create()` at line 85, `parse_record_ids()`, `connection.insert()`
- `D:/ailocal/acm-ai/open_notebook/extractors/orchestrator.py` — `_get_docling_tables()` at line 37
- `D:/ailocal/acm-ai/open_notebook/graphs/acm_extraction.py` — `extract_items_node` ~line 1024-1040 (per-row path)

**Read (row segmenter — downstream consumer):**
- `D:/ailocal/acm-ai/open_notebook/extractors/row_segmenter.py` — `segment_multiple_tables()`, `COLUMN_ALIASES`

**Read (node data flow verification):**
- `D:/ailocal/acm-ai/open_notebook/graphs/acm_extraction.py` — `metadata_and_structure_node`, `inventory_node`, `extract_building_node`, `extract_items_node`, `save_records_node`
- `D:/ailocal/acm-ai/open_notebook/extractors/metadata_and_structure.py` — metadata output → ExtractionState
- `D:/ailocal/acm-ai/open_notebook/extractors/building_inventory.py` — inventory output → ExtractionState

**Read (SurrealDB schema):**
- `D:/ailocal/acm-ai/migrations/48.surrealql` — `DEFINE FIELD docling_document_json ON TABLE acm_table_section TYPE option<object>`
- `D:/ailocal/acm-ai/migrations/48_down.surrealql` — rollback migration

**Read (tests):**
- `D:/ailocal/acm-ai/tests/test_docling_json_storage.py` — existing tests (uses `export_to_dict()` not `model_dump()`)

**Read (ground truth):**
- `D:/ailocal/acm-ai/benchmarks/ground_truth/broadmeadows.json` — expected output (1 building, 31 records)

**Modify (fixes):**
- `D:/ailocal/acm-ai/open_notebook/extractors/providers/docling_adapter.py` — add debug logging, potential fix
- `D:/ailocal/acm-ai/commands/source_commands.py` — add debug logging, potential serialization fix
- `D:/ailocal/acm-ai/open_notebook/database/repository.py` — add debug logging, potential fix for `parse_record_ids()`
- `D:/ailocal/acm-ai/migrations/48.surrealql` — potential type change from `option<object>` to `option<any>`

**Modify (tests):**
- `D:/ailocal/acm-ai/tests/test_docling_json_storage.py` — update to use `model_dump()` instead of `export_to_dict()`

**Write (output):**
- `D:/ailocal/acm-ai/docs/sprint-artifacts/docling-json-fix/findings.md` — diagnosis findings
- `D:/ailocal/acm-ai/docs/sprint-artifacts/docling-json-fix/task_plan.md` — task plan
- `D:/ailocal/acm-ai/docs/sprint-artifacts/docling-json-fix/progress.md` — progress tracker

---

## Plan

Read `docs/sprint-artifacts/docling-json-fix/task_plan.md` before starting. Update it as you work.

### Task Plan Reference

- task_plan.md: `D:/ailocal/acm-ai/docs/sprint-artifacts/docling-json-fix/task_plan.md`
- findings.md: `D:/ailocal/acm-ai/docs/sprint-artifacts/docling-json-fix/findings.md`
- progress.md: `D:/ailocal/acm-ai/docs/sprint-artifacts/docling-json-fix/progress.md`

### Execution Strategy

**Phase 1 — Diagnosis (add debug logging, trace data)**

Step 1: Read `docling_adapter.py` line 151. Add `logger.debug()` AFTER `model_dump()` to log:
- `type(docling_json)`, `len(docling_json)`, `list(docling_json.keys())`
- `len(docling_json.get("table_cells", []))` if key exists
- `sys.getsizeof(json.dumps(docling_json))` (byte size)

Step 2: Read `source_commands.py:181-199`. Add `logger.debug()` BEFORE `repo_create()` to log:
- `type(table.get("docling_json"))`, `len(str(table.get("docling_json")))`
- Whether the value is `{}`, `None`, or has content

Step 3: Read `repository.py:85-99`. Add `logger.debug()` BEFORE and AFTER `connection.insert()` to log:
- Pre-insert: `data.get("docling_document_json")` type and boolean truthiness
- Post-insert: returned record's `docling_document_json` value

Step 4: Run a test extraction. Use the API endpoint or direct function call:
```python
# Option A: Via API
curl -X POST http://localhost:5055/api/acm/extract \
  -H 'Content-Type: application/json' \
  -d '{"source_id": "source:mc5llofksqsglrjsfssj", "force": true}'

# Option B: Direct SurrealDB query after extraction
# SELECT id, string::len(raw_text) AS raw_len,
#        docling_document_json, table_index
# FROM acm_table_section
# WHERE source_id = 'source:mc5llofksqsglrjsfssj'
# ORDER BY table_index;
```

Step 5: Analyze debug logs — identify the exact layer where data goes from populated to empty.

**Phase 2 — Root Cause Investigation**

Step 6: If data is present in adapter but empty after `repo_create()`:
- Test SurrealDB `TYPE option<object>` constraint. Docling JSON contains `table_cells` which is an ARRAY. The `object` type in SurrealDB might reject arrays inside objects.
- Create a test migration: `DEFINE FIELD docling_document_json ON TABLE acm_table_section TYPE option<any>;`
- Insert a test record with nested arrays via SurrealQL and verify it persists.

Step 7: If data is present in `repo_create()` input but empty in DB:
- Check `parse_record_ids()` — does it traverse nested dicts and modify values?
- Check Python SurrealDB client `insert()` method — does it have size limits?
- Test with a small vs large `docling_json` payload to isolate size-related truncation.

Step 8: If data is empty from `model_dump()` itself:
- Test `model_dump(mode="json")` on a real Docling `TableData` object in isolation
- Compare `model_dump(mode="json")` vs `model_dump()` vs `export_to_dict()` outputs
- Check if `table.data` is actually a `TableData` object or something else

**Phase 3 — Fix Implementation**

Step 9: Apply the fix based on root cause:
- **If SurrealDB type**: New migration changing `option<object>` to `option<any>` (migration 51)
- **If Python client size limit**: Serialize to JSON string before insert, deserialize on retrieval
- **If parse_record_ids()**: Skip nested dict traversal for non-ID fields
- **If adapter**: Fix the `model_dump()` call

Step 10: Add a round-trip integration test:
- Create a `docling_document_json` with realistic size (50+ cells)
- Insert via `repo_create()`
- Retrieve via `repo_query("SELECT * FROM acm_table_section WHERE id = $id")`
- Assert retrieved value matches inserted value exactly

**Phase 4 — Node Data Flow Verification**

Step 11: Verify each graph node saves its output to the correct DB table AND passes required data to the next node via `ExtractionState`:

| Node | Saves To | Passes To Next Node Via |
|------|----------|------------------------|
| `metadata_and_structure_node` | (state only) | `state["document_meta"]`, `state["document_structure"]` |
| `inventory_node` | `building_record` table | `state["building_inventory"]`, `state["building_meta_cache"]` |
| `extract_building_node` | `building_record` table (update) | `state["building_meta_cache"]` (enriched) |
| `extract_items_node` | (accumulates) | `state["extracted_records"]` |
| `save_records_node` | `acm_record` table | (terminal) |

Step 12: Verify `_get_docling_tables()` is called with correct page range and returns populated `docling_document_json`.

Step 13: Verify `segment_multiple_tables()` can parse the Docling JSON and produce `RawTableRow` objects.

**Phase 5 — E2E Verification**

Step 14: Full extraction run with `force=True` on Broadmeadows source.
Step 15: Verify per-row path triggered (look for `per_row` in worker logs, NOT `bulk fallback`).
Step 16: Compare against ground truth: target 31/31 records.
Step 17: Run full test suite and lint.

---

## Agent Strategy

Strategy: SUBAGENT-DISPATCH
Use the Task tool to dispatch independent investigation streams in parallel.
**All subagents should use `model: "sonnet"` for team-based work.**

### Phase 1 Subagents (launch in parallel)

**Subagent 1: docling-output-inspector**
- Model: sonnet
- Task: Read `docling_adapter.py` (full file), `base.py` (NormalizedTable), and `source_commands.py:181-199` + `source_commands.py:420-470`. Trace how `docling_json` flows from `model_dump()` through `NormalizedTable` through `_merge_provider_tables()` to `_store_docling_tables()`. Identify any point where the value could be lost, overwritten, or empty. Also check: does the test file `test_docling_json_storage.py` use `export_to_dict()` while the real code uses `model_dump(mode="json")`? Are these different? Return structured findings with file:line references.
- Skills: /systematic-debugging

**Subagent 2: surrealdb-storage-inspector**
- Model: sonnet
- Task: Read `repository.py` (full file, focus on `repo_create()` and `parse_record_ids()`), `migrations/48.surrealql`, and `migrations/48_down.surrealql`. Investigate: (1) Does `parse_record_ids()` modify nested dict values? (2) Does `TYPE option<object>` in SurrealDB accept nested arrays like `table_cells: [...]`? (3) Does `connection.insert()` from the `surrealdb` Python client have known issues with large nested objects? (4) Grep the codebase for any other `TYPE option<object>` usage and check if those fields also store nested data. Return structured findings with file:line references.
- Skills: /systematic-debugging

**Subagent 3: graph-node-data-flow-auditor**
- Model: sonnet
- Task: Read `acm_extraction.py` (focus on the graph definition, node functions, and state passing). For each node in the extraction graph, document: (1) What it reads from `ExtractionState`, (2) What it writes to DB, (3) What it passes to the next node. Pay special attention to `extract_items_node` lines 1024-1090 — trace the per-row path. Also read `orchestrator.py:37-100` (`_get_docling_tables`) and `row_segmenter.py:1-80` to verify the downstream consumer expects the same JSON shape that `model_dump(mode="json")` produces. Return structured findings.
- Skills: /systematic-debugging

### Phase 2 (after subagents complete)

Synthesize all 3 subagent outputs. Apply targeted fix. Run verification.

---

## Context7 Directives

Run these at session start to load current library documentation:

1. resolve-library-id for "docling" → query-docs for "TableData model_dump export_to_dataframe table cells"
2. resolve-library-id for "surrealdb python" → query-docs for "insert record nested object field types"
3. resolve-library-id for "pydantic" → query-docs for "model_dump mode json vs python"

---

## Verification Checklist

Run these checks before marking the session complete. All must pass.

- [ ] **Diagnosis complete**: Exact layer where `docling_document_json` goes from populated to `{}` identified and documented
- [ ] **Root cause documented**: Written in `findings.md` with specific `file:line` references
- [ ] **Fix applied**: Code change resolves the empty dict issue
- [ ] **SurrealDB verified**: `SELECT docling_document_json FROM acm_table_section LIMIT 1` returns populated JSON (not `{}`)
- [ ] **Per-row path triggered**: Worker log shows `per_row` extraction, NOT `bulk fallback`
- [ ] **`docling_json_tables` non-empty**: `extract_items_node` at line 1040 enters the `if docling_json_tables:` branch
- [ ] **Row segmenter works**: `segment_multiple_tables()` produces `RawTableRow` objects from the Docling JSON
- [ ] **Node data flow verified**: Each node's output reaches the correct downstream node
- [ ] **Ground truth**: ≥29/31 records extracted (ideally 31/31 with per-row enabled)
- [ ] **No infinite re-extraction loop**: Stale detection does NOT re-trigger after successful re-extraction
- [ ] **Round-trip test**: Insert + retrieve of `docling_document_json` preserves exact data (unit test)
- [ ] **Test file updated**: `test_docling_json_storage.py` uses `model_dump(mode="json")` not `export_to_dict()`
- [ ] `uv run ruff check .` — Python lint (0 errors)
- [ ] `uv run pytest tests/ -x` — Backend tests (all pass)
- [ ] Test suite: ≥931 tests pass, 0 new failures

---

## Files Summary

| Operation | Count | Files |
|-----------|-------|-------|
| READ | ~15 | docling_adapter.py, base.py, source_commands.py, repository.py, orchestrator.py, acm_extraction.py, row_segmenter.py, metadata_and_structure.py, building_inventory.py, 48.surrealql, 48_down.surrealql, broadmeadows.json, test_docling_json_storage.py |
| MODIFY | ~5 | docling_adapter.py, source_commands.py, repository.py, 48.surrealql (or new migration), test_docling_json_storage.py |
| NEW | 3 | docling-json-fix/task_plan.md, findings.md, progress.md |
| DELETE | 0 | — |

---

## Commit Template

When work is complete, use this commit message structure:

```
fix(extraction): resolve docling_document_json empty dict — restore per-row extraction path

Root cause: [TO BE FILLED — e.g., SurrealDB TYPE option<object> rejected nested arrays].
Fix: [TO BE FILLED — e.g., changed field type to option<any>, added serialization layer].
Per-row extraction now triggers correctly. Ground truth: X/31 records.

Closes #104, unblocks #105.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```

---

## Critical Rules

1. **DIAGNOSE BEFORE FIXING** — follow /systematic-debugging strictly. Add debug logging, observe, then fix. No guessing.
2. **Preserve existing data** — do NOT delete `acm_table_section` records until the fix is verified on new data
3. **`mode="json"` everywhere** — `mode="python"` returns non-serializable enums. Any remaining `mode="python"` call is a bug.
4. **Per-row path must trigger** — the fix is not complete until `extract_items_node` enters the `if docling_json_tables:` branch at line 1040
5. **Ground truth comparison** — all findings must be contextualized against Broadmeadows expected output (1 building, 31 records)
6. **File:line references** — all findings must cite specific `file_path:line_number` locations
7. **Present before acting** — all recommendations must be presented to user before any code changes are proposed
8. **Node data flow** — verify that metadata/building/table data flows correctly between ALL graph nodes, not just the per-row path
9. **Test file discrepancy** — `test_docling_json_storage.py` uses `export_to_dict()` but real code uses `model_dump(mode="json")`. Fix the test to match reality.

---

## Quick-Start Commands

Run these at session start to establish ground state:

```bash
# 1. Confirm services are running
curl http://localhost:5055/health
docker ps | grep acm-ai-db

# 2. Check current acm_table_section state
# Run via SurrealDB REST or Python:
# uv run python -c "
# import asyncio
# from open_notebook.database.repository import repo_query
# async def check():
#     rows = await repo_query(
#         'SELECT id, string::len(raw_text) AS raw_len, docling_document_json, table_index '
#         'FROM acm_table_section ORDER BY table_index LIMIT 5;'
#     )
#     for r in rows:
#         print(f'  {r[\"id\"]}: raw_len={r[\"raw_len\"]}, docling_json={r[\"docling_document_json\"]}, idx={r[\"table_index\"]}')
# asyncio.run(check())
# "

# 3. Read the 4 key files for investigation
# docling_adapter.py, source_commands.py, repository.py, acm_extraction.py

# 4. Add debug logging and re-run extraction
```

---

## Previous Session References

- Pipeline debug findings: `docs/sprint-artifacts/pipeline-debug/findings.md` (RC8 section)
- PDF format audit findings: `docs/sprint-artifacts/pdf-format-audit/findings.md`
- Pipeline debug prompt pack: `docs/sprint-artifacts/prompt-packs/2026-03-14-pdf-format-audit.md` (RC8 investigation steps)
- GitHub issues: #104, #105, #106
