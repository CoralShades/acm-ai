# E19 + E20 Implementation Prompts — Ralph Loop Bundle

**Change Proposal:** SCP-20260224 (2026-02-24)
**Purpose:** Ready-to-paste Claude Code prompts for Ralph autonomous loop execution

---

## ⚠️ COST AWARENESS INJECTION (prepend to ALL extraction-related prompts)

> **CRITICAL — API COST AWARENESS:**
> Every extraction call triggers real OpenRouter spend. Do NOT run real PDF extractions during unit test development. Write all code and tests first, verify lint + unit tests pass, THEN run ONE real extraction on `docs/samplePDF/` to validate. Never re-run extraction unless a specific bug is confirmed unfixed.

---

## E19 PROMPTS — Standard User UX Redesign

---

### E19-S1: Migration 032 — Review Status

```
Implement story E19-S1: Migration 032 — Add review_status field to source table and delete all acm_records.

Read the full story spec at: docs/sprint-artifacts/e19-s1-migration-32-review-status.md

Key tasks:
1. Create migrations/032_review_status.surql with the exact SurrealQL from the spec
2. Register the migration in open_notebook/database/migration_runner.py (AsyncMigrationManager)
3. Update the Source Pydantic model to add review_status: Optional[str] = None
4. Write unit tests verifying: migration applies cleanly, review_status field exists, acm_records deleted
5. Run: uv run ruff check . && uv run pytest

⚠️ DESTRUCTIVE: This migration deletes ALL acm_record rows. Do not run against production without user confirmation.

When complete, mark the story done in docs/sprint-artifacts/sprint-status.yaml and update progress in docs/sprint-artifacts/party-mode-20260224/progress.md.
```

---

### E19-S2: Jobs Dashboard

```
Implement story E19-S2: Jobs Dashboard — Replace the Documents library with a Jobs dashboard.

Read the full story spec at: docs/sprint-artifacts/e19-s2-jobs-dashboard.md

Key tasks:
1. Update frontend/src/app/jobs/page.tsx (or create if not exists) with job cards showing review_status pills
2. Update sidebar navigation: rename "Documents" to "Jobs", update icon to 📋
3. Add [+ New Job] button to jobs page header
4. Job cards show: name, status pill, upload date, record count (if published), building count (if published)
5. Context-aware CTA buttons: [Resume Review] for pending/in-review, [View] for published
6. After upload completes, redirect to /jobs/{id}/review/buildings (Step 1 wizard)
7. Update GET /api/sources to support ?review_status= filter param if not already present
8. Run: cd frontend && npm run build && npm run lint
9. Run: uv run ruff check . && uv run pytest

When complete, mark e19-s2-jobs-dashboard done in sprint-status.yaml.
```

---

### E19-S3: Feature Gating

```
Implement story E19-S3: Feature Gating — Standard/Admin user mode toggle.

Read the full story spec at: docs/sprint-artifacts/e19-s3-feature-gating.md

Key tasks:
1. Create frontend/src/stores/userModeStore.ts (Zustand store, persisted to localStorage 'acm-user-mode')
2. Add mode toggle button to sidebar footer (Standard ↔ Admin)
3. Wrap CONFIGURE sidebar section in {mode === 'admin' && ...} conditional
4. Default mode: 'standard' for new users, 'admin' for existing users with config already set
5. No backend changes required — client-side only
6. Run: cd frontend && npm run build && npm run lint

When complete, mark e19-s3-feature-gating done in sprint-status.yaml.
```

---

### E19-S4: Raw Extraction Table

```
Implement story E19-S4: Raw Extraction Table — Live AG Grid showing all extracted records during and after extraction.

Read the full story spec at: docs/sprint-artifacts/e19-s4-raw-extraction-table.md

Key tasks:
1. Create frontend/src/components/acm/RawExtractionTable.tsx (if not exists — check first)
2. Create frontend/src/app/jobs/[id]/extract/page.tsx — extraction progress page
3. AG Grid showing all extracted records (flat, no building tabs, read-only at this stage)
4. Reuse existing AG-UI SSE streaming pattern from E17 (use-extraction-agent.ts)
5. After extraction complete: show [Review Buildings →] CTA button
6. Source review_status transitions: 'extracting' → 'pending_review' when extraction completes
7. Run: cd frontend && npm run build && npm run lint

When complete, mark e19-s4-raw-extraction-table done in sprint-status.yaml.
```

