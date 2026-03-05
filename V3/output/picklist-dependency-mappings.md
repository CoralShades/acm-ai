# Dependent Picklist Mappings — Building__c & Item__c

**Sources:** `building-list.txt`, `item-list.txt` (Salesforce metadata), `docs/reference/product-taxonomy.md`, `register_taxonomy.*.json`
**Generated:** March 2026

---

## Overview of Dependency Chains

### Building__c
```
Building_Type__c (114 values) → Building_Category__c (13 values)
```

### Item__c
```
Friability_of_Material__c (2 values) → ACM_Classification__c / ACM Product Group (18 values)
                                              ↓
                               ACM_Sub_Classification__c / ACM Product Type (133 values)
```

**Note:** `Item_Name__c` (294 values) is a **restricted** picklist but is NOT marked as a dependent picklist in the Salesforce metadata — it has no `controllerName`. It is independent of the classification chain.

---

## Chain 1 — Building__c: Building_Type__c → Building_Category__c

**Controller:** `Building_Type__c` (114 values)
**Dependent:** `Building_Category__c` (13 values)

> **Decoding note:** The Salesforce `validFor` binary data in the raw text file is largely non-printable and cannot be fully decoded from the text export. The mapping below is derived from domain knowledge of the VAEA context.

| Building_Category__c Value | Building_Type__c Values |
|---------------------------|------------------------|
| **Agriculture** | Farm annexe, Farm depot house, Fruit shed, Grain storage shed, Hay shed, Hothouse, Polyhouse, Poultry pen, Stables, Stockyard |
| **Commercial and retail** | Commercial, Docklands studios, Film vault, Retail, Shop / Kiosk |
| **Correctional and justice facilities** | Court, Juvenile, Prison |
| **Defence and emergency services** | Airbase, Ambulance garage, Ambulance station, CFA/FRV, Fire pump shed, Police Station |
| **Educational and training facilities** | Building nursery, Child care, Children's centre, Classroom, Education centre, School, TAFE, Teacher house, Training centre, Youth camp |
| **Factories, warehouses and shops** | Canteen, Factory, Storage Shed, Storeroom, Warehouse, Workshop |
| **Health services** | Aged Care, Bush nursing, Community Health Centre, Consulting rooms, Day centre, Dental clinic, Health centre, Hospital, Nursing home, Rehab, Specialist clinic |
| **Housing and accommodation** | Accommodation unit, Apartment, Curator house, Flat, Hostel, House, Housing - disability, Housing - Other, Lodge, Residence, Teacher house |
| **IT and communications** | Communication tower, Computer centre, Radio tower |
| **Offices and professional services** | Administration, Conference centre, Head office, HQ, Office, Ranger's office, Reception, Research facility |
| **Public and family services** | Activities shelter, Amenities, Art centre, Assembly hall, Band room, Basketball court, Community centre, Community hall, Concert hall, Gallery, Gymnasium, Hall, Information centre, Leisure centre, Library, Multipurpose hall, Museum, Pavilion, Recreation and sport, Recreation centre, Rotunda, Tennis pavilion, Theatre, Visitor centre |
| **Transport** | Bridge, Car, Control building, Control centre (train network), Control centre (tram network), Control room, Crew room, Depot, Forklift, Level crossing, Roadway, Train maintenance facility, Train station, Train station precinct, Train substation, Train yard, Tram depot, Tram substation, Transport depot, Truck, Tunnel, Van |
| **Unknown/other** | Barrier or Fencing, Bicycle enclosure, Building, Building room, Business interruption, Facility, Garage, Main building, Other, Pipe, Plant and equipment, Plant room, Pump house, Shed, Shelter, Shelter shed, Shipping Container, Toilet, Tower |

---

## Chain 2 — Item__c: Friability_of_Material__c → ACM_Classification__c

**Controller:** `Friability_of_Material__c`
**Dependent:** `ACM_Classification__c` (ACM Product Group)

The `(f)` suffix in Salesforce picklist values maps to the **Friable** controller value.

