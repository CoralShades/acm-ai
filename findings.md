# Findings & Decisions - Course Correction Analysis

## Requirements
- Input: PDF Asbestos Risk Assessment documents
- Output: Excel BAR (Building Asbestos Register) spreadsheets
- UI: View extracted records, process, manipulate, reference, edit
- Goal: Accurate extraction and transformation without guessing mappings

## Research Findings

### Project Documents Analysis

#### PRD ACM Data Model (Current)
From PRD Section 5.1, the current schema has **20 fields**:
- source_id, school_name, school_code
- building_id, building_name, building_year, building_construction
- room_id, room_name, room_area, area_type
- product, material_description, extent, location
- friable, material_condition, risk_status, result
- page_number, extraction_confidence, created_at

#### Architecture ACM Schema (Current)
Same 20 fields as PRD, designed for NSW School SAMP documents.

### Output Excel Analysis (CRITICAL FINDINGS)

#### Clutch_Broadmeadows_Police_BAR.xlsx
- **Single sheet**: Sheet1
- **43 columns** (vs 20 in PRD - MAJOR GAP!)
- **32 data rows**

**Excel Columns NOT in PRD Schema:**
1. Department (DJCS) - NEW
2. Agency (Victoria Police) - NEW
3. Sub Agency - NEW
4. Site Name (if applicable) - NEW
5. Building Type (Police Station) - NEW
6. Building Address - NEW
7. Suburb - NEW
8. Postcode - NEW
9. Owned or Leased - NEW
10. Building Unique ID - NEW
11. Frequency of use - NEW
12. Public Access? - NEW
13. Date of Inspection - NEW
14. Est. Building Size (m2) - NEW
15. Number of Levels - NEW
16. Construction Type - maps to building_construction
17. Roof Type - NEW
18. Internal / External - maps to area_type
19. Level - NEW
20. Room or Area - maps to room_name
21. Location in Room - maps to location
22. Specific Item/ACM Name - maps to product
23. Friability of material - maps to friable
24. ACM Product Group - NEW
25. ACM Product Type - NEW (more specific than "product")
26. NATA Endorsed Sample number - NEW
27. Sample Result - NEW (different from "result")
28. Identifying Hygiene or Consulting Company - NEW
29. Condition - maps to material_condition
30. Disturbance Potential - NEW
31. Quantity - NEW (was "extent" but different meaning)
32. Labelled - NEW
33. Label Details - NEW
34. Hygienist Recommendations - NEW
35. Additional Comments - NEW
36. PSB Supplied ACM ID - NEW
37. Assumed Removed? - NEW
38. Date of Removal - NEW
39. Quantity Removed - NEW
40. Asbestos Removal Notification No - NEW
41. EPA Waste Transport Certificate No - NEW

#### Clucth_Alexandra_District_BAR.xlsm
- **26 sheets** (reference data + DATA ENTRY main sheet)
- **47 columns in DATA ENTRY** (even more than Broadmeadows!)
- **533 data rows**
- **5 unique buildings**

**Additional columns vs Broadmeadows:**
- FRIABILITY NAME EXCEL (lookup field)
- ACM GROUP NAME EXCEL (lookup field)
- Removal Comments
- Photo Reference Number

### Input PDF Analysis (COMPLETED)

#### Clutch_Broadmeadows Police Station PDF (19 pages)
**Provider:** Prensa Pty Ltd
**PDF Table Headers (Asbestos Register):**
1. Area / Level
2. Room & Location
3. Feature
4. Item Description
5. Hazard Type
6. Hazard Status (Negative, Assumed positive, etc.)
7. Sample Number
8. Friability
9. Labelled Y/N
10. Source of Asbestos That is Not Fixed or Installed
11. Workplace Activities Likely to Disturb Asbestos
12. Disturb. Potential
13. Condition
14. Risk Status
15. Approx. Quantity
16. Control Priority
17. Comments & Recommendations
18. Date of Identification
19. Reinspect Date
20. Photograph

**Site metadata available in PDF:**
- Job No (34511-039)
- Address (15 Dimboola Road, Broadmeadows, Victoria)
- Client (Victoria Police)
- Date (June 2020)

#### Clucth_Alexandra District Hospital PDF (34 pages)
**Provider:** Greencap
**PDF Table Headers (Asbestos Register):**
1. Item No.
2. Location - Item Description
3. Hazard Type
4. Sample No.
5. Item Status
6. Photo No.
7. Est. Extent
8. Condition
9. Friability
10. Dist. Potential
11. Risk Rating
12. Current Label
13. Reinspect Date
14. Control Priority
15. Control Recommendation
16. Record Of Works Undertaken

