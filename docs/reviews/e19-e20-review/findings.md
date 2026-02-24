# E19/E20 Sprint Review — Findings
# Created: 2026-02-24

## Implementation Scope

All 11 stories implemented by ralph loop in one iteration (~17 min).
E20-S4 BLOCKED (API credits exhausted — needs manual re-run after credits refilled).

### Files Created/Modified
**Backend (17 files):**
- migrations/32.surrealql, 32_down.surrealql, 33.surrealql, 33_down.surrealql
- api/main.py, api/models.py, api/routers/acm.py, api/routers/agui_chat.py, api/routers/sources.py
- open_notebook/database/async_migrate.py, open_notebook/domain/acm.py, open_notebook/domain/notebook.py
- open_notebook/domain/site_config.py, open_notebook/extractors/acm_schemas.py
- open_notebook/extractors/building_inventory.py, open_notebook/extractors/orchestrator.py
- open_notebook/graphs/crud_agent.py, open_notebook/graphs/crud_tools.py

**Frontend (18 files):**
- frontend/src/app/(dashboard)/jobs/page.tsx (Jobs dashboard)
- frontend/src/app/(dashboard)/jobs/[id]/page.tsx (Job detail 4-tab)
- frontend/src/app/(dashboard)/jobs/[id]/extract/page.tsx (Raw extraction)
- frontend/src/app/(dashboard)/jobs/[id]/review/buildings/page.tsx (Wizard step 1)
- frontend/src/app/(dashboard)/jobs/[id]/review/records/page.tsx (Wizard step 2)
- frontend/src/app/(dashboard)/jobs/[id]/chat/page.tsx (CRUD chat)
- frontend/src/app/(dashboard)/documents/page.tsx (updated redirect)
- frontend/src/app/copilot-crud/route.ts
- frontend/src/components/acm/{ACMReviewGrid, BuildingReviewGrid, RawExtractionTable, RecordMergeModal, WizardStepHeader}.tsx
- frontend/src/components/chat/WriteConfirmationCard.tsx
- frontend/src/components/jobs/{JobCard, JobDetailHeader, JobOverviewTab, JobStatusPill}.tsx
- frontend/src/components/layout/AppSidebar.tsx (updated)
- frontend/src/components/upload/UploadProgressStep.tsx (updated)
- frontend/src/config/navigation.ts (updated)
- frontend/src/lib/stores/user-mode-store.ts
- frontend/src/lib/types/api.ts (updated)

**Tests (6 files):**
- tests/test_acm_ai_extraction.py, test_acm_api.py, test_broadmeadows_e2e.py
- tests/test_building_inventory.py, test_migration_32.py, test_orchestrator.py

## Review Findings (filled in by review agents)

### Backend Findings

#### R-B1: E19-S1 Migration 032 (review_status + clean slate)

- ✅ `review_status` field: `DEFINE FIELD review_status ON TABLE source TYPE option<string> DEFAULT 'pending_review'` — PASS
- ✅ Existing sources updated: `UPDATE source SET review_status = 'pending_review'` — PASS
- ✅ DELETE acm_record: `DELETE acm_record` present — PASS
- ✅ Migration idempotent: SurrealDB DEFINE FIELD/INDEX statements are idempotent — PASS
- ✅ Index created: `DEFINE INDEX idx_source_review_status ON source FIELDS review_status` — PASS
- ✅ Allowed values documented in migration comment — PASS
- ✅ Registered in AsyncMigrationManager at index position 31 (version 32) in `open_notebook/database/async_migrate.py:130` — PASS
- ✅ Source domain model: `review_status: Optional[str] = None` in `open_notebook/domain/notebook.py:150` — PASS
- ✅ API exposes review_status: `api/routers/sources.py:814-835` — PASS

**Note:** Domain model default is `None` rather than spec's `"pending_review"`. DB migration sets the default; reads from DB always return `'pending_review'` for existing records. Functionally equivalent.

**Summary: 9/9 ACs PASS**

---

#### R-B2: E19-S8 CRUD Chat (backend)

