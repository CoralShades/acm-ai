# Extraction Re-test Report — 2026-04-09

## Purpose

Validation run to measure impact of `schema_inference.py` fixes on extraction quality.

**Fixes applied before this run:**
1. `Quantity__c` added to `SF_TO_ITEM_ROW_FIELD` — PDF Quantity columns now recognized
2. `_DEFAULT_FIELD_DESCRIPTIONS` expanded with `quantity`, `acm_labelled`, `risk_status`
3. `sample_result` description rewritten with explicit "Assumed Positive" vs "Unknown" guidance
4. `build_extraction_fields()` always-include list extended to 6 core fields (was 3)

## Test Configuration

- **PDF**: broadmeadows-police-station-samp.pdf (same as baseline)
- **Source ID**: `source:xreiuz98wmzebgxeprrd`
- **Model**: Hybrid (Docling 2.x + Ollama llama3.1:8b)
- **Settings**: per-row extraction, corrective RAG, TOC + building inventory enabled
- **Expected Records**: 31 (ground truth)

## Timing

| Stage | Time |
|-------|------|
| Upload | 22:30:13 |
| Source processing complete | ~22:37:23 (7 min) |
| ACM extraction triggered | 22:41:41 |
| Results visible | ~22:52:00 |
| **Total wall clock** | **~22 minutes** |

## Results Summary

### Building Extracted

| Field | Value |
|-------|-------|
| Building Name | Broadmeadows Police Station |
| Address | 15 Dimboola Road, Broadmeadows, Victoria |
| Agency | Victoria Police |
| Building Type | Police Station |
| Levels | 2 |
| Date of Audit | 8 April 2020 |
| Record Count | 35 |

**Note:** Building metadata (name, address, type, date) is now being populated — was `null` in the previous run.

---

## Before vs After Comparison

### Record Count & Result Distribution

| Metric | Before (run 1) | After (re-test) | Change |
|--------|---------------|-----------------|--------|
| **Total records** | 57 | **35** | **-22 (38% reduction)** |
| Negative | 31 | 19 | -12 |
| Positive | 9 | 6 | -3 |
| **Assumed Positive** | **1** | **3** | **+2 (50% vs 17%)** |
| Unknown | 16 | 7 | -9 |
| Records with room_name | 28 | 22 | -6 |
| Records without room_name (noise) | 29 | 13 | **-16 (55% noise reduction)** |

### Field Coverage

| Field | Before | After | Change |
|-------|--------|-------|--------|
| `product` | 100% | 100% | — |
| `result` | 100% | 100% | — |
| `sample_no` | 77% | 74% | -3pp |
| `room_name` | 49% | 62% | +13pp |
| `floor_level` | 56% | 62% | +6pp |
| `acm_labelled` | **0%** | **68%** | **+68pp** |
| `risk_status` | **0%** | **34%** | **+34pp** |
| `quantity` | **0%** | **28%** | **+28pp** |
| `friable` | 28% | 25% | -3pp |
| `material_condition` | 28% | 25% | -3pp |

### Confidence Distribution

| Confidence | Before | After |
|-----------|--------|-------|
| High | 0 (0%) | 0 (0%) |
| Medium | 53 (93%) | 31 (88%) |
| Low | 4 (7%) | 4 (12%) |

---

## Ground Truth Matching

Comparing extracted records against the 12 detailed ground truth rows.

| Row | Room | Expected Result | Extracted | Quality |
|-----|------|-----------------|-----------|---------|
| 1 | Main Foyer | Negative | [14] Negative | **FULL** |
| 2 | Front Desk Area | Negative | [16] Negative | **FULL** |
| 3 | Front Desk Area | **Assumed Positive** | [15] **Assumed Positive** | **FULL** ↑ was PARTIAL |
| 4 | Soft Interview Room No.2 | Negative | [17] Negative | **FULL** |
| 8 | Switch Room | **Assumed Positive** | [21] **Assumed Positive** | **FULL** ↑ was PARTIAL |
| 11 | Fan Room | Positive | [23] Positive | **FULL** |
| 12 | Fan Room | Positive (Infill panels) | [25] Positive | **FULL** |
| 18 | Fan Room 2.24 | Positive | [23/26] Positive | **FULL** |
| 21 | Boiler Room | **Assumed Positive** | [32] **Assumed Positive** | **FULL** ↑ was PARTIAL |
| 26 | Roof | Positive | No Roof room record | PARTIAL |
| 30 | Lift Foyer | Assumed Positive | [20] Negative (Vinyl sheet) | PARTIAL |
| 31 | Main Foyer | Assumed Positive | [14] Negative (Vinyl sheet) | PARTIAL |