---

### E19-S5: Building Review Wizard — Step 1

```
Implement story E19-S5: Building Review Wizard — Step 1 of the post-extraction review wizard.

Read the full story spec at: docs/sprint-artifacts/e19-s5-building-review-wizard.md

Key tasks:
1. Create frontend/src/app/jobs/[id]/review/buildings/page.tsx
2. Create frontend/src/components/acm/BuildingReviewGrid.tsx — editable AG Grid for 21 building fields from docs/samplePDF/building_data-schema.md
3. Read building fields schema from building_data-schema.md to get exact field list
4. [Mark Out of Scope] action per building row (sets building_out_of_scope = true)
5. Changes auto-save via PUT /api/sources/{id}/buildings/{building_id} (debounced 500ms)
6. [→ Next: Review Records] button navigates to /jobs/{id}/review/records
7. Sets source.review_status = 'building_review' when step opens
8. Add building_out_of_scope and building_out_of_scope_comments fields to site_config if not present (add to migration 032 or new 033)
9. Wizard step indicator: "Step 1 of 2: Review Buildings"
10. Run: cd frontend && npm run build && npm run lint && uv run ruff check . && uv run pytest

When complete, mark e19-s5-building-review-wizard done in sprint-status.yaml.
```

---

### E19-S6: ACM Schema Mapping Wizard — Step 2

```
Implement story E19-S6: ACM Schema Mapping Wizard — Step 2 of the post-extraction review wizard.

Read the full story spec at: docs/sprint-artifacts/e19-s6-acm-schema-mapping-wizard.md

Key tasks:
1. Create frontend/src/app/jobs/[id]/review/records/page.tsx
2. Create frontend/src/components/acm/ACMReviewGrid.tsx — editable AG Grid for 29 ACM fields from docs/samplePDF/acm_data-schema.md
3. Per-building tab navigation (reuse BuildingTabs.tsx) + "Unassigned Records" + "All Records" tabs
4. Tab badges show record count; Unassigned tab shown in amber if unassigned records exist
5. [+ Add Record] / [Delete] / [Merge Duplicate] actions
6. RecordMergeModal.tsx for merging duplicate rows
7. Enum dropdowns use values from docs/samplePDF/instructions-sample/register_enums.json
8. [Publish to Register →] button with confirmation dialog → POST /api/acm/jobs/{id}/publish
9. Add no_access (bool) and smf_present (string) fields to acm_record in migration 032 or 033
10. Add POST /api/acm/jobs/{source_id}/publish endpoint to api/routers/acm.py
11. Sets source.review_status = 'acm_review' when step opens, 'published' after publish
12. Run: cd frontend && npm run build && npm run lint && uv run ruff check . && uv run pytest

When complete, mark e19-s6-acm-schema-mapping-wizard done in sprint-status.yaml.
```

---

### E19-S7: Job Detail Page

```
Implement story E19-S7: Job Detail Page — Permanent tabbed page for a published or in-review job.

Read the full story spec at: docs/sprint-artifacts/e19-s7-job-detail-page.md

Key tasks:
1. Create frontend/src/app/jobs/[id]/page.tsx — Job detail page with 4 tabs
2. Create frontend/src/components/jobs/JobDetailHeader.tsx — header with status pill + inline-editable name + actions
3. Create frontend/src/components/jobs/JobOverviewTab.tsx — summary cards, quick actions, extraction timeline
4. Tab: Overview — summary cards + [Re-Extract] [Re-Review Buildings] [Re-Review Records] actions
5. Tab: Buildings — reuse BuildingReviewGrid.tsx from E19-S5
6. Tab: ACM Records — reuse ACMReviewGrid.tsx from E19-S6 with [Export CSV] [Export Excel] toolbar
7. Tab: Extraction Log — reuse ExtractionProgressPanel.tsx from E17
8. Add source_id query param filter to GET /api/acm/export/csv and GET /api/acm/export/excel if not already present
9. [Re-Extract] resets review_status = 'extracting', triggers POST /api/acm/extract, navigates to /jobs/{id}/extract
10. Run: cd frontend && npm run build && npm run lint && uv run ruff check . && uv run pytest

When complete, mark e19-s7-job-detail-page done in sprint-status.yaml.
```

