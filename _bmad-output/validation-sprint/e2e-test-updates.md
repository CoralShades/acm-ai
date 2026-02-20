# E2E Test Updates - Sprint 1 Validation

**Date:** 2026-02-16
**Agent:** e2e-validator
**Task:** Update E2E test expectations to reflect Sprint 1 improvements

## Summary

Updated E2E test suite expectations in `tests/e2e/acm-extraction.spec.ts` to reflect the significant accuracy improvements delivered in Sprint 1. The extraction baseline improved from 26% (8/31 records) to 87% (27/31 records), and the target has been raised to 95% (30/31 records).

## Changes Made

### 1. Updated Accuracy Thresholds (80% → 95%)

**File:** `tests/e2e/acm-extraction.spec.ts`

#### Line 8-9: Updated documentation header
```diff
- * Target: 80%+ extraction accuracy (25/31 records from Broadmeadows SAMP)
- * Baseline: 26% accuracy (8/31 records)
+ * Target: 95%+ extraction accuracy (30/31 records from Broadmeadows SAMP)
+ * Baseline: 87% accuracy (27/31 records as of Sprint 1)
```

#### Line 51-53: Updated constants
```diff
  const EXPECTED_RECORD_COUNT = expectedResults.metadata.total_records; // 31
- const TARGET_ACCURACY = 0.8; // 80%
- const TARGET_EXTRACTED_COUNT = Math.ceil(EXPECTED_RECORD_COUNT * TARGET_ACCURACY); // 25
+ const TARGET_ACCURACY = 0.95; // 95%
+ const TARGET_EXTRACTED_COUNT = Math.ceil(EXPECTED_RECORD_COUNT * TARGET_ACCURACY); // 30
```

#### Line 66: Updated test name
```diff
- test('extracts all records from Broadmeadows SAMP with 80%+ accuracy', async ({
+ test('extracts all records from Broadmeadows SAMP with 95%+ accuracy', async ({
```

#### Lines 100-115: Updated assertions and comments
```diff
- // Then: Verify extraction accuracy meets 80%+ threshold
+ // Then: Verify extraction accuracy meets 95%+ threshold
  const actualCount = await getACMRecordCount(page);
  const accuracy = actualCount / EXPECTED_RECORD_COUNT;

  // Capture final grid state
  await captureEvidence(page, `acm-grid-final-count-${actualCount}`);

+ // Log accuracy for debugging
+ console.log(
+   `Extraction: ${actualCount}/${EXPECTED_RECORD_COUNT} records (${(accuracy * 100).toFixed(1)}% accuracy)`
+ );
+
- // Assert accuracy threshold
- expect(actualCount).toBeGreaterThanOrEqual(
-   TARGET_EXTRACTED_COUNT,
-   `Expected at least ${TARGET_EXTRACTED_COUNT} records (80% of ${EXPECTED_RECORD_COUNT}), got ${actualCount} (${(accuracy * 100).toFixed(1)}%)`
- );
- expect(accuracy).toBeGreaterThanOrEqual(
-   TARGET_ACCURACY,
-   `Extraction accuracy ${(accuracy * 100).toFixed(1)}% is below 80% threshold`
- );
+ // Assert accuracy threshold (95% = 30/31 records)
+ expect(actualCount).toBeGreaterThanOrEqual(TARGET_EXTRACTED_COUNT);
+ expect(accuracy).toBeGreaterThanOrEqual(TARGET_ACCURACY);
```

**Rationale:**
- Removed custom error messages from `expect()` calls - Playwright's `toBeGreaterThanOrEqual()` only accepts 1 argument
- Added console.log for debugging output instead
- Simplified assertions for better type safety

### 2. Added BAR Compliance Fields Validation

**New Test Added:** `test('extracts BAR compliance fields from SAMP documents')`

**Location:** After the "extracts all compliance fields completely" test (around line 270)

**Fields Validated:**
- `identifying_company`
- `date_inspected`
- `inspection_type`
- `bar_report_no`
- `date_of_bar_report`
- `asbestos_assessor`
- `result_classification`

**Test Structure:**
1. Upload Broadmeadows SAMP
2. Wait for extraction
3. Navigate to ACM grid
4. Verify BAR field columns exist in grid
5. Get first record details
6. Assert all 7 BAR fields are present in record structure
7. Verify at least one BAR field has a non-null value
8. Capture evidence screenshots

**Implementation Notes:**
- Test uses `getACMRecordDetails()` helper to fetch record data
- Validates field presence using `toHaveProperty()` assertions
- Checks for any non-null BAR values (not all SAMPs populate all BAR fields)
- Captures screenshots: `bar-fields-grid` and `bar-fields-record-detail`

### 3. Added Alexander District Hospital Baseline Test

**New Test Added:** `test.skip('establishes extraction baseline for Alexander District Hospital SAMP')`

**Location:** End of test suite, before closing brace (around line 351)

**Status:** Currently skipped - requires fixture files to be added

**Purpose:** Placeholder for establishing a second extraction baseline on a different SAMP document

