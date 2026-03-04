# E28-S1: ARA "Not Sampled" Spike Results

**Date**: 2026-02-28
**Agent**: Mary (BA/Researcher)

## The 17 "Not Sampled" Records in Ground Truth

| # | Building | Room | Product | Result | PDF Item |
|---|----------|------|---------|--------|----------|
| 4 | Mortuary Buildings | Boiler Room | Fire Door(s) | Assumed Positive | 5 |
| 5 | Mortuary Buildings | Mortuary Room | Ceiling | Assumed Positive | 6 |
| 6 | Mortuary Buildings | Mortuary Room | Wall(s) | Negative | 7* |
| 7 | Mortuary Buildings | Shower Room (Behind Tile) | Shower Cubicle | Assumed Positive | 8 |
| 8 | Mortuary Buildings | Shower Room (Beneath Tray) | Shower Cubicle | Assumed Positive | 9 |
| 14 | VMO Accommodations | Exterior / Eaves | Eaves | Assumed Positive | 16 |
| 16 | Old Alexandra Hospital | Roof / Ductwork | Ductwork | Assumed Positive | 19 |
| 20 | Old Alexandra Hospital | Bathroom Adj Labour Ward | Shower Cubicle | Assumed Positive | 29 |
| 23 | Old Alexandra Hospital | CCSD - Entry | Fire Door(s) | Assumed Positive | 32 |
| 28 | Old Alexandra Hospital | Flamable Liquids Store | Ceiling | Assumed Positive | 38 |
| 30 | Old Alexandra Hospital | Former Laundry - Ext Passage | Electrical board | Assumed Positive | 40 |
| 32 | Old Alexandra Hospital | Multi Purpose Area Adj CCSD | Fire Door(s) | Assumed Positive | 44 |
| 34 | Old Alexandra Hospital | Reception | Insulation (Safe) | Assumed Positive | 52 |
| 35 | Old Alexandra Hospital | South Store Room | Ceiling | Assumed Positive | 53 |
| 36 | Old Alexandra Hospital | Store Offices | Ceiling | Assumed Positive | 54 |
| 39 | Old Alexandra Hospital | Ward 12 | Shower Cubicle | Assumed Positive | 57 |
| 40 | Old Alexandra Hospital | West Passage Adj CCSD | Fire Door(s) | Assumed Positive | 58 |

*Note: GT #6 (Mortuary Room, Wall) has sample_no="Not Sampled" but result="Negative" in CSV — PDF shows it as item 7 with J169642-001-003/Negative. May be a ground truth discrepancy.

## ARA Format "Not Sampled" Text Patterns

### Consistent Pattern (found on pages 8, 10, 11, 12, 13, 14)

```
{item_number}
{room_name}
{item_description} - {material}
Asbestos
Not Sampled
{access_restriction}
Presumed Positive
{photo_ref}
{extent}
{condition}
{friability}
...
```

### Access Restriction Variants Found

| Restriction Text | Count | Examples |
|-----------------|-------|---------|
| `Restricted Access` | 10 | Fire doors, shower cubicles, safe |
| `Height Restricted` | 6 | Eaves, ceilings, ductwork |
| `Live Electrical Hazard` | 1 | Electrical distribution board |

### Specific Examples from PDF

**Page 8 - Fire Door (item 5):**
```
5
Boiler Room
Fire Door - Fire Door Core
Asbestos
Not Sampled
Restricted Access
Presumed Positive
```

**Page 13 - Electrical Board (item 40):**
```
Former Laundry - External
Passage
Electrical Distribution Board -
Compressed Bituminous Electrical
Panel
Asbestos
Not Sampled
Live Electrical Hazard
Presumed Positive
```

**Page 10 - Eaves (item 16):**
```
16
External - Throughout
Eaves - Flat Cement Sheeting -
Painted white
Asbestos
Not Sampled
Height Restricted
Presumed Positive
```

## Root Cause Analysis

### 1. Does `_recover_no_access_records()` run for Alexander? YES — but fails

**Evidence**: Graph edges show `deduplicate → recover_no_access → save` for BOTH paths.

