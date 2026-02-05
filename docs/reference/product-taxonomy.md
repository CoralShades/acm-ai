# ACM Product Taxonomy Reference

> **Version:** 1.0
> **Date:** 2026-02-05
> **Source:** Victorian BAR APPENDIX A & B sheets

This document defines the official ACM product classification taxonomy for Victorian Building Asbestos Registers.

---

## Overview

ACM products are classified into two main categories based on friability:

| Category | Groups | Description |
|----------|--------|-------------|
| **Non-Friable** | T1-T8 | ACM where fibers are bound in a matrix (cement, vinyl, etc.) |
| **Friable** | T1-T6 | ACM that can be crumbled by hand pressure |

---

## Non-Friable Taxonomy (T1-T8)

### T1: Cement Products
```json
{
  "pc_code": "T1",
  "primary_classification": "Cement products",
  "product_types": [
    "Ceiling Tiles",
    "Cement Flue",
    "Cement Pipe",
    "Cement Strapping",
    "Communications Pit",
    "Compressed Flat Sheeting",
    "Contaminated Soil (Non-friable Debris)",
    "Corrugated Roof Sheeting",
    "Debris",
    "Dust",
    "Dust and Debris",
    "Electrical Arc Shields",
    "Faux Brick Cladding",
    "Faux Timber Sheeting",
    "Flat Sheeting",
    "Flue Cap",
    "Internal Lining",
    "Laminated Cement Sheeting",
    "Moulded Sheet",
    "Pebble Rendered Cement Sheeting",
    "Profiled Roof Sheeting",
    "Rainwater Guttering",
    "Ridge Capping",
    "Roof Tiles",
    "Toilet Cisterns",
    "Unknown",
    "Valley Gutters",
    "Vents",
    "Water Tanks",
    "Weatherboards"
  ]
}
```

### T2: Bitumen Products
```json
{
  "pc_code": "T2",
  "primary_classification": "Bitumen products",
  "product_types": [
    "Acoustic Pad",
    "Adhesive or Glue",
    "Asphalt",
    "Bitumen Coated Paper",
    "Bitumen Coated Polystyrene",
    "Bitumen Coating",
    "Bitumen Washer",
    "Bituminous Membrane",
    "Blackjack (Bitumen Adhesive)",
    "Brake Pads",
    "Caulking",
    "Circuit Breaker",
    "Compressed Electrical Panels",
    "Contaminated Soil (Non-friable Debris)",
    "Debris",
    "Dust",
    "Dust and Debris",
    "Electrical Cable Shrouding",
    "Electrical Components",
    "Electrical Meters",
    "Galbestos",
    "Internal Lining",
    "Malthoid",
    "Mastic",
    "Pipe Lagging Residues",
    "Toilet Cisterns",
    "Toilet Seats",
    "Unknown",
    "Washers"
  ]
}
```

### T3: Vinyl Products
```json
{
  "pc_code": "T3",
  "primary_classification": "Vinyl products",
  "product_types": [
    "Contaminated Soil (Non-friable Debris)",
    "Dust",
    "Dust and debris",
    "Hessian backed Vinyl sheet",
    "Linoleum (use Vinyl sheet for descriptor)",
    "Millboard/paper-backed sheet vinyl",
    "Unknown",
    "Vinyl product debris",
    "Vinyl sheet and adhesive",
    "Vinyl sheet",
    "Vinyl tiles and adhesive",
    "Vinyl Tiles"
  ]
}
```

### T4: Gasket, Friction Products and Adhesives
```json
{
  "pc_code": "T4",
  "primary_classification": "Gasket, friction products and adhesives",
  "product_types": [
    "Brake pads",
    "Caulking",
    "Clutch Plates",
    "Contaminated Soil (Non-friable Debris)",
    "Debris",
    "Dust and Debris",
    "Flange Gaskets",
    "Gasket Debris",
    "Gasket(s)",
    "Mastic",
    "Putty",
    "Rope or Braided Gasket",
    "Rubber Gasket",
    "Rubber Products",
    "Silicone",
    "Unknown",
    "Washers"
  ]
}
```

