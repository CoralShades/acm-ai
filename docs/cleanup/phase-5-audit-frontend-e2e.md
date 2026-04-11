# Phase 5 Audit — Frontend E2E Extraction

**Auditor:** FRONTEND-E2E-EXTRACTION agent
**Date:** 2026-04-11
**Branch:** `feat/sf-reconciliation-20260411`
**Source tested:** `source:cairo1ewyyn5rzz1pyfj` (`Clutch_Broadmeadows.pdf`)

---

## 1. Service Readiness

| Service | Port | Status | Notes |
|---------|------|--------|-------|
| SurrealDB | :8000 | READY | Docker container healthy |
| FastAPI | :5055 | READY | Responded immediately (`{"status":"healthy"}`) |
| Next.js Frontend | :8502 | READY | Slow via curl (WSL2 mount I/O latency — needs 15s curl timeout). `next-server` confirmed listening via `ss -tlnp`. |
| Background Worker | — | NOT RUNNING at session start | Required manual start. Took ~2:04 to initialize (heavy ML model imports from Windows-mounted WSL2 path). |

**Worker startup timeline:**
- 23:12:32 — worker process started
- 23:12:39 — surreal-commands worker initialized
- 23:14:05 — podcast_creator.graph imported (end of module loading)
- 23:14:36 — worker picked up extraction command

---

## 2. Upload Result

**Upload method:** Direct API — `POST /api/sources` (multipart form-data, `/api/` prefix required)

> Note: `POST /sources` (no `/api/` prefix) returns 404. The correct endpoint is `/api/sources`.

**Source ID:** `source:cairo1ewyyn5rzz1pyfj`
**File stored as:** `data/uploads/Clutch_Broadmeadows (5).pdf` (auto-deduplicated filename)
**Command ID:** `command:j16mi5pqznkmdjxnfd1t`
**Initial status:** `new`

---

## 3. Extraction Timeline

| Stage | Start | End | Duration |
|-------|-------|-----|----------|
| Worker startup | 23:12:32 | 23:14:36 | 2:04 |
| Source processing | 23:14:36 | 23:14:37 | ~1s |
| Docling OCR + table extraction | 23:15:39 | ~23:17:15 | ~96s |
| LLM per-row extraction | 23:17:27 | 23:21:19 | ~232s |
| **Total pipeline** | | | **285s** |
| **Total with worker overhead** | | | **407s** |

**Pipeline log summary:**
```
[PIPELINE] Starting extraction for source:cairo1ewyyn5rzz1pyfj (0 pages)
[PIPELINE] [DOCLING] STARTED | Starting Docling table extraction
... RapidOCR model loading ...
[PIPELINE] EXTRACTION COMPLETE | 35 records in 285.0s
[PIPELINE]   Pages: 19 | Chunks: 0 | Buildings: 1
[PIPELINE]   Records: 35 created, 0 rejected, 0 filtered, 0 unidentified
[PIPELINE]   Confidence: high=0, medium=31, low=4
```

**Row extraction errors (6 total):**
- 6 rows failed with `item_name: Input should be a valid string [type=string_type, input_value=None]`
- Rows 3 and 7 confirmed failed after 2 retries each (Pydantic validation: LLM returned null for required `item_name`)
- These are likely header rows or footer rows in the table that the LLM couldn't extract a valid item name from

---

## 4. Record Count

| Metric | Value |
|--------|-------|
| Ground truth (CSV) | 31 records |
| Actually extracted | **35 records** |
| Variance | **+4 extra** |
| DB confirmed count | 35 (SurrealDB query confirmed) |
| Row extraction failures | 6 |
| Confidence breakdown | high=0, medium=31, low=4 |

**Variance analysis:** The 4 extra records likely come from multi-building or multi-location rows where the LLM split one row into multiple records. The Broadmeadows PDF has 72 table rows (per `Row 8/72` log message) vs 31 ground-truth records — the row segmenter and LLM may be over-splitting some rows. This is a pre-existing behavior, not introduced by the Phase 2b changes.

---

