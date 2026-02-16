# E2E Data Validation Findings

## Test Date: 2026-02-11
## Source: Broadmeadows Police Station SAMP (source:lap4wnbxllavswdgghro)

---

## Executive Summary

**Overall Score: 23.9% (FAIL)**

The system extracted 8 records from the Broadmeadows Police Station SAMP document containing 31 ACM records. After matching, 7 of 8 extracted records correspond to ground truth entries (1 appears to be a false positive). No negative results were extracted, and 2 assumed positive records were also missed. Coverage is 22.6%, virtually unchanged from the previous test (Issue #14 baseline: 25.8%).

---

## Scores

| Category | Score | Target | Status |
|----------|-------|--------|--------|
| Coverage | 22.6% (7/31) | >90% | FAIL |
| Core ID Accuracy | 53.6% (15/28) | >80% | FAIL |
| Assessment Accuracy | 87.5% (24.5/28) | >70% | PASS |
| Compliance Accuracy | 0% (0/28) | >50% | FAIL |
| Classification | 0% (0/14) | informational | FAIL |

**Weighted Overall:** (22.6% x 0.40) + (53.6% x 0.25) + (87.5% x 0.20) + (0% x 0.15) = **39.9%**

---

## Coverage Breakdown

### By Result Type
| Result Type | CSV Count | Extracted | Coverage | Change from Previous |
|-------------|-----------|-----------|----------|---------------------|
| Negative | 20 | 0 | 0% | No change (was 0%) |
| Positive | 5 | 4 | 80% | -20% (was 5/5 = 100%) |
| Assumed Positive | 6 | 3 | 50% | -17% (was 3/3+1 shifted) |
| **Total** | **31** | **7** | **22.6%** | -3.2% (was 8/31 = 25.8%) |

### Missing Records Detail
- **20 Negative records:** Completely skipped. The extraction prompt/logic filters out negative results.
- **1 Positive record (External Fan Room AHU):** May have been merged with internal Fan Room AHU match.
- **2 Assumed Positive records (Lift Foyer internal lining, Main Foyer unknown):** Skipped despite being assumed positive. These had "No access" notes and "Unknown" condition, which may have caused them to be filtered.
- **1 Assumed Positive record (Switch Room Battery Charger):** The second Switch Room item was not extracted separately; only one Switch Room record extracted.

### False Positive
- **Ceiling Space / Ductwork:** No corresponding CSV record. No room called "Ceiling Space" exists in ground truth. This appears to be a hallucinated or misinterpreted record.

---

## Accuracy Analysis

### Core ID Fields (53.6%)
| Field | Accuracy | Issue |
|-------|----------|-------|
| room_name | 93% (6.5/7) | Generally good; one room name partially merged with location context |
| product | 57% (4/7) | Systematic issue: CSV "Location in Room" is being extracted as "product" instead of CSV "Specific Item/ACM Name". E.g., "Switchboard" (location) extracted as product instead of "Fuse cartridge" (actual item) |
| area_type | 64% (4.5/7) | Vocabulary mismatch: system uses "Interior" instead of CSV's "Internal" |
| location | 0% (0/7) | All null - location field never populated |

**Key Issue:** The extraction confuses the CSV columns "Location in Room" and "Specific Item/ACM Name". The "Location in Room" value is being placed in the `product` field, while the actual product (CSV "Specific Item/ACM Name") is either lost or placed in `material_description`.

### Assessment Fields (87.5%)
| Field | Accuracy | Issue |
|-------|----------|-------|
| friable | 100% (7/7) | Perfect |
| result | 50% (3.5/7) | "Detected" conflates Positive and Assumed Positive - no distinction |
| material_condition | 100% (7/7) | Perfect |
| risk_status | 100% (7/7) | Perfect |

**Key Issue:** Result values use "Detected"/"Not Detected" binary, but CSV has 3 values: "Positive", "Assumed Positive", "Negative". The distinction between Positive and Assumed Positive is compliance-critical (determines whether lab testing was performed).

### Compliance Fields (0%)
All compliance fields are absent from both the API response model and CSV export:
- `sample_no` - NATA endorsed sample number
- `quantity` - Material quantity
- `acm_labelled` - Whether ACM is labelled
- `identifying_company` - Hygiene/consulting company
- `disturbance_potential` - Disturbance risk assessment
- `hygienist_recommendations` - Professional recommendations

**This is a structural bug** - the domain model may have these fields but they are not exposed through the API.

### Classification Fields (0%)
- `acm_product_group` and `acm_product_type` are null for all records
- These fields exist in the API response but are never populated during extraction

---

## Comparison with Previous Test (Issue #14, 2026-02-10)

| Metric | Previous | Current | Change |
|--------|----------|---------|--------|
| Records extracted | 8 | 8 | No change |
| Coverage | 25.8% (8/31) | 22.6% (7/31) | -3.2% (1 false positive identified) |
| Core ID accuracy | 89.8% | 53.6% | -36.2% (stricter field matching) |
| Compliance accuracy | 0% | 0% | No change |
| Negative results extracted | 0 | 0 | No change |
| False positives | 0 identified | 1 identified | +1 |

Note: The previous test may have used different matching criteria. The current analysis applies stricter field-level comparison including location and area_type vocabulary matching.

---

## Structural Issues Found

### 1. Negative Results Not Extracted (CRITICAL)
20 of 31 records (65%) are negative results and NONE are extracted. The extraction logic or prompt appears to filter out negative/non-detected items. For a compliance register, ALL records must be captured regardless of result.

### 2. Product/Location Column Confusion (HIGH)
The extraction systematically maps CSV "Location in Room" to the `product` field instead of CSV "Specific Item/ACM Name". This is a prompt engineering or schema mapping issue.

### 3. Compliance Fields Missing from API (HIGH)
The ACMRecordResponse model does not expose compliance-critical fields (sample_no, quantity, acm_labelled, etc.). Even if the domain model stores them, they cannot be validated or displayed.

### 4. Result Type Conflation (MEDIUM)
"Detected" conflates "Positive" (lab-confirmed) and "Assumed Positive" (not sampled). This distinction is legally significant for compliance reporting.

### 5. area_type Vocabulary Mismatch (LOW)
System uses "Interior"/"External" vs CSV standard "Internal"/"External". Minor but could cause filtering/reporting mismatches.

### 6. location Field Never Populated (MEDIUM)
The `location` field is null for all extracted records. The "Location in Room" data is instead placed in the product field.

### 7. Classification Fields Not Populated (LOW)
`acm_product_group` and `acm_product_type` are never populated during extraction despite existing in the schema.

### 8. False Positive Record (LOW)
"Ceiling Space / Ductwork" has no ground truth match. The extraction may be hallucinating records from non-tabular content.

---

## Recommendations (Priority Order)

1. **Fix extraction prompt to include negative results** - This alone would push coverage from 22.6% to potentially >90%
2. **Fix product/location column mapping** - Correct the schema mapping so "Specific Item/ACM Name" maps to product and "Location in Room" maps to location
3. **Add compliance fields to ACMRecordResponse** - Expose sample_no, quantity, acm_labelled, identifying_company, disturbance_potential
4. **Distinguish Positive vs Assumed Positive** - Map result values to match the 3-value CSV convention
5. **Populate classification fields** - Extract acm_product_group and acm_product_type during processing
6. **Fix area_type vocabulary** - Use "Internal"/"External" to match industry standard
7. **Validate against hallucination** - Add a check to ensure extracted records correspond to actual table rows
