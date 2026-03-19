# Ground Truth CSVs for Prompt Evaluation

These CSVs are normalized versions of the BAR export CSVs, using ACMExtractionRecord field names.
They serve as the reference for automated prompt quality evaluation.

## Sources
- `broadmeadows.csv` — 30 records from `docs/samplePDF/Clutch_Broadmeadows.csv`
- `alexander.csv` — 43 records from `docs/samplePDF/Alexander_GroundTruth.csv`

## Field Mapping (BAR → ACMExtractionRecord)
| BAR Column | Record Field |
|---|---|
| Room or Area | room_name |
| Level | floor_level |
| Location in Room | location |
| Specific Item/ACM Name | product |
| ACM Product Type | material_description |
| Friability of material | friable |
| NATA Endorsed Sample number | sample_no |
| Sample Result | sample_result |
| Internal / External | area_type |
| Condition | material_condition |
| Disturbance Potential | disturbance_potential |
