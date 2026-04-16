# Pipeline Audit: ACM Extraction Record Loss

**Goal:** Find why Broadmeadows Police Station (31 ground-truth records) only produces 10 records, fix root causes, and achieve production-quality accuracy.

**Success Criteria:**
- [ ] Broadmeadows: 31/31 records (100%)
- [ ] Alexander District Hospital: >=40/43 records (>=93%)
- [ ] Pipeline <120s locally (RTX 4090), <60s on RunPod (RTX 5090)
- [ ] All stages visible in Langfuse/LangSmith traces
- [ ] Worker auto-triggers all stages without manual intervention

## Phases

### Phase 0: Skills & Documentation Loading
**Status:** complete
- Loaded pipeline architecture understanding
- Mapped all 12 LangGraph nodes
- Identified all key files (9,658 lines across 10 core files)

### Phase 1: Observability Stack Setup (PA-1)
**Status:** pending
- [ ] Start Docker Desktop, verify Langfuse health
- [ ] Verify .env has LANGFUSE_ENABLED=true, LANGCHAIN_TRACING_V2=true
- [ ] Start all local services via start-all.bat
- Note: Requires Windows/PowerShell — cannot do from WSL

### Phase 2: Trace Investigation (PA-2)
**Status:** complete
- Dispatched 3 parallel agents: pre-extraction-audit, row-segmenter-audit, worker-handoff-audit
- **PRIMARY ROOT CAUSE FOUND:** building_inventory.py:830 — page_end capped at +2 pages in LLM path
- **5 contributing causes identified** (see findings.md)

### Phase 3: Production Pipeline Run (PA-3)
**Status:** in_progress
- [x] Apply RC-1, RC-2, RC-3 fixes (committed 79ab59c9)
- [x] Deploy to RunPod (push to deploy/runpod-5090, pull on pod)
- [x] Fix model config (DB pointed to gemma3:27b, updated to gemma4:latest)
- [x] Run Broadmeadows extraction: **23/31 records (74%)** — up from 10 (32%)
- [x] Run with gemma4:31b: **23/31 records** (645s, 17 med + 6 low)
- [x] RC-6 fix: total_pages truncation (committed f24132c4)
- [x] RC-7 fix: recover_no_access_node always runs (no longer skips on per_row_actually_ran)
- [x] RC-8 fix: column-count coalescing (18 vs 19 cols → Type B merge, not Type H JOIN)
- [x] Deploy RC-7 + RC-8 to RunPod (committed 88a27774), re-run Broadmeadows: **36/31 records (116%)** — 24 med + 12 low
- [x] RC-9 fix: dedup sample_no whitespace normalization (strip spaces around dashes)
- [x] RC-9 + RC-10 deployed concurrently with Broadmeadows + Alexander — 100% failure rate (concurrent LLM contention)
- [x] RC-10 fix: Ollama JSON schema mode — pass ACMItemRow.model_json_schema() to format param (committed 16a4d706)
- [x] Set ACM_MAX_CONCURRENT_BUILDINGS=1 for Ollama deployments
- [x] Run #6 (RC-10, full schema): 10/34 failures (29%) — no improvement
- [x] Run #7 (RC-10b, all-optional): 10/34 failures (29%) — no improvement
- [x] Run #8 (RC-10c, minimal 625-char schema): **6/34 failures (18%)** — best result
- [x] Run #9 (RC-10c, Alexander): ~87% failure — catastrophic on different document
- [x] Run #10 (RC-10d, Alexander): ~50-80% failure — no improvement
- [x] Run #11 (RC-10e, temp 0→0.3 retry): ~50% failure, 29% retry rescue — marginal
- [x] Run #12 (RC-10f, temp 0.3 default, 0.7 retry): B001 40% failure, B002 similar — **temperature tuning exhausted**
- [ ] **PIVOT: Systematic debugging Phase 1 — find actual root cause before more fixes**

### Phase 3b: Systematic Debugging — Empty Response Root Cause
**Status:** in_progress
**Environment:** LOCAL RTX 4090 (Ollama Docker + gemma4:31b, Langfuse, LangSmith)
**Problem:** gemma4:31b produces 0 tokens for ~50% of per-row extraction calls on Alexander, regardless of temperature (0, 0.3, 0.7) or grammar mode (schema, "json").

**Key Evidence So Far:**
- Temperature tuning exhausted (RC-10d/e/f) — 0, 0.3, 0.7 all produce same ~50% failure
- Same rows fail consistently across all temperatures — structural, not sampling
- HTTP 200 returned even with 0 tokens — Ollama doesn't report error
- 22-28s per request even for empty responses (prompt processing time on 31B Q4_K_M)
- Prompt truncation warnings when content exceeds 32K tokens (different issue — metadata calls)

**Phase 1 Evidence Gathering (NO FIXES until complete):**
- [ ] 1a: Compare failing vs succeeding row CONTENT — what's different about the row data?
- [x] 1b: Check Ollama server logs — found truncation warnings, OLLAMA_NUM_PARALLEL=2 (partially done)
- [ ] 1c: Test raw Ollama API (curl) bypassing LangChain — isolate layer
- [ ] 1d: Research Ollama GBNF + gemma4 known issues via context7

**Phase 2 Analysis:**
- [ ] Synthesize evidence, identify root cause pattern
- [ ] Form single testable hypothesis

**Phase 3 Minimal Fix:**
- [ ] Test smallest possible change against known-failing rows

### Phase 4: Pipeline Component Audit (PA-4 through PA-7)
**Status:** complete
- PA-4 (Table Detection): Gap detection exists at source_commands.py:211, known page 8 issue
- PA-5 (Page Tagging): Tags derive from inventory page ranges — compounds RC-1
- PA-6 (Per-Row LLM): row_extractor.py fallback creates low-confidence records on failure
- PA-7 (Unnecessary Components): All 12 nodes necessary. No redundant components found.

