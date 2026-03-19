# Session: Audit pipeline fix integrity — verify 16 fixes from 3 debug sessions survived 25 subsequent commits

## Skills to Load

/systematic-debugging — structured diagnosis before proposing fixes
/acm-observability — query Langfuse traces, inspect graph state, verify extraction health
/planning-with-files — persistent markdown plan for session continuity (task_plan.md, findings.md, progress.md already created)
/verification-before-completion — verify findings before claiming audit complete

---

## Prerequisites

Before starting this session, verify:

- SurrealDB running: `docker ps | grep acm-ai-db`
- API running: `curl http://localhost:5055/health`
- Branch: ACMV3 (should be at or ahead of `bc97792d`)
- Worker running: `uv run python run_worker.py --import-modules commands`
- Planning files exist: `task_plan.md`, `findings.md`, `progress.md` in repo root
- Prior debug findings: `docs/sprint-artifacts/pipeline-debug/findings.md`, `docs/sprint-artifacts/docling-json-fix/findings.md`

---

## Project Glossary

| Term | Definition |
|------|-----------|
| `docling_document_json` | Lossless cell-level JSON from Docling's `table.data.model_dump(mode="json")`. Stored in `acm_table_section`. Required for per-row extraction. Must have `FLEXIBLE TYPE` in SurrealDB schema. |
| Migration 51 | SurrealDB migration adding `FLEXIBLE` keyword to `docling_document_json` field. Without it, nested arrays are silently stripped. |
| `_apply_ollama_extraction_settings` | Function in `utils.py` that forces `format="json"` on Ollama models. Must be called in metadata, inventory, AND item extraction stages. |
| `ensure_record_id()` | Converts string source IDs to SurrealDB record references. Required for param binding in queries. |
| Per-row extraction | One LLM call per table row. Requires populated `docling_document_json`. Falls back to bulk if `docling_document_json` is empty/`{}`. |
| `_get_docling_tables()` | Retrieves `acm_table_section` rows for a building's page range. Page overlap logic: `page_start <= $page_end AND page_end >= $page_start`. |
| ExtractionState | LangGraph TypedDict carrying all pipeline data between nodes. |
| Stale detection | Logic in `acm_commands.py` that checks if `docling_document_json` needs re-extraction. Must check both `IS NULL` AND `= {}`. |
| Ground truth | Broadmeadows: 1 building, 31 records. Alexander: 5 buildings, 43 records. |
| RC1-RC8 | Root cause identifiers from pipeline debug session. RC8 = empty `docling_document_json`. |
| C1/C2/C3/H1/M2 | Fix identifiers from PDF format audit session. C = Critical, H = High, M = Medium. |
| Skill | Markdown instruction set for Claude Code activated via `/skill-name`. |
| Subagent | Claude Code session spawned via Task tool for parallel work. |
| Plan mode | Session uses `task_plan.md` to track progress across steps. |

---

## Current State

- Branch: ACMV3 at `bc97792d` (25 commits ahead of docling-json-fix `f6441995`)
- 3 prior debug sessions applied 16 total fixes across ~15 files
- 25 subsequent commits touched several of those files:
  - `docling_adapter.py` — 3 RunPod GPU/CPU commits (7ffb01c4, 213f4ee8, d6067f47)
  - `source_commands.py` — 3 RunPod commits (same)
  - `acm_extraction.py` — 1 commit: wrong model provider fix (6fd92aaf)
  - `utils.py` — 1 commit: over-strict validation fix (6fd92aaf)
  - `orchestrator.py` — 1 commit: quantity parse crash (c0832fa8)
  - `building_inventory.py` — 2 commits: dedup + site name (54e188da, cb99a3aa)
- Quick spot check (just performed): 6/16 fix signatures verified present via grep
- Unknown: whether data in SurrealDB reflects fixes or is stale from before fixes

---

## Key Files

