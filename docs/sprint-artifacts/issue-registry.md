# ACM-AI Issue Registry

> Generated: 2026-03-17 | Source: Pipeline fix integrity audit + 3 exploration agents
> Status: Active — tracks all known issues across the stack

---

## P0 / CRITICAL (6 issues)

These block core extraction or make features unusable.

| # | ID | Layer | Issue | File | Notes |
|---|-----|-------|-------|------|-------|
| 1 | BUG-CORRECT-BYPASS | Worker | CORRECT stage bypassed when `rejected>0, with_issues=0` — records silently discarded | `open_notebook/graphs/acm_extraction.py` (should_correct node) | Condition checks `with_issues` but not `rejected`; rejected records vanish |
| 2 | BUG-CORRECT-JSON | Worker | `_apply_ollama_extraction_settings()` not called on correction LLM — 100% Ollama failure | `open_notebook/graphs/acm_extraction.py:~2600` | Correction model gets no `format="json"` → Ollama returns prose → parse fails |
| 3 | BUG-NO-ACCESS-DEAD | Worker | No-Access recovery catch-22: per-row skips recovery, bulk has no docling data | `open_notebook/graphs/acm_extraction.py:1024-1031` | Per-row path never enters recovery; bulk path lacks docling_document_json |
| 4 | BUG-PROGRESS-STUCK | Worker/API | `extraction_progress` stuck at "running" — 58% false timeout rate | `open_notebook/extractors/pipeline_logger.py`, `commands/acm_commands.py` | Final stage never emits "completed"; frontend shows spinner forever |
| 5 | BUG-BACKFILL-500 | API | `/api/acm/backfill-buildings` crashes: `source.name` should be `source.title` | `api/routers/acm.py` | AttributeError on backfill endpoint — dead on arrival |
| 6 | BUG-HITL-INFINITE | Frontend | HITL dialog infinite re-render — ALL write operations blocked | `frontend/src/components/jobs/CrudToolRenderers.tsx` | useEffect dependency loop; dialog renders, re-renders, never stabilizes |

---

## P1 / HIGH (6 issues)

Significant bugs affecting data quality or user workflows.

| # | ID | Layer | Issue | File | Notes |
|---|-----|-------|-------|------|-------|
| 7 | BUG-TWO-BUILDING | Worker | Two-building extractions silently abort after building 1 | `open_notebook/graphs/acm_extraction.py` | `asyncio.gather` error handling swallows building 2+ failures |
| 8 | BUG-COMPOUND-SAMPLE | Worker | Compound `sample_result` values + empty correction JSON | `open_notebook/extractors/orchestrator.py` | Multi-sample results like "Positive/Negative" not split; correction returns `{}` |
| 9 | BUG-ROOM-NAME | Backend | `room_name` field misalignment — 0% recall on Alexander Hospital | `open_notebook/graphs/acm_extraction.py`, `prompts/acm/` | Prompt asks for `room_name` but schema expects `Specific_Location__c` |
| 10 | BUG-HIDDEN-TABS | Frontend | "Raw Tables" and "Log" tabs have content but no triggers (unreachable) | `frontend/src/app/(dashboard)/jobs/[id]/page.tsx` | Tab content exists but tab triggers missing from TabsList |
| 11 | BUG-REREV-NULLIFY | API/Frontend | Re-Review Buildings silently nullifies intelligence fields | `open_notebook/database/repository.py:179-203` | MERGE update with partial object zeros out unset fields |
| 12 | BUG-CLOUD-RETRY | Worker | Cloud retry fires with `model_id=None` in Ollama-only mode | `open_notebook/graphs/acm_extraction.py` | TruncationError → cloud retry → no cloud model configured → crash |

---

## P2 / MEDIUM (10 issues)

UX problems, performance issues, or data quality gaps.

