# Sprint Status Board — 2026-03-28

> Auto-generated from `docs/sprint-artifacts/sprint-status.yaml`

## Summary

| Metric | Count |
|--------|-------|
| Epics | 63 total (50 done, 2 in-progress, 2 archived) |
| Stories | 236 total (216 done = 92%) |
| Bug fixes / MCS / Other | 95 (92 done) |
| **Overall Progress** | **308/331 done (93%)** |

## In Progress 🔄

| ID | Notes |
|-----|-------|
| `mcs11-jobs-source-unification-2026-03-19` | feat(ux): unify /jobs/[id] as canonical page. Phases 1-5 ALL CODE DONE (commits b06c5788,  |

## Backlog 📋

| ID | Notes |
|-----|-------|
| `e36-s5-functional-verification` | 5 SP. Verify all major features E2E with real data. |
| `e36-s6-ux-audit` | 2 SP. 3 viewports, loading/empty/error states, data-testid. |
| `e36-s7-devils-advocate-review` | 2 SP. Adversarial review of fixes and benchmark results. |
| `e36-s8-bmad-documentation-closeout` | 1 SP. Final artifact updates. |

## Recently Completed ✅ (last 15)

| ID | Notes |
|-----|-------|
| `bugfix-building-metadata-backfill-2026-03-21` | fix(extraction): Building fields (address, suburb, postcode, site_name) empty after extrac |
| `bugfix-cloud-fallback-truncation-2026-03-21` | fix(extraction): Truncation retry used model_id=None, causing Ollama to be re-provisioned  |
| `bugfix-extraction-timeout-configurable-2026-03-21` | fix(extraction): Extraction timeout was hard-coded at 1800s. Large multi-building document |
| `bugfix-notebook-name-enrichment-2026-03-21` | feat(extraction): Enrich notebook name from extracted DocumentMeta (site_name, consultant_ |
| `unified-chat-phase1-backend-2026-03-22` | feat(chat): Unified LangGraph agent replacing separate supervisor + crud graphs. thread-sa |
| `feat-auto-notebook-on-upload-2026-03-22` | feat: auto-create Notebook when PDF uploaded via POST /sources. Name from cleaned filename |
| `feat-ai-editor-rename-2026-03-22` | refactor(ui): rename "Notebooks" to "AI-Editor" in all user-facing labels. Route moved fro |
| `feat-cascade-delete-notebook-chat-2026-03-22` | fix(api): cascade-delete notebooks + chat sessions when source deleted. DELETE /sources/{i |
| `unified-chat-phase3-s1-llm-intent-router-2026-03-22` | feat(chat): LLM intent router (open_notebook/graphs/llm_router.py) with rule-based fast-pa |
| `unified-chat-phase3-s2-legacy-chat-deprecation-2026-03-22` | refactor(chat): delete 14 legacy chat files — 8 backend (supervisor_agent.py, crud_agent.p |
| `unified-chat-phase3-s3-polish-testing-2026-03-22` | chore(chat): Phase 3 polish — E2E live testing (4 queries, screenshots), prompt hardening  |
| `bugfix-page8-page-end-expansion-2026-03-23` | fix(extraction): page_end expansion for single-building docs added to LLM success path in  |
| `bugfix-docling-gap-detection-warning-2026-03-23` | fix(extraction): add Docling gap-detection warning in source_commands.py. Logs warning whe |
| `fix-chat-pipeline-async-tools-2026-03-23` | fix(chat): Convert all 16 tools to async (contextvars propagation fix), AsyncSqliteSaver r |
| `chat-debug-5-issues-2026-03-28` | fix(chat): 5 bugs resolved. #4: auto-bind unmatched $params in surreal_query (LLM-generate |

---

*Last updated: 2026-03-28 | Source: `docs/sprint-artifacts/sprint-status.yaml`*