**Fixture Files Needed:**
1. `tests/e2e/fixtures/samps/alexander-district-hospital-samp.pdf`
2. `tests/e2e/fixtures/samps/alexander-expected-results.json`

**Test Flow:**
1. Check if fixture files exist (auto-skip if not found)
2. Create notebook
3. Upload Alexander District Hospital SAMP
4. Wait for extraction (180s timeout)
5. Navigate to ACM grid
6. Count records extracted
7. If expected results exist, calculate accuracy
8. Log baseline metrics
9. Capture evidence screenshots

**Enabling the Test:**
1. Add `alexander-district-hospital-samp.pdf` to fixtures
2. Create ground truth data in `alexander-expected-results.json`
3. Remove `test.skip()` to enable

**Screenshots Captured:**
- `alexander-upload` workflow
- `alexander-grid-loaded`
- `alexander-baseline-{count}-of-{expected}` or `alexander-baseline-{count}-records`

## Test Files Reviewed

### Primary Test File
- ✅ `tests/e2e/acm-extraction.spec.ts` - Updated with new expectations

### Helper Files Reviewed (No Changes Needed)
- ✅ `tests/e2e/helpers/acm-helpers.ts` - ACM test utilities (unchanged)
- ✅ `tests/e2e/helpers/chat-helpers.ts` - Chat test utilities (unchanged)
- ✅ `tests/e2e/helpers/screenshot-helpers.ts` - Screenshot utilities (unchanged)
- ✅ `tests/e2e/helpers/index.ts` - Helper exports (unchanged)

### Other Test Files Reviewed (No Changes Needed)
- ✅ `tests/e2e/smoke.spec.ts` - Basic smoke tests (unchanged)
- ✅ `tests/e2e/user-journeys.spec.ts` - End-to-end user workflows (unchanged)

### Test Fixtures Reviewed
- ✅ `tests/e2e/fixtures/samps/broadmeadows-police-station-samp.pdf` - Primary test SAMP
- ✅ `tests/e2e/fixtures/samps/broadmeadows-expected-results.json` - Ground truth data
- ✅ `tests/e2e/fixtures/samps/1124-asbestos-register.pdf` - Merged cells test SAMP
- ✅ `tests/e2e/fixtures/samps/3980-asbestos-register.pdf` - Multi-page table test SAMP
- ✅ `tests/e2e/fixtures/samps/README.md` - Fixture documentation

## Expected Test Outcomes

### Before Sprint 1
- **Broadmeadows extraction:** 8/31 records (26%)
- **BAR fields:** Not extracted (0% population)
- **Negative records:** Skipped entirely

### After Sprint 1 (Current)
- **Broadmeadows extraction:** 27/31 records (87%)
- **BAR fields:** 7 fields added to schema and extracted
- **Negative records:** Extracted (all result types included)

### Target (95% Goal)
- **Broadmeadows extraction:** 30/31 records (97%)
- **BAR fields:** Populated from SAMP documents
- **Alexander District Hospital:** Baseline established

## Validation Checklist

- ✅ Updated accuracy threshold from 80% to 95%
- ✅ Updated expected record count from 25 to 30 (for Broadmeadows)
- ✅ Added BAR compliance field validation test
- ✅ Validated 7 BAR fields: identifying_company, date_inspected, inspection_type, bar_report_no, date_of_bar_report, asbestos_assessor, result_classification
- ✅ Added checks for BAR field presence in grid
- ✅ Added checks for BAR field non-null values in records
- ✅ Added placeholder test for Alexander District Hospital
- ✅ Documented baseline establishment process
- ✅ Added workflow screenshots for new tests
- ✅ Fixed TypeScript errors (removed unsupported error message parameters)
- ✅ All test files reviewed and documented

## Next Steps

1. **Run updated test suite** to verify 95% accuracy threshold is met
2. **Add Alexander District Hospital fixtures** to enable baseline test
3. **Review test failures** if accuracy falls below 95%
4. **Update GitHub Actions CI** to run E2E tests on every PR
5. **Document any test failures** for gap analysis

## Notes

- The accuracy improvement from 26% to 87% represents a **3.3x increase** in extraction completeness
- The 95% target (30/31 records) leaves room for 1 edge case failure
- BAR field validation ensures compliance data is extracted and accessible
- Alexander District Hospital test provides a second validation dataset
- All changes maintain backward compatibility with existing test infrastructure

## Recommendations

1. **Monitor test stability:** Run the updated test suite 5+ times to ensure consistent 95% accuracy
2. **Identify remaining gaps:** Analyze which record(s) fail extraction in the 5% gap
3. **Expand BAR validation:** Add field-specific assertions (e.g., date format validation, assessor name presence)
4. **Add negative result validation:** Create dedicated test for negative vs. positive classification accuracy
5. **Performance testing:** Ensure extraction completes within 180s timeout consistently

---

**Status:** ✅ Complete
**Deliverable:** `tests/e2e/acm-extraction.spec.ts` updated with 95% accuracy target and BAR field validation
