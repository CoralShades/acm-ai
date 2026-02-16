# Extraction Accuracy Analysis

**Test**: Broadmeadows Police Station SAMP
**Date**: Baseline 2026-02-10 (pending fresh test run)
**Source**: Previous E2E test findings
**Model**: Claude 3.5 Haiku (anthropic/claude-3-5-haiku-20241022)
**Strategy**: full_llm (single chunk, 29,411 chars)

---

## Overall Metrics

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| **Records Extracted** | 8/31 | 25/31 | ❌ **FAIL** |
| **Extraction Rate** | 25.8% | 80%+ | ❌ **FAIL** |
| **Precision** | 87.5% (7/8 correct) | 80%+ | ✅ PASS |
| **False Positives** | 0% | <5% | ✅ PASS |
| **Negative Detection** | 0/20 | 20/20 | ❌ **FAIL** |

### Breakdown by Result Type

| Result Type | CSV Count | Extracted | Coverage | Target |
|-------------|-----------|-----------|----------|--------|
| Negative | 20 | 0 | **0%** | 100% |
| Positive | 5 | 4 | 80% | 100% |
| Assumed Positive | 6 | 3 | 50% | 100% |
| **Total** | **31** | **7** | **23%** | **80%+** |

**Note**: 1 extracted record unmatched ("Ceiling Space" - possible hallucination)

---

## Field-Level Accuracy

Analysis of 7 correctly matched records:

### Core Identification Fields (89.8% average)

| Field | Correct | Incorrect | Missing | Accuracy |
|-------|---------|-----------|---------|----------|
| room_name | 7 | 0 | 0 | **100%** ✅ |
| area_type (Int/Ext) | 7 | 0 | 0 | **100%** ✅ |
| friable | 7 | 0 | 0 | **100%** ✅ |
| material_condition | 7 | 0 | 0 | **100%** ✅ |
| risk_status | 7 | 0 | 0 | **100%** ✅ |
| product | 5 | 2 | 0 | **71%** ⚠️ |
| material_description | 4 | 3 | 0 | **57%** ⚠️ |

**Product Partial Matches**:
- "Ductwork" vs "AHU Ductwork" (semantically close)

**Material Description Issues**:
- "Flange Mastic" vs "Flange joints" (terminology variation)
- "Fuses" vs "Fuse cartridge" (partial match)

### Compliance/Admin Fields (0% average) ❌

| Field | Correct | Missing | Accuracy | Impact |
|-------|---------|---------|----------|--------|
| result | 0 | 7 | **0%** | Shows "Detected" instead of "Positive"/"Assumed Positive" |
| floor_level | 0 | 7 | **0%** | Missing "Ground"/"Level 1" values |
| quantity | 0 | 7 | **0%** | Missing counts (e.g., 60, 3, 12) |
| sample_no | 0 | 7 | **0%** | Missing sample IDs (e.g., "S1234", "Not Sampled") |
| acm_labelled | 0 | 7 | **0%** | Missing YES/NO values |
| school_name | 0 | 7 | **0%** | Shows filename instead of facility name |
| building_name | 0 | 7 | **0%** | Not populated |
| acm_product_group | 0 | 7 | **0%** | Missing classification (e.g., "Insulation Products") |
| acm_product_type | 0 | 7 | **0%** | Missing type (e.g., "Pipe/Duct Insulation") |

---

## Negative Detection Analysis

### Expected Negative Records: 20

**Examples of missed negatives**:
- Main Foyer - Floor covering (Not Sampled)
- Front Desk Area - Floor covering (Not Sampled)
- Soft Interview Room No.2 - Skirting (Not Sampled)
- *(17 more negative records not shown)*

### Detection Rate: 0/20 (0%)

**Root Cause**: Extraction algorithm focuses only on ACM-positive materials. Negative samples (tested but no asbestos found) are completely skipped.

### Impact

- **Incomplete compliance register**: Victorian BAR format requires ALL tested materials, including negatives
- **Regulatory risk**: Auditors expect to see "clear" results to prove due diligence
- **Missing inventory**: 65% of the register (20/31 records) absent

---

