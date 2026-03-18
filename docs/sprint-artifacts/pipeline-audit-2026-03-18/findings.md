# Pipeline Audit — Findings
**Date:** 2026-03-18

## F1: Pipeline Fragility — Repeated 0-Record Starts
**Evidence:** 3 separate debugging sessions (Bug Fix 11, Pipeline Debug 03-14, Dogfood 03-17) each started from 0 records.
**Root causes identified:**
- `ObjectModel.save()` returns None (not the saved object) — checks on return value silently fail
- SurrealDB record IDs (`model:xxx`) passed as model names to LLM providers → 404
- Provider model mismatch: non-Ollama model names routed to Ollama
- `_apply_ollama_extraction_settings()` overwrites caller's `num_ctx`
- Page range overlap logic (CONTAINMENT instead of OVERLAP)
- `generate_internal_id()` race condition under asyncio.gather
**Recommendation:** These are recurring patterns. Need defensive programming patterns enforced via code review + integration tests that verify the full pipeline end-to-end on known PDFs.

## F2: Prompt Quality — No Systematic Evaluation
**Evidence:** Prompts rewritten multiple times (metadata 141→56 lines, inventory 130→58 lines). Ground truth varies: Broadmeadows 28-31/31, Alexander 36-43/43.
**Root causes:**
- No automated prompt evaluation pipeline (eval harness)
- LangSmith playground used ad-hoc, no regression tests
- Per-row (9 fields) vs bulk (13 fields) field coverage gap
- Ollama models (qwen2.5) don't follow JSON instructions reliably
**Recommendation:** Set up eval-audit framework with ground truth CSV, automated scoring, and regression alerts.

## F3: Consultant Format Lock-in
**Evidence:** Pipeline tuned for 2 PDF types (SAMP + ARA). Hardcoded patterns:
- `COLUMN_ALIASES` in row_segmenter.py (hardcoded column name mapping)
- `_LEVEL_REGEX` for room/area header detection (SAMP-specific)
- `_recover_not_sampled_records_ara()` — ARA-specific regex
- Building inventory extraction assumes specific header patterns
- Pre-extraction intelligence prompts reference "SAMP" terminology
**Gap:** No mechanism to:
1. Auto-detect table schema/column layout from unknown PDFs
2. Dynamically generate column mappings
3. Create/reuse consultant format profiles
4. Fallback to LLM-driven schema inference when patterns don't match
**Recommendation:** Design a consultant format registry + LLM-driven schema inference layer.

## F4: Frontend/Backend Desync — Job Lifecycle
**Evidence:**
- SSE infrastructure exists but components are disconnected
- No `POST /api/jobs/{id}/cancel` or restart endpoint
- No duplicate extraction guard (user can upload same doc twice while processing)
- ExtractionProgressPanel shows stages but not live records
- SSE terminal event (E35-S5) implemented in backend but frontend doesn't handle `complete` event properly
- CopilotKit/AG-UI adapter crashes on `execute_write_node` AIMessage (BUG-4)
- Upload wizard has no processing state animation
**Recommendation:** 3 sessions — (1) SSE+progress fix, (2) job lifecycle API+UI, (3) live record streaming view.

## F5: Bug Fix 12 — 9 Unresolved Issues
**Issues N1-N9 from extraction audit 2026-03-12:**
- N1-N9 documented but fixes not applied
- Per-run log categorization infra built (pipeline_logger.py dirs, run_worker.py tee sink)
- 3 LangSmith observations (L1-L3) also pending
**Recommendation:** Dedicated session to triage and fix N1-N9.

## Skills Identified for Sessions

### Pipeline & Debugging
1. `systematic-debugging` — structured root-cause analysis
2. `find-bugs` — systematic bug discovery
3. `acm-observability` — Langfuse/LangSmith trace reference
4. `langgraph-fundamentals` — LangGraph workflow patterns
5. `dogfood` — E2E exploration with real data

### Prompt Quality
6. `prompt-engineering` — prompt optimization
7. `hamelsmu/evals-skills@eval-audit` — LLM evaluation framework (TO INSTALL)

### Format Adaptability
8. `aj-geddes/useful-ai-prompts@gap-analysis` — gap analysis methodology (TO INSTALL)
9. `langgraph-human-in-the-loop` — HITL for manual schema mapping

### Frontend/UX
10. `sse-streaming` — SSE implementation patterns
11. `e2e-test` — self-healing E2E tests

### Orchestration
12. `planning-with-files` — session persistence
13. `dispatching-parallel-agents` — parallel subagent work
14. `subagent-driven-development` — implementation with review gates
15. `code-review` — review audit findings

## F6: SAMP→ARA Terminology Contamination (Cross-Cutting)
**Date discovered:** 2026-03-18 (during prompt pack execution in WSL)
**Evidence:** 200+ references to "SAMP" (School Asbestos Management Plan) across the ENTIRE codebase. All documents processed by the pipeline are ARA (Asbestos Register Assessment) documents. The "SAMP vs ARA" distinction in the code is actually about consultant table formats (Clutha vs Alexander), not document types.

**Impact assessment:**
- **LLM Prompts (CRITICAL):** ~10 references telling models to look for "SAMP" patterns. This actively misleads extraction — models may look for school-specific terminology that doesn't exist in all ARA documents.
- **Pipeline Logic (HIGH):** `_SAMP_BUILDING_ID` regex gates extraction strategy (REGEX_ONLY vs FULL_LLM). Variable name implies SAMP-specific when it's actually a general building ID pattern.
- **Frontend UI (HIGH):** 11 user-visible strings say "SAMP document" — confuses users.
- **E2E Tests (MEDIUM):** 80+ references, `uploadSAMP()` function, `fixtures/samps/` directory.
- **Agent Definitions (MEDIUM):** Claude Code agents instructed to look for "SAMP" — propagates to all future sessions.
- **CLAUDE.md (MEDIUM):** Project overview loaded into every session contains "SAMP documents".

**Root cause:** Early development used "SAMP" loosely. It propagated because it was baked into CLAUDE.md, which is loaded into every AI session, which then generated more SAMP references.

**Fix:** Dedicated prompt pack created: `2026-03-18-samp-to-ara-terminology-fix.md`
**Dependencies:** Must run BEFORE Pack 3 (Multi-Consultant) and Pack 4 (Frontend UX).
**Recommendation:** This is the highest-priority fix because it affects prompt quality, pipeline logic, AND user experience simultaneously.
