# E2E Test Plan: ACM Extraction Pipeline - Clutch_Broadmeadows.pdf

## Goal
Full end-to-end test of the ACM extraction pipeline from PDF upload through to data validation against known-good CSV. Test all layers: UI, API, worker, database. Document bugs, UX issues, and log quality.

## Test Artifact
- **Input PDF:** `docs/samplePDF/Clutch_Broadmeadows.pdf`
- **Expected Output:** `docs/samplePDF/Clutch_Broadmeadows.csv` (31 records, 42 columns)
- **Pass Criteria:** 90%+ of records extracted with correct field values

## CSV Field Mapping (42 BAR columns)
Department, Agency, Sub Agency, Site Name, Building Name, Building Type, Building Address, Suburb, Postcode, Owned or Leased, Building Unique ID, Frequency of use, Public Access?, Date of Inspection, Estimated Year Built, Est. Building Size, Number of Levels, Construction Type, Roof Type, Internal/External, Level, Room or Area, Location in Room, Specific Item/ACM Name, Friability of material, ACM Product Group, ACM Product Type, NATA Endorsed Sample number, Sample Result, Identifying Hygiene or Consulting Company, Condition, Disturbance Potential, Quantity, Labelled, Label Details, Hygienist Recommendations, Additional Comments, PSB Supplied ACM ID, Assumed Removed?, Date of Removal, Quantity Removed, Asbestos Removal Notification No, EPA Waste Transport Certificate No

## Key System URLs
- Frontend: http://localhost:8502
- API: http://localhost:5055
- SurrealDB: ws://localhost:8000/rpc
- ACM Register: http://localhost:8502/acm

## Phases

### Phase 0: Service Health Check `pending`
- [ ] Verify SurrealDB running on port 8000
- [ ] Verify FastAPI running on port 5055
- [ ] Verify Frontend running on port 8502
- [ ] Verify Worker process running
- [ ] Screenshot: Frontend loads correctly

### Phase 1: PDF Upload via UI `pending`
- [ ] Navigate to frontend (http://localhost:8502)
- [ ] Screenshot: Home page / dashboard
- [ ] Open Add Source dialog
- [ ] Screenshot: Add Source dialog (Step 1)
- [ ] Upload Clutch_Broadmeadows.pdf
- [ ] Screenshot: File selected state
- [ ] Complete site configuration step
- [ ] Screenshot: Site config step
- [ ] Select notebook/organization
- [ ] Screenshot: Organization step
- [ ] Enable ACM extraction and submit
- [ ] Screenshot: Processing step
- [ ] Record command_id returned
- [ ] Capture API logs during upload
- [ ] Capture worker logs during processing

### Phase 2: Monitor Extraction Progress `pending`
- [ ] Monitor worker logs for `process_source` command
- [ ] Wait for PDF text extraction (Docling) to complete
- [ ] Monitor worker logs for `acm_extract` command
- [ ] Monitor AI extraction progress (LangGraph)
- [ ] Screenshot: Any progress indicator in UI
- [ ] Capture extraction timing metrics
- [ ] Record any errors/warnings in logs

### Phase 3: Validate Extracted Records `pending`
- [ ] Navigate to ACM Register page (http://localhost:8502/acm)
- [ ] Screenshot: ACM Register with records loaded
- [ ] Count total records displayed
- [ ] Compare record count vs CSV (expect 31)
- [ ] API call: GET /api/acm/records to retrieve all records
- [ ] Field-by-field comparison against CSV for key fields
- [ ] Calculate match percentage per field
- [ ] Identify missing or incorrect records
- [ ] Screenshot: Scrolled grid showing all records

### Phase 4: UI/UX Bug Hunt `pending`
- [ ] Screenshot: Column headers and sizing
- [ ] Screenshot: Risk status badges
- [ ] Test column sorting
- [ ] Test quick filter search
- [ ] Test column visibility toggle
- [ ] Check responsive behavior
- [ ] Check for console errors (JS)
- [ ] Check for missing/broken icons
- [ ] Check for truncated text
- [ ] Document all UX issues with screenshots

### Phase 5: Log Quality Assessment `pending`
- [ ] Review API logs for informativeness
- [ ] Review worker logs for extraction pipeline events
- [ ] Review frontend console for errors/warnings
- [ ] Assess: Are logs sufficient for debugging?
- [ ] Assess: Are there missing log points?
- [ ] Assess: Are there excessively verbose logs?
- [ ] Document log improvement recommendations

### Phase 6: Final Report `pending`
- [ ] Compile all screenshots
- [ ] Compile validation results
- [ ] Compile UX/UI bug list
- [ ] Compile log assessment
- [ ] Calculate overall pass/fail against 90% threshold
- [ ] Write final test report

## Errors Encountered
| Error | Phase | Resolution |
|-------|-------|------------|
| (none yet) | | |

## Agent Team Structure
- **Team Lead (main):** Coordinate, decisions, final report
- **browser-tester:** Playwright MCP - UI interaction, screenshots, UX bugs
- **log-monitor:** Watch all service logs, capture key events
- **data-validator:** Compare extracted records vs CSV, calculate match %