| Friability_of_Material__c | ACM_Classification__c (ACM Product Group) |
|--------------------------|------------------------------------------|
| **Non-friable** | Bitumen products |
| **Non-friable** | Cement products |
| **Non-friable** | Coatings |
| **Non-friable** | Gasket, friction products and adhesives |
| **Non-friable** | Insulation Products |
| **Non-friable** | Other |
| **Non-friable** | Reinforced plastics/resins (excluding bitumen products) |
| **Non-friable** | Textiles |
| **Non-friable** | Vinyl products |
| **Friable** | Bitumen products (f) |
| **Friable** | Cement products (f) |
| **Friable** | Coatings (f) |
| **Friable** | Gasket, friction products and adhesives (f) |
| **Friable** | Insulation products (f) |
| **Friable** | Other (f) |
| **Friable** | Reinforced plastics/resins (excluding bitumen products) (f) |
| **Friable** | Textiles (f) |
| **Friable** | Vinyl products (f) |

**Confirmed from raw data:** The `validFor` binary encoding in `item-list.txt` confirms:
- Empty/`\x00` byte = Non-friable (bit 0, controller index 0)
- `@` (0x40) byte = Friable (bit 1, controller index 1)

---

## Chain 3 — Item__c: ACM_Classification__c → ACM_Sub_Classification__c

**Controller:** `ACM_Classification__c` (ACM Product Group)
**Dependent:** `ACM_Sub_Classification__c` (ACM Product Type)

Source: `docs/reference/product-taxonomy.md` + `register_taxonomy.*.json`

### NON-FRIABLE Product Groups

#### Cement products → ACM Product Types
Ceiling Tiles, Cement Flue, Cement Pipe, Cement Strapping, Communications Pit, Compressed Flat Sheeting, Contaminated Soil (Non-friable Debris), Corrugated Roof Sheeting, Debris, Dust, Dust and Debris, Electrical Arc Shields, Faux Brick Cladding, Faux Timber Sheeting, Flat Sheeting, Flue Cap, Internal Lining, Laminated Cement Sheeting (Tilux), Moulded Sheet, Pebble Rendered Cement Sheeting, Profiled Roof Sheeting, Rainwater Guttering, Ridge Capping, Roof Tiles, Toilet Cisterns, Unknown, Valley Gutters, Vents, Water Tanks, Weatherboards

#### Bitumen products → ACM Product Types
Acoustic Pad, Adhesive or Glue, Asphalt, Bitumen Coated Paper, Bitumen Coated Polystyrene, Bitumen Coating, Bitumen Washer, Bituminous Membrane, Bituminous adhesive (BlackJack), Brake Pads, Caulking, Compressed Electrical Panels, Contaminated Soil (Non-friable Debris), Debris, Dust, Dust and Debris, Electrical Cable Shrouding, Electrical Components, Galbestos (Asbestos coated metal sheet), Internal Lining, Malthoid, Mastic, Pipe Lagging Residues, Toilet Cisterns, Toilet Seats, Unknown, Washers/Bitumen Washers

#### Vinyl products → ACM Product Types
Contaminated Soil (Non-friable Debris), Dust, Dust and Debris, Hessian backed vinyl sheet, Millboard or paper-backed vinyl sheet, Unknown, Vinyl sheet, Vinyl sheet and adhesive, Vinyl tiles, Vinyl tiles and adhesive

#### Gasket, friction products and adhesives → ACM Product Types
Brake pads, CAF gasket(s), CAF gasket debris, Caulking, Clutch Plates, Contaminated Soil (Non-friable Debris), Debris, Dust and Debris, Gland Packing, Gasket(s), Gasket debris, Mastic, Putty, Rope or Braided Gasket, Rubber Gasket, Rubber Products, Silicone, Unknown, Washers

#### Coatings → ACM Product Types
Contaminated Soil (Non-friable Debris), Debris, Dust and Debris, Paint, Textured Coating, Unknown

#### Reinforced plastics/resins (excluding bitumen products) → ACM Product Types
Compressed Electrical Panels, Contaminated Soil (Non-friable Debris), Debris, Dust, Dust and Debris, Electrical Components, Plastic, Resinous Block, Rubber Products, Toilet Cisterns, Toilet Seats, Unknown, Water Tanks