## Missing Positive/Assumed Positive Records (4/11)

| CSV # | Room | Item | Material | Result | Likely Cause |
|-------|------|------|----------|--------|--------------|
| #9 | Switch Room | Auto Battery Charger | Fuse cartridge | Assumed Positive | Merged with CSV #8 (same room) |
| #20 | Fan Room (External) | AHU Ductwork | Flange joints | Positive | Merged with internal Fan Room records |
| #30 | Lift Foyer | Lift | Internal lining | Assumed Positive | Low-detail entry ("No access") - insufficient context |
| #31 | Main Foyer | Room Adj. Disabled Toilet | Unknown | Assumed Positive | Low-detail entry ("No access") - insufficient context |

**Extraction recall for positives**: 63.6% (7/11)

---

## Gap Analysis by Priority

### 🔴 Critical Gaps (Blocking 80% target)

1. **Zero negative detection** (0/20 records)
   - **Fix**: Update extraction prompt to include ALL tested materials
   - **Impact**: Missing 65% of total register

2. **Compliance fields not extracted** (0% accuracy)
   - **Missing fields**: sample_no, quantity, acm_labelled, floor_level
   - **Fix**: Add fields to extraction schema and prompt
   - **Impact**: Records unusable for BAR compliance reporting

3. **Result type incorrect mapping**
   - **Issue**: All records show "Detected" instead of "Positive"/"Assumed Positive"/"Negative"
   - **Fix**: Map to 3-value enum correctly
   - **Impact**: Cannot distinguish between confirmed vs assumed ACM

### 🟡 Medium Gaps

4. **Missing positive records** (4/11 not extracted)
   - **Issue**: Low-detail entries and room-based deduplication
   - **Fix**: Improve chunking strategy, preserve all distinct entries
   - **Impact**: 36% recall for positives

5. **Site metadata from filename**
   - **Issue**: school_name shows "Clutch_Broadmeadows.pdf"
   - **Fix**: Extract facility name from document header
   - **Impact**: Poor data quality for reporting

6. **Product classification not run**
   - **Missing**: acm_product_group, acm_product_type
   - **Fix**: Trigger classification post-extraction
   - **Impact**: Missing Victorian BAR required fields

### 🟢 Low Priority

7. **Material description terminology** (57% accuracy)
   - **Issue**: "Flange Mastic" vs "Flange joints"
   - **Fix**: Improve prompt examples with Victorian BAR terminology
   - **Impact**: Minor - semantically equivalent

---

## Root Cause Hypotheses

### Algorithm Issues
- ✅ **Confirmed**: Extraction skips negative results by design
- ✅ **Confirmed**: Single chunk processing (29K chars) may hit model output limits
- ⚠️ **Likely**: Deduplication merges similar entries from same room

### Schema Issues
- ✅ **Confirmed**: Compliance fields (sample_no, quantity, labelled, floor_level) not in schema
- ✅ **Confirmed**: Result field binary ("Detected") instead of tri-state enum
- ✅ **Confirmed**: Site metadata populated from filename, not document parsing

### Prompt Issues
- ⚠️ **Likely**: Extraction prompt doesn't request negative samples
- ⚠️ **Likely**: Prompt missing examples of Victorian BAR terminology
- ⚠️ **Possible**: Low-detail entries ("No access") filtered out as insufficient data

---

## Summary

**PASS/FAIL**: ❌ **FAIL** - 26% extraction vs 80% target

**Strengths**:
- ✅ High precision (87.5%) - low false positive rate
- ✅ Core fields accurate (89.8%) for extracted records
- ✅ Correct risk assessment and friability classification

**Critical Failures**:
- ❌ Only 26% record coverage (8/31 extracted)
- ❌ Zero negative detection (0/20 missed)
- ❌ Zero compliance field accuracy (sample_no, quantity, labelled, floor_level all missing)

**Recommended Fixes** (Priority order):
1. Update extraction to include negative results
2. Add compliance fields to schema (sample_no, quantity, acm_labelled, floor_level)
3. Fix result type enum mapping
4. Extract site metadata from document content
5. Improve chunking to capture all positive records
6. Trigger ACM product classification