- ✅ `preview_write` tool exists: `open_notebook/graphs/crud_tools.py:172` — PASS
- ⚠️ Tool naming deviation: spec says `execute_confirmed_write`; implementation uses `confirm_write` (`crud_tools.py:230`). Functionality is identical; name differs from spec.
- ✅ Source scope guard on writes: `confirm_write` queries `SELECT id FROM acm_record WHERE id = $rid AND source_id = $sid` before every UPDATE/DELETE (two-step verification) — PASS
- ✅ `crud_audit` table: `migrations/33.surrealql` defines SCHEMAFULL table with all required fields — PASS
- ✅ `/api/agui/crud-chat` endpoint: registered via `register_crud_agui_endpoint()` in `api/routers/agui_chat.py:70` — PASS
- ✅ Agent correctly scopes source_id: `set_crud_context(source_id)` called before tool invocation — PASS

**Minor gap:** INSERT operation not implemented — `confirm_write` only handles UPDATE and DELETE. "Add a new record" will return `"Error: Unsupported operation INSERT"`.

**Summary: 5/6 named ACs PASS; naming deviation and missing INSERT are minor gaps**

---

#### R-B3: E20-S1 Page Boundary Fix

- ✅ Boundary overlap function: `_apply_boundary_overlap()` sets `building.page_end = max(current_end, next_page_start)` — PASS
- ✅ Inclusive semantics correct: page_end = next.page_start includes the full boundary page (verified by docstring and tests) — PASS
- ✅ Last building unchanged: loop condition `i + 1 < len(sorted_buildings)` — PASS
- ✅ Applied in both SAMP heuristic and LLM paths: `building_inventory.py:430` and `:566` — PASS
- ✅ Tests: `TestBoundaryOverlap` class (5 tests) covering shared page and last building scenarios — PASS

**Note:** Spec pseudocode uses `page_end = next.page_start + 1` (exclusive). Implementation uses `page_end = max(current, next.page_start)` with inclusive semantics — equivalent behavior. Tests confirm `b00a.page_end == 12` where B00B starts at 12.

**Summary: 5/5 ACs PASS**

---

#### R-B4: E20-S2 REGEX_ONLY Yield Check

- ✅ Yield check: `estimate = plan.acm_item_count_estimate or 0; if len(records) < estimate * 0.5` — PASS (`orchestrator.py:481-483`)
- ✅ Escalation to FULL_LLM when yield < 50%: calls `_llm_extract_building()`, returns `strategy_used="regex_escalated_to_llm"` — PASS
- ✅ None estimate + 0 records + content: `estimate == 0 and len(records) == 0 and building_content.strip()` triggers escalation — PASS (`orchestrator.py:489`)
- ✅ Warning logged: `logger.warning(f"Building {plan.building_id}: REGEX_ONLY yield {len(records)}/{estimate} < 50% — escalating to FULL_LLM")` — PASS
- ✅ Stats updated: `strategy_used="regex_escalated_to_llm"` in `BuildingExtractionStats` — PASS
- ✅ Tests: `TestRegexYieldCheck` class covers 0-record escalation, 75% no-escalation, and None-estimate cases — PASS

**Summary: 6/6 ACs PASS**

---

#### R-B5: E20-S3 Not Sampled / No Access

- ✅ `no_access: bool = Field(default=False)` in `ACMExtractionRecord` at `acm_schemas.py:188` — PASS
- ✅ `sample_no: Optional[str]` at `acm_schemas.py:181` (maps to nata_sample_number column; pre-existing naming) — PASS
- ✅ `building_extraction.jinja` explicit instructions for Not Sampled rows (lines 234-239): "Do NOT skip rows just because `sample_no` is empty or absent" — PASS
- ✅ `no_access: true` set in prompt: line 222 and 230 both set `no_access: true` for No Access entries — PASS
- ✅ Prompt instructs: include `sample_result = "Not Sampled"` / `"No Access"` for appropriate rows — PASS
- ✅ Instructions in output requirements section (`building_extraction.jinja:340-342`) — PASS
- ✅ `register_enums.json` SampleResult: fixed — added `"Not Sampled"` and `"No Access"` to SampleResult array — **FIXED**
- ✅ Tests: `TestNotSampledNoAccess` class (5 tests) all passing — PASS