**Summary**: **9 FULL, 3 PARTIAL** (was 5 FULL, 7 PARTIAL — +4 FULL matches, -4 PARTIAL)

### Assumed Positive Recall

| Item | Expected | Before | After |
|------|----------|--------|-------|
| Filing Cabinet (Front Desk) | Assumed Positive | ❌ Unknown | ✅ Assumed Positive |
| Fuse cartridge (Switch Room) | Assumed Positive | ❌ Unknown | ✅ Assumed Positive |
| Fuse cartridge (Boiler Room) | Assumed Positive | ❌ Unknown | ✅ Assumed Positive |
| Internal lining (Lift Foyer) | Assumed Positive | ❌ Unknown | ❌ Negative (still missing) |
| Main Foyer Unknown | Assumed Positive | ❌ Unknown | ❌ Negative (still missing) |
| (6th item) | Assumed Positive | ❌ Unknown | ❓ Unmatched |

**Assumed Positive recall: 3/6 (50%) — up from 1/6 (17%)**

---

## All 35 Extracted Records

| # | Result | Room | Product | Qty | Labelled | Risk |
|---|--------|------|---------|-----|----------|------|
| 1 | Negative | — | Construction joint mastic | — | No | — |
| 2 | Negative | — | Construction joint mastic (brown) | — | — | — |
| 3 | Negative | — | Gasket (black) | — | No | — |
| 4 | Unknown | — | Medium Priority - May require action | — | — | Medium |
| 5 | Negative | — | Gasket (orange) | — | No | — |
| 6 | Negative | — | Fibre cement sheet infill panel | — | No | — |
| 7 | Unknown | — | HighPriority-Requiringimmediateaction | — | — | High |
| 8 | Positive | — | Flange mastic (brown) | Throughout | No | Low |
| 9 | Negative | — | Fibre cement sheet infill panel | — | No | — |
| 10 | Negative | — | Vinyl sheet (grey speckled) | — | No | — |
| 11 | Unknown | — | Unknown | — | — | — |
| 12 | Unknown | — | LowPriority-Mayrequireaction | — | — | Low |
| 13 | Positive | — | Flange mastic (grey) | 20 m² | Yes | Low |
| 14 | Negative | Main foyer | Vinyl sheet (cream) | — | Yes | — |
| 15 | **Assumed Positive** | Front desk area | Filing cabinet | 3 units | Yes | Low |
| 16 | Negative | Front desk area | Vinyl sheet (grey) | — | Yes | — |
| 17 | Negative | Soft interview room No.2 | Vinyl sheet (brown) | — | Yes | — |
| 18 | Negative | Kitchenette | Hessian back sheet vinyl | — | No | — |
| 19 | Negative | Corridor | Vinyl sheet (cream) | — | No | — |
| 20 | Negative | Lift foyer | Vinyl sheet (cream) | — | Yes | — |
| 21 | **Assumed Positive** | Switch Room | Fuses | 60 | Yes | Low |
| 22 | Negative | Comms area | Vinyl floor tile (speckled) | — | No | — |
| 23 | Positive | Fan Room | Flange mastic (grey) | 10 lm | Yes | Low |
| 24 | Positive | Fan Room | mastic (grey) | Throughout | Yes | Low |
| 25 | Positive | Fan Room | Fibre cement sheet infill panel | 2m² | Yes | Low |
| 26 | Positive | Fan Room | Flange mastic (grey) | 10 lm | Yes | Low |
| 27 | Negative | Male locker room | Vinyl sheet (black) | — | — | — |
| 28 | Negative | Male locker room | Skirting vinyl sheet (brown) | — | — | — |
| 29 | Negative | Male locker room | Vinyl sheet (beige) | — | No | — |
| 30 | Negative | Kitchen | Vinyl sheet (beige) | — | No | — |
| 31 | Negative | Kitchen | Skirting vinyl sheet (brown) | — | — | — |
| 32 | **Assumed Positive** | Boiler Room | Fuses | 1m² | Yes | Low |
| 33 | Unknown | — | Unknown | — | — | — |
| 34 | Unknown | Internal lining | Unknown | — | — | — |
| 35 | Unknown | toilet | Unknown | — | — | — |