#### Other → ACM Product Types
Cardboard, Concrete levelling compound, Contaminated Carpet Underlay, Contaminated Materials, Contaminated Soil (Non-friable Debris), Debris, Dust, Dust and Debris, Fibrous Material, Fire brick, Fire curtains, Gauze mats, Granular Material, Grout, Masonry, Mattresses, Mineral Fibre Tiles, Mortar, Naturally Occurring, Paper, Plaster, Putty, Render, Resinous Block, Terrazzo, Unknown

#### Insulation Products → ACM Product Types
Acoustic pad, Calico Wrap, Ceiling Tiles, Ceramic Fibre, Contaminated Soil (Non-friable Debris), Debris, Doonas, Dust, Dust and Debris, Electrical Arc Shields, Electrical Cable Shrouding, Electrical Components, Fire Door Core, Fire Rating Material, Fireproof Pillows, Foam Insulation, Gauze Mats, Gland Packing, Hessian, Horsehair, Insulation, Insulation Product Dust and Debris, Internal Insulation (Suspected), Internal Lining, Lagging, Limpet (Sprayed Insulation), Loose Fill Insulation, Low Density Asbestos Fibre Board (AIB), Millboard, Millboard or paper-backed vinyl sheet, Pipe Lagging Residues, SMF, SMF Insulation, Sprayed Insulation, Sprayed insulation (Limpet), Strawboard, Strawboard lined with millboard, Strawboard with cement sheet lining, Tape, Unknown, Vermiculite

#### Textiles → ACM Product Types
Calico Wrap, Carpet, Cloth, Contaminated Carpet Underlay, Contaminated Materials, Doonas, Fire blanket, Fire curtains, Fire-fighting clothing, Gauze mats, Gloves, Hessian, Horsehair, Mattresses, Paper, Polyester, Rope and String, Woven product

---

### FRIABLE Product Groups

#### Cement products (f) → ACM Product Types
Ceiling Tiles, Cement Flue, Cement Pipe, Cement Strapping, Communications Pit, Compressed Flat Sheeting, Contaminated Soil (Friable Debris), Corrugated Roof Sheeting, Debris, Dust, Dust and Debris, Electrical Arc Shields, Faux Brick Cladding, Faux Timber Sheeting, Flat Sheeting, Flue Cap, Internal Lining, Laminated Cement Sheeting (Tilux), Moulded Sheet, Pebble Rendered Cement Sheeting, Profiled Roof Sheeting, Rainwater Guttering, Ridge Capping, Roof Tiles, Toilet Cisterns, Unknown, Valley Gutters, Vents, Water Tanks, Weatherboards

#### Vinyl products (f) → ACM Product Types
Contaminated Soil (Friable Debris), Debris, Dust, Dust and Debris, Hessian backed Vinyl sheet, Millboard or paper-backed vinyl sheet, Unknown, Vinyl sheet, Vinyl sheet and adhesive, Vinyl Tiles, Vinyl tiles and adhesive

#### Insulation products (f) → ACM Product Types
AIB (Asbestos Insulated Board), Calico Wrap, Ceiling Tiles, Ceramic Fibre, Contaminated Soil (Friable Debris), Debris, Doonas, Dust, Dust and Debris, Electrical Arc Shields, Electrical Cable Shrouding, Electrical Components, Fibrous Material, Fire Brick, Fire Door Core, Fire Rating Material, Fireproof Pillows, Foam Insulation, Gauze Mats, Gland Packing, Hessian, Horsehair, Insulation, Insulation Product Dust and Debris, Internal Insulation (Suspected), Internal Lining, Lagging, Limpet, Loose Fill Insulation, Low Density Asbestos Fibre Board (AIB), Mattresses, Millboard, Pipe Lagging Residues, SMF Insulation, Sprayed Insulation, Strawboard, Tape, Unknown, Vermiculite

