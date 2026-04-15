# E38 E2E Verification — Findings Log

**Date:** 2026-04-15
**Branch:** `feat/sf-reconciliation-20260411`

## Alignment Baseline
- **SCP:** `sprint-change-proposal-20260411-sf-reconciliation.md`
- **Snapshot:** `config/sf-schema-snapshot.json` (25 Building + 27 Item extractable fields)
- **Mapping:** `config/bar_to_sf_mapping.yaml`
- **Decisions:** `docs/cleanup/assumptions-and-decisions.md` (DEC-001..DEC-020)

## Known E38 Stories (pre-existing, check if still valid)
| Story | Description | Status |
|-------|-------------|--------|
| E38-S6 | Fix _merge_site_config Department__c/Agency__c | drafted |
| E38-S7 | Fix Labelled__c bool-to-str translation | drafted |
| E38-S8 | ISO 8601 date normalization | drafted |
| E38-S10 | Re-add Est_Building_Size_m2__c + Hygienist_Recommendations__c | drafted |
| E38-S11 | Fix schema_inference.py fabricated names | drafted |
| E38-S12 | Pre-drop data migration sample_result | drafted |

## Service Startup Findings
<!-- log-monitor populates this section -->

### Docker Container Status (2026-04-15 ~18:00)
- `acm-ai-db` (SurrealDB v2.2.1): **UP, HEALTHY** ✅ — ports 0.0.0.0:8000→8000
- `acm-ai-ollama` (Ollama latest): **UP, UNHEALTHY** ⚠️ — port 11434/tcp (not exposed to host). This matches **E38-S13**: docker-compose.yml healthcheck uses `curl` but Ollama image lacks `curl` — should be `wget`. False-unhealthy, Ollama is likely serving correctly despite the health status.

---

### SurrealDB
- [2026-04-15T07:53:38Z] [SURREALDB] [INFO] Clean startup — SurrealDB 2.2.1 on linux/x86_64, kvs at `surrealkv://mydata/open_notebook.db`
- [2026-04-15T07:53:39Z] [SURREALDB] [WARN] `Credentials were provided, but existing root users were found. The root user 'root' will not be created` — **benign**, expected on warm restart when root already exists
- [2026-04-15T07:53:39Z] [SURREALDB] [WARN] `Consider removing the --user and --pass arguments from the server start command` — **benign**, cosmetic config warning
- **Status: HEALTHY** — listening on 0.0.0.0:8000, no errors

### FastAPI (port 5055)
- [2026-04-15 ~16:36] [API] [INFO] Multiple restarts today (16:36, 16:49, 17:16, 17:45×2, 17:55) — each producing `podcast_creator.graph: Creating podcast generation graph` at startup. **Normal API startup event**.
- [2026-04-15 17:55:09] [API] [INFO] Last confirmed restart at 17:55. `GET /health` returns `{"status":"healthy"}`.
- **SF schema verified loaded**: `GET /api/acm/field-schema` returns `version: "salesforce-v2-2026-04-11"`, 25 Building fields, all with real SF API names (`Building_Name__c`, `Building_Type__c`, etc.). **E38-S0 wiring confirmed functional.**
- **No new errors in api-error.log today** — all errors in that file are from 2026-03-22 (pre-E38 branch).
- **Status: HEALTHY** — API is up, SF snapshot wired correctly

### Worker (run_worker.py)
- [2026-04-15] [WORKER] **NO entries in worker.log today**. Last entry: `2026-04-11 23:14:05` (two dual-instance lines). Worker appears to have been stopped after Phase 5 audit.
- **Status: NOT RUNNING** — extraction commands will queue in SurrealDB but not process until worker is started

### Frontend (port 8502)
- Not reachable via localhost from WSL during log scan — frontend is served from Windows PowerShell (Windows npm). Status unknown from this agent.
- Phase 5 boot logs at `logs/phase5-frontend-boot2.log` last written 2026-04-11.
- **Status: UNKNOWN** — cannot verify from WSL without browser automation

