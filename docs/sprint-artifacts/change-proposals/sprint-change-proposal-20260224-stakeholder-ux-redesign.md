# Sprint Change Proposal — Standard User UX Redesign & Extraction Completeness

**Date:** 2026-02-24
**Status:** APPROVED
**Approved by:** Demi
**Priority:** P0 (E19-S1..S7, E20-S1..S4) / P1 (E19-S8)
**Scope:** Large
**Risk:** Medium (destructive migration, extraction pipeline changes)
**Path:** Epic Additions (2 new epics, 12 new stories)
**Trigger:** Post-demo stakeholder feedback — 4 critical UX and extraction quality issues

---

## 1. Motivation

Post-demo stakeholder review identified four critical issues requiring immediate sprint change proposals.

### Issue 1 — UI Complexity

The current application exposes extraction monitoring, AI model configuration, knowledge graph visualisation, and admin features to standard compliance officer users. This creates cognitive overload for the primary user group, who only need to upload documents, review extracted data, and export BAR-format registers.

**Impact:** Demo showed confusion and task abandonment from compliance officers unfamiliar with AI tooling.

### Issue 2 — Wrong Mental Model (Documents vs. Jobs)

The current "Documents" library mental model asks users to manage PDFs. Compliance officers think in terms of *jobs* — one uploaded document = one extraction job. The app should surface this as a Jobs system: submit a job, review the output, export the result.

**Impact:** Users tried to manage files rather than use the system as an extraction pipeline.

### Issue 3 — Incorrect Extraction UX Flow

The current flow sends all extracted records directly to a global ACM Register with no human checkpoint. The correct compliance workflow is:

1. **Raw records view**: After extraction, display ALL extracted records (including No Access, Not Sampled items) in a raw table — nothing filtered or lost
2. **Step 1 — Building Review Wizard**: Map records to buildings using the 21-field building schema (`building_data-schema.md`). Live update as user assigns/confirms buildings
3. **Step 2 — ACM Schema Mapping Wizard**: Map and verify 29 ACM fields per record (`acm_data-schema.md`), per-building tabs. Live AG Grid updates as user reviews
4. **Publish**: Commit reviewed records to the published ACM Register with 43-column BAR export

**Impact:** Records were going into the register unchecked. Compliance officers couldn't review before committing.

### Issue 4 — Incomplete Extraction (Missing Records)

The current extraction pipeline misses records in two scenarios:
1. Buildings that span multiple document pages have their `page_end` cut short at the next building header, losing records that appear after the header on the same page
2. SAMP buildings classified as `SIMPLE` get `REGEX_ONLY` strategy which silently drops records when document formatting deviates from the expected pattern
3. "Not Sampled" and "No Access" edge-case records are not consistently captured by the current LLM prompts

**Target:** 100% record capture on Broadmeadows Police Station (32/32 records, including all edge cases).

---

## 2. Decisions Made During Design Session (2026-02-24)

| Decision | Outcome |
|----------|---------|
| Epic numbering | E19 (UX Redesign), E20 (Extraction Completeness). E18 retained as Production Hardening. |
| Jobs mental model | UI rename only — `source` stays as internal model, surfaced as "Job" in UI. No DB migration. |
| Building data source | Map to existing `site_config` + `acm_record` building fields. No new DB table. |
| Review wizard trigger | Both: mandatory after upload AND re-editable on permanent job detail page. |
| Chat CRUD scope | Full CRUD in job detail only. Global register chat is read-only. P1 priority. |
| Priority split | P0: Jobs + 2-step review wizard + building tabs. P1: CRUD chat. |
| Migration 32 | First story: adds `review_status` to `source`, deletes all existing `acm_record` data. |
| Existing record handling | All existing `acm_record` rows deleted. Existing sources set to `pending_review`. |
| E20 accuracy target | 100% — 32/32 records on Broadmeadows including "Not Sampled" edge cases. |
| Implementation order | Sequential, Ralph autonomous loop. E19-S7 migration first. |

---

## 3. Change Proposals

### CP-1: New Epic 19 — Standard User UX Redesign

**Scope:** Redesign the complete user journey for standard compliance officer users. Simplify navigation, introduce Jobs mental model, add mandatory post-extraction review wizard with live building and ACM schema mapping.

**New Stories (E19):**

| Story | Title | Priority | Size |
|-------|-------|----------|------|
| E19-S1 | Migration 32 — review_status on source, delete acm_records | P0 | S |
| E19-S2 | Jobs Dashboard — rename Documents to Jobs with job cards | P0 | S |
| E19-S3 | Feature Gating — hide admin features for standard users | P0 | XS |
| E19-S4 | Raw Extraction Table — live-streaming raw records display | P0 | M |
| E19-S5 | Building Review Wizard Step 1 — 21-field building mapping | P0 | L |
| E19-S6 | ACM Schema Mapping Wizard Step 2 — 29-field per-building review | P0 | L |
| E19-S7 | Job Detail Page — permanent review tabs + per-building export | P0 | M |
| E19-S8 | Conversational CRUD Chat — LangGraph CRUD agent (P1) | P1 | XL |

