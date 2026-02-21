# SAMP Test Fixtures

Test data for ACM extraction end-to-end testing.

## Files

### Test Documents

| Filename | Source | Records | Purpose |
|----------|--------|---------|---------|
| `broadmeadows-police-station-samp.pdf` | Clutch Broadmeadows Police Station SAMP | 31 | Baseline test document with known ground truth |
| `1124-asbestos-register.pdf` | Asbestos Register 1124 | TBD | Format variation test |
| `3980-asbestos-register.pdf` | Asbestos Register 3980 | TBD | Format variation test |

### Expected Results

| Filename | Associated PDF | Description |
|----------|----------------|-------------|
| `broadmeadows-expected-results.json` | broadmeadows-police-station-samp.pdf | Ground truth data with 31 records, baseline accuracy 26% |

## Broadmeadows Police Station SAMP

**Test File**: `broadmeadows-police-station-samp.pdf`
**Expected Results**: `broadmeadows-expected-results.json`

### Ground Truth

- **Total Records**: 31
- **Breakdown**:
  - Negative: 20 records
  - Positive: 5 records
  - Assumed Positive: 6 records

### Baseline Performance (2026-02-10)

- **Accuracy**: 26% (8/31 records extracted)
- **Coverage by Result Type**:
  - Negative: 0% (0/20)
  - Positive: 80% (4/5)
  - Assumed Positive: 50% (3/6)

### Known Issues

1. **Structural API Bugs**:
   - `sample_no` field missing from API schema
   - `quantity` field missing from API schema
   - `acm_labelled` field missing from API schema

2. **Extraction Issues**:
   - Negative results completely skipped (0% extraction)
   - Result type conflation (Assumed Positive → Detected)
   - `floor_level` not properly extracted
   - `area_type` vocabulary mismatch (Internal → Interior)

3. **Compliance Fields**:
   - `identifying_company` not extracted (0%)
   - `acm_product_group` not extracted (0%)
   - `acm_product_type` not extracted (0%)

### Target Accuracy

- **Goal**: 80%+ (25/31 records)
- **All result types should be extracted**, including negatives

## Usage in Tests

```typescript
import { test, expect } from '../../support/fixtures';
import expectedResults from '../fixtures/samps/broadmeadows-expected-results.json';

test('ACM extraction accuracy', async ({ page, apiClient }) => {
  // Upload SAMP
  await uploadSAMP(page, 'tests/e2e/fixtures/samps/broadmeadows-police-station-samp.pdf');

  // Wait for extraction
  await waitForExtraction(page);

  // Validate results
  const extracted = await apiClient.get('/acm-records');
  const accuracy = validateAccuracy(extracted, expectedResults.ground_truth_records);

  expect(accuracy).toBeGreaterThan(0.80); // 80%+ target
});
```

## Adding New Test Documents

1. Copy PDF to `tests/e2e/fixtures/samps/`
2. Create corresponding `*-expected-results.json` file
3. Update this README with document details
4. Add test case in test suite

## Format Variations

The additional SAMP documents (1124, 3980) test different format variations:
- Different consultant firms
- Different table layouts
- Different section structures
- Different terminology

Expected results for these documents should be created after initial implementation.
