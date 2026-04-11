# Extraction Test Report — 2026-04-09

## Test Configuration
- **PDF**: broadmeadows-police-station-samp.pdf
- **Model**: Hybrid (Docling table extraction + Ollama llama3.1:8b AI extraction)
- **Expected Records**: 31 (20 Negative, 5 Positive, 6 Assumed Positive)
- **Source ID**: `source:gn4mity61x2pcil3rjtv`
- **Extraction Backend**: Docling 2.x (8 tables across pages 2, 4, 5, 6, 7, 11, 12, 13)
- **Extraction Method**: `hybrid` (with corrective RAG, TOC extraction, building inventory enabled)

## Upload Results

```json
{
  "id": "source:gn4mity61x2pcil3rjtv",
  "status": "new",
  "command_id": "command:mc0fgjqg9rypx36nhgas",
  "processing_info": { "async": true, "queued": true }
}
```

## Extraction Progress

| Stage | Time | Notes |
|-------|------|-------|
| Upload | 21:43:05 | PDF queued for processing |
| Source processing start | 21:43:05 | Docling + text extraction |
| Source processing complete | 21:50:16 | 421 seconds (7 min) |
| ACM extraction triggered | 21:50:22 | Command: `command:kzcaeiue40v1a5a6sdcs` |
| First building detected | ~21:51:35 | 1 building, 0 records |
| Records populated | ~21:55:41 | 57 records, 1 building |
| ACM extraction complete | ~21:55:41 | 306 seconds (5 min) |
| **Total wall clock time** | **~727 seconds (~12 minutes)** | Source + ACM extraction |

## Results

### Buildings Extracted

| Building ID | Name | Agency | Record Count |
|-------------|------|--------|--------------|
| B001 | (null) | Victoria Police | 57 |

### ACM Records — Quantity vs Expected

| Metric | Expected | Actual | Delta |
|--------|----------|--------|-------|
| **Total Records** | 31 | 57 | +26 |
| Buildings | 1 | 1 | 0 |
| Negative results | 20 | 31 | +11 |
| Positive results | 5 | 9 | +4 |
| Assumed Positive | 6 | 1 | -5 |
| Unknown results | 0 | 16 | +16 |

### Confidence Distribution
- High: 0 / 57 (0%)
- Medium: 53 / 57 (93%)
- Low: 4 / 57 (7%)

### Field Coverage Analysis

| Field | Coverage | Notes |
|-------|----------|-------|
| `product` | 100% (57/57) | Always populated |
| `result` | 100% (57/57) | But wrong categories (Unknown vs Assumed Positive) |
| `area_type` | 100% (57/57) | Internal/External |
| `sample_no` | 77% (44/57) | Good coverage |
| `floor_level` | 56% (32/57) | Partial coverage |
| `room_name` | 49% (28/57) | Only for table-sourced records |
| `friable` | 28% (16/57) | Low coverage |
| `material_condition` | 28% (16/57) | Low coverage |
| `acm_labelled` | **0% (0/57)** | **MISSING — critical field** |
| `quantity` | **0% (0/57)** | **MISSING — critical field** |
| `risk_status` | **0% (0/57)** | **MISSING — critical field** |

## Ground Truth Matching Analysis

Comparing extracted records against the 12 detailed ground truth records in the expected results:

