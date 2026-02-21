# Browser Pilot Findings - E2E Test 2026-02-11

## UI/UX Issues Found

### BUG-1: Building column empty in grid (Severity: Medium)
- **Location**: ACM Register page, AG Grid
- **Expected**: Building name should show (e.g., "Broadmeadows Police Station")
- **Actual**: Building column is empty for all 8 rows. Only Building Code (B001) shows.
- **Root cause**: `building_name` field is null in API response. LLM extraction doesn't populate it.
- **Screenshot**: 10-acm-grid-with-data.png
- **Related**: Issue #14

### BUG-2: Page column empty in grid (Severity: Medium)
- **Location**: ACM Register page, AG Grid
- **Expected**: Page number should reference source PDF page
- **Actual**: Page column is empty for all 8 rows
- **Root cause**: `page_number` field is null in API response. LLM extraction doesn't populate it.
- **Screenshot**: 10-acm-grid-with-data.png
- **Related**: Issue #14

### BUG-3: Friable dropdown shows blank in edit dialog (Severity: Medium)
- **Location**: Edit ACM Record dialog, Assessment section, Friable combobox
- **Expected**: Should display current value "Non-friable"
- **Actual**: Dropdown trigger shows blank (just chevron icon). Opening reveals options: "Friable", "Non Friable"
- **Root cause**: Value mismatch - data has "Non-friable" (hyphenated) but dropdown option is "Non Friable" (space, no hyphen)
- **Screenshot**: 12-friable-dropdown.png
- **Related**: Issue #14

### BUG-4: Search bar doesn't filter grid results (Severity: Low)
- **Location**: ACM Register page, search textbox
- **Expected**: Typing "Fan Room" should filter grid to show only Fan Room rows
- **Actual**: All 8 rows remain visible after typing search term
- **Notes**: Search input appears to clear or not persist. May be AG Grid quickFilter not connected.
- **Screenshot**: 13-search-fan-room.png

### BUG-5: Document Library doesn't refresh after upload (Severity: Low)
- **Location**: Documents page, Library tab
- **Expected**: After uploading a document, Library tab should show the new document
- **Actual**: Still shows "No Documents Yet" empty state after upload
- **Notes**: User must manually navigate away and back
- **Screenshot**: 06-upload-submitted.png

### BUG-6: Console error on wizard step 2 (Severity: Low)
- **Location**: Upload wizard, when navigating to Site Configuration step
- **Error**: "Query data cannot be undefined. Please make sure to provide data..."
- **Notes**: React Query error, doesn't block functionality

### BUG-7: File renamed with "(2)" suffix (Severity: Informational)
- **Location**: Upload wizard
- **Expected**: File should retain original name "Clutch_Broadmeadows.pdf"
- **Actual**: Renamed to "Clutch_Broadmeadows (2).pdf"
- **Notes**: Likely from previous upload that wasn't cleaned up. Not a bug per se, but file naming could be cleaner.

### BUG-8: AG Grid deprecation warnings (Severity: Informational)
- **Location**: Browser console
- **Warnings**:
  - "As of version 32.2.1, using `rowSelection` as a string is deprecated"
  - "As of v32.2, suppressRowClickSelection is deprecated"
  - "invalid colDef property 'suppressRowClickSelection'"
- **Notes**: AG Grid API needs updating to v32.2+ patterns

## Working Features (PASS)

### PASS-1: Stats cards
- All 4 cards present and showing correct data
- Total Records: 8, Risk Status: High 0 / Medium 0 / Low 8, Buildings: 1, Rooms: 7

### PASS-2: AG Grid populated
- 8 rows displayed correctly with all data columns
- Pagination footer shows "1 to 8 of 8, Page 1 of 1"

### PASS-3: Risk color coding
- Low risk badges shown in green styling
- Tooltip text: "Low risk asbestos material"

### PASS-4: Edit dialog
- Opens correctly from edit button on each row
- All sections present: School Info, Building Info, Room Info, ACM Details, Assessment, Reference
- Fields populated with extracted data
- Area Type dropdown works (Interior/Exterior)
- Risk Status dropdown works (Low/Medium/High)
- Cancel and Save Changes buttons present

### PASS-5: Export functionality
- Export dropdown shows CSV and Excel options
- CSV export downloads successfully as "acm_export_source_lap4wnbxllavswdgghro.csv"
- Toast notification: "CSV downloaded successfully"

### PASS-6: Source selector dropdown
- Dropdown lists available sources with ACM records
- Selecting source loads grid and stats correctly

### PASS-7: Column headers and sorting
- All 11 data columns visible: Building Code, Building, Room ID, Room, Product, Description, Risk, Result, Friable, Condition, Page
- Actions column with Edit/Delete buttons
- Filter icons visible on columns

### PASS-8: Upload wizard flow
- 4-step wizard works smoothly
- File upload, Site Configuration (optional), Organization, Processing
- ACM extraction checkbox enabled by default
- Toast notifications on successful upload

### PASS-9: Sidebar navigation
- All navigation links work: Dashboard, Documents, ACM Register, Search
- Active page highlighted in sidebar
- Collapse sidebar button present

### PASS-10: Breadcrumb navigation
- Shows "Home > ACM Register" path
- Home link is clickable