### CP-2: New Epic 20 — Extraction Completeness

**Scope:** Fix extraction pipeline to achieve 100% record capture including edge cases. Target: 32/32 records on Broadmeadows Police Station.

**New Stories (E20):**

| Story | Title | Priority | Size |
|-------|-------|----------|------|
| E20-S1 | Fix Page Boundary Truncation — extend building page_end | P0 | M |
| E20-S2 | REGEX_ONLY Yield Check + FULL_LLM Escalation | P0 | M |
| E20-S3 | "Not Sampled" / No Access Record Capture | P0 | M |
| E20-S4 | E2E Accuracy Validation — 100% Broadmeadows test | P0 | S |

---

## 4. Proposed UX Architecture (E19)

### Navigation (Standard User)
```
WORKSPACE
  📋 Jobs           ← replaces Documents
  📊 ACM Register   ← published records (read-only global view)
  💬 Chat           ← read-only query (P0), CRUD in job detail (P1)

CONFIGURE (hidden from standard users, visible to admin/power users)
  ⚙️  Extraction Settings
  🤖  AI Models
  📊  Extraction Monitor
  🧠  Knowledge Graph
```

### Job Lifecycle
```
[+ New Job] → Upload PDF → Extraction (live SSE streaming)
  → [Raw Records Table: ALL extracted records appear live]
  → [Step 1: Building Review Wizard — 21-field mapping, live update]
  → [Step 2: ACM Schema Mapping Wizard — 29-field per-building tabs, live AG Grid]
  → [Publish to Register]
  → Job appears as "Published" in Jobs list
```

### Post-Extraction Review Wizard

**Step 1 — Building Review (21 fields from building_data-schema.md):**
- Shows all detected buildings as editable grid rows
- Fields: Organisation, Site Name, Building Name, Building Type, Address, Suburb, Postcode, Owned/Leased, Building Unique ID, Frequency of Use, Public Access?, Date of Audit Report, Estimated Year Built, Building Size (m²), Levels, Construction Type, Roof Type, PSB District/Region, Out of Scope, Out of Scope Comments, Additional Comments
- [+ Add Building] and [Mark Out of Scope] actions
- Unassigned records shown in "Unassigned" tab — nothing is lost

**Step 2 — ACM Register Review (29 fields from acm_data-schema.md):**
- Per-building tabs using existing `BuildingTabs.tsx` component
- Fields: organisation, Building Code, Internal/External, No Access, Level, Room Or Area, Location in Room/Area, ACM Name, Friability, ACM Product Group, ACM Product Type, SMF Present, Sample no, Sample Result, Identifying Company, Condition, Disturbance Potential, Quantity, ACM Labelled, Label Details, Hygienist Recommendations, Additional Comments, Psb Supplied ACM Id, Removal Status, Date Of Removal, Quantity Removed, Clearance Certificates Available, Asbestos Removal Notification No, EPA Waste Record
- Inline editable AG Grid (existing ACMGrid.tsx adapted)
- [+ Add Record] [Delete Row] [Merge Duplicate] actions
- "Unassigned" tab captures all "Not Sampled" / No Access records

### Job Detail Page (permanent)
```
Tabs: Overview | Buildings | ACM Records | Extraction Log
Actions: [Re-Extract] [Re-Review Buildings] [Re-Review Records] [Export CSV] [Export Excel per-building]
```

---

## 5. Architecture Decisions (E19/E20)

### Migration 32 (E19-S1)
```sql
-- Add review_status field to source table
DEFINE FIELD review_status ON source TYPE option<string>
  DEFAULT 'pending_review';

-- Values: 'extracting' | 'pending_review' | 'building_review' | 'acm_review' | 'published'

-- Existing sources: set to pending_review (they must go through new review flow)
UPDATE source SET review_status = 'pending_review';

-- Delete all existing acm_record rows (fresh start — data quality enforcement)
DELETE acm_record;
```

⚠️ **DESTRUCTIVE MIGRATION**: All extracted ACM records will be deleted. Users who have not exported their data will lose it. This is intentional — the new review flow enforces data quality before records enter the register.

### API Changes Required
- `GET /api/acm/jobs/{source_id}/buildings` — new: aggregate 21-field building summary
- `PUT /api/acm/jobs/{source_id}/review-status` — new: advance review state machine
- `POST /api/acm/jobs/{source_id}/publish` — new: promote draft records to published
- Existing: `GET /api/acm/records?source_id={id}` — parameterised filtering (already works)

