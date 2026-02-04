# Victorian BAR (Building Asbestos Register) Schema Reference

> **Version:** 1.0
> **Date:** 2026-02-05
> **Source:** Official Victorian Government BAR template (Alexandra District BAR.xlsm)

This document defines the authoritative schema for Victorian Building Asbestos Registers.

---

## Column Definitions

### Required Fields (Columns A-AH)

| Col | Field Name | Type | Validation | Description |
|-----|------------|------|------------|-------------|
| A | Department | string | Required | Victorian Government department (DJCS, DHHS, DET, DOT, DJPR) |
| B | Agency | string | Required | Sub-department or agency name |
| C | Sub Agency | string | Optional | Further subdivision if applicable |
| D | Site Name (if applicable) | string | Optional | Site identifier |
| E | Building Name | string | Required | Name of the building |
| F | Building Type | string | Required | Type classification (Police Station, Hospital, School, etc.) |
| G | Building Address | string | Required | Street address |
| H | Suburb | string | Required | Suburb name |
| I | Postcode | string | Required | 4-digit Victorian postcode |
| J | Owned or Leased | enum | Required | `[Owned, Leased]` |
| K | Building Unique ID | string | Required | Government-assigned building identifier |
| L | Frequency of use | enum | Required | See [Frequency of Use](#frequency-of-use) |
| M | Public Access? | enum | Optional | `[YES, NO]` |
| N | Date of Inspection | date | Required | YYYY-MM-DD format |
| O | Estimated Year Built | number | Required | 4-digit year |
| P | Est. Building Size (m2) | number | Required | Floor area in square meters |
| Q | Number of Levels | number | Required | Total floor count |
| R | Construction Type | string | Required | Wall construction material |
| S | Roof Type | string | Required | Roof material |
| T | Internal / External | enum | Required | `[Internal, External, External & Internal]` |
| U | Level | string | Required | Floor level (Ground, Level 1, Basement, etc.) |
| V | Room or Area | string | Required | Room name or area description |
| W | Location in Room | string | Required | Specific location within room |
| X | Specific Item/ACM Name | string | Required | ACM material description |
| Y | Friability of material | enum | Required | `[Non-friable, Friable]` |
| Z | FRIABILITY NAME EXCEL | string | Required | Display name for friability |
| AA | ACM Product Group | string | Required | Classification group (T1-T8) |
| AB | ACM GROUP NAME EXCEL | string | Required | Display name for product group |
| AC | ACM Product Type | string | Required | Specific product type within group |
| AD | NATA Endorsed Sample number (if available) | string | Required | Sample ID or "Not Sampled" |
| AE | Sample Result | enum | Required | See [Sample Result](#sample-result) |
| AF | Identifying Hygiene or Consulting Company | string | Required | Company that performed inspection |
| AG | Condition | enum | Required | See [Condition](#condition) |
| AH | Disturbance Potential | enum | Required | See [Disturbance Potential](#disturbance-potential) |

### Recommended Fields (Columns AI-AU)

| Col | Field Name | Type | Description |
|-----|------------|------|-------------|
| AI | Quantity | number | Amount of ACM material |
| AJ | Labelled | enum | `[YES, NO]` - Whether ACM is labelled |
| AK | Label Details | string | Description of labelling |
| AL | Hygienist Recommendations | string | Recommended actions from hygienist |
| AM | Additional Comments | string | Any additional notes |
| AN | PSB Supplied ACM ID | string | Property Services Branch ACM identifier |
| AO | Assumed Removed? | enum | `[YES, NO]` |
| AP | Date of Removal | date | When ACM was removed |
| AQ | Quantity Removed | number | Amount removed |
| AR | Asbestos Removal Notification No | string | WorkSafe notification number |
| AS | EPA Waste Transport Certificate No | string | EPA certificate number |
| AT | Removal Comments | string | Notes about removal |
| AU | Photo Reference Number | string | Reference to photo documentation |

---

## Enum Definitions

### Frequency of Use
```json
[
  "Every day",
  "Every day with intermittent breaks",
  "Once every 3–5 days",
  "Every 2–3 weeks",
  "Once every 2–3 months",
  "Annually or less frequently"
]
```

### Sample Result
```json
["Positive", "Assumed Positive", "Negative", "Assumed Negative"]
```

**Note:** "Assumed Positive" is used when sampling was not possible (height restriction, live electrical, etc.) but material is presumed to contain asbestos based on visual identification.

### Condition
```json
["Poor", "Fair", "Good", "Unknown", "N/A (negative)", "N/A (assumed negative)"]
```

**Business Rule:** If Sample Result is "Negative" or "Assumed Negative", Condition should be set to the corresponding N/A value.

### Disturbance Potential
```json
["High", "Moderate", "Low", "Unknown", "N/A (negative)", "N/A (assumed negative)"]
```

**Business Rule:** If Sample Result is "Negative" or "Assumed Negative", Disturbance Potential should be set to the corresponding N/A value.

### Internal / External
```json
["Internal", "External", "External & Internal"]
```

### Yes/No Fields
```json
["YES", "NO"]
```
Used for: Public Access?, Labelled, Assumed Removed?

---

## Field Mapping: ACM-AI → BAR

| ACM-AI Internal Field | BAR Column | Notes |
|-----------------------|------------|-------|
| `department` | A - Department | Direct |
| `agency` | B - Agency | Direct |
| `sub_agency` | C - Sub Agency | Direct |
| `site_name` | D - Site Name | Direct |
| `building_name` | E - Building Name | Direct |
| `building_type` | F - Building Type | Direct |
| `building_address` | G - Building Address | Direct |
| `suburb` | H - Suburb | Direct |
| `postcode` | I - Postcode | Direct |
| `owned_or_leased` | J - Owned or Leased | Direct |
| `building_unique_id` | K - Building Unique ID | Direct |
| `frequency_of_use` | L - Frequency of use | Direct |
| `public_access` | M - Public Access? | Direct |
| `date_of_inspection` | N - Date of Inspection | Format: YYYY-MM-DD |
| `building_year` | O - Estimated Year Built | Direct |
| `building_size_m2` | P - Est. Building Size | Direct |
| `number_of_levels` | Q - Number of Levels | Direct |
| `building_construction` | R - Construction Type | Direct |
| `roof_type` | S - Roof Type | Direct |
| `area_type` | T - Internal / External | Validate enum |
| `level` | U - Level | Direct |
| `room_name` | V - Room or Area | Direct |
| `location` | W - Location in Room | Direct |
| `product` | X - Specific Item/ACM Name | Direct |
| `friable` | Y - Friability of material | Validate enum |
| `friability_display` | Z - FRIABILITY NAME EXCEL | Derived from friable |
| `acm_product_group` | AA - ACM Product Group | From taxonomy |
| `acm_group_display` | AB - ACM GROUP NAME EXCEL | Derived |
| `acm_product_type` | AC - ACM Product Type | From taxonomy |
| `nata_sample_number` | AD - NATA Sample number | Direct |
| `sample_result` | AE - Sample Result | Validate enum |
| `hygiene_company` | AF - Identifying Company | Direct |
| `material_condition` | AG - Condition | Validate enum |
| `disturbance_potential` | AH - Disturbance Potential | Validate enum |
| `extent` | AI - Quantity | Direct |
| `labelled` | AJ - Labelled | Validate enum |
| `label_details` | AK - Label Details | Direct |
| `hygienist_recommendations` | AL - Hygienist Recommendations | Direct |
| `additional_comments` | AM - Additional Comments | Direct |
| `psb_acm_id` | AN - PSB Supplied ACM ID | Direct |
| `assumed_removed` | AO - Assumed Removed? | Validate enum |
| `date_of_removal` | AP - Date of Removal | Format: YYYY-MM-DD |
| `quantity_removed` | AQ - Quantity Removed | Direct |
| `removal_notification_no` | AR - Removal Notification No | Direct |
| `epa_certificate_no` | AS - EPA Certificate No | Direct |
| `removal_comments` | AT - Removal Comments | Direct |
| `photo_reference` | AU - Photo Reference Number | Direct |

---

## Business Rules

### 1. Negative Sample Handling
When `Sample Result` is "Negative" or "Assumed Negative":
- Set `Condition` to "N/A (negative)" or "N/A (assumed negative)"
- Set `Disturbance Potential` to "N/A (negative)" or "N/A (assumed negative)"
- Leave removal tracking fields blank

### 2. Leased Building Rule
If `Owned or Leased` is "Leased", data entry stops (Victorian Government responsibility ends).

### 3. Removed ACM Rule
ACM that has been **entirely removed** does NOT need to be entered into the register.
- If partially removed, enter remaining ACM
- Provide clearance certificates for removed ACM

### 4. Sample Number Requirements
- If sampled: Use NATA-endorsed sample number (e.g., "34511-039-001")
- If not sampled but assumed positive: "Not Sampled - Assumed"
- If same as previous sample: "As Per [sample_number]"

### 5. Derived Fields
The following fields are computed, not stored:
- `risk_status`: Derived from Condition + Disturbance Potential
- Display name fields (Z, AB): Derived from enum values

---

## Validation Rules

### Required Field Check
```python
REQUIRED_COLUMNS = ['A', 'B', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L',
                    'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W',
                    'X', 'Y', 'Z', 'AA', 'AB', 'AC', 'AD', 'AE', 'AF',
                    'AG', 'AH']
```

### Enum Validation
All enum fields must match exactly (case-sensitive) from the defined lists.

### Date Format
All dates should be stored in ISO format (YYYY-MM-DD) and formatted appropriately for Excel export.

---

## References

- Source file: `docs/samplePDF/instructions-sample/register_row.schema.json`
- Enum definitions: `docs/samplePDF/instructions-sample/register_enums.json`
- Sample BAR: `docs/samplePDF/instructions-sample/Clucth_Alexandra_District_BAR.xlsm`