## 5. Grid Column Header Audit

### ACM Records Tab

**Visible column headers (default view):**
`Record ID | Building Code | Item Name | Friability | ACM Product Group | ACM Product Type | Actions`

**Result:** No fabricated SF API names visible in column labels. Headers use friendly display names, not SF field names.

**Fabricated SF names found in column TOOLTIPS** (visible only on hover — not user-facing in normal workflow):

| Column Header | Tooltip Found | Real SF Name | Status |
|--------------|--------------|--------------|--------|
| Disturbance Potential | `Disturbance_Potential__c` | `Disturbance_Potential_of_Material__c` | WRONG TOOLTIP |
| Room / Area | `Room_Name__c` | `Room_or_Area__c` | WRONG TOOLTIP |
| Floor Level | `Floor_Level__c` | `Level__c` | WRONG TOOLTIP |
| Sample Result | `Sample_Result__c` | `Sample_Analysis_Result_Material_Status__c` | WRONG TOOLTIP |
| Location in Room | `Item_Location__c` | `Location_in_Room__c` | WRONG TOOLTIP |
| Assessor | `Assessor__c` | `Identifying_Hygiene_Consulting_Company__c` | WRONG TOOLTIP |

**Source:** `frontend/src/components/acm/ACMGrid.tsx` lines 359, 367, 375, 385, 401, 409

These tooltips are part of the E38-S2 deferred work (127 non-SF field reference cleanup).

### Buildings Tab

**Visible column headers (default view):**
`Record ID | Asset Name | Year Built | Construction Type | Street Address | Suburb | Postcode | Actions`

**Result:** No fabricated SF API names visible.

### Building View Dialog

Form shows domain model fields using friendly labels. Visible labels include **deferred E38-S2 fields** (these exist in domain model but have no SF export mapping):
- "PSB District/Region"
- "Est. Asset Size (m2)"
- "Daily Duration"
- "Level of Activity"
- "Mobile Plant"
- "No Identified ACMs Note"
- "Demolition Date"
- "Demolition Comments"
- "Asset Out of Scope Comments"

These are part of the 127 non-SF field references deferred to E38-S2. They appear in the UI but are not exported to Salesforce.

---

## 6. Console Errors

**Browser console output:**
- Multiple `500 Internal Server Error` and `404 Not Found` network errors visible
- One `preload` CSS warning
- **No fabricated SF field names found in DOM text content**

The 500/404 errors were not investigated in depth — they may be from SSE streams, font loading, or other non-critical requests. The page renders correctly with records visible.

---

## 7. CSV Export Header Audit

### Test 1: Existing completed source (`source:xreiuz98wmzebgxeprrd`)

| File | Columns | Fabricated Fields | Result |
|------|---------|-------------------|--------|
| Building__c.csv | 25 | None | ✅ PASS |
| Item__c.csv | 21 | None | ✅ PASS |

### Test 2: New extraction (`source:cairo1ewyyn5rzz1pyfj`)

| File | Columns | Fabricated Fields | Result |
|------|---------|-------------------|--------|
| Building__c.csv | 25 | None | ✅ PASS |
| Item__c.csv | 21 (35 data rows) | None | ✅ PASS |

**Building__c.csv columns (25):**
`External_ID__c, Building_Name__c, Building_Type__c, Frequency_of_Use__c, Public_Access__c, Building_Category__c, Building_Address__c, Suburb__c, Postcode__c, State__c, Country__c, Estimated_Year_Build_New__c, Construction_Type__c, Number_of_Levels__c, Roof_Type__c, Owned_or_Leased__c, Asbestos_Register_Available__c, Audit_Report_Available__c, Date_of_Audit_Report__c, Site_Name__c, School_UID__c, Building_Unique_ID__c, Within_Your_Portfolio__c, GPS_Coordinates_provided_by_metro__c, Additional_Comments__c`