### E20 Pipeline Fixes
- `open_notebook/extractors/building_inventory.py`: Extend `page_end` to overlap boundary pages
- `open_notebook/extractors/orchestrator.py`: Add yield-check after REGEX_ONLY; escalate to FULL_LLM if count < expected
- `prompts/`: Update extraction prompt to explicitly capture "Not Sampled", "No Access", "Not Accessible" as distinct records

---

## 6. Impact Analysis

### Breaking Changes
| Change | Impact | Mitigation |
|--------|--------|-----------|
| Migration 32 deletes acm_record | All existing extracted data lost | Warn users; encourage export before migration |
| Upload wizard flow change | UploadResults.tsx navigation changes | Update E7 wizard tests |
| Navigation feature gating | Admin users lose nothing; standard users lose access to Configure | Two user modes with clear documentation |
| source.review_status new field | No breaking change to existing queries | Default value prevents null issues |

### Dependencies
| Story | Depends On | Blocks |
|-------|-----------|--------|
| E19-S1 | — | All other E19 stories |
| E19-S2 | E19-S1 | — |
| E19-S3 | E19-S1 | — |
| E19-S4 | E19-S1 | E19-S5, E19-S6 |
| E19-S5 | E19-S4 | E19-S6 |
| E19-S6 | E19-S5 | E19-S7 |
| E19-S7 | E19-S6 | — |
| E19-S8 | E19-S6 | — |
| E20-S1 | — | E20-S2, E20-S3 |
| E20-S2 | E20-S1 | E20-S4 |
| E20-S3 | E20-S1 | E20-S4 |
| E20-S4 | E20-S1..S3 | — |

---

## 7. Updated Story Counts

| Category | Before | After |
|----------|--------|-------|
| Total stories | 130 | 142 |
| Done | 116 | 116 |
| In-progress | 1 (E18-S4) | 1 |
| New stories | — | +12 (E19×8, E20×4) |
| Backlog | 0 | 12 |
| Total epics | 18 | 20 |

---

## 8. Implementation Order (Sequential — Ralph Loop)

```
Sprint E19 — Standard User UX:
  E19-S1  Migration 32 (review_status + delete acm_records)     [FIRST — DB]
  E19-S2  Jobs Dashboard                                          [UI]
  E19-S3  Feature Gating                                          [UI]
  E19-S4  Raw Extraction Table                                    [UI + SSE wiring]
  E19-S5  Building Review Wizard Step 1                           [UI + API]
  E19-S6  ACM Schema Mapping Wizard Step 2                        [UI + API]
  E19-S7  Job Detail Page                                         [UI]
  E19-S8  Conversational CRUD Chat (P1)                          [Backend + UI]

Sprint E20 — Extraction Completeness:
  E20-S1  Fix Page Boundary Truncation                           [Backend]
  E20-S2  REGEX_ONLY Yield Check + Escalation                    [Backend]
  E20-S3  "Not Sampled" / No Access Record Capture               [Backend + Prompts]
  E20-S4  E2E Accuracy Test at 32/32                             [Tests]
```

---

## 9. Files Changed by This Proposal

| File | Change |
|------|--------|
| `docs/sprint-artifacts/sprint-status.yaml` | Append E19, E20 sections |
| `docs/sprint-artifacts/epic-19-standard-user-ux.md` | New epic summary file |
| `docs/sprint-artifacts/epic-20-extraction-completeness.md` | New epic summary file |
| `docs/sprint-artifacts/e19-s{1..8}-*.md` | 8 new story files |
| `docs/sprint-artifacts/e20-s{1..4}-*.md` | 4 new story files |
| `docs/sprint-artifacts/e19-e20-implementation-prompts.md` | Claude Code prompts bundle |
| `docs/sprint-artifacts/prd-update-notes-20260224.md` | PRD sections to update |
| `migrations/032_review_status.surql` | New migration file (written in E19-S1) |
| `open_notebook/extractors/building_inventory.py` | Page boundary fix (E20-S1) |
| `open_notebook/extractors/orchestrator.py` | Yield check + escalation (E20-S2) |
| `prompts/` | Not Sampled capture prompt update (E20-S3) |
| `frontend/src/components/acm/` | New wizard components (E19-S4..S6) |
| `frontend/src/app/jobs/` | New Jobs route (E19-S2) |

---

## Cost Awareness — ALL E20 Stories

⚠️ **API COST: Every extraction triggers real OpenRouter spend.**
- Write and verify full implementation + unit tests FIRST
- Run ONE real extraction to validate (Broadmeadows ≈32 records, Alexandra ≈533 records)
- Only re-extract if a specific confirmed bug was fixed
- NEVER use mocked LLM responses to test extraction accuracy — real PDFs only from docs/samplePDF/