| Row | Expected Room | Expected Product | Expected Result | Extracted Match | Quality |
|-----|--------------|-----------------|-----------------|-----------------|---------|
| 1 | Main Foyer | Floor covering | Negative | [30] Negative | **FULL** |
| 2 | Front Desk Area | Floor covering | Negative | [31] Negative | **FULL** |
| 3 | Front Desk Area | Filing Cabinet | Assumed Positive | [32] **Unknown** | PARTIAL |
| 4 | Soft Interview Room No.2 | Skirting | Negative | [33] Negative | **FULL** |
| 8 | Switch Room | Fuse cartridge | Assumed Positive | [37] **Unknown** | PARTIAL |
| 11 | Fan Room | Flange joints | Positive | [39] Positive | **FULL** |
| 12 | Fan Room | Infill panels | Positive | [40] Positive | **FULL** |
| 18 | Fan Room 2.24 | Flange joints | Positive | [39] Positive (wrong room) | PARTIAL |
| 21 | Boiler Room | Fuse cartridge | Assumed Positive | [49] **Unknown** | PARTIAL |
| 26 | Roof | Flange joints | Positive | Best: [39] Fan Room | PARTIAL |
| 30 | Lift Foyer | Internal lining | Assumed Positive | [36] Vinyl sheet **Negative** | PARTIAL |
| 31 | Main Foyer | Unknown | Assumed Positive | [30] **Negative** | PARTIAL |

**Summary**: 5 FULL matches, 7 PARTIAL matches, 0 complete misses (out of 12 detailed records)

## Key Issues Found

### 1. Assumed Positive → Unknown Mapping Failure (CRITICAL)
All 6 expected "Assumed Positive" records are being extracted as "Unknown".
- Filing Cabinet (Front Desk) → Unknown
- Fuse cartridge (Switch Room) → Unknown
- Fuse cartridge (Boiler Room) → Unknown
- Internal lining (Lift Foyer) → missed/wrong result
- Main Foyer Unknown → missed

The LLM is not recognizing "Assumed Positive" as a distinct ACM classification. This is the same bug listed in `critical_bugs` from the expected results file.

### 2. Over-Extraction (57 vs 31 records)
Records 1-29 have no `room_name` and come from different table types (material tables, summary tables, diagnostic tables). These are noise records that shouldn't be in the final count.

The 28 records with `room_name` (records 30-57) are more representative, but still contain duplicates (e.g., records 39, 41, 43 all reference Fan Room Flange mastic).

### 3. Missing Critical Fields
Three critical fields are completely absent:
- **`acm_labelled`**: YES/NO flag — 0% extraction
- **`quantity`**: Item count — 0% extraction
- **`risk_status`**: Low/Medium/High — 0% extraction

These were also listed as critical bugs in the original baseline test from 2026-02-10.

### 4. Product Name Divergence
Products extracted don't exactly match expected ground truth:
- Expected "Flange joints" → Extracted "Flange mastic (grey)"
- Expected "Infill panels" → Extracted "Fibre cement sheet infill panel"
- Expected "Fuse cartridge" → Extracted "Fuses"

This is acceptable terminology variation but makes automated matching harder.

### 5. Room-Level Deduplication Needed
For Fan Room, there are 4 extracted records (39, 40, 41, 43) where expected has 2 (rows 11, 12). Records 41 and 43 appear to be duplicates of record 39.

## Trace Analysis

No Langfuse trace URL available (self-hosted). Key metadata from extraction result:
```json
{
  "extraction_method": "ai",
  "processing_time": 306.6,
  "records_created": 57,
  "records_embedded": 57,
  "confidence_distribution": {"high": 0, "low": 4, "medium": 53}
}
```

Extraction settings:
```json
{
  "extraction_method": "hybrid",
  "fallback_enabled": true,
  "enable_toc_extraction": true,
  "enable_building_inventory": true,
  "enable_page_tagging": true,
  "enable_metadata_enhancement": true,
  "enable_corrective_rag": true,
  "max_correction_attempts": 2
}
```

## Comparison with Baseline

| Metric | Baseline (2026-02-10) | Previous Best (2026-02-22) | Current (2026-04-09) |
|--------|----------------------|--------------------------|----------------------|
| Records extracted | 8 | 25 | 57 |
| Record count accuracy | 26% (8/31) | 81% (25/31) | ~55% (28 with rooms / 31) |
| Negative coverage | 0% | ~80%+ | 155% (31 vs 20 expected — over-extraction) |
| Positive coverage | 80% | ~90%+ | 180% (9 vs 5 — over-extraction) |
| Assumed Positive coverage | 50% | ~70%+ | 17% (1/6 — **regression**) |
| acm_labelled | Missing | Missing | Missing |
| quantity | Missing | Missing | Missing |