### T5: Coatings
```json
{
  "pc_code": "T5",
  "primary_classification": "Coatings",
  "product_types": [
    "Contaminated Soil (Non-friable Debris)",
    "Debris",
    "Dust and Debris",
    "Paint",
    "Textured Coating",
    "Unknown"
  ]
}
```

### T6: Reinforced Plastics/Resins
```json
{
  "pc_code": "T6",
  "primary_classification": "Reinforced plastics/resins (excluding bitumen products)",
  "product_types": [
    "Compressed Electrical Panels",
    "Contaminated Soil (Non-friable Debris)",
    "Debris",
    "Dust",
    "Dust and Debris",
    "Electrical Components",
    "Electrical Meters",
    "Plastic",
    "Radiator and sink tap hand wheels",
    "Resinous Block",
    "Rubber Products",
    "Stair Nosing",
    "Toilet Cisterns",
    "Toilet Seats",
    "Unknown",
    "Water Tanks"
  ]
}
```

### T7: Other
```json
{
  "pc_code": "T7",
  "primary_classification": "Other",
  "product_types": [
    "Cardboard",
    "Concrete/levelling compound",
    "Contaminated Carpet Underlay",
    "Contaminated Materials",
    "Contaminated Soil (Non-friable Debris)",
    "Debris",
    "Dust",
    "Dust and Debris",
    "Fibrous Material",
    "Fire brick",
    "Fire curtains",
    "Gauze mats",
    "Granular Material",
    "Grout",
    "Masonry",
    "Mattresses",
    "Mineral Fibre Tiles",
    "Mortar",
    "Naturally Occurring",
    "Paper",
    "Plaster",
    "Putty",
    "Render",
    "Resinous Block",
    "Terrazzo",
    "Unknown"
  ]
}
```

### T8: Insulation
```json
{
  "pc_code": "T8",
  "primary_classification": "Insulation",
  "product_types": [
    "Calico Wrap",
    "Ceiling Tiles",
    "Ceramic Fibre",
    "Contaminated Soil (Non-friable Debris)",
    "Debris",
    "Doonas",
    "Dust",
    "Dust and Debris",
    "Electrical Arc Shields",
    "Electrical Cable Shrouding",
    "Electrical Components",
    "Fire Door Core",
    "Fire Rating Material",
    "Fireproof Pillows",
    "Foam Insulation",
    "Gauze Mats",
    "Gland Packing",
    "Hessian",
    "Horsehair",
    "Insulation",
    "Insulation Product Dust and Debris",
    "Internal Insulation (Suspected)",
    "Internal Lining",
    "Lagging",
    "Limpet",
    "Loose Fill Insulation",
    "Low Density Asbestos Fibre Board (Asbestos Insulated Board)",
    "Millboard",
    "Pipe Lagging Residues",
    "SMF Insulation",
    "Strawboard",
    "Tape",
    "Unknown",
    "Vermiculite"
  ]
}
```

---

## Friable Taxonomy (T1-T6)

### T1: Cement Products (Friable)
```json
{
  "pc_code": "T1",
  "primary_classification": "Cement products (f)",
  "product_types": [
    "Ceiling Tiles",
    "Cement Flue",
    "Cement flues/pipes",
    "Cement Pipe",
    "Cement Strapping",
    "Communications Pit",
    "Compressed Flat Sheeting",
    "Contaminated Soil (Friable Debris)",
    "Corrugated Roof Sheeting",
    "Debris",
    "Dust",
    "Dust and Debris",
    "Electrical Arc Shields",
    "Faux Brick Cladding",
    "Faux timber panelling/sheeting",
    "Faux Timber Sheeting",
    "Flat Sheeting",
    "Flue Cap",
    "Flue capping",
    "Internal Lining",
    "Laminated Cement Sheeting",
    "Moulded Sheet",
    "Pebble Rendered Cement Sheeting",
    "Profiled Roof Sheeting",
    "Rainwater Guttering",
    "Ridge capping",
    "Roof products (excluding sheeting)",
    "Roof Tiles",
    "Roof tiles/slates asbestos roof tiles",
    "Tilux sheeting",
    "Toilet Cisterns",
    "Unknown",
    "Valley Gutters",
    "Vents",
    "Water Tanks",
    "Weatherboards"
  ]
}
```