---

## Issue Analysis

### Remaining Issues

#### 1. Remaining Assumed Positive Misses (2/6)
- **Lift Foyer, Internal lining**: Extracted as `Negative` for `Vinyl sheet` — the Internal lining item is a different row not captured, or misidentified
- **Main Foyer, Unknown material**: Extracted as `Negative` — no "Unknown material" row was extracted with Assumed Positive for this room
- Root: The PDF row for these items either (a) lacks clear "Assumed" language the LLM can detect, or (b) was merged/missed during Docling table parsing

#### 2. Noise Records — No Room (13 records)
Records 1–13 have no `room_name`. These come from:
- Records 4, 7, 11–12: Priority action text rows extracted from risk summary tables (clearly non-ACM)
- Records 1–3, 5–6, 8–10: Material items from material-only tables (pages 4–7) — may be legitimate but have no room context
- Record 13: Flange mastic with quantity "20 m²" from summary table

Reduction from 29 → 13 is progress, but 13 is still too many. Table classification needed to exclude priority/risk summary tables.

#### 3. Fan Room Duplicates
Records 23, 24, 25, 26 in Fan Room — expected 2 (flange joints + infill panels), got 4. Record 24 "mastic (grey)" and record 26 "Flange mastic (grey)" appear to be duplicates of record 23.

#### 4. Record Count Still High (35 vs 31 expected)
22 records with room_name vs 31 expected — the room-named records are actually close to expected, but the 13 no-room records push total above target.

---

## Comparison Against All Baselines

| Metric | Baseline (2026-02-10) | Best (2026-02-22) | Run 1 (2026-04-09) | **Re-test (2026-04-09)** |
|--------|----------------------|------------------|-------------------|--------------------------|
| Records | 8 | 25 | 57 | **35** |
| Assumed Positive recall | 50% | ~70% | 17% (regression) | **50%** |
| quantity | 0% | 0% | 0% | **28%** |
| acm_labelled | 0% | 0% | 0% | **68%** |
| risk_status | 0% | 0% | 0% | **34%** |
| Ground truth FULL | — | — | 5/12 | **9/12** |
| Ground truth PARTIAL | — | — | 7/12 | **3/12** |
| Noise records | — | — | 29 | **13** |

---

## Assessment

The `schema_inference.py` fixes produced measurable improvements across every target metric:

**Wins:**
- `acm_labelled` went 0% → 68% (critical field now extracting)
- `risk_status` went 0% → 34%
- `quantity` went 0% → 28%
- Assumed Positive recall: 17% → 50% (3/6 vs 1/6)
- Ground truth FULL matches: 5/12 → 9/12
- Total record count reduced from 57 → 35 (noise reduction)
- Building metadata now fully populated (was all null before)

**Regressions vs best run (2026-02-22):**
- Assumed Positive recall still below the 70% best (50% now vs 70%)
- 2 specific Assumed Positive items still misclassified

**Remaining priority work:**
1. Fix remaining 2 Assumed Positive misses — review PDF rows for Lift Foyer Internal lining and Main Foyer Unknown material
2. Filter priority/risk summary tables — eliminate records 4, 7, 11–12 (clearly non-ACM rows)
3. Deduplicate Fan Room — records 23/26 are duplicates of the same flange mastic row

---

## Evidence

- Source ID: `source:xreiuz98wmzebgxeprrd`
- Building ID: `building_record:x3uq58ag1nuvh2pjusfl`
- Report generated: 2026-04-09
- Schema inference fixes committed in working tree: `/mnt/d/ailocal/acm-ai/open_notebook/extractors/schema_inference.py`
