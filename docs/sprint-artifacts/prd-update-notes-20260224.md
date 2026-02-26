# PRD Update Notes — 2026-02-24

**Change Proposal:** SCP-20260224
**PRD Location:** `_bmad-output/project-planning-artifacts/acm-ai/03-prd.md`
**PRD Version:** v1.6 → v1.7 (proposed)
**Author:** Party Mode Session (PM: John, UX: Sally, Architect: Winston, SM: Bob, Dev: Amelia)

---

## Summary of Changes

This document describes the PRD sections and functional requirements that need to be added or updated to reflect Epic 19 (Standard User UX Redesign) and Epic 20 (Extraction Completeness). The PRD is not automatically updated — apply these changes when performing a formal PRD revision.

---

## New Functional Requirements to ADD

### FR-1200 Series — Standard User UX (Epic 19)

**FR-1201: Jobs Mental Model**
> The system SHALL present uploaded documents as "Jobs" with a lifecycle state machine: `extracting → pending_review → building_review → acm_review → published`.

**FR-1202: Jobs Dashboard**
> The system SHALL provide a Jobs Dashboard at `/jobs` showing job cards with status pills, metadata (upload date, record count, building count), and context-aware action buttons (Resume Review / View).

**FR-1203: Feature Gating**
> The system SHALL support a Standard user mode that hides administrative features (Extraction Settings, AI Models, Knowledge Graph, Monitor) from primary users. Mode is toggled client-side and persisted to localStorage.

**FR-1204: Post-Extraction Review Flow**
> After extraction completes, the system SHALL require a mandatory 2-step review wizard before records are published to the global ACM Register:
> - Step 1: Building Review — validate and map 21 building fields from `building_data-schema.md`
> - Step 2: ACM Schema Mapping — validate and map 29 ACM record fields per building (from `acm_data-schema.md`) using per-building tabs with inline-editable AG Grid

**FR-1205: Building Out of Scope**
> Compliance officers SHALL be able to mark individual buildings as "Out of Scope" during Step 1 review. Out-of-scope buildings are excluded from the published ACM Register.

**FR-1206: Record Publish Confirmation**
> Before publishing records to the global ACM Register, the system SHALL present a confirmation dialog showing the record count and an explicit "cannot be undone" warning.

**FR-1207: Job Detail Page**
> Published jobs SHALL have a permanent detail page at `/jobs/{id}` with tabs for Overview, Buildings, ACM Records, and Extraction Log. The page supports re-extraction, re-review, and export (CSV, Excel) actions.

**FR-1208: Conversational CRUD Chat (P1)**
> The system SHALL provide a job-scoped chat interface supporting natural language CRUD operations on ACM records within a single job. All write operations require explicit user confirmation via a preview-write protocol. CRUD chat is available for jobs with status `published` or `acm_review` only.

**FR-1209: CRUD Audit Log**
> Every confirmed write operation via the CRUD chat SHALL be logged to a `crud_audit` table including the natural language input, generated SurrealQL, operation type, job ID, and confirmation timestamp.

---

### FR-1300 Series — Extraction Completeness (Epic 20)

**FR-1301: Page Boundary Overlap**
> The extraction pipeline SHALL include one overlap page past the start of the next building when defining each building's page range, to capture records that appear on shared boundary pages.

**FR-1302: REGEX_ONLY Yield Validation**
> After REGEX_ONLY extraction, the system SHALL compare extracted record count against `acm_item_count_estimate`. If yield < 50% of estimate (or zero records when estimate > 0), the system SHALL automatically escalate to FULL_LLM extraction and log a warning.

**FR-1303: Not Sampled and No Access Records**
> The LLM extraction prompt SHALL explicitly instruct the model to include "Not Sampled" and "No Access" records as valid ACM items, even when no sample number is present. `no_access = true` SHALL be set on No Access records.

**FR-1304: Extraction Accuracy Target**
> The extraction pipeline SHALL achieve ≥ 100% record capture (32/32) on the Broadmeadows Police Station reference document after all Epic 20 fixes are applied.

---

## Existing FR Changes

### FR-300 Series — Data Schema (update)

**FR-301 update:** Add new optional fields to `acm_record`:
- `no_access: bool` (default false) — indicates room was inaccessible
- `smf_present: string` ("Yes" / "No" / "Unknown") — synthetic mineral fibre present

**FR-305 update:** Add new `review_status` field to `source`:
- Values: `extracting | pending_review | building_review | acm_review | published`
- Default: `pending_review`

### FR-200 Series — User Journey (update)

**FR-201 update:** Primary navigation items for Standard users:
- Jobs (was: Documents)
- Register
- Chat
- _(Admin only: Extraction Settings, AI Models, Knowledge Graph, Monitor)_

---

## New Non-Functional Requirements

**NFR-501: Extraction Cost Awareness**
> The system SHALL minimize unnecessary LLM API calls. REGEX_ONLY strategy SHALL be the default for SIMPLE-classified buildings. LLM escalation SHALL only occur when yield validation fails. The pipeline SHOULD NOT call the LLM for buildings that have zero page content.

---

## Migration Notes

**Migration 032** (breaking):
- Adds `review_status` field to `source` table
- **Deletes ALL existing `acm_record` rows** (clean slate for new review workflow)
- Rationale: Existing records were extracted without review workflow and lack field-level verification

**Migration 033** (additive):
- Adds `no_access` and `smf_present` fields to `acm_record`
- Adds `crud_audit` table (if E19-S8 bundled in same migration)

---

## UX Architecture Additions

### New User Journey (Standard User)

```
Upload PDF → Extraction (live AG Grid) → Step 1: Building Review → Step 2: ACM Record Review → Publish → Job Detail Page
                                                                                                              ↓
                                                                                                    ACM Register (read-only global)
```

### Jobs Status State Machine

```
pending_review → building_review → acm_review → published
     ↑                                                |
     └─────────── Re-Extract (from Job Detail) ───────┘
```

---

## Story Files (all drafted)

| Epic | Story | File |
|------|-------|------|
| E19 | S1 | docs/sprint-artifacts/e19-s1-migration-32-review-status.md |
| E19 | S2 | docs/sprint-artifacts/e19-s2-jobs-dashboard.md |
| E19 | S3 | docs/sprint-artifacts/e19-s3-feature-gating.md |
| E19 | S4 | docs/sprint-artifacts/e19-s4-raw-extraction-table.md |
| E19 | S5 | docs/sprint-artifacts/e19-s5-building-review-wizard.md |
| E19 | S6 | docs/sprint-artifacts/e19-s6-acm-schema-mapping-wizard.md |
| E19 | S7 | docs/sprint-artifacts/e19-s7-job-detail-page.md |
| E19 | S8 | docs/sprint-artifacts/e19-s8-conversational-crud-chat.md |
| E20 | S1 | docs/sprint-artifacts/e20-s1-page-boundary-fix.md |
| E20 | S2 | docs/sprint-artifacts/e20-s2-regex-yield-check.md |
| E20 | S3 | docs/sprint-artifacts/e20-s3-not-sampled-capture.md |
| E20 | S4 | docs/sprint-artifacts/e20-s4-e2e-accuracy-validation.md |

---

*PRD update notes generated by Party Mode session — SCP-20260224 (2026-02-24)*
*Apply to `_bmad-output/project-planning-artifacts/acm-ai/03-prd.md` to produce PRD v1.7*