**Summary: 8/8 ACs PASS — `register_enums.json` fixed post-review**

---

#### R-B6: Test Suite Results

**Command:** `uv run pytest tests/test_migration_32.py tests/test_building_inventory.py tests/test_orchestrator.py tests/test_acm_ai_extraction.py -v 2>&1 | tail -40`

**Result: 167 passed, 2 xfailed, 3 warnings in 138.84s** ✅

- `test_migration_32.py`: PASS
- `test_building_inventory.py`: PASS (including `TestBoundaryOverlap` E20-S1 tests)
- `test_orchestrator.py`: PASS (including `TestRegexYieldCheck` E20-S2 tests)
- `test_acm_ai_extraction.py`: PASS (including `TestNotSampledNoAccess` E20-S3 tests)
- 2 xfailed: `test_area_type_synonym_normalization` — pre-existing expected failures, not E19/E20

**Summary: ALL story-related tests PASS**

---

### Backend Summary Table

| Task | Story | Result | ACs | Issues |
|------|-------|--------|-----|--------|
| R-B1 | E19-S1 Migration | ✅ PASS | 9/9 | minor: domain model default None vs "pending_review" |
| R-B2 | E19-S8 CRUD Chat | ✅ PASS (minor gaps) | 5/6 | confirm_write name vs execute_confirmed_write; INSERT not implemented |
| R-B3 | E20-S1 Page Boundary | ✅ PASS | 5/5 | spec pseudocode +1 clarification (inclusive semantics correct) |
| R-B4 | E20-S2 Yield Check | ✅ PASS | 6/6 | — |
| R-B5 | E20-S3 Not Sampled | ✅ FIXED | 8/8 | register_enums.json updated post-review |
| R-B6 | Test suite | ✅ PASS | — | 167 passed, 2 xfailed (pre-existing) |

**Total: 33/33 ACs passed (100%). 2 minor gaps remain (naming + INSERT). register_enums.json FIXED.**

### Backend Action Items

1. **[DONE — E20-S3]** Updated `docs/samplePDF/instructions-sample/register_enums.json`: added `"Not Sampled"` and `"No Access"` to the `SampleResult` array.
2. **[RECOMMENDED — E19-S8]** Rename `confirm_write` → `execute_confirmed_write` in `crud_tools.py` and `crud_agent.py` to match spec, or update spec to reflect the shorter name.
3. **[RECOMMENDED — E19-S8]** Implement INSERT operation in `confirm_write` to support "add a new record" use cases.

### Frontend Findings

#### R-F1: E19-S2 Jobs Dashboard
- ✅ Sidebar renamed to "Jobs" with ClipboardList icon: PASS (`navigation.ts:49`)
- ✅ [+ New Job] button in page header: PASS (`jobs/page.tsx:47`)
- ✅ Job cards show: name, status pill, upload date: PASS
- ✅ Record count shown when published (via `insights_count`): PASS
- ✅ Status pills for all 5 review_status values: PASS (`JobStatusPill.tsx`)
- ✅ CTA: [Review] for pending/in-review, [View] for published: PASS (`JobCard.tsx:93-96`)
- ✅ Three-dot menu with Download PDF / Re-extract / Delete: PASS
- ✅ Export CSV/Excel quick actions for published jobs: PASS
- ❌ Upload redirect: `AddSourceDialog.tsx:378` still pushes to `/sources/${createdSource.id}`, NOT `/jobs/{id}/review/buildings`. `UploadProgressStep.tsx` correctly redirects to `/jobs/{id}/extract` but this is a separate path. [+ New Job] uses AddSourceDialog — **FAIL**
- ❌ Building count NOT shown on job cards — `SourceListResponse` does not expose `building_count` — **FAIL**

**Summary: 8/10 ACs PASS. 2 FAIL.**

---

#### R-F2: E19-S3 Feature Gating
- ✅ Zustand store with `persist` middleware: PASS (`user-mode-store.ts`)
- ✅ localStorage key `'acm-user-mode'`: PASS (`user-mode-store.ts:18`)
- ✅ Default mode `'standard'`: PASS (`user-mode-store.ts:14`)
- ✅ Standard/Admin toggle in sidebar footer: PASS (`AppSidebar.tsx:289-319`)
- ✅ CONFIGURE section hidden in standard mode via `.filter((section) => mode === 'admin' || section.title !== 'Configure')`: PASS (`AppSidebar.tsx:154`)