The function IS called after the orchestrator completes. However, it fails because:

- **`level_re`** pattern (`^(Ground|First|Second|Third|Level|Roof|Basement)\s*$`) requires a **bare level line** — SAMP format.
- ARA format uses section headers like `"Mortuary Buildings - Interior - Ground Level"` — these don't match `level_re`.
- Without a level indicator match, the function never enters its scanning loop and returns `[]` (empty recovery).

**Critical**: The recovery function receives the FULL document text (`source.full_text`) and DOES search for "No access|Height restriction|Restricted Access" — but the entry point (level indicator) is gated on SAMP patterns.

### 2. Does Docling injection work for Alexander buildings? NO

**Evidence**: `e26_s4_accuracy_validation.py` line 518: `register_tables=None` — "No Docling tables for Alexander"

The orchestrator's `extract_building()` calls `_get_docling_tables(source_id, page_start, page_end)` which queries `acm_table_section` records from the DB. For Alexander, no table section records exist (it was never processed with Docling table extraction enabled).

**Impact**: Without Docling DataFrames, the LLM only sees PyMuPDF text, which is messy vertical text where "Not Sampled" items are visually distinct but textually hard to parse.

### 3. What text does the LLM see for a "Not Sampled" row?

The orchestrator extracts per-building page ranges via `_extract_building_content()`. For each building, the LLM sees PyMuPDF text which has the table content laid out vertically:

```
5
Boiler Room
Fire Door - Fire Door Core
Asbestos
Not Sampled
Restricted Access
Presumed Positive
J169642-0     ← photo ref (split across lines)
01-Photo0
10
1 Unit/s
Fair
Friable
Low
Low
Not
Labelled
```

The LLM prompt already has excellent rules for ARA format (building_extraction.jinja lines 240-346) and explicit "Not Sampled" instructions (lines 13, 369-386). The LLM *should* extract these but may struggle with:
- Multi-line item descriptions splitting across lines
- Dense vertical text with many fields per item
- No clear row delimiters in the text

### 4. Are the "Not Sampled" rows in Docling tables or plain text?

**Plain text only.** Docling tables are NOT available for Alexander. The LLM gets only PyMuPDF vertical text.

## Recommended Fix Strategy

### Primary Fix: ARA-Specific Recovery Regex (HIGH CONFIDENCE)

Add a new ARA pattern scanner to `_recover_no_access_records()` that looks for the pattern:

```regex
{item_number}\n{room}\n{desc}\nAsbestos\nNot Sampled\n{restriction}\nPresumed Positive
```

This is a highly consistent pattern. Every "Not Sampled" entry in the Alexander PDF follows this exact structure. A regex-based recovery will reliably catch all 16-17 items.

**Implementation approach:**
1. In `_recover_no_access_records()`, add an ARA-format scan AFTER the existing SAMP scan
2. Pattern: find "Not Sampled" lines, look backward for "Asbestos", room/desc, item number
3. Dedup against `existing_records` to avoid duplicating items the LLM already captured

### Secondary Fix: No prompt changes needed

The building_extraction.jinja template already has comprehensive ARA format rules and Not Sampled instructions. The issue isn't the prompt — it's that the LLM misses some items in the dense vertical text.

### Not Needed: Docling injection fix

While Docling tables would help, they require re-processing the Alexander source. The regex recovery approach is simpler, deterministic, and sufficient for the current goal.

## Files to Change

| File | Change | Priority |
|------|--------|----------|
| `open_notebook/graphs/acm_extraction.py` | Add ARA pattern to `_recover_no_access_records()` | P1 |
| `tests/test_e28_ara_recovery.py` | Unit tests for ARA recovery | P1 |
| `scripts/research/e28_s1_gap_analysis.py` | Gap analysis script (already created) | Done |

## Key Decision: Modify existing function vs new function

**Recommendation: Modify `_recover_no_access_records()`** to add an ARA scan section after the SAMP scan. Reasons:
- Single point of recovery logic
- Same dedup guards apply
- The function already receives `full_text` which is all it needs
- No graph structure changes required
- SAMP logic untouched (G6 guardrail satisfied)