**Site/Building metadata in each register section:**
- Full Address
- Building Name
- Number of Levels
- Survey Date
- Property ID
- Est. Building Size
- Est. Building Age
- Roof Type
- Construction Type
- Client Name
- Inspected By
- Company

## Technical Decisions
| Decision | Rationale |
|----------|-----------|
| PRD schema needs major expansion | 20 fields → 47+ fields required for BAR export |
| Victorian Government format differs from NSW SAMP | Different agency structure, more metadata |

## Issues Encountered
| Issue | Resolution |
|-------|------------|
| PDF tool unavailable (pdftoppm not installed) | Will use Python pdf libraries instead |
| Excel files have different structures | Need flexible schema to handle variations |

## Resources
- Input PDF 1: docs/samplePDF/Clutch_Broadmeadows Police Station Div 5 34511-039 V2_done.pdf
- Input PDF 2: docs/samplePDF/Clucth_Alexander_District_Hospital_Asbestos_Risk_Assessment_2020-09-07 (1) 24 Cooper.pdf
- Output Excel 1: docs/samplePDF/Clutch_Broadmeadows_Police_BAR.xlsx (43 columns)
- Output Excel 2: docs/samplePDF/Clucth_Alexandra_District_BAR.xlsm (47 columns, 26 sheets)

## Visual/Browser Findings

### Excel Column Mapping Analysis (CRITICAL)

#### Required Output Fields NOT in Current PRD:

**Building/Site Metadata (NEW SECTION NEEDED):**
| Excel Column | PRD Field | Gap Analysis |
|--------------|-----------|--------------|
| Department | MISSING | Need new field |
| Agency | MISSING | Need new field |
| Sub Agency | MISSING | Need new field |
| Site Name | MISSING | Need new field |
| Building Type | MISSING | Need new field |
| Building Address | MISSING | Need new field |
| Suburb | MISSING | Need new field |
| Postcode | MISSING | Need new field |
| Owned or Leased | MISSING | Need new field |
| Building Unique ID | MISSING | Need new field |
| Frequency of use | MISSING | Need new field |
| Public Access? | MISSING | Need new field |
| Date of Inspection | MISSING | Need new field |
| Est. Building Size (m2) | MISSING | Need new field |
| Number of Levels | MISSING | Need new field |
| Roof Type | MISSING | Need new field |

**ACM Item Details (NEW FIELDS NEEDED):**
| Excel Column | PRD Field | Gap Analysis |
|--------------|-----------|--------------|
| Level | MISSING | Need new field |
| ACM Product Group | MISSING | Need new field (classification) |
| ACM Product Type | MISSING | Need new field (specific type) |
| NATA Sample Number | MISSING | Need new field |
| Sample Result | result | Need clarification - different meaning |
| Hygiene Company | MISSING | Need new field |
| Disturbance Potential | MISSING | Need new field |
| Quantity | extent | Need clarification - different semantics |
| Labelled | MISSING | Need new field |
| Label Details | MISSING | Need new field |
| Hygienist Recommendations | MISSING | Need new field |
| Additional Comments | MISSING | Need new field |
| PSB Supplied ACM ID | MISSING | Need new field |

**Removal Tracking (ENTIRE NEW SECTION):**
| Excel Column | PRD Field | Gap Analysis |
|--------------|-----------|--------------|
| Assumed Removed? | MISSING | Need new field |
| Date of Removal | MISSING | Need new field |
| Quantity Removed | MISSING | Need new field |
| Asbestos Removal Notification No | MISSING | Need new field |
| EPA Waste Transport Certificate No | MISSING | Need new field |
| Removal Comments | MISSING | Need new field |
| Photo Reference Number | MISSING | Need new field |

## COMPLETE FIELD MAPPING: PDF Input → Excel BAR Output

### Organization/Site Metadata (MUST be captured from PDF or configured)
| Excel BAR Column | PDF Source | Notes |
|------------------|------------|-------|
| Department | NOT IN PDF | Must be configured per client (DJCS, DHHS, etc.) |
| Agency | PDF: Client/Organization | Victoria Police, Alexandra District Health |
| Sub Agency | PDF: Site Name | Broadmeadows Police Station, Alexandra District Hospital |
| Site Name (if applicable) | PDF: Site Address area | May need parsing |
| Building Name | PDF: Building Name (per register section) | Direct mapping |
| Building Type | NOT IN PDF | Must be configured (Police Station, Hospital, etc.) |
| Building Address | PDF: Full Address | Direct mapping |
| Suburb | PDF: Address parsing | Extract from address |
| Postcode | PDF: Address parsing | Extract from address |
| Owned or Leased | NOT IN PDF | Must be configured |
| Building Unique ID | NOT IN PDF | May auto-generate or configure |
| Frequency of use | NOT IN PDF | Must be configured |
| Public Access? | NOT IN PDF | Must be configured |
| Date of Inspection | PDF: Survey Date | Direct mapping |
| Estimated Year Built | PDF: Est. Building Age | Parse "1990s" → 1990 |