### Pre-existing API errors (from api-error.log, all dated 2026-03-22, pre-E38)
- [2026-03-22] [API] [ERROR] `Error listing raw extractions for source source:abc: DB connection failed` — test fixture artifact, not a real source
- [2026-03-22] [API] [ERROR] `Row 1/1: extraction failed after retries: Failed to extract row 0 after 2 attempts: No JSON object found in response text` — test run failure, pre-E38
- [2026-03-22] [API] [ERROR] `Schema check failed: building_record table does not exist` — pre-migration-run artifact, not current
- **Assessment: None of these errors are active today** — all from March test runs

## Extraction Run Findings
<!-- log-monitor + team-lead populate this section -->

### Static Code Scan — Fabricated SF Field References (pre-extraction, confirmed by log monitor)

The following issues were confirmed by code scan matching E38 story scope. These are **latent bugs** — they don't appear in startup logs but will manifest at export/extraction time.

#### E38-S6 CONFIRMED: Department__c + Agency__c in sf_export.py
- [2026-04-15] [API/CODE] [ERROR] `open_notebook/extractors/exporters/sf_export.py:229,233` writes `row["Department__c"]` and `row["Agency__c"]` — **both fabricated** (real field is `Responsible_Agency_Department__c`). Fires when `SiteConfig.department`/`.agency` is populated.
- Code: `_merge_site_config()` at lines 215-237
- **Impact**: Any export where site config is populated will include unmappable columns. SF Data Loader will reject or silently drop them.
- **Story**: E38-S6 (1 SP, drafted)

#### E38-S7 CONFIRMED: Labelled__c bool→str translation missing
- [2026-04-15] [API/CODE] [WARN] `ACMRecord.acm_labelled` is `bool`, but `ITEM_SF_MAPPING` reads `labelled_sf` (str). No translation layer between them.
- Verified: In April 11 extraction, `acm_labelled: false` in records — but `Labelled__c` column will be EMPTY in every Item CSV export.
- **Impact**: `Labelled__c` SF field always blank in exports, even when extraction found a value.
- **Story**: E38-S7 (1 SP, drafted)

#### E38-S10 CONFIRMED: Est_Building_Size_m2__c + Hygienist_Recommendations__c over-dropped
- [2026-04-15] [API/CODE] [WARN] `open_notebook/domain/acm.py:766` still has `AliasChoices("est_building_size_m2", "Est_Building_Size_m2__c")` — domain model retains field but sf_export.py does NOT include it in `BUILDING_SF_MAPPING`. This is a real SF field incorrectly removed in Phase 2b.
- `acm.py:251` has `AliasChoices("hygienist_recommendations", "Hygienist_Recommendations__c")` — likewise retained in domain but absent from export.
- `schema_inference.py:157,214` still includes `Hygienist_Recommendations__c` in `SF_FIELD_CATALOG` and `SF_TO_CANONICAL` — shows it is a real field the system knows about.
- **Impact**: Two real SF fields not exported to CSV. VAEA SF Data Loader loses them.
- **Story**: E38-S10 (1 SP, drafted)

#### E38-S11 CONFIRMED: schema_inference.py fabricated field names
- [2026-04-15] [API/CODE] [ERROR] `schema_inference.py` `SF_FIELD_CATALOG` contains:
  - `"Disturbance_Potential__c"` — **fabricated** (real: `Disturbance_Potential_of_Material__c`)
  - `"Building_Code__c"` — **fabricated** (does not exist on `Building__c` object per live describe)
- `SF_TO_CANONICAL` and `SF_TO_ITEM_ROW_FIELD` both contain `Disturbance_Potential__c` (lines ~214-232)
- These names drive per-run column alias resolution and leak into parsing logic for header detection.
- **Impact**: Column aliasing silently fails for disturbance_potential fields when PDF headers match the fabricated name; values may not be extracted to the correct field.
- **Story**: E38-S11 (2 SP, drafted)