---

### E19-S8: Conversational CRUD Chat (P1)

```
Implement story E19-S8: Conversational CRUD Chat — CRUD-capable chat scoped to job detail.

Read the full story spec at: docs/sprint-artifacts/e19-s8-conversational-crud-chat.md

⚠️ P1 PRIORITY — Implement AFTER E19-S1..S7 are all complete.

Key tasks:
1. Create open_notebook/graphs/crud_tools.py — preview_write, execute_confirmed_write, query_job_records tools
2. Extend supervisor agent (open_notebook/graphs/chat.py) to support CRUD tools when source_id context is present
3. Create frontend/src/components/chat/WriteConfirmationCard.tsx — AG-UI confirmation component
4. Create frontend/src/app/jobs/[id]/chat/page.tsx — job-scoped chat page
5. Create migrations/033_crud_audit.surql — crud_audit table
6. Load taxonomy files as system context: register_taxonomy.*.json, register_row.schema.json, register_enums.json, consultant_wording_rules.json from docs/samplePDF/instructions-sample/
7. Security: ALL SurrealDB write queries MUST include WHERE source_id = $source_id scope guard
8. [Confirm] and [Cancel] buttons in chat for all write operations — no writes without explicit confirmation
9. Run: cd frontend && npm run build && npm run lint && uv run ruff check . && uv run pytest

When complete, mark e19-s8-conversational-crud-chat done in sprint-status.yaml.
```

---

## E20 PROMPTS — Extraction Completeness

---

### E20-S1: Page Boundary Fix

```
⚠️ API COST: Do NOT run real extractions during development. Write all code + tests first.

Implement story E20-S1: Fix Page Boundary Truncation.

Read the full story spec at: docs/sprint-artifacts/e20-s1-page-boundary-fix.md

Key tasks:
1. In open_notebook/extractors/building_inventory.py, find the _assign_page_ranges() function (or equivalent loop)
2. Change: building.page_end = buildings[i + 1].page_start
   To:    building.page_end = buildings[i + 1].page_start + 1
3. Last building's page_end unchanged (already extends to document end)
4. Write unit tests in tests/test_building_inventory*.py:
   - Two buildings sharing a page → verify building A's page_end includes boundary page
   - Last building's page_end unchanged
   - Existing boundary assertions updated if needed
5. Run: uv run ruff check . && uv run pytest

Do NOT run a real extraction yet — wait for E20-S2 and S3 before the single validation run.

When complete, mark e20-s1-page-boundary-fix done in sprint-status.yaml.
```

---

### E20-S2: REGEX_ONLY Yield Check

```
⚠️ API COST: Do NOT run real extractions during development. Write all code + tests first.

Implement story E20-S2: REGEX_ONLY Yield Check + FULL_LLM Escalation.

Read the full story spec at: docs/sprint-artifacts/e20-s2-regex-yield-check.md

Key tasks:
1. In open_notebook/extractors/orchestrator.py, after REGEX_ONLY extraction, add yield check:
   - If len(records) < 50% of building.acm_item_count_estimate AND estimate > 0 → escalate to FULL_LLM
   - If acm_item_count_estimate is None and len(records) == 0 and building has content → escalate to FULL_LLM
   - Log warning: f"Building {id}: REGEX_ONLY yield {n}/{estimate} < 50% — escalating to FULL_LLM"
   - Update stats: strategy_distribution["regex_escalated_to_llm"] += 1
2. Review _select_strategy() for SAMP buildings: confirm > 3 pages of content is not mis-classified SIMPLE
3. Write unit tests:
   - REGEX_ONLY returning 0 records, estimate=5 → verify FULL_LLM called
   - REGEX_ONLY returning 3 records, estimate=4 (75% yield) → verify NO escalation
   - building with acm_item_count_estimate=None and 0 REGEX records → verify escalation
4. Run: uv run ruff check . && uv run pytest

Do NOT run a real extraction yet — wait for E20-S3 before the single validation run.

When complete, mark e20-s2-regex-yield-check done in sprint-status.yaml.
```

