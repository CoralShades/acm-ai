# Pipeline Audit Progress Log

## Session: 2026-04-16 (current)

### Entry 1: Kickoff and Architecture Mapping
- Loaded /pipeline-audit skill command
- Read sprint-status.yaml — confirmed pipeline-audit items exist
- Glob timed out on WSL2 cross-filesystem — switched to Bash ls
- Identified 10 core pipeline files (9,658 lines total):
  - acm_extraction.py (3,514 lines — main LangGraph graph)
  - source_commands.py (843 lines — process_source command)
  - acm_commands.py (652 lines — acm_extract command)
  - row_segmenter.py (1,140 lines — deterministic row parser)
  - building_inventory.py (887 lines — building identification)
  - orchestrator.py (631 lines — per-building extraction)
  - row_extractor.py (511 lines — per-row LLM extraction)
  - page_tagger.py (477 lines)
  - schema_inference.py (762 lines)
  - docling_adapter.py (241 lines)

### Entry 2: Parallel Agent Dispatch (PA-2)
- Dispatched 3 agents simultaneously:
  1. `pre-extraction-audit` (acm-extraction-pre) — building inventory + page tagging
  2. `row-segmenter-audit` (acm-extraction-core) — row segmentation logic
  3. `worker-handoff-audit` (backend-specialist) — command trigger chain
- All 3 completed within ~83s
- Found 5 PEA findings, 6 RSA findings, full trigger chain mapped

### Entry 3: Root Cause Confirmed
- Read building_inventory.py:830-842 — found `_PAGE_END_EXPANSION_MARGIN = 2`
- Read building_inventory.py:618-627 — found correct fix already in heuristic path
- Confirmed: LLM path uses +2 cap, heuristic path uses total_pages
- Cross-validation at line 846 can't fix because it only ADDS buildings, not extends
- This is the PRIMARY root cause: explains 15-20 record loss

### Entry 4: Audit Document Written
- Created `docs/sprint-artifacts/observability/pipeline-audit-2026-04-16.md`
- Full pipeline architecture map (12 nodes, purpose, LLM calls)
- Root cause analysis (RC-1 through RC-5)
- Fix priority table
- Speed analysis

### Entry 5: Planning Files Created
- Created task_plan.md, findings.md, progress.md (this file)
- Phases 0, 2, 4, 5 marked complete
- Phases 1, 3, 6, 7, 8 pending

### Entry 6: Fixes Applied
- RC-1: Changed `_PAGE_END_EXPANSION_MARGIN = 2` to `bld.page_end = total` in building_inventory.py:830-842
- RC-2: Changed cross-validation to extend page ranges for matching buildings (building_inventory.py:846-880)
- RC-3: Added per-table rejection logging in row_segmenter.py:765-784 + 7 new column aliases
- Ruff lint: All checks passed
- Files changed: building_inventory.py (+52/-23 lines), row_segmenter.py (+29/-1 lines)

### Entry 7: Deployed to RunPod + First Production Test
- Committed fixes: `79ab59c9` on `feat/sf-reconciliation-20260411`
- Pushed to `origin/deploy/runpod-5090` — fast-forward pull on pod
- Restarted API + worker tmux sessions
- All 6 services healthy: SurrealDB, Ollama (5 models), API, Worker, Frontend, Tunnel
- **Model config issue found**: DB `default_extraction_model` pointed to `gemma3:27b` (not loaded in Ollama). Updated to `gemma4:latest` (`model:sddrd1n6kofnzqmykd26`)

### Entry 8: Broadmeadows Extraction Run #1 (gemma4:latest)
- Source: `source:4kbzs3tpsvfdl9hrlr2t` ("Boradmeadows.pdf")
- Previous: **10 records** → Now: **23 records** (74% of 31 ground truth)
- Pipeline time: 250s (4m 10s) — slower than expected due to per-row LLM latency with gemma4
- Key metrics:
  - register_start=5, page_end=18 (full range captured — RC-1 fix working)
  - RC-2 cross-validation extended B001 page range from [13-18] to [5-18]
  - 24 rows segmented from Docling tables on pages 5-7
  - 3 tables on pages 11-13 correctly rejected (sample analysis, not ACM register)
  - 4 tables excluded by page range filter (pages 1-4, before register start)
  - 24 extracted → 1 dedup → 23 saved
  - Confidence: 19 medium, 4 low (fallback records from JSON parse failures)