**Assessment**: The current run shows **regression on Assumed Positive** classification (from ~70% to 17%) despite overall record count being much higher. The over-extraction (57 vs 31) indicates noise from non-ACM tables being included. The 28 records with room_name are more aligned with expectations but still have critical result classification issues.

## Recommendations

### Priority 1 (Immediate — Blocks Accuracy)
1. **Fix "Assumed Positive" detection**: The LLM prompt must explicitly define "Assumed Positive" as an ACM result category distinct from "Unknown". Add examples to the row extraction prompt (`prompts/acm/row_extraction.jinja`).

2. **Add `acm_labelled`, `quantity`, `risk_status` to extraction schema**: These fields have been missing since the baseline test (2026-02-10). Check `open_notebook/domain/acm_row_schemas.py` to add these fields.

### Priority 2 (Quality)
3. **Filter non-ACM tables**: Implement table classification to exclude summary tables, TOC tables, and diagnostic tables. Only extract from main ACM register tables.

4. **Deduplicate records**: Implement deduplication by (room_name, product, result) tuple within the same building.

### Priority 3 (Refinement)
5. **Product name normalization**: Map common variations (e.g., "Fuses" → "Fuse cartridge", "Flange mastic" → "Flange joints") via the normalizer enums.

6. **Increase confidence threshold**: Only 0% high-confidence records. Review the confidence scoring in the extraction pipeline.

## Browser Verification (Secondary)

### Frontend Status
- **Frontend URL**: http://localhost:8503 (dev mode, via `next dev -p 8503`)
- **Backend proxy**: Working (`/api/*` → `http://localhost:5055` ✓)
- **Page rendering**: BROKEN — 500 Internal Server Error on all dashboard pages

### Root Cause: Missing Vendor Chunks
The Next.js dev server at port 8503 is running from a **different repo clone**:
- Serving from: `/home/demi/gitrepo/acm-ai/frontend/` (separate WSL clone)
- Working directory: `/mnt/d/ailocal/acm-ai/` (Windows mount)

The build in the serving clone is **corrupted/incomplete**. The compiled page bundles reference vendor chunks that were never generated:
```
Error: Cannot find module './vendor-chunks/streamdown.js'
```

Required vendor chunks (50+ packages including `streamdown`, `@copilotkit`, `ag-grid-community`, `zod`, `katex`, etc.) are missing. Only 3 of the required vendor chunks exist:
- `@swc.js`, `lucide-react.js`, `next.js`

### Port Discrepancy
| Expected (CLAUDE.md) | Actual |
|---------------------|--------|
| Frontend: http://localhost:8502 | Frontend: http://localhost:8503 |
| Port 8502: "Internal Server Error" | Port 8503: Next.js dev (broken build) |

### Screenshots Taken
- `docs/sprint-artifacts/reports/screenshots/01-jobs-page.png` — Port 8502 returns 500 (blank page)
- `docs/sprint-artifacts/reports/screenshots/02-jobs-page-loaded.png` — Port 8503 "Connecting to server" (JS not loading)
- `docs/sprint-artifacts/reports/screenshots/03-job-detail-page.png` — Port 8503 shows Next.js Runtime Error overlay

### Fix Required
Rebuild the frontend in the serving clone:
```bash
cd /home/demi/gitrepo/acm-ai && git pull
cd frontend && npm install && npm run build
```
Or restart dev server (from Windows): `start-all.bat`

**Note**: The extraction test results (57 records, API verified) are valid despite the frontend being broken. The backend API at port 5055 is fully functional.

## Evidence
- Source ID: `source:gn4mity61x2pcil3rjtv`
- Report generated: 2026-04-09
- Extraction took ~12 minutes total (7 min Docling + 5 min AI)
- Raw extractions: 8 Docling tables (pages 2, 4, 5, 6, 7, 11, 12, 13)
- Screenshots: `docs/sprint-artifacts/reports/screenshots/`
