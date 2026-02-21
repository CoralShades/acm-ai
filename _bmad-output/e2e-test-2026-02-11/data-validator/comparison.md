# Record-by-Record Comparison

## Coverage Matrix: All 31 Ground Truth Records

| # | Room (CSV) | Product (CSV) | Result (CSV) | Level (CSV) | Int/Ext | Matched? | Extracted Room | Extracted Product | Extracted Result | Notes |
|---|-----------|---------------|-------------|-------------|---------|----------|----------------|-------------------|------------------|-------|
| 1 | Main Foyer | Floor covering | Negative | Ground | Internal | NO | - | - | - | Not extracted (negative) |
| 2 | Front Desk Area | Floor covering | Negative | Ground | Internal | NO | - | - | - | Not extracted (negative) |
| 3 | Front Desk Area | Filing Cabinet | Assumed Positive | Ground | Internal | YES | Front Desk Area | Filing Cabinet | Detected | Match #1 |
| 4 | Soft Interview Room No.2 | Skirting | Negative | Ground | Internal | NO | - | - | - | Not extracted (negative) |
| 5 | Kitchenette | Floor covering | Negative | Ground | Internal | NO | - | - | - | Not extracted (negative) |
| 6 | Corridor Adjacent Cells and Custody Counter | Floor covering | Negative | Ground | Internal | NO | - | - | - | Not extracted (negative) |
| 7 | Lift Foyer | Floor covering | Negative | Ground | Internal | NO | - | - | - | Not extracted (negative) |
| 8 | Switch Room | Fuse cartridge | Assumed Positive | Level 1 | Internal | YES | Switch Room | Switchboard | Detected | Match #2 |
| 9 | Switch Room | Fuse cartridge | Assumed Positive | Level 1 | Internal | NO | - | - | - | Second Switch Room item (Battery Charger) not extracted separately |
| 10 | Comms Area | Floor covering | Negative | Level 1 | Internal | NO | - | - | - | Not extracted (negative) |
| 11 | Fan Room | Flange joints | Positive | Level 1 | Internal | YES | Fan Room | Air Handling Unit Ductwork | Detected | Match #5 |
| 12 | Fan Room | Infill panels | Positive | Level 1 | Internal | YES | Fan Room | Wall | Detected | Match #4 |
| 13 | Male Locker Room | Floor covering | Negative | Level 1 | Internal | NO | - | - | - | Not extracted (negative) |
| 14 | Male Locker Room | Wall lining | Negative | Level 1 | Internal | NO | - | - | - | Not extracted (negative) |
| 15 | Throughout | Skirting | Negative | Level 1 | Internal | NO | - | - | - | Not extracted (negative) |
| 16 | Kitchen | Floor covering | Negative | Level 1 | Internal | NO | - | - | - | Not extracted (negative) |
| 17 | Kitchen | Skirting | Negative | Level 1 | Internal | NO | - | - | - | Not extracted (negative) |
| 18 | Fan Room 2.24 | Flange joints | Positive | Level 1 | Internal | YES | Fan Room 2.24 | Air Handling Unit Ductwork | Detected | Match #6 |
| 19 | Fan Room | Expansion joint | Negative | Level 1 | Internal | NO | - | - | - | Not extracted (negative) |
| 20 | Fan Room | Flange joints | Positive | Ground | External | NO | - | - | - | External Fan Room AHU - may have been merged with Match #5 |
| 21 | Boiler Room | Fuse cartridge | Assumed Positive | Ground | External | YES | Boiler Room | Switchboard | Detected | Match #7 |
| 22 | Boiler Room | Pipework | Negative | Ground | External | NO | - | - | - | Not extracted (negative) |
| 23 | Boiler Room | Pipework | Negative | Ground | External | NO | - | - | - | Not extracted (negative, second pipe) |
| 24 | Boiler Room | Expansion joint | Negative | Ground | External | NO | - | - | - | Not extracted (negative) |
| 25 | East Roof Fan Room | Wall(s) | Negative | Ground | External | NO | - | - | - | Not extracted (negative) |
| 26 | Roof | Flange joints | Positive | Ground | External | YES | East Roof | Ductwork | Detected | Match #8 |
| 27 | East Roof Fan Room | Ceiling | Negative | Ground | External | NO | - | - | - | Not extracted (negative) |
| 28 | Exterior | Expansion joint | Negative | Ground | External | NO | - | - | - | Not extracted (negative) |
| 29 | Property Storage | Floor covering | Negative | Ground | Internal | NO | - | - | - | Not extracted (negative) |
| 30 | Lift Foyer | Internal lining | Assumed Positive | Ground | Internal | NO | - | - | - | Not extracted (assumed positive) |
| 31 | Main Foyer | Unknown | Assumed Positive | Ground | Internal | NO | - | - | - | Not extracted (assumed positive) |

### Unmatched Extracted Record
| Extracted Room | Extracted Product | Notes |
|----------------|-------------------|-------|
| Ceiling Space | Ductwork | No "Ceiling Space" room in CSV. May be a hallucination or misinterpretation of a ceiling-mounted duct reference |