### Building Characteristics
| Excel BAR Column | PDF Source | Notes |
|------------------|------------|-------|
| Est. Building Size (m2) | PDF: Est. Building Size | Parse "800m²" → 800 |
| Number of Levels | PDF: Number of Levels | Direct mapping |
| Construction Type | PDF: Construction Type | Direct mapping |
| Roof Type | PDF: Roof Type | Direct mapping |

### ACM Item Location
| Excel BAR Column | PDF Source | Notes |
|------------------|------------|-------|
| Internal / External | PDF: Location | Parse "External - Throughout" → External |
| Level | PDF: Area / Level | "Ground floor", "First floor", "Ground Level" |
| Room or Area | PDF: Room & Location / Location | "Main foyer", "External - Throughout" |
| Location in Room | PDF: Feature / Location detail | "Floor", "Eaves", "Window Frames" |

### ACM Item Details
| Excel BAR Column | PDF Source | Notes |
|------------------|------------|-------|
| Specific Item/ACM Name | PDF: Item Description | "Vinyl sheet (cream)", "Flat Cement Sheeting" |
| Friability of material | PDF: Friability | "Non-friable", "Friable" |
| ACM Product Group | NOT IN PDF | Must derive from Item Description |
| ACM Product Type | NOT IN PDF | Must derive from Item Description |
| NATA Endorsed Sample number | PDF: Sample Number | Direct mapping |
| Sample Result | PDF: Hazard Status / Item Status | "Negative", "Positive", "Assumed positive" |
| Identifying Hygiene Company | PDF: Company header | Prensa Pty Ltd, Greencap |
| Condition | PDF: Condition | "Good", "Fair", etc. |
| Disturbance Potential | PDF: Disturb. Potential | Direct mapping |
| Quantity | PDF: Approx. Quantity / Est. Extent | "3 units", "5 m²" |

### Labeling & Documentation
| Excel BAR Column | PDF Source | Notes |
|------------------|------------|-------|
| Labelled | PDF: Labelled Y/N / Current Label | "Yes", "No", "Not Labelled" |
| Label Details | NOT IN PDF | Optional |
| Hygienist Recommendations | PDF: Comments & Recommendations / Control Recommendation | Direct mapping |
| Additional Comments | PDF: Extra notes | May combine fields |
| PSB Supplied ACM ID | NOT IN PDF | May be blank |
| Photo Reference Number | PDF: Photograph / Photo No. | Direct mapping |

### Removal Tracking (NEW SECTION - rarely in source PDF)
| Excel BAR Column | PDF Source | Notes |
|------------------|------------|-------|
| Assumed Removed? | NOT IN PDF | Default: blank |
| Date of Removal | NOT IN PDF | Default: blank |
| Quantity Removed | NOT IN PDF | Default: blank |
| Asbestos Removal Notification No | NOT IN PDF | Default: blank |
| EPA Waste Transport Certificate No | NOT IN PDF | Default: blank |
| Removal Comments | PDF: Record Of Works Undertaken | If available |

## GAP ANALYSIS SUMMARY

### Fields That CANNOT Be Extracted from PDF (Require Configuration)
1. **Department** - Government department (DJCS, DHHS, DET, etc.)
2. **Building Type** - Classification (Police Station, Hospital, School, etc.)
3. **Owned or Leased** - Property ownership status
4. **Frequency of use** - How often building is used
5. **Public Access?** - Whether public has access
6. **Building Unique ID** - Unique identifier
7. **ACM Product Group** - Classification category
8. **ACM Product Type** - Specific ACM type

### Fields That Require Parsing/Derivation
1. **Suburb** - Parse from address
2. **Postcode** - Parse from address
3. **Estimated Year Built** - Parse "1990s" → numeric
4. **Est. Building Size** - Parse "800m²" → numeric
5. **Internal/External** - Derive from location text
6. **ACM Product Group/Type** - AI classification from item description

### Fields That Are Direct Mappings
- Building Name, Address, Date of Inspection, Roof Type, Construction Type
- Room, Level, Item Description, Friability, Sample Number, Condition
- Risk Rating, Disturbance Potential, Quantity, Recommendations, Photos

---
*Update this file after every 2 view/browser/search operations*
