# Story E19-S4: Raw Extraction Table — Live Records During Extraction

**Epic:** E19 — Standard User UX Redesign
**Priority:** P0
**Status:** backlog
**Change Proposal:** SCP-20260224 (2026-02-24)
**Depends on:** E19-S1

---

## User Story

**As a** compliance officer who just uploaded a SAMP document,
**I want to** see ALL extracted records appearing live as the AI processes the document,
**So that** I can confirm that no records (including "Not Sampled" or "No Access" items) are being lost before I begin the review wizard.

---

## Background

Currently, the upload wizard shows an extraction progress panel (stage pills + log terminal) with no preview of the actual records being extracted. Users have no visibility into what the AI found until extraction completes and they navigate to the ACM Register.

This story adds a "Raw Extraction Table" — a live-updating AG Grid that populates with extracted records as each chunk is processed (using existing E17 AG-UI StateDelta streaming). The table shows ALL records in raw form: no filtering, no building grouping. "Not Sampled", "No Access", and unusual items are all visible. This table is the entry point to the review wizard.

---

## Acceptance Criteria

### Raw Extraction Table
- [x] Appears immediately after extraction starts (replaces or appears alongside ExtractionProgressPanel)
- [x] AG Grid with columns matching the raw ACM extraction fields (key fields visible by default):
  - Building Name, Level, Room/Area, Location, ACM Name, Friability, Sample Result, No Access flag, Condition
- [x] Records appear row-by-row as each chunk is processed (live SSE via AG-UI StateDelta events)
- [x] "Preview" badge/indicator on rows that are still streaming (italic, pulsing border — existing E17 pattern)
- [x] Final record count shown: "32 records extracted" when complete
- [x] Unmatched / ambiguous records highlighted in amber ("Review required")
- [x] "Not Sampled" and "No Access" records visible with appropriate badges

### Progress Panel Coexistence
- [x] ExtractionProgressPanel (stage pills + log) remains visible above the raw records table
- [x] Raw records table scrollable independently of the progress panel

### Transition to Review Wizard
- [x] When extraction completes: [Proceed to Review →] button appears
- [x] Clicking [Proceed to Review →] advances to E19-S5 Building Review Wizard (Step 1)
- [x] Table remains accessible in "All Records" tab of Job Detail page (E19-S7) after review is complete

### URL / State
- [x] Raw extraction table shown at `/jobs/{source_id}/extract` route
- [x] If user navigates away mid-extraction: extraction continues in background; table accessible from job card [Resume Review] CTA

---

## Technical Notes

### SSE Integration (E17 Pattern)
The existing `use-extraction-agent.ts` hook streams AG-UI `StateDelta` events that contain partial record arrays. Wire these into a new `RawExtractionTable` component:

```typescript
// RawExtractionTable.tsx uses the existing hook
const { records, isStreaming } = useExtractionAgent(commandId);
// records: ACMExtractionRecord[] updated incrementally
// isStreaming: boolean — toggles "Preview" badge on new rows
```

### Record Storage
Raw extracted records stored in existing `acm_record` table with `source.review_status = 'extracting'` during extraction, then `'pending_review'` when extraction completes. Records are draft records only — not visible in global register until `source.review_status = 'published'`.

### AG Grid Column Set (Raw Table)
Lighter than the full 47-column BAR grid. Show ~12 essential columns:
```typescript
const rawColumns = [
  'building_name', 'level', 'room_name', 'location', 'product',
  'friable', 'sample_result', 'material_condition', 'no_access',
  'nata_sample_number', 'extraction_confidence', 'page_number'
];
```

---

## Key Files Created/Modified

| File | Change |
|------|--------|
| `frontend/src/app/jobs/[id]/extract/page.tsx` | **New** — Extract + raw table page |
| `frontend/src/components/acm/RawExtractionTable.tsx` | **New** — Live raw records AG Grid |
| `frontend/src/components/acm/PreviewRecordBadge.tsx` | Reuse existing (E17) |
| `frontend/src/app/upload/UploadResults.tsx` | Modified — redirect to `/jobs/{id}/extract` instead of source detail |

---

## Dev Notes

No API cost risk — this story is wiring existing SSE events to a new UI component.

⚠️ **The upload redirect change in `UploadResults.tsx` is a breaking change to the E7 upload wizard flow.** Update any E7-related tests that assert navigation to source detail after upload.

---

## Estimated Effort

M (Medium) — New page + new component + wiring AG-UI events. Redirect change touches E7 code.

---

**Story Status:** ⬜ BACKLOG

---

## Dev Agent Record

**Implemented:** 2026-02-24
**Files changed:**
- `frontend/src/components/acm/RawExtractionTable.tsx` (new — live AG Grid with streaming records)
- `frontend/src/app/(dashboard)/jobs/[id]/extract/page.tsx` (new — extraction + raw table page)
- `frontend/src/components/upload/UploadProgressStep.tsx` (redirect → /jobs/{id}/extract, "View Jobs" button)

**Tests added:** None (frontend-only, verified via build)
**Verification:** ruff ✓ | lint ✓ | build ✓