**Audit targets (READ — check fix signatures):**
- `D:/ailocal/acm-ai/open_notebook/extractors/providers/docling_adapter.py` — `model_dump(mode="json")` at ~line 165
- `D:/ailocal/acm-ai/open_notebook/extractors/metadata_and_structure.py` — `_apply_ollama_extraction_settings` call
- `D:/ailocal/acm-ai/open_notebook/extractors/building_inventory.py` — `_apply_ollama_extraction_settings` + dedup fix
- `D:/ailocal/acm-ai/open_notebook/graphs/acm_extraction.py` — per-row path, diagnostic query fix
- `D:/ailocal/acm-ai/open_notebook/graphs/utils.py` — `_apply_ollama_extraction_settings` function def
- `D:/ailocal/acm-ai/open_notebook/extractors/orchestrator.py` — `_get_docling_tables()` page overlap, area_type mapping, material_description fallback
- `D:/ailocal/acm-ai/commands/source_commands.py` — `_store_docling_tables()`, PyMuPDF page markers
- `D:/ailocal/acm-ai/commands/acm_commands.py` — stale detection `IS NULL OR = {}`, `ensure_record_id`
- `D:/ailocal/acm-ai/open_notebook/database/repository.py` — `repo_create()`, `parse_record_ids()`
- `D:/ailocal/acm-ai/migrations/51.surrealql` — `FLEXIBLE TYPE option<object>`
- `D:/ailocal/acm-ai/prompts/acm/metadata_and_structure.jinja` — shortened template
- `D:/ailocal/acm-ai/prompts/acm/building_inventory.jinja` — shortened template
- `D:/ailocal/acm-ai/prompts/acm/row_split.jinja` — example-based template

**Test files (READ — check test alignment):**
- `D:/ailocal/acm-ai/tests/test_docling_json_storage.py` — `TestDoclingAdapterModelDump` class
- `D:/ailocal/acm-ai/tests/test_building_inventory.py` — updated assertions
- `D:/ailocal/acm-ai/tests/test_building_inventory_merge.py` — merge-specific tests

**Ground truth (READ):**
- `D:/ailocal/acm-ai/benchmarks/ground_truth/broadmeadows.json` — 31 records, 1 building

**Prior findings (READ for context):**
- `D:/ailocal/acm-ai/docs/sprint-artifacts/pipeline-debug/findings.md`
- `D:/ailocal/acm-ai/docs/sprint-artifacts/pdf-format-audit/findings.md`
- `D:/ailocal/acm-ai/docs/sprint-artifacts/docling-json-fix/findings.md`

**Modify (only if regressions found):**
- Any file where a fix was overwritten

---

## Plan

Read `task_plan.md` before starting. Update it as you work.

### Task Plan Reference
- task_plan.md: `D:/ailocal/acm-ai/task_plan.md`
- findings.md: `D:/ailocal/acm-ai/findings.md`
- progress.md: `D:/ailocal/acm-ai/progress.md`

### Execution Strategy

**Phase 1 — Automated Fix Signature Audit**

Run these grep checks systematically. For each fix, record PRESENT / ABSENT / MODIFIED in `findings.md`.

```bash
# F1: format="json" on metadata LLM
grep -n "_apply_ollama_extraction_settings" open_notebook/extractors/metadata_and_structure.py

# F2: format="json" on inventory LLM
grep -n "_apply_ollama_extraction_settings" open_notebook/extractors/building_inventory.py

# F3: Shortened prompts (check line counts)
wc -l prompts/acm/metadata_and_structure.jinja prompts/acm/building_inventory.jinja prompts/acm/row_split.jinja

# F4: WebSocket retry
grep -n "for attempt in range" open_notebook/extractors/orchestrator.py

# F5: Stale detection
grep -n "IS NULL OR.*= {}" commands/acm_commands.py

# F6: ensure_record_id in stale check
grep -n "ensure_record_id" commands/acm_commands.py

# F7: Page overlap logic
grep -n "page_start <= \$page_end" open_notebook/extractors/orchestrator.py

# F8: Diagnostic query fix
grep -n "IS NONE OR.*= {}" open_notebook/graphs/acm_extraction.py

# C1: area_type mapping
grep -rn "area_type" open_notebook/extractors/orchestrator.py open_notebook/graphs/acm_extraction.py

# C2: material_description fallback
grep -rn "material_description" open_notebook/extractors/orchestrator.py

# C3: PyMuPDF page markers
grep -rn "Page.*marker\|pymupdf\|fitz" commands/source_commands.py open_notebook/extractors/

# H1: ARA header detection
grep -rn "one.line.*header\|single.*building.*header" open_notebook/extractors/building_inventory.py

# M2: sample_result
grep -rn "sample_result" open_notebook/extractors/row_extractor.py open_notebook/graphs/acm_extraction.py

# Migration 51
cat migrations/51.surrealql

# Test file fix
grep -n "TestDoclingAdapterModelDump" tests/test_docling_json_storage.py
```

