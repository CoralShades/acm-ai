# Data Validator Task Plan

## Objective
Compare 8 extracted ACM records against 31 ground truth records from Broadmeadows Police Station SAMP.

## Data Sources
- **Ground Truth:** `/docs/samplePDF/Clutch_Broadmeadows.csv` (31 records, 42 columns)
- **Extracted JSON:** API endpoint `GET /api/acm/records?source_id=source:lap4wnbxllavswdgghro&limit=100` (8 records)
- **Extracted CSV:** `GET /api/acm/export?source_id=source:lap4wnbxllavswdgghro&format=csv` (8 records, 13 columns)

## Methodology
1. Parse ground truth CSV - categorize by result type (Positive/Assumed Positive/Negative)
2. Parse extracted records from JSON API response
3. Match extracted records to ground truth by room_name + product fuzzy match
4. Field-by-field accuracy for each matched pair across 4 categories
5. Calculate coverage and accuracy scores
6. Compare with previous test baseline (Issue #14: 8/31 = 26%)

## Key Observations (Pre-Analysis)
- CSV export is missing compliance fields (sample_no, quantity, acm_labelled, etc.)
- API response model also lacks these fields - structural bug
- All 8 extracted records have result="Detected" - no negative results extracted
- All 8 records have extraction_confidence="high"
- area_type uses "Interior"/"External" instead of CSV's "Internal"/"External"
- Result mapping: "Detected" conflates Positive and Assumed Positive

## Output Files
- `findings.md` - Executive summary and scores
- `comparison.md` - Record-by-record comparison table
- `progress.md` - Step-by-step validation log
