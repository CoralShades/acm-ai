# E2E Test Report - 2026-02-11

## Executive Summary

| Item | Value |
|------|-------|
| **Test Date** | 2026-02-11 |
| **Duration** | ~12 minutes (extraction pipeline) + monitoring |
| **Overall Score** | **5.0/10 (FAIL)** |
| **Previous Score** | 5.5/10 (2026-02-10) |
| **Delta** | -0.5 |
| **Pass Threshold** | >= 7.0/10 |
| **PDF Under Test** | Clutch_Broadmeadows.pdf (Broadmeadows Police Station SAMP, Div 5) |
| **Ground Truth** | Clutch_Broadmeadows.csv (31 records, 42 BAR columns) |
| **Extraction Model** | Claude 3.5 Haiku (claude-3-5-haiku-20241022) via direct Anthropic API |
| **Test Method** | Automated 5-agent team (health-checker, browser-pilot, log-monitor, data-validator, reporter) |

The system extracted 8 records from a 31-record SAMP document (25.8% coverage). Only positive and assumed positive results were captured; all 20 negative results were skipped. One extracted record was identified as a false positive (hallucinated). Compliance fields remain completely absent from the API response model. The model had to be manually fixed mid-test (OpenRouter -> direct Anthropic) due to the same configuration issue found in the previous test.

---

## Scorecard

| Phase | Weight | Score | Previous | Delta |
|-------|--------|-------|----------|-------|
| Service Health | 10% | 10.0/10 | 10/10 | 0 |
| PDF Upload | 15% | 8.0/10 | 9/10 | -1.0 |
| Extraction | 30% | 2.6/10 | 4/10 | -1.4 |
| Data Accuracy | 30% | 4.0/10 | 3/10 | +1.0 |
| UI/UX | 15% | 5.5/10 | 7/10 | -1.5 |
| **Overall** | **100%** | **5.0/10** | **5.5/10** | **-0.5** |

See `scorecard.md` for detailed calculation methodology.

---

## Key Context: Model Fix Required Mid-Test

The extraction pipeline failed twice before succeeding:
1. **Attempt 1**: Race condition - `acm_extract` ran before `process_source` finished (0.025s failure)
2. **Attempt 2**: Model `anthropic/claude-3.5-haiku-20241022` returned 404 on OpenRouter (10.1s failure)
3. **Attempt 3**: Team lead fixed model to use direct Anthropic API - **SUCCESS** (75.56s, 8 records)

This is the same model configuration issue discovered in the previous test (2026-02-10). The fix has not been permanently resolved in the codebase.

---

## Key Improvements vs Previous Test (2026-02-10)

1. **Critical routing bugs FIXED**: Previous test had BUG-001 (/acm route redirect), BUG-002 (sidebar link broken), BUG-003 (source selector empty), BUG-004 (API parse failure). All four are now resolved.
2. **Full ACM grid testing possible**: For the first time, the populated AG Grid could be fully tested with data, revealing real data-quality bugs.
3. **Assessment accuracy strong**: 87.5% on assessment fields (friable, condition, risk_status all 100%).
4. **Export functionality confirmed**: CSV export works correctly with toast notification.
5. **More rigorous validation methodology**: Field-level comparison with partial match scoring provides more accurate picture.

---

## Remaining Issues (Carried Forward)

1. **Extraction coverage: 8/31 records (25.8%)** - Far below 90% threshold. 20 negative results completely skipped.
2. **Compliance fields: 0%** - sample_no, quantity, acm_labelled, identifying_company, disturbance_potential, hygienist_recommendations all absent from API response model. This is a structural bug.
3. **Result field mapping**: "Detected" conflates "Positive" and "Assumed Positive" - legally significant distinction for compliance reporting.
4. **Model configuration complexity**: Still requires manual SurrealDB intervention to set correct model. No fix deployed since last test.
5. **Classification fields unpopulated**: acm_product_group and acm_product_type are null for all records.
6. **SiteConfig schema error**: `source_id` field type mismatch (`record<source>` vs string) - non-blocking but recurring.

---

## New Issues Found

### Race Condition Bug (CRITICAL)
Both `process_source` and `acm_extract` commands are dispatched simultaneously. `acm_extract` fails in 25ms because PDF text has not been parsed yet. The `acm_extract` command must wait for `process_source` to complete.

