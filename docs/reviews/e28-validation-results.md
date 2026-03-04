# E28 Validation Results — Alexander "Not Sampled" Recovery

Date: 2026-02-28
Model: anthropic/claude-sonnet-4 (via OpenRouter, Anthropic provider)

## Results

| Document | Before E28 | After E28 | Delta | Target |
|----------|-----------|-----------|-------|--------|
| Broadmeadows | 31/31 (100%) | 31/31 (100%) | 0 | 31/31 |
| Alexander | 29/43 (67.4%) | 36/43 (83.7%) | +7 | >=40/43 |

### Alexander Per-Category Breakdown

| Category | Before | After | Delta |
|----------|--------|-------|-------|
| NATA-sampled | ~19/19 | 18/19 | -1 |
| As Per | ~5/7 | 7/7 | +2 |
| Not Sampled | ~5/17 | 11/17 | +6 |

## Missing Records Recovered (by ARA regex fallback)

8 records recovered by `_recover_not_sampled_records_ara()`:

1. **Exterior / Eaves / Eaves** (item 16, VMO Accommodations) — Height Restricted
2. **Roof / Ductwork / Ductwork** (item 19, Old Alexandra Hospital) — Height Restricted
3. **CCSD - Entry / Fire Door** (item 32, Old Alexandra Hospital) — Restricted Access
4. **Former Laundry - External Passage / Electrical Distribution Board** (item 40) — Live Electrical Hazard
5. **Multi Purpose Area - Adjacent CCSD / Fire Door** (item 44) — Restricted Access
6. **Store Offices / Ceiling / Ceiling** (item 54) — Height Restricted
7. **Ward 12 / Shower Cubicle** (item 57) — Restricted Access
8. **West Passage - Adjacent CCSD / Fire Door** (item 58) — Restricted Access

## Still Missing (7 records)

| # | Room | Location | Item | Sample | Root Cause |
|---|------|----------|------|--------|------------|
| 1 | Shower Room | Cubicle - Behind Ceramic Tile | Shower Cubicle | Not Sampled | Validation matching: LLM extracted as "Shower Cubicle / Flat Cement Sheeting" |
| 2 | Shower Room | Cubicle - Beneath Shower Tray | Shower Cubicle | Not Sampled | Same as #1 — two shower cubicle variants, LLM merged location details |
| 3 | Bathroom Adj Labour Ward | Shower Cubicle - Beneath Shower Tray | Shower Cubicle | Not Sampled | Validation matching: LLM extracted but location field differs |
| 4 | Multi Purpose Area Adjacent CCSD | Fire Door | Fire Door(s) | Not Sampled | Room name punctuation: "- Adjacent" (recovered) vs "  Adjacent" (GT double space) |
| 5 | Rear Exit Foyer | Floor | Floor covering (beneath carpet) | 35766/07 35766/08X | Sample number format: "Greencap 35766/07 & 35766/08X" vs "35766/07 35766/08X" |
| 6 | Ward 12 | Shower Cubicle - Beneath Shower Tray | Shower Cubicle | Not Sampled | Validation matching: recovered record location differs from GT |
| 7 | West Passage | Adjacent CCSD Fire Door | Fire Door(s) | Not Sampled | Room name: "West Passage - Adjacent CCSD" (recovered) vs "West Passage" (GT) |

### Analysis of Remaining Gaps

- **3 records** (1, 2, 3): Shower cubicle location mismatch — LLM/recovery extracts "Shower Cubicle" as product but GT has specific "Cubicle - Behind Ceramic Tile" / "Cubicle - Beneath Shower Tray" in location field
- **2 records** (4, 7): Room name punctuation/format differences between ARA PDF text and BAR CSV ground truth
- **1 record** (5): Sample number format — LLM captures "Greencap" prefix from PDF header
- **1 record** (6): Combined shower cubicle + location format issue

All 7 items ARE present in the extracted data (either from LLM or recovery). The gap is validation matching precision, not extraction coverage.

## Root Cause Summary

The 14 "Not Sampled" items missing from Alexander were caused by:
1. **`_recover_no_access_records()` was SAMP-format only** — its `level_re` regex (`^Ground$`, `^First$`, etc.) never matched ARA's section headers like "Mortuary Buildings - Interior - Ground Level"
2. **The recovery function DID run** on the orchestrator path (graph edge: deduplicate -> recover_no_access -> save) but returned 0 records for ARA documents
3. **No Docling tables were injected** for Alexander, making the LLM more likely to miss unsampled rows in the dense vertical PDF text

## Fix Applied

- Added `_recover_not_sampled_records_ara()` function to scan for ARA-specific "Not Sampled" pattern:
  ```
  {item_no} / {room} / {desc} / Asbestos / Not Sampled / {restriction} / Presumed Positive
  ```
- This runs after the existing SAMP scan in `_recover_no_access_records()`
- 8 records recovered deterministically via regex (no API cost)
- SAMP path completely untouched (G6 guardrail)
- Broadmeadows maintained at 31/31 (G1 guardrail)

## Decision Gate

| Outcome | Result | Status |
|---------|--------|--------|
| Alexander >= 40/43 | 36/43 (83.7%) | MISS |
| Alexander 36-39/43 | 36/43 (83.7%) | **PARTIAL SUCCESS** |
| Alexander < 36/43 | N/A | N/A |
| Broadmeadows = 31/31 | 31/31 (100%) | **PASS** |

**Decision: PARTIAL SUCCESS** — Commit with gap note. Create E28-S4 follow-up story for remaining 7 items (validation matching improvements).