#### Gasket, friction products and adhesives (f) → ACM Product Types
Adhesive or Glue, Brake Pads, CAF gasket(s), CAF gasket debris, Caulking, Clutch Plates, Contaminated Soil (Friable Debris), Debris, Dust, Dust and Debris, Flange Gaskets, Gasket Debris, Gasket(s), Gland Packing, Mastic, Putty, Rope and String, Rope or Braided Gasket, Rubber Gasket, Unknown

#### Textiles (f) → ACM Product Types
Cloth, Fire blanket, Fire-fighting clothing, Gloves, Paper, Rope and String

#### Other (f) → ACM Product Types
Cardboard, Ceiling Tiles, Concrete Levelling Compound, Contaminated Carpet Underlay, Contaminated Materials, Contaminated Soil (Friable Debris), Debris, Dust, Dust and Debris, Fibrous Material, Granular Material, Grout, Masonry, Mattresses, Mineral Fibre Tiles, Mortar, Naturally Occurring, Plaster, Render, Resinous Block, Terrazzo, Unknown

#### Bitumen products (f) → ACM Product Types
*(Same as non-friable Bitumen products — no separate BAR friable bitumen category)*
Acoustic Pad, Asphalt, Bitumen Coated Paper, Bitumen Coating, Bitumen Washer, Bituminous adhesive (BlackJack), Bituminous Membrane, Malthoid

#### Coatings (f) → ACM Product Types
*(Same as non-friable Coatings — no separate BAR friable coatings category)*
Paint, Textured Coating, Debris, Dust, Dust and Debris, Unknown

#### Reinforced plastics/resins (excluding bitumen products) (f) → ACM Product Types
*(Same as non-friable — no separate BAR friable plastics/resins category)*
Compressed Electrical Panels, Electrical Components, Plastic, Resinous Block, Rubber Products, Unknown

---

## Important Notes for AI Extraction

### 1. Negative Result Cascade (Business Rule)
When `Sample_Analysis_Result_Material_Status__c = "Negative"` or `"Assumed Negative"`:
- Set `Condition__c = "N/A (negative)"` or `"N/A (assumed negative)"`
- Set `Disturbance_Potential_of_Material__c = "N/A (negative)"` or `"N/A (assumed negative)"`

### 2. Product Type Overlap
Many ACM Product Types appear under multiple Product Groups (e.g., "Debris", "Dust", "Unknown"). The AI must select based on the primary material classification of the ACM, not just the product type name.

### 3. Friable BAR Taxonomy Differences
The BAR taxonomy for Friable differs from Non-Friable in ordering and coverage:
- Non-Friable: T1=Cement, T2=Bitumen, T3=Vinyl, T4=Gasket, T5=Coatings, T6=Plastics, T7=Other, T8=Insulation
- Friable: T1=Cement, T2=Vinyl, T3=Insulation, T4=Gasket, T5=Textiles, T6=Other
- Friable BAR has NO Bitumen, Coatings, Plastics groups (Salesforce has them as catch-all)

### 4. Textiles (Non-Friable)
`Textiles` exists as a Salesforce ACM_Classification value for Non-Friable items but is NOT in the BAR non-friable taxonomy. Items classified as non-friable textiles typically map to `Other` or `Insulation Products` in practice.

### 5. Data Issue in register_taxonomy.nonfriable.json
The `primary_classification` field in the JSON file is rotated incorrectly. The `product_group_header` field is the correct label. Use `product-taxonomy.md` as the authoritative reference.

---

## Quick Reference: Validation Rules

| Field | Depends On | Rule |
|-------|-----------|------|
| `ACM_Classification__c` | `Friability_of_Material__c` | Values with `(f)` suffix require Friable; without require Non-friable |
| `ACM_Sub_Classification__c` | `ACM_Classification__c` | Product Type must be in the list for its Product Group |
| `Building_Category__c` | `Building_Type__c` | Category must match the type's category group |
| `Condition__c` | `Sample_Analysis_Result_Material_Status__c` | If Negative → must be N/A variant |
| `Disturbance_Potential_of_Material__c` | `Sample_Analysis_Result_Material_Status__c` | If Negative → must be N/A variant |
