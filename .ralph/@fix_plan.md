# Fix Plan: ACM Record Detail Slide-Out Panel

## Source
- **Story file**: docs/sprint-artifacts/e16-s2-record-detail-panel.md
- **Story ID**: E16-S2
- **Generated**: 2026-02-21T07:15:00+11:00

## Tasks

### Panel Behaviour
- [x] AC1: Clicking any row in the ACM grid opens a right-side slide-out drawer (380px width)
- [x] AC2: Clicking the same row again, or pressing Escape, closes the panel
- [x] AC3: Arrow keys cycle through records (previous/next in current sort order)
- [x] AC4: Panel animates in/out smoothly (slide from right, 200ms)
- [x] AC5: Grid stays interactive while panel is open (user can scroll, filter, etc.)
- [x] AC6: Selected row is highlighted in the grid while panel is open

### Field Display
- [x] AC7: All 47 fields organized into 8 labeled sections (Organisation, Building, Location, ACM Details, Assessment, Documentation, Removal Tracking, Metadata)
- [x] AC8: Empty/null fields shown as "—" (not blank)
- [x] AC9: Extraction confidence shown as % badge if available
- [x] AC10: Boolean fields (friable, labelled, acm_labelled) shown as YES/NO badges

### PDF Citation
- [x] AC11: "View in PDF" button visible if page_number is set
- [x] AC12: Clicking opens the existing PDF viewer modal (E3) at the stored page_number

### Edit Mode
- [x] AC13: "Edit" toggle button in panel header
- [x] AC14: In edit mode all fields become inline inputs (text, number, select as appropriate)
- [x] AC15: "Save" button calls PUT /api/acm/{id}
- [x] AC16: "Cancel" button reverts to read mode without saving
- [x] AC17: Toast notification on save success/error

### New Files
- [x] AC18: Create frontend/src/components/acm/ACMRecordDetailPanel.tsx
- [x] AC19: Create frontend/src/components/acm/RecordFieldSection.tsx
- [x] AC20: Create frontend/src/lib/hooks/use-acm-record.ts

### Integration
- [x] AC21: Wire ACMRecordDetailPanel into ACMSpreadsheet.tsx
- [x] AC22: Wire onRowClicked handler and row highlight into ACMGrid.tsx

## Completion Criteria
- All tasks above are checked off
- All tests passing: `pytest tests/ -x`
- No lint errors: `ruff check .`
- Frontend builds: `cd frontend && npm run lint && npm run build`
- Changes committed with conventional commit message