### T2: Vinyl Products (Friable)
```json
{
  "pc_code": "T2",
  "primary_classification": "Vinyl products (f)",
  "product_types": [
    "Millboard/paper-backed sheet vinyl",
    "Vinyl sheet",
    "Vinyl sheet and adhesive",
    "Vinyl Tiles",
    "Vinyl tiles and adhesive",
    "Debris",
    "Dust",
    "Dust and debris",
    "Hessian backed Vinyl sheet",
    "Unknown",
    "Contaminated Soil (Friable Debris)"
  ]
}
```

### T3: Insulation Products (Friable)
```json
{
  "pc_code": "T3",
  "primary_classification": "Insulation products (f)",
  "product_types": [
    "AIB (insulation board)",
    "Calico Wrap",
    "Ceiling Tiles",
    "Ceramic Fibre",
    "Contaminated Soil (Friable Debris)",
    "Debris",
    "Doonas",
    "Dust",
    "Dust and Debris",
    "Electrical Arc Shields",
    "Electrical Cable Shrouding",
    "Electrical Components",
    "Fibrous Material",
    "Fire Brick",
    "Fire Door Core",
    "Fire Rating Material",
    "Fireproof bags/pillows",
    "Fireproof Pillows",
    "Foam Insulation",
    "Gauze Mats",
    "Gland Packing",
    "Hessian",
    "Horsehair",
    "Insulation",
    "Insulation board",
    "Insulation Product Dust and Debris",
    "Internal Insulation (Suspected)",
    "Internal Lining",
    "Lagging",
    "Lagging (thermal Insulation)",
    "Limpet",
    "Loose Fill Insulation",
    "Low Density Asbestos Fibre Board (Asbestos Insulated Board)",
    "Mattresses",
    "Millboard",
    "Pipe Lagging Residues",
    "Pipe lagging residues (to walls, ceilings, pipework)",
    "SMF Insulation",
    "Sprayed Insulation",
    "Sprayed insulation (not limpet or vermiculite)",
    "Strawboard",
    "Tape",
    "Unknown",
    "Vermiculite"
  ]
}
```

### T4: Gasket Products (Friable)
```json
{
  "pc_code": "T4",
  "primary_classification": "Gasket products (f)",
  "product_types": [
    "Adhesive or Glue",
    "Brake pads",
    "Caulking",
    "Clutch Plates",
    "Contaminated Soil (Friable Debris)",
    "Debris",
    "Dust",
    "Dust and Debris",
    "Flange Gaskets",
    "Gasket Debris",
    "Gasket(s)",
    "Mastic",
    "Putty",
    "Rope and String",
    "Rope or Braided Gasket",
    "Rubber Gasket",
    "Unknown"
  ]
}
```

### T5: Textiles (Friable)
```json
{
  "pc_code": "T5",
  "primary_classification": "Textiles (f)",
  "product_types": [
    "Cloth",
    "Fire blanket",
    "Fire-fighting clothing",
    "Gloves",
    "Paper",
    "Rope and string"
  ]
}
```

### T6: Other (Friable)
```json
{
  "pc_code": "T6",
  "primary_classification": "Other (f)",
  "product_types": [
    "Cardboard",
    "Ceiling tiles",
    "Concrete Levelling Compound",
    "Contaminated Carpet Underlay",
    "Contaminated Materials",
    "Contaminated Soil (Friable Debris)",
    "Debris",
    "Dust",
    "Dust and Debris",
    "Fibrous Material",
    "Granular Material",
    "Grout",
    "Masonry",
    "Mattresses",
    "Mineral Fibre Tiles",
    "Mortar",
    "Naturally Occurring",
    "Plaster",
    "Plaster/lath",
    "Render",
    "Resinous Block",
    "Terrazzo",
    "Unknown"
  ]
}
```