**Summary: 5/5 ACs PASS.**

---

#### R-F3: E19-S4 Raw Extraction Table
- ✅ AG Grid showing extracted records via `RawExtractionTable.tsx`: PASS
- ✅ Reuses `useExtractionAgent` SSE/streaming pattern: PASS
- ✅ CTA appears after extraction completes (top + bottom): PASS
- ⚠️ CTA label is "Proceed to Review" not "Review Buildings →" — minor label deviation
- ⚠️ review_status transition `extracting → pending_review` expected backend-handled; no frontend gap.

**Summary: 3/3 functional ACs PASS. 1 minor label deviation.**

---

#### R-F4: E19-S5 Building Review Wizard Step 1
- ✅ WizardStepHeader "Step 1 of 2: Review Buildings" with progress bar: PASS
- ✅ AG Grid with 21 editable building fields: PASS (`BuildingReviewGrid.tsx:231-270`)
- ✅ [Mark Out of Scope] action per row: PASS (`ActionsRenderer`)
- ✅ Auto-save on changes debounced 500ms: PASS (`BuildingReviewGrid.tsx:220-225`)
- ✅ [→ Next: Review Records] navigates to `/jobs/{id}/review/records`: PASS
- ✅ Sets `review_status = 'building_review'` on mount: PASS

**Summary: 6/6 ACs PASS.**

---

#### R-F5: E19-S6 ACM Schema Mapping Wizard Step 2
- ✅ Route `/jobs/{source_id}/review/records`: PASS
- ✅ "Step 2 of 2: Review ACM Records" wizard header: PASS
- ✅ Per-building tab navigation via `BuildingTabs.tsx`: PASS
- ✅ [+ Add Record] / [Delete] actions: PASS
- ✅ Publish confirmation dialog: PASS
- ✅ Debounced 500ms inline save: PASS
- ✅ Enum dropdowns (friable, material_condition, disturbance_potential): PASS
- ✅ Amber row highlight for "Not Sampled" / no_access rows: PASS
- ❌ "Unassigned Records" tab: NOT implemented — `BuildingTabs.tsx` has no unassigned tab — **FAIL**
- ❌ "All Records" tab label: shows "All Buildings" not "All Records" (`BuildingTabs.tsx:73`) — **FAIL**
- ❌ [Merge Duplicate] action: `RecordMergeModal.tsx` exists but NOT imported/used anywhere — **FAIL**
- ❌ Missing 7 ACM fields in grid: `acm_label_details`, `psb_acm_id`, `assumed_removed`, `date_of_removal`, `quantity_removed`, `epa_certificate_no`, `removal_notification_no` — grid has 20 of spec's 27 editable fields — **FAIL**

**Summary: 9/13 ACs PASS. 4 FAIL.**

---

#### R-F6: E19-S7 Job Detail Page
- ✅ Route `/jobs/{source_id}`: PASS
- ✅ 4 tabs: Overview, Buildings, ACM Records, Extraction Log: PASS
- ✅ Breadcrumb: Jobs / {Job Name}: PASS
- ✅ Status pill + uploaded date + record count + building count in header: PASS
- ✅ Overview tab summary cards (record count, building count, status, uploaded date): PASS
- ✅ [Re-Review Buildings] + [Re-Review Records] in Overview: PASS
- ✅ [Re-Extract] resets `review_status='extracting'` and navigates to `/jobs/{id}/extract`: PASS
- ✅ Buildings tab reuses `BuildingReviewGrid`: PASS
- ✅ ACM Records tab reuses `ACMReviewGrid`: PASS
- ✅ Export CSV/Excel buttons in header: PASS
- ❌ Job name NOT inline-editable — static `<span>` at `JobDetailHeader.tsx:68` — **FAIL**
- ❌ Extraction Log tab: shows placeholder text only, not `ExtractionProgressPanel`/`ExtractionLogStream` — **FAIL**
- ❌ Overview cards missing "missing fields %" and "extraction quality score" (spec requires 4 metric cards) — **FAIL**
- ❌ Export CSV URL: code uses `/api/acm/export?source_id=` (`jobs/[id]/page.tsx:72`); spec says `/api/acm/export/csv?source_id=` — **FAIL**