#### api/routers/acm.py references Risk_Status__c (formula field)
- [2026-04-15] [API/CODE] [WARN] `api/routers/acm.py:840-841` references `Risk_Status__c` for grid color coding: `if header == "Risk_Status__c" and i_row.get(header) in RISK_COLORS`. Per Phase 2b SCP, `Risk_Status__c` is a **formula/roll-up field**, not writable. Grid shows stale/wrong coloring.
- **Impact**: Visual only (grid UI), but contributes to domain confusion. Tracked under E38-S2 clean-up scope.

### April 11 Extraction Run Analysis (source:cairo1ewyyn5rzz1pyfj — Clutch_Broadmeadows 5.pdf)
Extracted prior to this verification run. Snapshot from API at 17:55 today:

| Metric | Value | Expected | Status |
|--------|-------|----------|--------|
| Records extracted | 35 | 31 | OVER (4 garbage rows present) |
| Buildings found | 1 | 1 | OK |
| material_condition | "Stable" | "Stable" | ✅ BAR→SF mapping working |
| risk_status in records | "Medium" | N/A (should be dropped, formula field) | ⚠️ Still populated |
| building_name | null | populated | ⚠️ Not extracted |
| agency | "Victoria Police" | "Victoria Police" | ✅ |
| acm_labelled | false (bool) | — | ⚠️ E38-S7: won't export to Labelled__c |
| Garbage rows | 1+ ("Medium Priority - May require action...") | 0 | ⚠️ Section header misidentified as ACM row |

- [2026-04-11 13:21] [API] [WARN] Record `b9d9urtw7ql9rilohbkv` has `data_issues: ["No taxonomy match for item_name: 'Medium Priority - May require action in the short term'"]` — section header parsed as ACM row. Row-level dedup issue.
- Worker completed extraction at `2026-04-11T13:21:23` (processing_info.completed_at=null is a known cosmetic issue).

### April 11 Extraction Pipeline Log (from logs/runs/2026-04-11T13-16-33_yyn5rzz1pyfj/extraction.log)
Full pipeline trace — **NO errors, NO tracebacks**:
```
[STRUCTURE] COMPLETED in 27.9s | Inventory + page tags synthesized: 1 buildings | pages_tagged=13
[ORCHESTRATOR] Building extraction: 1/1 saved
[ORCHESTRATOR] Item extraction: 72 records from 1 buildings
[EXTRACT] COMPLETED in 0.0s | 72 raw records extracted
[VALIDATE] COMPLETED in 0.0s | 72 accepted, 0 rejected, 0 filtered
[STORE] Deduplicated: 37 merged, 35 unique
[STORE] COMPLETED in 1.3s | 35 saved, 1 parent sections, 0 errors
EXTRACTION COMPLETE | 35 records in 285.0s
  Confidence: high=0, medium=31, low=4
```
- **Assessment**: Pipeline ran cleanly. 4 low-confidence records are the over-extraction culprit (35 vs 31 expected). No runtime errors or exceptions.

### Log Monitoring Baseline (2026-04-15 ~18:00)
- `api.log`: 1641 lines (last entry 17:55:09 — API startup)
- `worker.log`: 104 lines (last entry 2026-04-11 23:14 — worker NOT running)
- `surrealdb.log`: 22 lines (startup only, clean)
- Most recent run dir: `2026-04-11T13-16-33_yyn5rzz1pyfj` (April 11)
- **Watching for**: new entries in all logs + new subdirs in `logs/runs/`

## Frontend/UI Findings
<!-- frontend-auditor populates this section -->

## Data Quality Findings

**Source tested:** `source:cairo1ewyyn5rzz1pyfj` — Clutch_Broadmeadows (5).pdf  
**Verified:** 2026-04-15 via live API at http://localhost:5055  
**Method:** Direct record inspection (`/api/acm/records`) + SF CSV export (`/api/acm/export/sf-csv`) + code review  