- **Data quality issue**: ALL 23 records have `item_name=null`, `item_description=null`
  - gemma4:latest (12B) extracts `floor_level` and `sample_no` but not item/description
  - This is a model capability issue, not a pipeline bug
- **Missing 8 records**: Pages 8-10 have no Docling tables (RC-4: TableFormer detection gap)

### Entry 9: RC-6 Found and Fixed (total_pages truncation)
- **Bug**: `metadata_and_structure_node` truncates content to 15K chars for LLM, but `_extract_total_pages()` ran on this truncated text → returned 10 instead of 19
- **Impact**: Building page_end expansion (RC-1 fix) used 10 instead of 19
- **Fix**: After calling `extract_metadata_and_structure`, re-count total_pages from FULL text
- **Committed**: `f24132c4` — deployed to RunPod
- **Verified**: Log shows `total_pages corrected from 10 to 19`, `expanding page_end from 8 to 19`

### Entry 10: Broadmeadows Extraction Run #3 (gemma4:31b + RC-6)
- Completed: 23 records in 645s, page range [5-19] ✓
- 12 tables total, 6 excluded by page filter, 3 rejected by _is_acm_table()
- 24 rows extracted from 3 Docling tables (pages 5-7)
- Pages 8-10 still have no Docling tables (RC-4: TableFormer gap persists)

## Session 2: 2026-04-16 (continued)

### Entry 11: Corrected Data Quality Finding
- **Previous "item_name=null" finding was WRONG** — `acm_record` table has `product` field, not `item_name`
- Queried RunPod SurrealDB: `product` IS populated for 17/17 medium-confidence records
- Good values: "Vinyl sheet (cream)", "Fibre cement sheet", "mastic (grey)", "Hessian back sheet vinyl (dark grey)"
- 1 medium record has literal string "null" for product (LLM returned "null")
- 6 low-confidence records: 3 "Unknown" (fallback), 2 with actual data, 1 garbage

### Entry 12: Ground Truth Page Analysis
- Pages 5-7: ~30 register entries in raw text
- Page 8: 2 "No Access" entries (Docling missed this table)
- Pages 9-10: Lab analysis cover page/letter (NOT register data)
- Pages 11-12: Lab sample analysis tables (NOT register)
- Pages 13+: Assessment report text (NOT register)
- Total ground truth: ~32 entries (30 register + 2 No Access)
- Docling tables: 3 tables (pages 5, 6, 7), columns 18/18/19 per page, 12 rows each

### Entry 13: RC-7 Fix Applied — No Access Recovery
- `recover_no_access_node` at acm_extraction.py:2682 was skipping when `per_row_actually_ran=True`
- Fix: removed early return, always run recovery with dedup against existing records
- Also fixed BUG-NO-ACCESS-DEAD: now iterates all buildings in inventory instead of just context building
- Tests: 42 passed, 0 new failures

### Entry 14: RC-8 Fix Applied — Column Count Coalescing
- Docling tables on pages 5-6 had 18 cols, page 7 had 19 cols (detection variance)
- This triggered Type H JOIN path instead of simpler Type B merge
- Type H JOIN can drop rows with duplicate key values (RSA-2 finding)
- Fix: coalesce column-count groups with ≤2 difference into single group for Type B merge
- Added to row_segmenter.py at line 816-835
- Tests: 42 passed, 0 new failures

## Session 3: 2026-04-16 (continued)

### Entry 15: Broadmeadows Run #4 (RC-7+RC-8, gemma4:31b)
- Deployed commit `88a27774` (RC-7+RC-8) to RunPod
- Extraction completed: **36 records** in 907s (15m 7s)
- Confidence: 24 medium + 12 low (0 high)
- **34 rows segmented** (up from 24) — RC-8 column coalescing confirmed working
- **3 No Access records recovered** — RC-7 confirmed working (Lift Foyer, Ceiling Space, Main Foyer)
- Row extraction failures: 10/34 (29%) — gemma4:31b JSON parse failures
- Failed rows: 3, 10, 17, 22, 27, 29, 31, 32, 33, 34
- Dedup issues found: sample_no whitespace ("34511-039- 016" vs "34511-039-016")
- True unique count after manual dedup: ~33-34 records (vs 31 ground truth)
- Embedding failed: mxbai-embed-large model OOM (gemma4:31b uses all VRAM)