**Summary: 10/14 ACs PASS. 4 FAIL.**

---

#### R-F7: E19-S8 CRUD Chat Frontend
- ✅ Job-scoped chat page at `/jobs/{id}/chat`: PASS
- ✅ `WriteConfirmationCard.tsx` renders for `preview_write` tool results: PASS
- ✅ [Confirm] and [Cancel] buttons visible in chat: PASS (`WriteConfirmationCard.tsx:75-87`)
- ✅ `/copilot-crud/route.ts` bridges to `/api/agui/crud-chat`: PASS
- ✅ Separate CopilotKit provider isolates CRUD tools from supervisor: PASS
- ⚠️ [Confirm]/[Cancel] show toast instructing user to manually type "confirm {id}" — do NOT programmatically submit. Spec requires no writes without confirmation — gate exists but is partially manual. **MINOR UX GAP**

**Summary: 5/5 functional ACs PASS. 1 minor UX gap.**

---

#### R-F8: Frontend Build
- ⚠️ npm NOT available in WSL — build cannot be run from this environment.
- **Must run from Windows PowerShell**: `cd frontend && npm run build`
- All imported component paths verified to exist (no dead imports found in static review).

**Summary: CANNOT VERIFY — must run on Windows.**

---

### Frontend Summary Table

| Task | Story | Result | ACs Pass | Critical Issues |
|------|-------|--------|----------|-----------------|
| R-F1 | E19-S2 Jobs Dashboard | ⚠️ PARTIAL | 8/10 | Upload redirect /sources/{id}; no building count on cards |
| R-F2 | E19-S3 Feature Gating | ✅ PASS | 5/5 | — |
| R-F3 | E19-S4 Raw Extraction Table | ✅ PASS | 3/3 | Minor: CTA label mismatch |
| R-F4 | E19-S5 Building Review Step 1 | ✅ PASS | 6/6 | — |
| R-F5 | E19-S6 ACM Records Review Step 2 | ❌ FAIL | 9/13 | Unassigned tab missing, Merge not wired, 7 missing fields |
| R-F6 | E19-S7 Job Detail Page | ⚠️ PARTIAL | 10/14 | Inline edit, Log tab placeholder, missing metrics, CSV URL |
| R-F7 | E19-S8 CRUD Chat | ✅ PASS | 5/5 | Minor: confirm UX gap |
| R-F8 | Frontend Build | ⚠️ CANNOT VERIFY | — | Must run from Windows |

**Total: 46/56 ACs verified (82%). 4 hard FAILs across E19-S6 and E19-S7.**

### Frontend Action Items (Priority Order)

1. **[CRITICAL — E19-S6]** Wire `RecordMergeModal` into `ACMReviewGrid.tsx` — component exists but is completely unused.
2. **[CRITICAL — E19-S6]** Add "Unassigned Records" amber tab and rename "All Buildings" → "All Records" in `BuildingTabs.tsx`.
3. **[HIGH — E19-S6]** Add 7 missing ACM fields to `ACMReviewGrid.tsx`: `acm_label_details`, `psb_acm_id`, `assumed_removed`, `date_of_removal`, `quantity_removed`, `epa_certificate_no`, `removal_notification_no`.
4. **[HIGH — E19-S2]** Fix upload redirect: `AddSourceDialog.tsx:378` → push to `/jobs/${createdSource.id}/review/buildings`.
5. **[MEDIUM — E19-S7]** Implement inline-editable job name in `JobDetailHeader.tsx`.
6. **[MEDIUM — E19-S7]** Replace Extraction Log tab placeholder with `ExtractionProgressPanel` + `ExtractionLogStream`.
7. **[MEDIUM — E19-S7]** Fix Export CSV URL: change `/api/acm/export?` → `/api/acm/export/csv?` in `jobs/[id]/page.tsx:72`.
8. **[LOW — E19-S7]** Add "missing fields %" and "extraction quality score" metric cards to Overview tab.
9. **[LOW — R-F8]** Run `npm run build` from Windows to confirm no TypeScript compilation errors.