---

### DA-01 — CRITICAL: Record count 35 vs 31 expected; 7 junk rows in SF export

**Evidence:**
- API returns 35 records; expected 31 (per E2E test baseline).
- 4 records are priority-label banners extracted as ACM items:
  - `acm_record:k3nsan3y8dihus10i89q` — product: `"HighPriority-Requiringimmediateaction"`
  - `acm_record:b9d9urtw7ql9rilohbkv` — product: `"Medium Priority - May require action in the short term"`
  - `acm_record:jrriq8ypiukgvzatcv7p` — product: `"LowPriority-Mayrequireaction in themedium term"`
  - `acm_record:qghj6jbndapyfpg2fwqr` — product: `"Unknown"`, raw_text: `"VeryLowPriority-Requiresongoingmanagement..."`
- 3 records are "No access" note rows that failed LLM extraction:
  - `acm_record:obzqhaojprgv5fkgtzb7` — raw_text: `"- — No access"`
  - `acm_record:rdri2sbjxukxou4sumw6` — raw_text: `"Internal lining: No access at the time of the Assessment"`
  - `acm_record:eb7cewed97vbl5btxfpw` — raw_text: `"toilet: No access due to locked door"`
- All 7 junk rows export to `Item__c.csv` with `Item_Name__c` set to the junk text or "Unknown".
- Priority labels (`"HighPriority-Requiringimmediateaction"`) are NOT valid SF `Item_Name__c` picklist values (294 restricted values); they are not in `If_Other_Item_Name__c` fallback either (set to same value).
- "No access" rows have all Item fields blank — they will insert as empty SF items.

**Root cause:** Row-level dedup/filter does not exclude section headers or "no access" notes. Layer 2 LLM correction was disabled (correct per DEC-005), but no pre-filter step discards non-ACM rows.

**SF impact:** CRITICAL — 7 invalid Item__c rows will be submitted to Data Loader. "HighPriority..." item name will fail restricted picklist validation. "No access" items will insert as blank records.

---

### DA-02 — CRITICAL: `_merge_site_config` writes fabricated `Department__c` + `Agency__c` fields

**Evidence:**
- `open_notebook/extractors/exporters/sf_export.py:229,233`:
  ```python
  row["Department__c"] = str(department)   # line 229 — FABRICATED
  row["Agency__c"] = str(agency)           # line 233 — FABRICATED
  ```
- `config/sf-schema-snapshot.json` confirms neither `Department__c` nor `Agency__c` exist on `Building__c`.
- The real field is `Responsible_Agency_Department__c` (string, non-required, label: "Responsible Agency/Department").
- Confirmed by cross-checking the full extractable fields list: `Responsible_Agency_Department__c` is present; `Department__c` and `Agency__c` are absent.

**SF impact:** CRITICAL — When `SiteConfig.department` or `.agency` is non-null, the export CSV will contain columns `Department__c` and `Agency__c` that SF Data Loader will reject. The actual `Responsible_Agency_Department__c` field will be blank. **Pre-existing known story: E38-S6.**

---

### DA-03 — CRITICAL: `Labelled__c` is EMPTY for all 35 rows in Item CSV export

**Evidence:**
- CSV column `Labelled__c`: all 35 rows = `""` (confirmed via CSV parse).
- `ITEM_SF_MAPPING` maps `("Labelled__c", "labelled_sf")` — reads `ACMRecord.labelled_sf`.
- `ACMRecord.labelled_sf` (domain/acm.py:306) is NEVER populated by the extraction pipeline. Pipeline populates `acm_labelled` (bool) but no step converts bool → `labelled_sf` str.
- Pipeline grep confirms zero assignments to `labelled_sf` in orchestrator.py or acm_extraction.py.
- Live records show: `acm_labelled=True` for 12 records, `acm_labelled=False` for 12 records, `acm_labelled=None` for 11 records — but `labelled_sf` is `None` for all.