| # | ID | Layer | Issue | Notes |
|---|-----|-------|-------|-------|
| 13 | UX-DASHBOARD-PRIO | Frontend | Dashboard shows Documents-first; Jobs should be primary tab | Users land on stale documents list instead of active jobs |
| 14 | UX-INSCOPE-LABEL | Frontend | "In Scope / Out of Scope" labels in Buildings tab to remove | Confusing for users; no business logic behind it |
| 15 | UX-CHAT-COLLAPSED | Frontend | Chat panel defaults to collapsed on desktop | Users don't discover chat functionality |
| 16 | UX-RETRY-FULL | Frontend | Failed building "Retry" triggers full re-extraction | Should retry only the failed building, not entire pipeline |
| 17 | BUG-500-LIMIT | Frontend | Hard 500 record limit with no pagination | Large documents truncated silently |
| 18 | BUG-BUILDING-NAMES | Worker | Building names all identical for multi-building documents | `site_name` copied to all buildings instead of per-building name |
| 19 | BUG-SAVE-TIMER | Worker | Save timer reports total pipeline time instead of DB write time | Misleading performance metrics |
| 20 | BUG-STRUCTURE-LAT | Worker | STRUCTURE stage 148-208s latency with Ollama | Metadata extraction too slow; needs prompt trimming or caching |
| 21 | UX-NAV-SPLIT | Frontend | Document title → `/source/:id`, View button → `/jobs/:id` — confusing | Two different views for same source, unclear which is "right" |
| 22 | BUG-DISTINCT-SURREAL | Backend | SurrealDB DISTINCT syntax error in CRUD buildings query | `SELECT DISTINCT building_name` not valid SurrealQL |

---

## P3 / LOW — TECH DEBT (12 issues)

Non-urgent improvements and cleanup.

| # | ID | Layer | Issue |
|---|-----|-------|-------|
| 23 | DEBT-MSG-COUNT | API | `message_count=0` hardcoded in chat endpoints |
| 24 | DEBT-MAX-OUTPUT | Backend | `max_output_tokens` hardcoded across 6+ files instead of config |
| 25 | DEBT-L3-STUB | Backend | L3 LLM Arbitration stub in ConflictResolver never implemented |
| 26 | DEBT-AREA-SYNONYM | Backend | `area_type` synonym normalization incomplete (xfail test) |
| 27 | DEBT-TOOL-LABELS | Frontend | Orphaned tool labels in `tool-labels.ts` for removed tools |
| 28 | DEBT-TS-EXPECT | Frontend | `@ts-expect-error` / `as any` casts in AddSourceDialog, CopilotKit routes |
| 29 | DEBT-DUP-BANNER | Frontend | Duplicate OfflineBanner + ConnectionGuard components |
| 30 | DEBT-LOG-NOISE | Tests | Test log contamination — no conftest.py log redirect |
| 31 | DEBT-PRE-EXISTING | Tests | 3 pre-existing test failures (stale mocks, RecordID assertion) |
| 32 | DEBT-PROGRESS-API | API | `/api/acm/extraction-progress/{id}` returns stale cached data |
| 33 | DEBT-DOCLING-CACHE | Worker | Docling re-extracts on every run — no cache/skip for existing data |
| 34 | DEBT-MIGRATION-DOWN | DB | Down migrations 50-52 may not exist as files |

---

## Cross-Reference

| Source Document | Location |
|----------------|----------|
| Pipeline debug findings | `docs/sprint-artifacts/pipeline-debug/findings.md` |
| PDF format audit | `docs/sprint-artifacts/pdf-format-audit/findings.md` |
| Docling JSON fix | `docs/sprint-artifacts/docling-json-fix/findings.md` |
| Pipeline fix integrity audit | `docs/sprint-artifacts/prompt-packs/2026-03-17-pipeline-fix-integrity-audit.md` |
| UI/UX screenshots | `docs/UI-UX-issues/*.png` |
| Dogfood report | `dogfood-output/report.md` |

---

## Resolution Tracking

When an issue is resolved, update the row:
- Add `FIXED` prefix to the Issue column
- Add commit hash to Notes
- Move to a "Resolved" section at bottom if desired