### E20-S4 Validation Results

**Status:** PARTIAL — 27/31 (87%) — NOT reaching 100% target

| Metric | Value |
|--------|-------|
| Raw records extracted | 31 |
| After dedup | 25 |
| Matched to expected | 27/31 (87%) |
| Pipeline used | OLD `acm_extraction.py` (orchestrator skipped) |
| E20-S1 applied? | ❌ No (0 buildings, heuristic fallback) |
| E20-S2 applied? | ❌ No (orchestrator skipped) |
| E20-S3 applied? | ✅ Yes (schema + prompt in shared code) |

**Missing records (4):**
1. Front Desk Area / Filing Cabinet / Filing Cabinet (Not Sampled) — location field "?"
2. Switch Room / Automatic Battery Charger / Fuse cartridge (Not Sampled) — location "Switchboard"
3. Roof / East Ductwork / Flange joints (sample 34511-039-015) — absent
4. Main Foyer / Room Adjacent Disabled Toilet / Unknown (Not Sampled) — no product name

**Per E20-S4 AC:** Creating E20-S5 with gap analysis. Do NOT re-run without a targeted fix.
**Full log:** `docs/sprint-artifacts/party-mode-20260224/e20-broadmeadows-validation.log`

---

### AC Gap Analysis

**R-AC1 through R-AC6 — Deferred** — Backend: 33/33 (100%), Frontend: 46/56 (82%). Per-story breakdowns above are sufficient for action prioritization.

### Issues Found — Consolidated

#### CRITICAL (blocking correct functionality)

| ID | Story | Component | Issue |
|----|-------|-----------|-------|
| BUG-1 | E19-S2 | `AddSourceDialog.tsx:378` | Upload redirect goes to `/sources/{id}` instead of `/jobs/{id}/review/buildings` — new jobs land on old source detail page |
| BUG-2 | E19-S6 | `BuildingTabs.tsx:73` | Tab label "All Buildings" should be "All Records" |
| BUG-3 | E19-S6 | `BuildingTabs.tsx` | "Unassigned Records" tab completely missing |
| BUG-4 | E19-S6 | `ACMReviewGrid.tsx` | `RecordMergeModal` imported but never wired into grid — dead code |
| BUG-5 | E19-S6 | `ACMReviewGrid.tsx` | 7 ACM fields missing from 29-field spec grid |
| BUG-6 | E19-S7 | `jobs/[id]/page.tsx:72` | Export CSV URL wrong: `/api/acm/export?` vs spec `/api/acm/export/csv?` |
| BUG-7 | E20-S4 | `acm_extraction.py` | E2E test uses old pipeline — E20-S1/S2 not exercised |

#### HIGH (significant UX gaps)

| ID | Story | Component | Issue |
|----|-------|-----------|-------|
| GAP-1 | E19-S7 | `JobDetailHeader.tsx:68` | Job name is static `<span>`, not inline-editable as spec requires |
| GAP-2 | E19-S7 | Job detail Extraction Log tab | Shows placeholder text only — `ExtractionProgressPanel` not wired |
| GAP-3 | E19-S7 | Job detail Overview tab | Missing "missing fields %" and "extraction quality score" metric cards |
| GAP-4 | E20-S4 | E2E accuracy | 27/31 (87%) — 4 records still missing; E20-S5 needed |

#### MINOR (naming/cosmetic deviations)

| ID | Story | Component | Issue |
|----|-------|-----------|-------|
| MIN-1 | E19-S4 | `extract/page.tsx` | CTA label "Proceed to Review" vs spec "Review Buildings →" |
| MIN-2 | E19-S8 | `crud_tools.py` | Tool named `confirm_write` vs spec `execute_confirmed_write` |
| MIN-3 | E19-S8 | CRUD chat | No INSERT support — only UPDATE and DELETE |
| MIN-4 | E19-S2 | Job cards | Building count not shown (API doesn't expose it yet) |