**Root cause:** The bool-to-string bridge (`acm_labelled → labelled_sf`) was never implemented. `bar_to_sf_mapping.yaml` maps `"YES" → "Yes"` for this field, but the LLM outputs a bool, not a string — so that mapping also never fires.

**SF impact:** CRITICAL — `Labelled__c` (a key compliance field) will be blank on every imported item. **Pre-existing known story: E38-S7.**

---

### DA-04 — HIGH: Date_of_Audit_Report__c is NOT ISO 8601 — SF Data Loader will reject

**Evidence:**
- Building CSV: `Date_of_Audit_Report__c = "8th April 2020"` (human-readable, non-ISO).
- SF `Date_of_Audit_Report__c` is type `date` — Data Loader requires ISO 8601 format (`YYYY-MM-DD`).
- `Survey_Date__c` in Item rows is also a date field; all rows export empty (no date extracted), so currently no failure — but if populated, same issue applies.

**Root cause:** No date normalization step converts extracted date strings to ISO 8601. The extraction pipeline stores raw text (`"8th April 2020"`) from the PDF.

**SF impact:** HIGH — Data Loader will reject the Building row on date parse failure. **Pre-existing known story: E38-S8.**

---

### DA-05 — HIGH: 74% of records (26/35) have NULL Condition, Friability, and Disturbance Potential

**Evidence:**
```
Condition__c values:    {'Stable': 9, None: 26}
Friability values:      {'Non-friable': 9, None: 26}
Disturbance_Potential:  {'Low': 9, None: 26}
```
- The same 9 records have all three fields populated; 26 records have all three blank.
- These are core ACM risk assessment fields — blank values mean SF cannot compute risk scores for 74% of items.

**Root cause:** Extraction pipeline only populates condition/friability/disturbance for rows where the LLM found clear values. For 26 rows (largely vinyl sheet, gaskets, mastic items), these fields were not extracted.

**Note:** This may reflect genuine absent data in the PDF (not all rows have condition assessed), but the rate (74% blank) warrants investigation against the source PDF.

**SF impact:** HIGH — VAEA risk scoring formulas depend on `Condition__c` and `Disturbance_Potential_of_Material__c`. 26 blank items will score as null/zero.

---

### DA-06 — HIGH: `Frequency_of_Use__c` = "Occupied" — not a valid SF picklist value

**Evidence:**
- Building CSV: `Frequency_of_Use__c = "Occupied"`.
- SF picklist values (from sf-schema-snapshot.json): `["Every day", "Every day with intermittent breaks", "Once every 3–5 days", "Every 2–3 weeks", "Once every 2–3 months", "Annually or less frequently"]`.
- "Occupied" is not in this list.

**Root cause:** Extraction pipeline returned the PDF's occupancy descriptor ("Occupied") without mapping it to a valid SF picklist value. No mapping entry exists in `bar_to_sf_mapping.yaml` for `Frequency_of_Use__c`.

**SF impact:** HIGH — Building__c `Frequency_of_Use__c` is a **required custom field**. Data Loader insert will fail picklist validation for this required field, blocking the entire building row (and cascade-blocking all 35 child items).

---

### DA-07 — HIGH: `GPS_Coordinates_provided_by_metro__c` and `Country__c` are not in SF snapshot

**Evidence:**
- `BUILDING_SF_MAPPING` contains: `("GPS_Coordinates_provided_by_metro__c", "gps_coordinates")` and `("Country__c", "country")`.
- `config/sf-schema-snapshot.json` extractable fields for `Building__c` do NOT include either field.
- The SCP mentions `GPS_Coordinates_provided_by_metro__c` was "added" (line 159) but it was not added to the snapshot — the snapshot only covers extractable fields, and it's unclear if this field is extractable from ARA PDFs.
- Both columns export as `""` (empty) since neither field has data, but they add unmapped columns to the CSV.