**Phase 2 — Live Data Verification**

Query SurrealDB to verify data state:

```python
# Run via: uv run python -c "..."
import asyncio
from open_notebook.database.repository import repo_query

async def audit():
    # 2.1: docling_document_json populated?
    rows = await repo_query(
        "SELECT id, docling_document_json FROM acm_table_section LIMIT 3"
    )
    for r in rows:
        dj = r.get("docling_document_json")
        print(f"  {r['id']}: type={type(dj).__name__}, truthy={bool(dj)}, keys={list(dj.keys()) if isinstance(dj, dict) else 'N/A'}")

    # 2.2: building names clean?
    buildings = await repo_query("SELECT building_code, building_name FROM building_record LIMIT 5")
    for b in buildings:
        print(f"  {b.get('building_code')}: {b.get('building_name')}")

    # 2.3: record count
    count = await repo_query("SELECT count() as cnt FROM acm_record GROUP ALL")
    print(f"  Total ACM records: {count[0].get('cnt') if count else 0}")

asyncio.run(audit())
```

**Phase 3 — Observability Check**

Use /acm-observability to:
1. Query latest Langfuse traces for extraction runs
2. Check if `format="json"` appears in model kwargs
3. Check if per-row or bulk path was used
4. Look for any validation errors or silent failures

**Phase 4 — Fix any regressions found**

**Phase 5 — Final verification**

---

## Agent Strategy

Strategy: SUBAGENT-DISPATCH
Use the Task tool to run Phase 1 audit checks in parallel with Phase 2 data queries.
**All subagents should use `model: "sonnet"`.**

Subagents:
- **code-auditor**: Run all Phase 1 grep checks against current HEAD. Return structured table of fix status.
- **data-auditor**: Run Phase 2 SurrealDB queries. Return data state summary.
- **synthesizer**: After both complete, compare results, identify regressions, propose fixes.

---

## Context7 Directives

Run these at session start to load current library documentation:

1. resolve-library-id for "surrealdb python" → query-docs for "FLEXIBLE field type nested object insert"
2. resolve-library-id for "docling" → query-docs for "TableData model_dump export cells"
3. resolve-library-id for "pydantic" → query-docs for "model_dump mode json"

---

## Verification Checklist

All must pass before marking the audit complete:

- [ ] All 16 fix signatures verified PRESENT in current HEAD (or justified as intentionally replaced)
- [ ] Migration 51 (`FLEXIBLE TYPE`) applied in running SurrealDB instance
- [ ] `docling_document_json` populated in `acm_table_section` (not `{}`)
- [ ] Per-row extraction path reachable (code path exists + data supports it)
- [ ] `_apply_ollama_extraction_settings` called in metadata, inventory, AND item extraction
- [ ] Page overlap logic in `_get_docling_tables()` uses `<=` / `>=` (not containment)
- [ ] Stale detection checks both `IS NULL` and `= {}`
- [ ] Building names are clean strings (not pipe-delimited table data)
- [ ] Record count ≥ 29 for Broadmeadows source (ground truth: 31)
- [ ] `uv run pytest tests/ -x` — all pass
- [ ] `uv run ruff check .` — lint clean
- [ ] findings.md updated with complete audit results
- [ ] progress.md updated with session summary

---

## Files Summary

| Operation | Count | Files |
|-----------|-------|-------|
| READ (audit) | ~20 | All key extraction/pipeline files + migrations + tests + prior findings |
| MODIFY (if regression) | 0-5 | Only files where fixes were overwritten |
| NEW | 0 | — |
| DELETE | 0 | — |

---

## Commit Template

```
fix(extraction): restore pipeline fixes after 25-commit drift audit

Verified 16 fixes from 3 debug sessions (pipeline-debug, pdf-format-audit, docling-json-fix).
[X/16 intact, Y restored]. Per-row extraction path confirmed working.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
```

---

## Critical Rules

1. **READ BEFORE MODIFYING** — this is an audit. Do NOT change code unless a regression is confirmed.
2. **Evidence-based** — every fix status must cite file:line and grep output.
3. **Update planning files** — task_plan.md checkboxes, findings.md tables, progress.md summary after each phase.
4. **Ground truth anchored** — all data checks must reference Broadmeadows (31 records) or Alexander (43 records).
5. **Observability first** — use Langfuse traces to verify runtime behavior, not just static code analysis.
6. **Present before fixing** — if a regression is found, document it in findings.md and present to user before applying any fix.