---

### E20-S3: Not Sampled / No Access Capture

```
⚠️ API COST: Do NOT run real extractions during development. Write all code + tests first.

Implement story E20-S3: Explicit "Not Sampled" / "No Access" Record Capture.

Read the full story spec at: docs/sprint-artifacts/e20-s3-not-sampled-capture.md

Key tasks:
1. Find the ACM extraction prompt template (look in prompts/ for .j2 files or similar)
2. Add explicit instruction to the output requirements section:
   "Include rows where sample_result is 'Not Sampled' or 'No Access'. These are valid ACM records
    even if no sample number exists. Set no_access = true for No Access rooms."
3. Add instruction: do NOT skip rows just because nata_sample_number is empty
4. In open_notebook/extractors/acm_schemas.py, confirm:
   - no_access: bool = Field(default=False) field exists (add if missing)
   - nata_sample_number: Optional[str] = None (ensure it's optional)
5. Confirm register_enums.json includes "Not Sampled" and "No Access" sample_result values
6. Write unit tests:
   - Mock LLM response with "Not Sampled" row → verify record included with correct sample_result
   - Mock LLM response with "No Access" room → verify no_access = true
7. Run: uv run ruff check . && uv run pytest

When all three E20-S1..S3 unit tests pass, proceed to E20-S4 for the ONE real extraction run.

When complete, mark e20-s3-not-sampled-capture done in sprint-status.yaml.
```

---

### E20-S4: E2E Accuracy Validation

```
⚠️ API COST: This is the ONE real extraction run for Epic 20. Run ONLY after E20-S1, S2, S3 unit tests all pass.

Implement story E20-S4: E2E Accuracy Validation on Broadmeadows PDF.

Read the full story spec at: docs/sprint-artifacts/e20-s4-e2e-accuracy-validation.md

Pre-flight checklist:
- E20-S1, S2, S3 unit tests all pass: uv run pytest tests/test_building_inventory*.py tests/test_orchestrator*.py tests/test_acm_extraction*.py
- Full suite: uv run pytest
- Lint: uv run ruff check .

Validation run:
1. Update tests/test_broadmeadows_e2e.py accuracy threshold to 100% (32/32 records)
2. Run ONE real extraction on Broadmeadows PDF via pytest or direct API call
3. Save extraction log to docs/sprint-artifacts/party-mode-20260224/e20-broadmeadows-validation.log
4. Record results in docs/sprint-artifacts/party-mode-20260224/progress.md:
   - Record count achieved vs target (32/32)
   - Which fixes contributed to which additional records
   - Any remaining gaps with root cause hypothesis
5. If count == 32: mark epic-20 done and all E20 stories done in sprint-status.yaml
6. If count < 32: document specific missing records, create E20-S5 gap analysis story

Do NOT re-run extraction without a confirmed specific bug fix.
```

---

## IMPLEMENTATION ORDER

| Step | Story | Priority | Depends On |
|------|-------|----------|------------|
| 1 | E19-S1 | P0 | — |
| 2 | E19-S2 | P0 | E19-S1 |
| 3 | E19-S3 | P0 | E19-S1 |
| 4 | E19-S4 | P0 | E19-S1 |
| 5 | E19-S5 | P0 | E19-S4 |
| 6 | E19-S6 | P0 | E19-S5 |
| 7 | E19-S7 | P0 | E19-S6 |
| 8 | E19-S8 | P1 | E19-S6 |
| 9 | E20-S1 | P0 | — (parallel with E19) |
| 10 | E20-S2 | P0 | E20-S1 |
| 11 | E20-S3 | P0 | E20-S2 |
| 12 | E20-S4 | P0 | E20-S1, S2, S3 |

> **Note on E20:** E20-S1..S3 can be developed in parallel with E19 (no shared code). Combine into a single API validation run in E20-S4.

---

*Generated by Party Mode session — SCP-20260224 (2026-02-24)*