**SF impact:** MEDIUM-HIGH — If `GPS_Coordinates_provided_by_metro__c` doesn't exist on `Building__c` in the live org (not confirmed from snapshot), Data Loader will fail on unknown column. Needs verification against live org before merge.

---

### DA-08 — HIGH: `Responsible_Agency_Department__c` missing from Building CSV export

**Evidence:**
- `config/sf-schema-snapshot.json`: `Responsible_Agency_Department__c` is a real extractable Building field.
- `BUILDING_SF_MAPPING`: no entry for `Responsible_Agency_Department__c`.
- Building CSV export: field absent entirely.

**Root cause:** The Phase 2b rewrite deleted `Department__c` and `Agency__c` (fabricated) but did NOT add the real replacement `Responsible_Agency_Department__c` to the mapping table.

**SF impact:** HIGH — Department/agency information is permanently lost from SF exports even when `_merge_site_config` would provide it (DA-02 is the write path, this is the column path — both broken simultaneously).

---

### DA-09 — MEDIUM: `Units_of_Measure__c` is empty for ALL 35 items

**Evidence:**
- `Units_of_Measure__c` = `""` for all 35 rows.
- `ITEM_SF_MAPPING` maps `("Units_of_Measure__c", "extent")` — reads `ACMRecord.extent`.
- `ACMRecord.extent` is `None` for all records despite `quantity` holding values like `"20 m²"`, `"2m²"`, `"10 lm"`, `"Throughout"`.

**Root cause:** The extraction pipeline stores compound quantity+unit strings in `quantity` (e.g., `"20 m²"`) but never splits them into `quantity` (numeric) and `extent` (unit string). The field was renamed from `Extent__c` (fabricated) to `Units_of_Measure__c` in Phase 2b, but the data population path was not created.

**SF impact:** MEDIUM — `Units_of_Measure__c` on all inserted items will be blank. Operators must manually fill units after import.

---

### DA-10 — MEDIUM: Duplicate sample numbers across multiple records

**Evidence:**
```
Duplicate NATA_Endorsed_Sample_no__c values:
  34511-039-016: 3 occurrences
  34511-039-001: 3 occurrences
  34511-039-003: 3 occurrences
  34511-039-007: 3 occurrences
  34511-039-009: 2 occurrences
```
- Sample `34511-039-007` appears on 3 records: `wl2t6tlhwzj51unx1gse` (roof ductwork), `qtrns7fges23cx9x2tgy` (AHU ductwork), `uen4qkwruwhyytpqjyob` (mastic grey). These are distinct physical items that legitimately share a sample number (same lab analysis covers multiple items) — this is valid behaviour.
- However, sample `34511-039-001` appears on 3 vinyl sheet items with different `acm_labelled` values (True, False, True) and different `floor_level` values. Two of these (`acm_record:unnh56du02c8ola32rum` and `acm_record:axu5kxl5rylmd4gcw58f`) appear to be near-duplicates of the same item.

**SF impact:** MEDIUM — Legitimate multi-item samples are fine. Potential near-duplicate items will insert as separate SF records and require manual deduplication post-import.

---

### DA-11 — MEDIUM: `Building_Category__c` = "Educational and training facilities" — misidentification

**Evidence:**
- Building CSV: `Building_Category__c = "Educational and training facilities"`.
- Building is "Broadmeadows Police Station" — a police/protective services facility.
- `Building_Type__c = "Office/Commercial Building"` (plausible but generic).

**Root cause:** The extraction pipeline assigned category based on LLM inference without validating against the `Building_Type__c → Building_Category__c` dependent picklist constraint. "Educational and training facilities" is not a valid child category for "Office/Commercial Building" — dependent picklist chains are documented in the snapshot but not enforced.

**SF impact:** MEDIUM — Data Loader will reject `Building_Category__c` if it's not a valid dependent value for the selected `Building_Type__c`. Dependent picklist validation in SF is strict.