---

## Classification Algorithm

### Pattern-Based Classification

```python
CLASSIFICATION_PATTERNS = [
    # Vinyl products
    (r"vinyl\s*(sheet|flooring)", "Friable" if friable else "Non-friable", "T3", "Vinyl sheet"),
    (r"vinyl\s*tile", "Friable" if friable else "Non-friable", "T3", "Vinyl Tiles"),
    (r"hessian\s*back", "Friable" if friable else "Non-friable", "T3", "Hessian backed Vinyl sheet"),
    (r"linoleum", "Non-friable", "T3", "Vinyl sheet"),

    # Cement products
    (r"(fibre|fiber)\s*cement", "Non-friable", "T1", "Flat Sheeting"),
    (r"fc\s*sheet|flat\s*sheet", "Non-friable", "T1", "Flat Sheeting"),
    (r"corrugated.*roof", "Non-friable", "T1", "Corrugated Roof Sheeting"),
    (r"weatherboard", "Non-friable", "T1", "Weatherboards"),
    (r"cement\s*flue", "Non-friable", "T1", "Cement Flue"),

    # Gasket products
    (r"mastic|flange.*mastic", "Non-friable", "T4", "Mastic"),
    (r"gasket", "Non-friable", "T4", "Gasket(s)"),
    (r"caulking", "Non-friable", "T4", "Caulking"),

    # Insulation
    (r"lagging", "Friable", "T3", "Lagging"),
    (r"insulation", "Friable", "T3", "Insulation"),
    (r"millboard", "Non-friable", "T8", "Millboard"),
    (r"vermiculite", "Friable", "T3", "Vermiculite"),

    # Bitumen products
    (r"bitumen|bituminous", "Non-friable", "T2", "Bituminous Membrane"),
    (r"malthoid", "Non-friable", "T2", "Malthoid"),

    # Electrical
    (r"fuse|electrical.*component", "Non-friable", "T2", "Electrical Components"),
    (r"switchboard", "Non-friable", "T2", "Compressed Electrical Panels"),
]
```

### LLM Fallback Classification

For items that don't match patterns, use LLM with few-shot examples:

```python
CLASSIFICATION_PROMPT = """
Classify this ACM item into the correct Product Group and Product Type.

Item Description: {item_description}
Friability: {friability}

Available groups:
- T1: Cement products (flat sheeting, corrugated, roof tiles)
- T2: Bitumen products (mastic, membrane, electrical)
- T3: Vinyl products (sheet, tiles, hessian backed)
- T4: Gasket products (flange gaskets, caulking, rope)
- T5: Coatings (paint, textured coating)
- T6: Plastics/resins (electrical components, toilet cisterns)
- T7: Other (mortar, grout, plaster)
- T8: Insulation (lagging, millboard, fire door core)

For Friable items, use the friable-specific taxonomy (T1-T6).

Respond with JSON: {"product_group": "T3 Vinyl products", "product_type": "Vinyl sheet"}
"""
```

---

## Usage in ACM-AI

### Classification Integration

```python
from open_notebook.extraction.normalizers.taxonomy import classify_product

# During Stage 2 interpretation
raw_item = RawACMItem(
    item_description="Vinyl sheet flooring (cream)",
    friability="Non-friable"
)

product_group, product_type = classify_product(
    item_description=raw_item.item_description,
    friability=raw_item.friability
)

# Result: ("T3 Vinyl products", "Vinyl sheet")
```

### Export to BAR

The taxonomy codes map directly to BAR columns:
- **AA - ACM Product Group**: Full group name (e.g., "T3 Vinyl products")
- **AB - ACM GROUP NAME EXCEL**: Display name for Excel (same as above)
- **AC - ACM Product Type**: Specific type (e.g., "Vinyl sheet")

---

## References

- Non-friable taxonomy: `docs/samplePDF/instructions-sample/register_taxonomy.nonfriable.json`
- Friable taxonomy: `docs/samplePDF/instructions-sample/register_taxonomy.friable.json`
- BAR schema: `docs/reference/bar-schema.md`