### SiteConfig Schema Error (ERROR)
During STORE stage, `auto_populate_site_config` fails with:
```
Found 'source:lap4wnbxllavswdgghro' for field `source_id`, with record `site_config:ej1ljokhlbnxozug68zi`, but expected a record<source>
```
Non-blocking (records still save), but occurs every extraction run.

### Product/Location Column Confusion (HIGH)
The extraction systematically maps CSV "Location in Room" to the `product` field instead of CSV "Specific Item/ACM Name". E.g., "Switchboard" (location) extracted as product instead of "Fuse cartridge" (actual item).

### False Positive Record (MEDIUM)
"Ceiling Space / Ductwork" has no ground truth match. The extraction may be hallucinating records from non-tabular content in the PDF.

---

## Bug List

### Severity: Critical
| # | Bug | Component | Status |
|---|-----|-----------|--------|
| 1 | Race condition: acm_extract runs before process_source completes | Backend / Command Dispatch | NEW |
| 2 | Model config: OpenRouter model ID returns 404, requires manual DB fix | Backend / Model Config | RECURRING |

### Severity: High
| # | Bug | Component | Status |
|---|-----|-----------|--------|
| 3 | Product/Location column confusion in extraction | Backend / Extraction Prompt | NEW |
| 4 | Compliance fields missing from ACMRecordResponse API model | Backend / API Schema | RECURRING |
| 5 | Negative results (20/31) completely skipped by extraction | Backend / Extraction Logic | RECURRING |

### Severity: Medium
| # | Bug | Component | Status |
|---|-----|-----------|--------|
| 6 | Building column empty in grid (building_name null) | Extraction / Grid | RECURRING |
| 7 | Page column empty in grid (page_number null) | Extraction / Grid | RECURRING |
| 8 | Friable dropdown shows blank in edit dialog (value mismatch: "Non-friable" vs "Non Friable") | Frontend / Edit Dialog | NEW |
| 9 | Result conflates Positive and Assumed Positive as "Detected" | Backend / Schema | RECURRING |
| 10 | location field never populated (always null) | Backend / Extraction | NEW |
| 11 | SiteConfig auto-fill fails with record type mismatch | Backend / DB Schema | RECURRING |
| 12 | False positive: "Ceiling Space / Ductwork" has no ground truth match | Backend / Extraction | NEW |

### Severity: Low
| # | Bug | Component | Status |
|---|-----|-----------|--------|
| 13 | Search bar doesn't filter grid results | Frontend / AG Grid | RECURRING |
| 14 | Document Library doesn't refresh after upload | Frontend / Documents Page | NEW |
| 15 | Console error on wizard step 2 ("Query data cannot be undefined") | Frontend / Upload Wizard | RECURRING |
| 16 | area_type vocabulary mismatch: "Interior" vs standard "Internal" | Backend / Extraction | NEW |
| 17 | Classification fields (acm_product_group, acm_product_type) never populated | Backend / Extraction | RECURRING |

### Severity: Informational
| # | Bug | Component | Status |
|---|-----|-----------|--------|
| 18 | File renamed with "(2)" suffix on re-upload | Frontend / Upload | INFO |
| 19 | AG Grid deprecation warnings (v32.2 API changes) | Frontend / AG Grid | INFO |

---

## Phase-by-Phase Results

### Phase 1: Service Health (10.0/10)
- **Monitoring period**: 13:53:18 to 14:01:27 (~8 minutes, 13 checks)
- **SurrealDB**: 13/13 checks passed, 100% uptime
- **API (5055)**: 13/13 checks passed, 100% uptime
- **Frontend (8502)**: 13/13 checks passed, 100% uptime
- **Worker**: 13/13 checks passed, 2 processes consistently running
- **Conclusion**: Infrastructure fully stable throughout test

### Phase 2: PDF Upload (8.0/10)
- **Upload flow**: 4-step wizard completed successfully (file upload, site config, organization, processing)
- **ACM extraction**: Pre-checked by default
- **Processing**: Source processed in ~38 seconds, 23 embedded chunks
- **Issue**: Extraction required 3 attempts due to race condition (attempt 1) and model misconfiguration (attempt 2)
- **Successful extraction**: 75.56s, 8 records, 100% high confidence
- **Screenshots**: 14 captured documenting full flow

