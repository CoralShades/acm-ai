# Fix Plan: ACM Record Detail Slide-Out Panel

## Source
- **Story file**: docs/sprint-artifacts/e16-s2-record-detail-panel.md
- **Story ID**: E16-S2
- **Generated**: 2026-02-21T07:15:00+11:00

## Tasks

### Panel Behaviour
- [ ] AC1: Clicking any row in the ACM grid opens a right-side slide-out drawer (380px width)
- [ ] AC2: Clicking the same row again, or pressing Escape, closes the panel
- [ ] AC3: Arrow keys cycle through records (previous/next in current sort order)
- [ ] AC4: Panel animates in/out smoothly (slide from right, 200ms)
- [ ] AC5: Grid stays interactive while panel is open (user can scroll, filter, etc.)
- [ ] AC6: Selected row is highlighted in the grid while panel is open

### Field Display
- [ ] AC7: All 47 fields organized into 8 labeled sections (Organisation, Building, Location, ACM Details, Assessment, Documentation, Removal Tracking, Metadata)
- [ ] AC8: Empty/null fields shown as "—" (not blank)
- [ ] AC9: Extraction confidence shown as % badge if available
- [ ] AC10: Boolean fields (friable, labelled, acm_labelled) shown as YES/NO badges

### PDF Citation
- [ ] AC11: "View in PDF" button visible if page_number is set
- [ ] AC12: Clicking opens the existing PDF viewer modal (E3) at the stored page_number

### Edit Mode
- [ ] AC13: "Edit" toggle button in panel header
- [ ] AC14: In edit mode all fields become inline inputs (text, number, select as appropriate)
- [ ] AC15: "Save" button calls PUT /api/acm/{id}
- [ ] AC16: "Cancel" button reverts to read mode without saving
- [ ] AC17: Toast notification on save success/error

### New Files
- [ ] AC18: Create frontend/src/components/acm/ACMRecordDetailPanel.tsx
- [ ] AC19: Create frontend/src/components/acm/RecordFieldSection.tsx
- [ ] AC20: Create frontend/src/lib/hooks/use-acm-record.ts

### Integration
- [ ] AC21: Wire ACMRecordDetailPanel into ACMSpreadsheet.tsx
- [ ] AC22: Wire onRowClicked handler and row highlight into ACMGrid.tsx

## Completion Criteria
- All tasks above are checked off
- All tests passing: `pytest tests/ -x`
- No lint errors: `ruff check .`
- Frontend builds: `cd frontend && npm run lint && npm run build`
- Changes committed with conventional commit message