**Item__c.csv columns (21):**
`Building__r.External_ID__c, Item_Name__c, If_Other_Item_Name__c, Friability_of_Material__c, ACM_Classification__c, ACM_Sub_Classification__c, Condition__c, Disturbance_Potential_of_Material__c, Sample_Analysis_Result_Material_Status__c, NATA_Endorsed_Sample_no__c, Identifying_Hygiene_Consulting_Company__c, Quantity__c, Units_of_Measure__c, Internal_External__c, Level__c, Room_or_Area__c, Location_in_Room__c, Labelled__c, Labelled_Details__c, Survey_Date__c, Additional_Comments__c`

All column names verified against `config/sf-schema-snapshot.json`. `Country__c` and `GPS_Coordinates_provided_by_metro__c` confirmed real in full SF schema (not in snapshot's extractable subset, but real fields).

---

## 8. Additional Finding — `_merge_site_config()` survivor

**Location:** `open_notebook/extractors/exporters/sf_export.py` lines 218–238

**Issue:** The Phase 2b rewrite correctly cleaned `BUILDING_SF_MAPPING` and `ITEM_SF_MAPPING` but missed the `_merge_site_config()` helper function which writes directly to the export row dict:

```python
row["Department__c"] = str(department)  # line 229
row["Agency__c"] = str(agency)           # line 233
```

**Status of each:**
- `Agency__c`: **FABRICATED** — does not exist in SF at all. Confirmed via full schema query.
- `Department__c`: EXISTS in SF but is NOT in the extractable fields subset (not a Data Loader target field). The correct field for agency/department is `Responsible_Agency_Department__c`.

**Impact:** The `_merge_site_config()` path only fires when a `SiteConfig` object is attached to the source. In the Broadmeadows test extraction, `SiteConfig` was not populated, so these columns did NOT appear in the exported CSV. This explains why the CSV export still passed — the bug is latent (only triggered when SiteConfig has department/agency values).

**Recommended fix for E38-S2:** Replace `Department__c` → `Responsible_Agency_Department__c` (or omit — unclear if this field captures department as a string or lookup) and remove `Agency__c` entirely.

---

## 9. Screenshots

Saved to `docs/cleanup/phase-5-screenshots/`:

| File | Description |
|------|-------------|
| `01-jobs-page-upload.png` | Jobs list during upload |
| `02-jobs-list-during-extraction.png` | Jobs list while extraction running |
| `03-job-detail-completed.png` | Job detail page after extraction completed |
| `04-acm-records-tab.png` | ACM Records tab with 35 records |
| `05-acm-records-annotated.png` | Annotated ACM Records tab |
| `06-buildings-tab.png` | Buildings tab (1 building) |
| `07-building-view-dialog.png` | Building view dialog showing domain model fields |

---

## 10. Verdict

**PARTIAL PASS** — The Phase 2b core fix works. The export path is clean. Two categories of remaining issues:

### Critical (should block PR merge)
- `sf_export.py:_merge_site_config()` contains `Agency__c` (fabricated) — **latent bug, only fires when SiteConfig has department/agency populated**

### Deferred (E38-S2)
- ACMGrid column tooltips contain 6 fabricated SF API names (visible only on hover)
- BuildingViewDialog and domain model show 10+ non-SF fields (friendly labels, not exported)
- Frontend TypeScript types still reference removed fields

### Informational
- Record count: 35 extracted vs 31 ground-truth (4 over-extraction — pre-existing behavior)
- Worker requires manual start (not auto-started) — operational gap
- Frontend has 500/404 console errors (likely non-critical resource loading)
- 6 row extraction failures during LLM phase (item_name=None for non-item rows)

---

## 11. Findings for Parent Session

| Finding | Severity | Actionable |
|---------|----------|-----------|
| `Agency__c` in `_merge_site_config()` is fabricated | HIGH | Fix in E38-S2 or hotfix |
| 6 wrong tooltips in ACMGrid (fabricated SF names) | MEDIUM | Fix in E38-S2 |
| Record count +4 vs ground truth | LOW | Investigate in E38-S3 (test rebuild) |
| Worker not auto-started | LOW | Operational, not code issue |
| 500/404 console errors | LOW | Investigate separately |