## Coverage by Result Type

| Result Type | CSV Count | Extracted | Coverage |
|-------------|-----------|-----------|----------|
| Negative | 20 | 0 | 0% |
| Positive | 5 | 4 | 80% |
| Assumed Positive | 6 | 3 | 50% |
| **Total** | **31** | **7** | **22.6%** |

Note: 1 extracted record ("Ceiling Space / Ductwork") has no CSV match (possible false positive).

## Detailed Field Comparison for Matched Records

### Match #1: Front Desk Area / Filing Cabinet (CSV Row 3, Assumed Positive)

| Field | CSV Value | Extracted Value | Match? |
|-------|-----------|-----------------|--------|
| **Core ID Fields** | | | |
| room_name | Front Desk Area | Front Desk Area | YES |
| product | Filing Cabinet | Filing Cabinet | YES |
| area_type | Internal | Interior | PARTIAL (vocabulary mismatch) |
| location | Filing Cabinet | (null) | NO |
| **Assessment Fields** | | | |
| friable | Non-friable | Non-friable | YES |
| result | Assumed Positive | Detected | PARTIAL (conflated) |
| material_condition | Good | Good | YES |
| risk_status | Low | Low | YES |
| **Compliance Fields** | | | |
| sample_no | Not Sampled | (not in API) | N/A - STRUCTURAL BUG |
| quantity | 3 | (not in API) | N/A - STRUCTURAL BUG |
| acm_labelled | YES | (not in API) | N/A - STRUCTURAL BUG |
| identifying_company | Prensa Pty Ltd | (not in API) | N/A - STRUCTURAL BUG |
| **Classification Fields** | | | |
| acm_product_group | Insulation Products | (null) | NO |
| acm_product_type | Internal Lining | (null) | NO |

### Match #2: Switch Room / Switchboard (CSV Row 8, Assumed Positive)

| Field | CSV Value | Extracted Value | Match? |
|-------|-----------|-----------------|--------|
| **Core ID Fields** | | | |
| room_name | Switch Room | Switch Room | YES |
| product (CSV: Specific Item) | Fuse cartridge | Switchboard | PARTIAL (location used as product) |
| area_type | Internal | Interior | PARTIAL |
| location | Switchboard | (null) | NO |
| **Assessment Fields** | | | |
| friable | Non-friable | Non-friable | YES |
| result | Assumed Positive | Detected | PARTIAL |
| material_condition | Good | Good | YES |
| risk_status | Low | Low | YES |
| **Compliance Fields** | | | |
| sample_no | Not Sampled | (not in API) | N/A |
| quantity | 60 | (not in API) | N/A |
| acm_labelled | YES | (not in API) | N/A |
| identifying_company | Prensa Pty Ltd | (not in API) | N/A |
| **Classification Fields** | | | |
| acm_product_group | Insulation Products | (null) | NO |
| acm_product_type | Electrical Components | (null) | NO |

### Match #4: Fan Room / Wall (CSV Row 12, Positive)

| Field | CSV Value | Extracted Value | Match? |
|-------|-----------|-----------------|--------|
| **Core ID Fields** | | | |
| room_name | Fan Room | Fan Room | YES |
| product (CSV: Specific Item) | Infill panels | Wall | PARTIAL (generalized) |
| area_type | Internal | Interior | PARTIAL |
| location | Wall Opposite AHU Inlet | (null) | NO |
| **Assessment Fields** | | | |
| friable | Non-friable | Non-friable | YES |
| result | Positive | Detected | PARTIAL |
| material_condition | Good | Good | YES |
| risk_status | Low | Low | YES |
| **Compliance Fields** | | | |
| sample_no | 34511-039-008 | (not in API) | N/A |
| quantity | 2 | (not in API) | N/A |
| acm_labelled | YES | (not in API) | N/A |
| identifying_company | Prensa Pty Ltd | (not in API) | N/A |
| **Classification Fields** | | | |
| acm_product_group | Cement products | (null) | NO |
| acm_product_type | Flat Sheeting | (null) | NO |

### Match #5: Fan Room / Air Handling Unit Ductwork (CSV Row 11, Positive)

| Field | CSV Value | Extracted Value | Match? |
|-------|-----------|-----------------|--------|
| **Core ID Fields** | | | |
| room_name | Fan Room | Fan Room | YES |
| product (CSV: Specific Item) | Flange joints | Air Handling Unit Ductwork | PARTIAL (location used as product) |
| area_type | Internal | Interior | PARTIAL |
| location | Air Handling Unit Ductwork | (null) | NO |
| **Assessment Fields** | | | |
| friable | Non-friable | Non-friable | YES |
| result | Positive | Detected | PARTIAL |
| material_condition | Good | Good | YES |
| risk_status | Low | Low | YES |
| **Compliance Fields** | | | |
| sample_no | 34511-039-007 | (not in API) | N/A |
| quantity | (empty) | (not in API) | N/A |
| acm_labelled | YES | (not in API) | N/A |
| identifying_company | Prensa Pty Ltd | (not in API) | N/A |
| **Classification Fields** | | | |
| acm_product_group | Gasket, friction products and adhesives | (null) | NO |
| acm_product_type | Mastic | (null) | NO |