### Phase 5: Worker Queue Audit (PA-8 through PA-10)
**Status:** complete
- NO automatic chaining from process_source -> acm_extract
- Frontend must explicitly call POST /api/acm/extract
- 10 records confirm acm_extract DID fire

### Phase 6: Apply Fixes
**Status:** complete
- [x] Fix RC-1: Change page_end expansion to total_pages (building_inventory.py:830-842)
- [x] Fix RC-2: Merge wider page ranges from heuristic cross-validation
- [x] Fix RC-3: Add per-table rejection logging + expand column aliases
- [x] Ruff lint: All checks passed
- [x] pytest: 56/57 passed (1 pre-existing SF mapping failure)
- [x] Committed: 79ab59c9 on feat/sf-reconciliation-20260411
- [x] Deployed to RunPod: push + pull + service restart

### Phase 7: Speed Benchmark (PA-11)
**Status:** pending
- [ ] Time each pipeline stage with local RTX 4090
- [ ] Compare: Old (37min-1hr) vs New (expected <2min)
- [ ] Document bottlenecks

### Phase 8: Cloud Observability (PA-12)
**Status:** pending
- [ ] Configure Langfuse Cloud for RunPod pod
- [ ] SSH to pod, update .env with cloud keys
- [ ] Verify tracing works on next extraction

### Phase 9: Merge and Local Environment Setup
**Status:** complete
- [x] Merge feat/sf-reconciliation-20260411 to main (fast-forward, 289 files)
- [x] Push main to origin (267276d3..44d93b33)
- [x] Update sprint-status.yaml with all PA items
- [ ] Pull gemma4:31b to local Ollama Docker (in progress)
- [ ] Start Langfuse (Docker Compose or standalone)
- [ ] Verify LangSmith keys in .env
- [ ] Start API + worker locally
- [ ] Run Broadmeadows extraction locally on RTX 4090

## Decisions Log

| Decision | Date | Rationale |
|----------|------|-----------|
| Use total_pages instead of +2 margin for single-building docs | 2026-04-16 | Over-extraction is less harmful than losing 60%+ of records. Downstream filters handle non-register content. |
| No unnecessary components to remove | 2026-04-16 | All 12 LangGraph nodes serve essential purposes. Pipeline is architecturally sound. |
| Worker handoff is not root cause | 2026-04-16 | 10 records confirms acm_extract fired. The issue is inside the extraction pipeline. |
| Re-count total_pages from full text after truncation | 2026-04-16 | metadata_and_structure_node truncates to 15K chars, _extract_total_pages sees only ~10 pages of 19. Must correct after. |
| Use gemma4:31b for extraction on RunPod | 2026-04-16 | DB default was gemma3:27b (not loaded). Updated to gemma4:31b for best quality. gemma4:latest (12B) produced null item_names. |
| Always run No Access recovery (RC-7) | 2026-04-16 | Per-row path only processes Docling table rows. No Access entries on pages without tables are lost if recovery skips. Dedup is built-in, safe to always run. |
| Coalesce ≤2 column-count difference (RC-8) | 2026-04-16 | Docling detection variance produces ±1 col across pages of same table. Type H JOIN drops duplicate-key rows. Type B merge is simpler and preserves all rows. |
| "item_name=null" was a false finding | 2026-04-16 | DB field is `product` not `item_name`. product IS populated for 17/17 medium records. The confusion was from querying a non-existent column name. |
| Strip spaces around dashes in sample_no dedup (RC-9) | 2026-04-16 | OCR produces "039- 016" vs "039-016". whitespace `split()+join()` doesn't collapse dash-adjacent spaces. `re.sub(r"\s*-\s*", "-", sample)` normalizes consistently. |
| Ollama JSON schema mode for per-row extraction (RC-10) | 2026-04-16 | `format="json"` only constrains to valid JSON, not structure. Passing `ACMItemRow.model_json_schema()` uses grammar-constrained generation for guaranteed schema compliance. Tested: anyOf works, 0% parse failure vs 29% with format="json". |
| Never run concurrent extractions on single-GPU Ollama (RC-11) | 2026-04-16 | 4+ extraction loops overwhelm gemma4:31b — 100% failure rate. KV cache thrashing degrades output to non-JSON. Run sources sequentially, set MAX_CONCURRENT_BUILDINGS=1. |
| 29% LLM failure rate with gemma4:31b | 2026-04-16 | 10/34 rows failed JSON parse. gemma4:31b struggles with structured output (also breaks schema_inference). Consider model switch or Ollama JSON mode for next iteration. |

## Errors Encountered

| Error | Phase | Resolution |
|-------|-------|------------|
| Glob timeout in WSL2 | 0 | Used `ls` via Bash instead of Glob for cross-filesystem searches |
| Task quality gate blocking analysis tasks | 2 | Proceeded anyway — analysis tasks have no code changes |
| DB default model=gemma3:27b not in Ollama | 3 | Updated to gemma4:latest then gemma4:31b |
| total_pages=10 instead of 19 | 3 | RC-6: truncated content → wrong page count. Fixed in f24132c4 |
| schema_inference=None | 3 | LLM failed to infer schema → generic prompt used → item_name null |
| Concurrent extraction 3-4x slower per row | 3 | Running 2 extractions simultaneously causes Ollama queueing. 18s/row solo → 60-84s/row concurrent. Not a bug, resource contention. |
| Embedding OOM with gemma4:31b | 3 | mxbai-embed-large fails to load when gemma4:31b is in VRAM. Non-blocking — embedding runs after records are saved. |