### Entry 16: RC-9 Fix — Dedup sample_no whitespace
- Added `re.sub(r"\s*-\s*", "-", sample)` to `_generate_dedup_key()` at acm_extraction.py:254
- Strips spaces around dashes in sample_no for consistent dedup keys
- Also investigated schema_inference failure: `parse_json_response` raises ValueError when gemma4:31b returns non-JSON — model capability issue

### Entry 17: Concurrent Extraction Run #5 (RC-9, Broadmeadows + Alexander)
- Both triggered concurrently — Broadmeadows (34 rows, 1 building) + Alexander (102 rows, 6 buildings)
- Alexander buildings: Mortuary (10), Myrtle Street (10), VMO Accommodation (14), Nurses (3), Main Hospital (57), Pathology (8)
- **100% failure rate** — concurrent extraction of 4+ building loops overwhelms gemma4:31b
- Zero successful row extractions visible in logs — all produce fallback records
- Ollama serializes CUDA compute; 4+ concurrent LLM call streams thrash KV cache
- Solo extraction (Run #4) had 71% success; concurrent drops to ~0%

### Entry 18: RC-10 — Ollama JSON Schema Mode
- **Research**: Ollama supports `format=<json_schema_dict>` (not just `format="json"`)
- **ChatOllama**: `format` field type is `Union[Literal['', 'json'], dict, None]` — accepts dict ✓
- **Pydantic**: `ACMItemRow.model_json_schema()` generates valid schema (3348 chars, 16 fields, `anyOf` for Optional)
- **Live test**: gemma4:31b on RunPod with full ACMItemRow schema → valid JSON, correct field population, 36.6s
- **anyOf pattern**: `anyOf: [{type: "string"}, {type: "null"}]` works correctly with Ollama 0.20.7
- **Pydantic validation**: Sparse output (only populated fields) validates OK — missing fields get null defaults
- **Implementation**:
  - `_apply_ollama_extraction_settings()` accepts optional `schema_dict` param
  - `_inject_response_format()` passes schema through for Ollama
  - `extract_items_node` sets `ACMItemRow.model_json_schema()` on row model
- **Committed**: `16a4d706` — RC-10 Ollama JSON schema mode

### Entry 19: Run #6 — RC-10 with required item_name (same failure rate)
- Deployed RC-10 (commit 16a4d706) to RunPod, restarted services
- Deleted stale records (113 from concurrent runs)
- Broadmeadows Run #6: **36 records** in ~16 min (same as Run #4)
- **10/34 rows failed (29%)** — SAME as without schema mode
- All failures: `raw_response_preview=<empty>` — grammar deadlock
- Root cause: `item_name: str` is the only required field. Grammar can't produce valid JSON when the model can't determine item_name from ambiguous row data
- Ollama server crash during embed phase (mxbai-embed-large OOM) — not related to extraction
- Data quality for successful rows: similar to Run #4 (medium confidence records have good products)

### Entry 20: RC-10b — All-optional schema (commit 23d2a05a)
- Made `item_name: Optional[str]` in ACMItemRow
- RC-10 block now pops `required` from schema before passing to Ollama
- Added diagnostic log: `model.format=schema|'json'` at row extraction start
- Verified with context7: Ollama docs confirm format param accepts dict, no required = all optional
- Run #7 triggered, pending results

### Entry 21: Run #7 — RC-10b all-optional Pydantic schema
- Same 10/34 failures (29%), same rows as Run #4/6
- 24 medium + 12 low, 36 total records
- All 36 have non-null product (slight improvement over Run #4)
- Grammar deadlock is NOT caused by required fields — it's the schema complexity

### Entry 22: Run #8 — RC-10c minimal schema (commit 469959f2)
- **6/34 failures (18%)** — down from 10 (29%)!
- Minimal schema: 625 chars vs 3369, no anyOf/title/description/default
- Rows 2, 9, 16, 21 (always failed before) NOW SUCCEED
- Rows 27, 29, 31, 32, 33, 34 still fail (end of table + second table)
- 24 medium + 12 low, 36 total (same breakdown — 4 new successes rated low)
- Literal "null" string issue: `{type: "string"}` grammar produces "null" instead of JSON null
- Pipeline time: ~15 min extraction (34 rows × ~25s/row)

## Run Comparison Table

| Run | RC | Schema Format | Failures | Rate | Records | Change |
|-----|-----|--------------|----------|------|---------|--------|
| #4 | RC-7/8 | format="json" | 10/34 | 29% | 36 | baseline |
| #6 | RC-10 | full Pydantic schema (3369 chars) | 10/34 | 29% | 36 | no change |
| #7 | RC-10b | all-optional Pydantic (3369 chars) | 10/34 | 29% | 36 | no change |
| #8 | RC-10c | minimal schema (625 chars) | 6/34 | 18% | 36 | **-4 failures** |

### Entry 23: Alexander Baseline — RC-10c (commit 469959f2, Run #9)
- **Alexander District Hospital** — first extraction attempt
- 6 buildings identified, total_pages corrected 6→34 (RC-6 working)
- **Catastrophic failure rate: ~80-90% across all buildings**
- Grammar sampler deadlocks on nearly every row (all empty responses)
- Killed after B005 row 7/57 — baseline established, no point waiting

| Building | Rows | Failures | Rate |
|----------|------|----------|------|
| B001 Myrtle Street | 10 | ~5 | 50% |
| B002 Mortuary | 10 | ~8 | 80% |
| B003 Pathology | 8 | ~7 | 88% |
| B004 VMO | 14 | ~12 | 86% |
| B005 Main Hospital | 57 | 7/7 so far | ~100% |
| B006 Nurses | 3 | - | pending |

**Conclusion:** RC-10c minimal schema grammar is fundamentally broken for Alexander on gemma4:31b. Hybrid retry (RC-10d) needed.

### Entry 24: Alexander RC-10d Run Started (commit 51e50a1a, Run #10)
- Killed baseline run, restarted worker with RC-10d
- RC-10d: attempt 1 = schema grammar, attempt 2 = format="json" fallback
- Also includes null-string scrub ("null"→None before Pydantic validation)
- Extraction triggered at 04:05:05 UTC, pre-extraction stages in progress
- total_pages corrected 6→34 (confirmed)

## Run Comparison Table

| Run | RC | Schema Format | Failures | Rate | Records | Change | Document |
|-----|-----|--------------|----------|------|---------|--------|----------|
| #4 | RC-7/8 | format="json" | 10/34 | 29% | 36 | baseline | Broadmeadows |
| #6 | RC-10 | full Pydantic schema (3369 chars) | 10/34 | 29% | 36 | no change | Broadmeadows |
| #7 | RC-10b | all-optional Pydantic (3369 chars) | 10/34 | 29% | 36 | no change | Broadmeadows |
| #8 | RC-10c | minimal schema (625 chars) | 6/34 | 18% | 36 | **-4 failures** | Broadmeadows |
| #9 | RC-10c | minimal schema (625 chars) | ~39/45 | ~87% | killed | catastrophic | Alexander |
| #10 | RC-10d | hybrid (schema→json retry) | pending | - | - | - | Alexander |

### Entry 25: RC-10e + Dynamic num_ctx (commit 482eaa0b)
- **RC-10e**: On retry, bump `temperature=0` → `temperature=0.3` alongside `format="json"` fallback
- Root cause: `temperature=0` causes gemma4:31b to deterministically produce 0 tokens for certain row inputs
- The grammar deadlock was a red herring — the model generates nothing regardless of format mode
- RC-10d proved this: format="json" retry (attempt 2) also produced `<empty>` for the same rows
- A small temperature introduces enough randomness to break the deterministic degenerate path
- **Dynamic num_ctx**: Added `_get_ollama_model_context_length()` to query Ollama `/api/ps`
- Priority: `OLLAMA_NUM_CTX` env > `/api/ps` auto-detection > 32768 fallback
- Corrected docstring: Ollama default is 4096 (not 8192), confirmed via context7
- Ruff: passed, pytest: 45 passed (1 pre-existing SF mapping failure)
- Pushed to `deploy/runpod-5090`, ready to deploy after Run #10 completes

### Entry 26: Alexander RC-10d Results (Run #10, killed after B004)
- B001-B004 completed before kill. RC-10d hybrid retry (format switch) confirmed ineffective
- All attempt 2 (format="json") also produced `<empty>` — proving the issue is NOT grammar-related

### Entry 27: Alexander RC-10e Results (Run #11, killed after B002)
- B001 Myrtle Street: 5 first failures → **4 final** (1 rescued by temp=0.3) = **40%** fail
- B002 Mortuary: 9 first failures → **6 final** (3 rescued by temp=0.3) = **60%** fail
- **Overall retry rescue rate: 4/14 = 29%**
- Improvement over RC-10d: B001 50%→40%, B002 80%→60%
- Temperature perturbation (0→0.3 on retry) helps ~30% of failed rows
- But first-attempt failures still high because temperature=0 is the default

### Entry 28: RC-10f — Temperature 0.3 default (commit 41a5bf30)
- Changed per-row extraction temperature from 0 to **0.3** as default
- Env-configurable: `ACM_ROW_EXTRACTION_TEMPERATURE=0.3`
- Retry temperature bumped from 0.3 to **0.7**
- Hypothesis: many rows fail at temperature=0 but succeed at 0.3 on first attempt
- Run #12 triggered on Alexander with RC-10f

## Run Comparison Table

| Run | RC | Temperature | Failures | Rate | Records | Change | Document |
|-----|-----|-----------|----------|------|---------|--------|----------|
| #4 | RC-7/8 | 0 | 10/34 | 29% | 36 | baseline | Broadmeadows |
| #8 | RC-10c | 0 | 6/34 | 18% | 36 | **-4 failures** | Broadmeadows |
| #9 | RC-10c | 0 | ~39/45 | ~87% | killed | catastrophic | Alexander |
| #10 | RC-10d | 0 (retry: 0) | killed | ~50-80% | killed | no improvement | Alexander |
| #11 | RC-10e | 0 (retry: 0.3) | 10/20* | ~50% | killed | marginal (29% rescue) | Alexander |
| #12 | RC-10f | **0.3** (retry: 0.7) | pending | - | - | - | Alexander |

\* Run #11 only completed B001+B002 (20 rows total)

### Entry 29: Alexander RC-10f Run #12 Results (B001-B004 observed)
- **Temperature=0.3 default, 0.7 retry — NO IMPROVEMENT over temp=0**
- B001 Myrtle Street (10 rows): ~4/10 failures (40%) — same as RC-10e
- B002 Mortuary Buildings (10 rows): ~5/10 failures (50%)
- B003 Pathology Department (8 rows): 8/8 records produced but same pattern
- B004 VMO Accommodations (14 rows): ~7/14 failures (50%) — in progress when killed
- **CONCLUSION: Temperature tuning exhausted**. 0, 0.3, 0.7 all produce identical ~50% failure rates.
- The empty response issue is structural to gemma4:31b + certain row inputs, not sampling-related.

### Entry 30: Merge to Main + Push to Origin
- **Merged** feat/sf-reconciliation-20260411 → main (fast-forward at 44d93b33)
- **Pushed** main to origin (267276d3..44d93b33, 289 files)
- RunPod continues on deploy/runpod-5090 branch — client unaffected
- Client's Parks Victoria extraction (source:zf6opyipahvo8j9d64b9) completed bulk mode with 38 records

### Entry 31: Local Environment Inventory
- SurrealDB: Docker, healthy on port 8000
- Ollama Docker: running but unhealthy, has 14 models including gemma3:27b, qwen3:32b — NO gemma4:31b
- gemma4:31b pull initiated (background)
- Langfuse: NOT running — not in docker-compose.yml, localhost:3000 unreachable
- LangSmith: keys configured in .env (LANGCHAIN_TRACING_V2=true)
- Langfuse keys: configured in .env pointing to localhost:3000 (needs service)

## Run Comparison Table (FINAL)

| Run | RC | Temperature | Failures | Rate | Records | Change | Document |
|-----|-----|-----------|----------|------|---------|--------|----------|
| #1 | RC-1/2/3 | 0 | - | - | 23 | +13 from baseline 10 | Broadmeadows |
| #3 | RC-6 | 0 | - | - | 23 | total_pages fix | Broadmeadows |
| #4 | RC-7/8 | 0 | 10/34 | 29% | 36 | +13 (row coalescing + No Access) | Broadmeadows |
| #6 | RC-10 | 0 | 10/34 | 29% | 36 | full schema — no change | Broadmeadows |
| #7 | RC-10b | 0 | 10/34 | 29% | 36 | all-optional — no change | Broadmeadows |
| #8 | RC-10c | 0 | 6/34 | 18% | 36 | **minimal schema -4 failures** | Broadmeadows |
| #9 | RC-10c | 0 | ~39/45 | ~87% | killed | catastrophic on Alexander | Alexander |
| #10 | RC-10d | 0 (retry: 0) | killed | ~50-80% | killed | format switch — no improvement | Alexander |
| #11 | RC-10e | 0 (retry: 0.3) | 10/20 | ~50% | killed | marginal (29% rescue) | Alexander |
| #12 | RC-10f | **0.3** (retry: 0.7) | ~16/32 | ~50% | ongoing | **temp tuning exhausted** | Alexander |

## Session 5: 2026-04-16 (continued — Docker Ollama)

### Entry 32: Environment Change — Windows Ollama removed, Docker Ollama primary
- **Windows Ollama v0.18.1 removed** — was causing PC crashes under sustained 27B model load
- **Docker Ollama v0.20.7** now primary, healthy, port-mapped `0.0.0.0:11434->11434/tcp`
- gemma3:27b (17.4GB Q4_K_M) available in Docker Ollama
- All services running: API (5055), Langfuse v3.155.1 (3000), LangSmith, Frontend (8502), SurrealDB (8000)

### Entry 33: Broadmeadows Run #13 (gemma3:27b, previous session)
- **Model switch: gemma4:31b → gemma3:27b** (RC-12 fix — gemma4 structured output defect)
- Raw API verification: 4/4 batch test passes, 0% structured output failure, 21.4 tok/s
- Full pipeline extraction: **38 records created** (31 medium + 7 low), 555s
- **0% per-row JSON parse failures** (vs 29-50% with gemma4:31b)
- 17/17 unique sample_nos matched (100% coverage of ground truth samples)
- 73 total records in DB (includes duplicates from per-row + No Access recovery paths)
- Dedup needed — same samples appear 2-6x with slightly different product descriptions

### Entry 34: Alexander Run #14 (gemma3:27b) — triggered, PC crashed before results
- Triggered via POST /api/jobs/source:qnt6w2t1h251x0y0uxpw/restart
- Command: command:ssp5bt97otk9u98vpyc0
- PC crashed (Windows Ollama overload) before extraction completed
- Need to re-run on Docker Ollama

## Session 6: 2026-04-16 (continued — crash fixes applied)

### Entry 35: GPU Crash Prevention Fixes (committed b1931c18)
- P0: OLLAMA_CONTEXT_LENGTH=4096 in docker-compose.yml (gemma3:27b VRAM 20.7→17 GiB)
- P1: ACM_DEFER_EMBEDDING=true support in acm_commands.py (Field+default_factory)
- P2: OLLAMA_KEEP_ALIVE=30m (prevents model eviction between stages)
- Healthcheck fix: curl→ollama list (curl not in image)
- Both models coexist: gemma3:27b (19GB) + mxbai-embed-large (769MB) = 21.1/24 GiB

### Entry 36: Broadmeadows Run #15 (Docker Ollama v0.20.7, ctx=4096)
- **253s (4.2 min)** — fastest yet (vs 319s ctx=32768, vs 555s Windows Ollama)
- 37 records (31 med + 6 low), 37 embedded
- **0% per-row JSON parse failures**
- **17/17 unique sample_nos matched (100%)**
- Embedding succeeded inline (both models coexist, no VRAM swap needed)
- Commit: b1931c18 (crash prevention) + 95807643 (docs)

### Entry 37: Alexander Run #15 (Docker Ollama v0.20.7, ctx=4096) — COMPLETE
- Command: command:11viygogb6vvgtbsdj1v
- **110 records** (96 medium + 14 low), **616.7s (10.3 min)**
- **0% per-row JSON parse failures** (vs 50-87% with gemma4:31b!)
- 6 buildings: B001(20), B002(9), B003(7), B004(16), B005(55), B006(3)
- **45 unique sample_nos** vs ~43 ground truth = **105% coverage**
- 110 records embedded (embedding succeeded — both models coexist)
- B005 (Main Hospital) alone produced 55 records with 36 unique samples — largest building

## Run Comparison Table (UPDATED)

| Run | Model | Env | Failures | Rate | Records | Time | Document |
|-----|-------|-----|----------|------|---------|------|----------|
| #4 | gemma4:31b | RunPod | 10/34 | 29% | 36 | ~15m | Broadmeadows |
| #8 | gemma4:31b | RunPod | 6/34 | 18% | 36 | ~15m | Broadmeadows |
| #9 | gemma4:31b | RunPod | ~39/45 | ~87% | killed | - | Alexander |
| #12 | gemma4:31b | RunPod | ~16/32 | ~50% | killed | - | Alexander |
| **#15** | **gemma3:27b** | **Docker RTX4090** | **0/34** | **0%** | **37** | **253s** | **Broadmeadows** |
| **#15** | **gemma3:27b** | **Docker RTX4090** | **0/~102** | **0%** | **110** | **617s** | **Alexander** |

### Entry 38: Langfuse Observability Verification — COMPLETE
- Queried Langfuse v3.155.1 API for both Run #15 traces
- **Broadmeadows** (trace `8626e5af814e6764ceec447c37807883`):
  - 61 observations: 19 CHAIN + 42 GENERATION, all 14 pipeline nodes traced
  - 62,092 total tokens (53,909 in / 8,183 out)
  - **0/38 per-row empty responses (0.0%)**
  - 4.0s avg inter-row latency, 248s total
- **Alexander** (trace `008e1f30c4855e81e1ac268433b93b8d`):
  - 134 observations: 19 CHAIN + 115 GENERATION, all 14 pipeline nodes traced
  - 147,614 total tokens (126,392 in / 21,222 out)
  - **10/106 per-row empty responses (9.4%)** — gemma3:27b edge case, handled by fallback
  - 4.1s avg inter-row latency, 606s total
- No ERROR-level spans in either trace
- Session IDs not set (traces findable by `metadata.source_id` instead)
- Per-row token usage very consistent: ~600-650 in, ~150 out

## Run Comparison Table (UPDATED)

| Run | Model | Env | Parse Fail | Rate | Records | Time | Document |
|-----|-------|-----|------------|------|---------|------|----------|
| #4 | gemma4:31b | RunPod | 10/34 | 29% | 36 | ~15m | Broadmeadows |
| #8 | gemma4:31b | RunPod | 6/34 | 18% | 36 | ~15m | Broadmeadows |
| #9 | gemma4:31b | RunPod | ~39/45 | ~87% | killed | - | Alexander |
| #12 | gemma4:31b | RunPod | ~16/32 | ~50% | killed | - | Alexander |
| **#15** | **gemma3:27b** | **Docker RTX4090** | **0/38** | **0%** | **37** | **253s** | **Broadmeadows** |
| **#15** | **gemma3:27b** | **Docker RTX4090** | **10/106** | **9.4%** | **110** | **617s** | **Alexander** |

### Entry 39: RunPod Deployment — COMPLETE
- Pushed main → deploy/runpod-5090 (e666f520, 17 commits)
- SSH to pod: pulled code, pulled gemma3:27b (17GB)
- Updated .env: ACM_EXTRACTION_MODEL=gemma3:27b
- Updated SurrealDB: default_extraction_model → model:gxfnicio24wqkr5gkqex
- Restarted API + worker tmux sessions, verified healthy via CF tunnel
- Raw API test: gemma3:27b 100% pass, 10.3s on RTX 5090 (full 32K context, 24GB/32GB VRAM)
- **Storage audit:** Removed gemma4:26b (17GB freed, 88%→71% usage)
- **DB cleanup:** Removed 12 orphaned model records (phi4, qwen, llama, deepseek, mistral)
- **Fixed 2 broken defaults:** default_chat_model + default_tools_model pointed to deleted phi4:latest
  - Reassigned to gemma4:latest (model:sddrd1n6kofnzqmykd26)
- **Fixed model visibility:** gemma4:31b + gemma4:latest had `type: NONE` → set to `language`
- All 5 models now visible in frontend model list

### RunPod Default Model Assignments (CURRENT)

| Purpose | Model | Size |
|---------|-------|------|
| Chat / Tools / Transformation | gemma4:latest | 9.6GB |
| **Extraction** | **gemma3:27b** | **17GB** |
| Large Context | gemma4:31b | 19GB |
| Embedding | mxbai-embed-large | 669MB |

## Next Actions
1. ~~Commit crash prevention fixes~~ — DONE (b1931c18)
2. ~~Run Broadmeadows + Alexander~~ — DONE (Run #15)
3. ~~Langfuse observability verification~~ — DONE (Entry 38)
4. ~~Deploy gemma3:27b fix to RunPod~~ — DONE (Entry 39)
5. RunPod extraction validation run (cross-environment)
6. Phase 11: Field-level quality audit (PA-14)
7. Phase 7: Speed benchmark comparison