### Phase 3: Extraction Pipeline (2.6/10)
- **Records**: 9 raw -> 1 duplicate merged -> 8 saved
- **Coverage**: 8/31 = 25.8% (7 true matches + 1 false positive)
- **Pipeline stages**: STRUCTURE (49.9s) -> ORCHESTRATOR (21.0s) -> VALIDATE (~0s) -> STORE (0.3s) -> EMBED (0.9s)
- **LLM calls**: 5 total (4 structure + 1 orchestrator), all via direct Anthropic
- **Document type**: DIVISION_5, register pages 3-4 of 12 total
- **Key gap**: 20 negative results (65% of records) completely absent

### Phase 4: Data Accuracy (4.0/10)
- **Coverage**: 22.6% (7/31 true matches, excluding 1 false positive)
- **Core ID accuracy**: 53.6% (15/28 fields)
  - room_name: 93%, product: 57%, area_type: 64%, location: 0%
- **Assessment accuracy**: 87.5% (24.5/28 fields)
  - friable: 100%, material_condition: 100%, risk_status: 100%, result: 50%
- **Compliance accuracy**: 0% (structural bug - fields not in API)
- **Classification accuracy**: 0% (fields exist but never populated)

### Phase 5: UI/UX Quality (5.5/10)
- **Bugs found**: 8 (3 medium, 3 low, 2 informational)
- **Features passing**: 10 (stats cards, grid, risk coding, edit dialog, export, source selector, columns, upload wizard, sidebar nav, breadcrumbs)
- **Key improvement**: Previous critical routing/data bugs (BUG-001 through BUG-004) all FIXED
- **New findings**: Empty columns, friable dropdown mismatch, search filter not connected

---

## Recommendations for Next Sprint

### P0 - Critical
1. **Fix race condition**: Ensure `acm_extract` waits for `process_source` to complete before running
2. **Fix extraction prompt to include negative results**: This alone could push coverage from 22.6% to potentially >90%
3. **Persist model fix**: Update default model configuration in seed data or migration to use direct Anthropic API

### P1 - High
4. **Fix product/location column mapping**: Correct schema so "Specific Item/ACM Name" maps to product and "Location in Room" maps to location
5. **Add compliance fields to ACMRecordResponse**: Expose sample_no, quantity, acm_labelled, identifying_company
6. **Distinguish Positive vs Assumed Positive**: Map result values to match 3-value CSV convention

### P2 - Medium
7. **Fix friable dropdown value mismatch**: Normalize "Non-friable" vs "Non Friable" in either data or dropdown options
8. **Populate building_name and page_number**: Extract from document structure stage
9. **Fix search filter**: Connect AG Grid quickFilter to search input
10. **Fix SiteConfig schema**: Correct source_id field type

### P3 - Low
11. **Populate classification fields**: Run acm_product_group/acm_product_type during extraction
12. **Fix area_type vocabulary**: Use "Internal"/"External" to match industry standard
13. **Add hallucination guard**: Validate extracted records correspond to actual table rows
14. **Document Library refresh after upload**: Auto-refresh or invalidate query cache

---

## Evidence Links

- Screenshots: `_bmad-output/e2e-test-2026-02-11/browser-pilot/` (14 screenshots)
- Record-by-record comparison: `_bmad-output/e2e-test-2026-02-11/data-validator/comparison.md`
- Pipeline analysis: `_bmad-output/e2e-test-2026-02-11/log-monitor/findings.md`
- Service health log: `_bmad-output/e2e-test-2026-02-11/health-checker/progress.md`
- Previous test baseline: `_bmad-output/implementation-artifacts/findings.md`

---

## Test Methodology

This test was conducted by a 5-agent automated team:
- **health-checker**: Continuous service monitoring (30s intervals)
- **browser-pilot**: Playwright browser automation for upload and UI testing
- **log-monitor**: Real-time worker log analysis during extraction
- **data-validator**: Ground truth CSV comparison with field-level accuracy scoring
- **reporter**: (this report) Score calculation, delta analysis, GitHub issue update
