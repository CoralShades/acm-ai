# Browser Interaction Test Report — 2026-04-09

## Test Summary

| Scenario | Status | Issues Found |
|----------|--------|-------------|
| Scenario 1: Jobs Dashboard | PASS | None critical |
| Scenario 2: Job Detail Page (all tabs) | PASS | Status badge bug (detail shows "Extracting" when API says "completed") |
| Scenario 3: Chat Sidebar | PASS | None |
| Scenario 4: AI-Editor | PASS | Card click opens context menu instead of navigating |
| Scenario 5: Navigation & UI | PASS | Google Fonts fails (offline network) |

**Overall: 5/5 scenarios pass. 1 medium bug, 2 low issues found.**

---

## Scenario 1: Jobs Dashboard

**URL:** `http://localhost:8502/jobs`

**Result: PASS**

The jobs dashboard renders correctly:
- Page header shows "Jobs" with description "Track extraction and review progress for your documents"
- Stats counters visible: Total Jobs (2→3), Extracting (1→2), In Review (0), Published (0)
  - Note: counts changed during testing as Task #4 uploaded a new Broadmeadows PDF
- Search box ("Search jobs") functional
- Filter buttons: All, Extracting, Pending, In Review, Published, Refresh
- "New Job" button present

**Job Cards Observed:**
1. `AlexanderHospital (1).pdf` — Pending Review, 7 buildings, 120 records, Review link
2. `ssCF_Broadmread.pdf` — Extracting, Stage 1/9 — Initializing, progress bar visible
3. `broadmeadows-police-station-samp (1).pdf` — Extracting, Stage 1/9 — Document Structure (appeared during test run — Task #4 upload)

**Evidence:** `screenshots/jobs-dashboard.png`

---

## Scenario 2: Job Detail Page

**URL:** `http://localhost:8502/jobs/source:qnt6w2t1h251x0y0uxpw` (AlexanderHospital)

All 6 tabs tested successfully.

### Overview Tab — PASS
- Displays: Total Records (120), Buildings (7), Missing Fields % (42.7%), Extraction Quality (0/100), Validation Passed (all 120 records)
- Document Metadata: Type = ARA
- Quick Actions: Re-Review Buildings, Re-Review Records, Re-Extract
- Header action buttons: Cancel Extraction, Export CSV, Export Excel
- **Bug found:** Header status badge shows "Extracting" even though API reports `status: "completed"` and jobs list shows "Pending Review". Investigation shows `processing_info.completed_at` is `None` despite extraction completing. The frontend may use `completed_at` to derive display status rather than the `status` field.

**Evidence:** `screenshots/job-detail-overview.png`

### Buildings Tab — PASS
- AG Grid renders 7 buildings correctly
- Columns: Asset Name, Year Built, Construction Type, Street Address, Suburb, Postcode, Asset Type
- Pagination: 1 to 7 of 7 (single page)
- "Columns" button for column visibility
- "View building details" action button per row — opens dialog correctly
  - Dialog shows comprehensive building form: Identity (Building Code, Asset Name, Internal ID, External ID), Location (Address, Suburb, Postcode, State), Construction (Asset Type with full picklist)

**Evidence:** `screenshots/job-detail-buildings.png`, `screenshots/building-detail-dialog.png`

### ACM Records Tab — PASS
- Shows 120 records across 7 buildings
- Building tab strip: All Records (120), Myrtle Street Clinic (3), Pathology Department B00B (32), Main Hospital Building (55), Mortuary Buildings (7), Pathology Department B003 (2), VMO Accommodations (12), Nurses Accommodation (9)
- Grid columns: Building Code, Item Name, Friability, ACM Product Group, ACM Product Type, Condition, Disturbance Potential
- Pagination: 50 per page, 3 pages
- "Search records..." textbox, "Group by Room", "Columns", "Export" buttons

**Evidence:** `screenshots/job-detail-acm-records.png`

### Content Tab — PASS
- Shows raw PDF text content extracted per page (34 pages visible)
- "Open PDF" link (→ `/api/sources/source:xxx/download`)
- "Download PDF" button
- Text content rendered as paragraphs with page markers (e.g., "--- Page 1 ---")

**Evidence:** `screenshots/job-detail-content.png`

### Raw Tables Tab — PASS
- Shows 17 table section(s)
- Stats: Register: 0, Metadata: 0, Docling: 17, Merged cells: 16
- Each table shows page number, provider (Docling Direct API), and merged cell status
- Tables rendered in iframes

**Evidence:** `screenshots/job-detail-raw-tables.png`

### Log Tab — PASS
- Shows "Extraction in Progress — Pipeline Stages 1/9 complete"
- All 9 stages listed: Document Analysis, Format Detection, Building Inventory, Docling Tables (11m 20s), Extracting Records, Validation, Corrective Loop, Recovery Scan, Saving Records
- "Show Logs (5)" expandable button

**Evidence:** `screenshots/job-detail-log.png`

---

## Scenario 3: Chat Sidebar

**Result: PASS**

The chat sidebar opens and responds correctly:
- "Expand chat panel" button on job detail page opens the chat panel
- Chat panel shows: "ACM-AI Chat" header, session switcher, model selector ("Default")
- Suggested prompts: "Show ACM statistics summary", "List all buildings", "Find high risk items"
- "ACM Data" toggle (enabled by default)
- Message input: "Ask a question... (Ctrl+Enter to send)"

**Test message sent:** "How many buildings are in this document?"

**Response received:**
- First called statistics tool ("Analyzing statistics" button shown during processing)
- Then called building list tool ("Loading building list")
- Final response: Correctly identified 7 buildings with individual ACM record counts (Main Hospital Building: 55, Pathology B00B: 32, VMO Accommodations: 12, Nurses Accommodation: 9, Mortuary Buildings: 7, Pathology B003: 2, Myrtle Street Clinic: 3). Total = 120 records.
- Response was accurate and used proper tool-calling pattern

**Evidence:** `screenshots/job-detail-chat-open.png`, `screenshots/job-detail-chat-response.png`

---

## Scenario 4: AI-Editor

**Result: PASS (with UX note)**

**AI-Editor List (`/ai-editor`):**
- Page loads correctly (via sidebar link navigation)
- Shows "AI-Editors" heading, search box, "New AI-Editor" button
- 3 active AI-Editors visible:
  - `broadmeadows police station samp` — Auto-created 2026-04-09, 1 source
  - `AlexanderHospital` — Auto-created 2026-04-05, 1 source
  - `Broadmeadows Test` — Auto-created 2026-04-05, 1 source

**UX note:** Clicking the card area triggers a context menu (Archive/Delete) rather than navigating to the AI-Editor detail. The card title does not appear to be a clickable link. Direct URL navigation (`/ai-editor/notebook:xxx`) works but `agent-browser open` times out due to colon in URL (not an app issue).

**AI-Editor Detail (`/ai-editor/notebook:d6cajr5imht25hup23gp`):**
- Breadcrumb: Home > AI-Editor > AlexanderHospital
- Name editing: "AlexanderHospital" button
- Archive and Delete buttons
- Description: "Auto-created from upload of AlexanderHospital.pdf on 2026-04-05"
- Sources section: Shows "AlexanderHospital (1).pdf" with type "upload"
- Notes section: "No notes yet" state with "Write Note" prompt
- Chat panel with suggested prompts: "Summarize this document", "Key findings"
- Chat input functional

**Evidence:** `screenshots/ai-editor-list.png`, `screenshots/ai-editor-detail.png`

---

## Scenario 5: Navigation & UI

**Result: PASS**

### Sidebar Navigation
- Sidebar expand/collapse: Works correctly (toggle between "Expand sidebar"/"Collapse sidebar")
- Navigation links: Dashboard (`/`), Jobs (`/jobs`), AI-Editor (`/ai-editor`) all present
- "Upload Document" button in sidebar top area
- Logo: "VAEA - Victorian Asbestos Eradication Agency" image

**Evidence:** `screenshots/sidebar-expanded.png`

### Command Palette (Ctrl+K)
- Opens correctly via keyboard shortcut
- Groups: Navigation, Actions, Go to, Create, Theme
- Navigation options: Sources, Ask and Search, Models, Settings, Advanced, Visit Landing, Documentation
- Actions: Upload Document, Export ACM to CSV/Excel, Extract ACM Records, Add ACM Record
- Go to: Dashboard, ACM Register
- Create: Upload Document
- Theme: Light, Dark, System

**Evidence:** `screenshots/command-palette.png`

### Settings Menu
- Opens via Settings button (bottom of sidebar)
- Options: Extraction Monitor, Extraction, AI Models, Parsers, Field Schema, Processing, General
- Theme Toggle included
- Sign Out option

**Evidence:** `screenshots/settings-menu.png`

### Console/Network Errors
- **Google Fonts CSS fails to load** — `https://fonts.googleapis.com/css2?family=Inter...` returns status 0 (offline). This is a low-priority issue as the app uses system fallback fonts and remains functional.
- **No HTTP 4xx/5xx errors** detected on API calls during testing
- All primary data APIs returned 200 OK

---

## Issues Found

### Priority: Medium

1. **Status badge on job detail page shows wrong status**
   - **Page:** `/jobs/source:qnt6w2t1h251x0y0uxpw`
   - **Observed:** Header shows "Extracting Uploaded: 4 days ago 120 records 7 buildings"
   - **Expected:** Should show "Pending Review" (matching jobs list and API `review_status: "pending_review"`)
   - **Root cause likely:** `processing_info.completed_at` is `None` despite `processing_info.status` = "completed". Frontend may derive display status from `completed_at` rather than the `status` field.
   - **Impact:** Users see incorrect extraction status on the detail page

### Priority: Low

2. **AI-Editor card not directly clickable for navigation**
   - **Page:** `/ai-editor`
   - **Observed:** Clicking AI-Editor card body opens Archive/Delete context menu
   - **Expected:** Should navigate to detail page `/ai-editor/notebook:xxx`
   - **Impact:** UX friction — users may not know to avoid the card button area

3. **Google Fonts offline dependency**
   - **Observed:** Inter font CSS fails to load from `fonts.googleapis.com`
   - **Expected:** App should bundle fonts or have strong fallback
   - **Impact:** Minor visual difference in font rendering (fallback fonts used)

---

## Screenshots Index

| File | Description |
|------|-------------|
| `jobs-dashboard.png` | Jobs list page with 2 job cards |
| `job-detail-overview.png` | Job detail Overview tab |
| `job-detail-buildings.png` | Job detail Buildings tab with AG Grid |
| `job-detail-acm-records.png` | Job detail ACM Records tab |
| `job-detail-content.png` | Job detail Content tab (raw PDF text) |
| `job-detail-raw-tables.png` | Job detail Raw Tables tab |
| `job-detail-log.png` | Job detail Log tab with pipeline stages |
| `job-detail-chat-open.png` | Chat sidebar expanded |
| `job-detail-chat-response.png` | Chat AI response to building count query |
| `building-detail-dialog.png` | Building detail dialog (from Buildings tab) |
| `ai-editor-list.png` | AI-Editor list page |
| `ai-editor-detail.png` | AI-Editor detail page |
| `sidebar-expanded.png` | Sidebar in expanded state |
| `command-palette.png` | Command Palette (Ctrl+K) |
| `settings-menu.png` | Settings dropdown menu |