---

### DA-12 — MEDIUM: `data_issues` arrays contain duplicate row_index pairs — suggests merge artifact

**Evidence:**
- Many records have paired `row_index` entries (e.g., `['row_index: 27', 'row_index: 17']`, `['row_index: 54', 'row_index: 64']`). These pairs suggest two source rows were merged into one ACMRecord.
- Example: `acm_record:wl2t6tlhwzj51unx1gse` (flange mastic grey, roof) has `data_issues: ['row_index: 54', 'row_index: 64']` — rows 54 and 64 were deduplicated into one record.
- Row merging is correct (same item from two table sections), but in some cases merged records may carry inconsistent field values from the two source rows.

**SF impact:** MEDIUM — Row merges are functionally correct, but operators reviewing the grid cannot trace which PDF row drove a specific field value.

---

### DA-13 — LOW: BOM character on first CSV column header

**Evidence:**
- Building CSV first header: `﻿External_ID__c` (UTF-8 BOM prefix `\ufeff`).
- Item CSV first header: `﻿Building__r.External_ID__c`.
- SF Data Loader (Java-based) handles BOM correctly but third-party tools may not.

**SF impact:** LOW — cosmetic. Does not affect Data Loader. May confuse scripts parsing the CSV.

---

### DA-14 — LOW: `Estimated_Year_Build_New__c` = "1985" and `Number_of_Levels__c` = "2" need picklist value verification

**Evidence:**
- `Estimated_Year_Build_New__c = "1985"` — restricted picklist of ~330 year values (~1700–2029).
- `Number_of_Levels__c = "2"` — restricted picklist of 99 values (1–99).
- Both export as plain numeric strings. If SF picklist stores values as `"1985"` / `"2"` these will pass; if stored differently (e.g., `"Year 1985"`) they will fail.
- Cannot verify exact picklist string format without running a SOQL query against the live org.

**SF impact:** LOW-MEDIUM — likely to pass (year/number picklists typically store as string digits), but must be verified before go-live.

---

### Summary Table

| ID | Severity | Field / Area | Description | Status |
|----|----------|-------------|-------------|--------|
| DA-01 | CRITICAL | Record count | 35 records (7 junk) vs 31 expected; junk rows will reach SF | **→ E38-S14** |
| DA-02 | CRITICAL | `_merge_site_config` | Writes `Department__c`/`Agency__c` (fabricated) instead of `Responsible_Agency_Department__c` | **FIXED** (E38-S6) |
| DA-03 | CRITICAL | `Labelled__c` | Always empty — bool→str bridge missing; 100% blank in export | **FIXED** (E38-S7) |
| DA-04 | HIGH | `Date_of_Audit_Report__c` | "8th April 2020" — not ISO 8601; Data Loader will reject | E38-S8 |
| DA-05 | HIGH | Condition/Friability/DP | 74% (26/35) records have these blank; risk scoring disabled | **→ E38-S15** |
| DA-06 | HIGH | `Frequency_of_Use__c` | "Occupied" not a valid SF picklist value; required field — blocks building insert | **→ E38-S16** |
| DA-07 | HIGH | `GPS_Coordinates_*` + `Country__c` | In BUILDING_SF_MAPPING but absent from SF snapshot; unknown SF field status | **→ E38-S17** |
| DA-08 | HIGH | `Responsible_Agency_Department__c` | Real SF field absent from BUILDING_SF_MAPPING entirely | **FIXED** (E38-S6) |
| DA-09 | MEDIUM | `Units_of_Measure__c` | Always empty — quantity string not split into numeric+unit | **→ E38-S18** |
| DA-10 | MEDIUM | Sample number duplicates | 5 sample_nos with 2-3 occurrences; 2 near-duplicate records identified | No action |
| DA-11 | MEDIUM | `Building_Category__c` | "Educational..." wrong for police station; dependent picklist mismatch | **→ E38-S19** |
| DA-12 | MEDIUM | `data_issues` row pairs | Row merge artifacts — field provenance untraceable | No action |
| DA-13 | LOW | BOM in CSV headers | UTF-8 BOM on first column; cosmetic | Bundled → E38-S13 |
| DA-14 | LOW | Year/Level picklists | Value format unverified against live SF restricted picklist strings | **→ E38-S20** |