### Match #6: Fan Room 2.24 / Air Handling Unit Ductwork (CSV Row 18, Positive)

| Field | CSV Value | Extracted Value | Match? |
|-------|-----------|-----------------|--------|
| **Core ID Fields** | | | |
| room_name | Fan Room 2.24 | Fan Room 2.24 | YES |
| product (CSV: Specific Item) | Flange joints | Air Handling Unit Ductwork | PARTIAL (location used as product) |
| area_type | Internal | Interior | PARTIAL |
| location | Air Handling Unit Ductwork | (null) | NO |
| **Assessment Fields** | | | |
| friable | Non-friable | Non-friable | YES |
| result | Positive | Detected | PARTIAL |
| material_condition | Good | Good | YES |
| risk_status | Low | Low | YES |
| **Compliance Fields** | | | |
| sample_no | As Per 34511-039-007 | (not in API) | N/A |
| quantity | 10 | (not in API) | N/A |
| acm_labelled | YES | (not in API) | N/A |
| identifying_company | Prensa Pty Ltd | (not in API) | N/A |
| **Classification Fields** | | | |
| acm_product_group | Gasket, friction products and adhesives | (null) | NO |
| acm_product_type | Mastic | (null) | NO |

### Match #7: Boiler Room / Switchboard (CSV Row 21, Assumed Positive)

| Field | CSV Value | Extracted Value | Match? |
|-------|-----------|-----------------|--------|
| **Core ID Fields** | | | |
| room_name | Boiler Room | Boiler Room | YES |
| product (CSV: Specific Item) | Fuse cartridge | Switchboard | PARTIAL (location used as product) |
| area_type | External | External | YES |
| location | Switchboard | (null) | NO |
| **Assessment Fields** | | | |
| friable | Non-friable | Non-friable | YES |
| result | Assumed Positive | Detected | PARTIAL |
| material_condition | Good | Good | YES |
| risk_status | Low | Low | YES |
| **Compliance Fields** | | | |
| sample_no | Not Sampled | (not in API) | N/A |
| quantity | 1 | (not in API) | N/A |
| acm_labelled | YES | (not in API) | N/A |
| identifying_company | Prensa Pty Ltd | (not in API) | N/A |
| **Classification Fields** | | | |
| acm_product_group | Insulation Products | (null) | NO |
| acm_product_type | Electrical Components | (null) | NO |

### Match #8: East Roof / Ductwork (CSV Row 26, Positive)

| Field | CSV Value | Extracted Value | Match? |
|-------|-----------|-----------------|--------|
| **Core ID Fields** | | | |
| room_name | Roof | East Roof | PARTIAL (merged with location prefix) |
| product (CSV: Specific Item) | Flange joints | Ductwork | PARTIAL (location used as product) |
| area_type | External | External | YES |
| location | East Ductwork | (null) | NO |
| **Assessment Fields** | | | |
| friable | Non-friable | Non-friable | YES |
| result | Positive | Detected | PARTIAL |
| material_condition | Good | Good | YES |
| risk_status | Low | Low | YES |
| **Compliance Fields** | | | |
| sample_no | 34511-039-015 | (not in API) | N/A |
| quantity | 20 | (not in API) | N/A |
| acm_labelled | YES | (not in API) | N/A |
| identifying_company | Prensa Pty Ltd | (not in API) | N/A |
| **Classification Fields** | | | |
| acm_product_group | Gasket, friction products and adhesives | (null) | NO |
| acm_product_type | Mastic | (null) | NO |

## Accuracy Tally

### Core ID Fields (4 fields x 7 matches = 28 possible)
- room_name: 6 YES, 1 PARTIAL = 6.5/7
- product: 1 YES, 6 PARTIAL = 4/7 (counting PARTIAL as 0.5)
- area_type: 2 YES, 5 PARTIAL = 4.5/7
- location: 0 YES, 7 NO = 0/7
- **Core ID Total: 15/28 = 53.6%**

### Assessment Fields (4 fields x 7 matches = 28 possible)
- friable: 7 YES = 7/7
- result: 0 YES, 7 PARTIAL = 3.5/7
- material_condition: 7 YES = 7/7
- risk_status: 7 YES = 7/7
- **Assessment Total: 24.5/28 = 87.5%**

### Compliance Fields (4 fields x 7 matches = 28 possible)
- All fields missing from API response model
- **Compliance Total: 0/28 = 0% (STRUCTURAL BUG)**

### Classification Fields (2 fields x 7 matches = 14 possible)
- acm_product_group: 0/7 (all null)
- acm_product_type: 0/7 (all null)
- **Classification Total: 0/14 = 0%**