**Story mapping to pre-existing E38 backlog:**
- DA-02 → E38-S6 (confirmed)
- DA-03 → E38-S7 (confirmed)
- DA-04 → E38-S8 (confirmed)
- DA-01, DA-05, DA-06, DA-07, DA-08, DA-09, DA-11 → **New stories required** (not covered by existing E38-S1..S13)

## Fix Status (Updated 2026-04-15 post-crash recovery)

| Finding | Status | Notes |
|---------|--------|-------|
| DA-02 / E38-S6 | **FIXED** (uncommitted) | `_merge_site_config()` → `Responsible_Agency_Department__c`. Phase 2b rewrite. |
| DA-03 / E38-S7 | **FIXED** (uncommitted) | `item_to_sf_row()` bool→str bridge. Phase 2b rewrite. |
| DA-08 | **FIXED** (uncommitted) | `Responsible_Agency_Department__c` added to `BUILDING_SF_MAPPING`. Phase 2b rewrite. |
| DA-04 / E38-S8 | Existing story | ISO 8601 date normalization — story drafted. |
| E38-S10 | Existing story | Re-add `Est_Building_Size_m2__c` + `Hygienist_Recommendations__c`. |
| E38-S11 | Existing story | Fix `schema_inference.py` fabricated names. |
| DA-01 | **NEW → E38-S14** | Junk row filter (7 invalid rows in 35). CRITICAL. |
| DA-05 | **NEW → E38-S15** | 74% null condition/friability investigation. HIGH. |
| DA-06 | **NEW → E38-S16** | Frequency_of_Use__c picklist mapping. HIGH. |
| DA-07 | **NEW → E38-S17** | GPS_Coordinates + Country__c snapshot verification. HIGH. |
| DA-09 | **NEW → E38-S18** | Units_of_Measure__c quantity/unit split. MEDIUM. |
| DA-11 | **NEW → E38-S19** | Building_Category__c dependent picklist validation. MEDIUM. |
| DA-14 | **NEW → E38-S20** | Year/Level picklist value format verification. LOW. |
| DA-10 | No story | Duplicate sample numbers — legitimate multi-item samples. Informational. |
| DA-12 | No story | Row merge artifacts — informational, no SF impact. |
| DA-13 | Bundled into E38-S13 | BOM in CSV headers — cosmetic, added to housekeeping scope. |

## New Bug Stories Discovered
| Story ID | Title | Severity | Source Finding | SP |
|----------|-------|----------|----------------|-----|
| E38-S14 | Junk row filter (priority banners + no-access notes) | CRITICAL | DA-01 | 3 |
| E38-S15 | Null condition/friability/DP investigation | HIGH | DA-05 | 2 |
| E38-S16 | Frequency_of_Use__c picklist mapping | HIGH | DA-06 | 2 |
| E38-S17 | GPS/Country__c snapshot verification | HIGH | DA-07 | 1 |
| E38-S18 | Units_of_Measure__c quantity/unit split | MEDIUM | DA-09 | 2 |
| E38-S19 | Building_Category__c dependent picklist validation | MEDIUM | DA-11 | 2 |
| E38-S20 | Picklist value format verification | LOW | DA-14 | 1 |

## Iteration Log
### Iteration 1
- **Findings count:**
- **Fixes applied:**
- **Regressions:**

### Iteration 2
- **Findings count:**
- **Fixes applied:**
- **Regressions:**

### Iteration 3
- **Findings count:**
- **Fixes applied:**
- **Regressions:**
