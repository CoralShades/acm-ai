# V3 Continuation: SF-First Validation Pipeline

> **Created:** 2026-03-04
> **Context:** Post-implementation audit of E30-S4 + E30-S6
> **Purpose:** Resume document for the next session — contains all context needed to implement the SF-First validation fix
> **Branch:** ACMV3

---

## 1. Session Summary

### What Was Discussed

An audit of the 5 runtime configuration files in `docs/samplePDF/instructions-sample/` revealed that:

1. These files are **not documentation** — they are loaded at runtime by production code (`config_loader.py`, `taxonomy.py`, `recommendations.py`)
2. The BAR validation path (Path A) uses `register_enums.json` as its enum authority
3. The SF validation path (Path B, added in E30-S4) uses `SFSchemaBundle` from `load_sf_field_schema()` as its enum authority
4. **Path A runs upstream of Path B** — the correction loop feeds BAR-only values to the LLM, which silently overwrites SF-valid data

### Key Discovery: Correction Loop Silently Overwrites SF-Valid Values

The correction loop in `acm_extraction.py` (lines 1818–1946) uses `acm_validator.validate_acm_record()` to determine which records need correction. When the validator flags a field, it provides `valid_values` from `register_enums.json` (BAR values). The LLM then receives a correction prompt (`prompts/acm/correction.jinja`) containing **only BAR valid values** — it has no knowledge of SF picklist values.

**Concrete corruption scenario:**

```
1. LLM extracts: sample_result = "Negative - Treated as Positive"  (valid SF value)
2. validate_enum_fields() checks register_enums.json → NOT in BAR list → FAIL
3. correction.jinja renders valid_values: ["Positive", "Assumed Positive", "Negative", ...]
4. LLM "corrects" to: sample_result = "Negative"  (BAR-valid, but WRONG for SF)
5. SF chain validator (Path B) sees "Negative" — passes, but original meaning is lost
```

### Key Decisions

- **E30-S2**: No changes needed — `BuildingRecord` model is correct
- **E30-S4**: No changes needed — SF chain validator is the good path (Path B)
- **E32-S4**: Still needed — fixes F4 casing mismatch, should be implemented as planned
- **New story needed**: "SF-First Validation Pipeline" — separate from E32-S4, redirects Path A's enum authority to SF picklists

---

## 2. Current State of V3 Sprint

### Prompt Pack Position

| Step | Status | Notes |
|------|--------|-------|
| P0–08 | COMPLETE | All planning artifacts generated |
| 08b: Readiness Fixes | NOT YET RUN | Prompt at `V3/prompts/08b-readiness-fixes.md` |
| 09: Sprint Plan | EXISTS | `docs/sprint-artifacts/v3-sprint-plan.md` — 33 stories, 97 SP, 7 sprints |
| 10+: Implementation | IN PROGRESS | 5 stories complete, schema freeze unlocked |

### Implementation Progress

| Story | Status | Sprint |
|-------|--------|--------|
| E30-S1: SF Schema Config Loader | COMPLETE | V3-1 |
| E30-S2: Building Record Table + Domain Model | COMPLETE | V3-1 |
| E30-S3: ACM Record SF Item__c Alignment | COMPLETE | V3-1 |
| E30-S4: Dependent Picklist Validator | COMPLETE | V3-1 |
| E30-S6: BAR→SF Vocabulary Transition | COMPLETE | V3-2 |
| **SCHEMA_FREEZE gate** | **UNLOCKED** | 2026-03-03 |
| E30-S5: Data Migration Script | NOT STARTED | V3-2 |
| E30-S8: Anthropic Direct API + OpenRouter | NOT STARTED | V3-2 |
| E32-S4: Classifier Update (SF Taxonomy) | READY FOR DEV | V3-4 (can pull earlier) |

### E32-S4 Story File

Located at `docs/sprint-artifacts/e32-s4-classifier-update-sf-taxonomy.md`. Approach: SF-schema-based case normalization via `_normalize_to_sf_value()` helper in `sf_picklist_validator.py`. Does NOT touch `taxonomy.py` patterns.

---

## 3. The Problem: BAR Validation Corrupts SF Data

### Architecture: Two Validation Paths

```
Extracted record
      │
      ├──► PATH A (BAR Validation) ─────────────────────────────────────────┐
      │    acm_validator.validate_enum_fields()  (acm_validator.py:117)     │
      │    Enum source: register_enums.json (BAR values)                   │
      │    ✓ "Not Sampled" → VALID (in BAR list)                           │
      │    ✗ "Negative - Treated as Positive" → INVALID (not in BAR list)  │
      │                                                                     │
      │    ┌── IF INVALID ──────────────────────────────────────────┐       │
      │    │  correct_records() (acm_extraction.py:1818)            │       │
      │    │  correction.jinja provides BAR valid_values to LLM     │       │
      │    │  LLM "corrects" to nearest BAR value                   │       │
      │    │  → SF-valid data SILENTLY OVERWRITTEN                  │       │
      │    └────────────────────────────────────────────────────────┘       │
      │                                                                     │
      └──► PATH B (SF Validation) ─────────────────────────────────────────┤
           sf_picklist_validator.validate_all_chains()                      │
           (sf_picklist_validator.py:298)                                   │
           Enum source: SFSchemaBundle.dependencies (SF picklist values)   │
           ✗ "Not Sampled" → INVALID (not in SF picklist)                  │
           ✓ "Negative - Treated as Positive" → VALID (in SF picklist)     │
                                                                            │
      Both results combined in acm_validator.py:346:                       │
      ├── issues: list         ← blocking (from Path A)                    │
      └── chain_warnings: list ← non-blocking (from Path B)               │
```

### 5 Concrete Corruption Scenarios

| # | LLM Extracts | BAR Path A Says | Correction Loop Does | SF Path B Would Have Said |
|---|-------------|-----------------|---------------------|--------------------------|
| 1 | `sample_result = "Negative - Treated as Positive"` | INVALID (not in `register_enums.json` SampleResult) | LLM corrects → `"Negative"` | VALID — this is a real SF picklist value |
| 2 | `sample_result = "Positive - Non-friable"` | INVALID (not in BAR SampleResult list as compound) | LLM corrects → `"Positive"` (loses friability info) | VALID — SF `Sample_Analysis_Result_Material_Status__c` has this exact value |
| 3 | `labelled = "Yes"` | Normalized to `"YES"` by BAR path (register_enums.json has `"YES"`) | Stored as `"YES"` | SF expects `"Yes"` — case mismatch on export |
| 4 | `public_access = "No"` | Normalized to `"NO"` | Stored as `"NO"` | SF expects `"No"` |
| 5 | `sample_result = "Not Sampled"` | VALID (in BAR list) | No correction needed | INVALID — not in SF picklist. But Path A already approved it, so no correction ever triggers. |

### Mismatch Table: BAR vs SF Values

| Field | `register_enums.json` (BAR) | SF Picklist | Conflict |
|-------|---------------------------|-------------|---------|
| SampleResult | "Not Sampled" | *(absent)* | BAR passes, SF rejects |
| SampleResult | "No Access" | *(absent)* | BAR passes, SF rejects |
| SampleResult | *(absent)* | "Negative - Treated as Positive" | SF value has no BAR equivalent → correction loop destroys it |
| SampleResult | *(absent)* | "Positive - Non-friable" | Same |
| SampleResult | *(absent)* | "Positive - Friable" | Same |
| YesNo | `"YES"` / `"NO"` | `"Yes"` / `"No"` | Case mismatch — affects Labelled__c, Public_Access__c |

### Why the Correction Loop Is the Critical Issue

The problem is NOT just that Path A validates against BAR values (that's a known divergence, surfaced as warnings). The problem is that **Path A's validation failures feed the correction loop**, which actively changes record values using BAR-only vocabulary. The correction template (`prompts/acm/correction.jinja`, line 17) renders `valid_values` from `ValidationIssue.valid_values` — which comes from `register_enums.json`.

Key code path:
1. `validate_records_strict()` (`acm_extraction.py:1635`) calls `validate_acm_record(record_dict)`
2. `validate_acm_record()` (`acm_validator.py:346`) calls `validate_enum_fields(record)` which uses `_load_enum_values()` → `load_field_schema()` → `register_enums.json`
3. If invalid → appended to `validation.issues` with `valid_values` from BAR enums
4. `should_correct()` (`acm_extraction.py:2085`) routes to `correct_records()` if issues exist
5. `correct_records()` (`acm_extraction.py:1818`) tries Layer 1 (normalizer) then Layer 2 (LLM with `correction.jinja`)
6. LLM receives ONLY BAR valid values → "corrects" to nearest BAR match
7. Re-validates (edge: `correct` → `validate`, line 2951) — now passes BAR validation
8. SF chain validation (Path B) runs but is WARN-only — cannot undo the corruption

---

## 4. Architecture: What Uses samplePDF Files

### Pipeline Stage Table

| Pipeline Stage | Needs `register_enums.json`? | Needs taxonomy JSONs? | Needs `consultant_wording_rules.json`? | Needs `register_row.schema.json`? |
|---------------|:---:|:---:|:---:|:---:|
| Upload / Docling extraction | No | No | No | No |
| LLM extraction (orchestrator) | No | No | No | No |
| **Validation** (Path A) | **YES** — enum authority | No | No | No |
| **Correction loop** | **YES** — via validation issues | No | No | No |
| Classification (`classify_product()`) | No | **YES** — group/type lookup | No | No |
| Recommendation normalization | No | No | **YES** — phrase patterns | No |
| SF chain validation (Path B) | No | No | No | No |
| Save / Export | No | No | No | **YES** — column mapping |

### Two Config Sources Already Separated

| Source | Location | Loaded By | Authority For |
|--------|----------|-----------|---------------|
| **BAR config** | `docs/samplePDF/instructions-sample/` | `config_loader.py:load_field_schema()` | Path A validation, correction loop |
| **SF config** | Runtime-parsed from `V3/output/` summaries | `config_loader.py:load_sf_field_schema()` | Path B validation (chain validator) |

The SF loader (`load_sf_field_schema()`) already has SF picklist values loaded into `SFSchemaBundle`. The fix is to plumb these into Path A instead of (or in addition to) the BAR enums.

---

## 5. What E32-S4 Fixes (and What It Doesn't)

### E32-S4 Fixes: F4 Casing Mismatch

- **Problem:** `taxonomy.py` `CLASSIFICATION_PATTERNS` outputs Title Case ("Flat Sheeting"), SF expects sentence case ("Flat sheeting")
- **Fix:** Add `_normalize_to_sf_value()` in `sf_picklist_validator.py` — case-insensitive lookup against SF schema values
- **Scope:** Sub-Classification normalization only, at the validation boundary
- **Story file:** `docs/sprint-artifacts/e32-s4-classifier-update-sf-taxonomy.md`

### E32-S4 Does NOT Fix

| Gap | Why Not |
|-----|---------|
| Correction loop using BAR enums | E32-S4 only touches `sf_picklist_validator.py`, not `acm_validator.py` or `correction.jinja` |
| `register_enums.json` as Path A authority | E32-S4 doesn't change the enum source |
| Missing SF SampleResult values ("Negative - Treated as Positive") | Not in E32-S4 scope |
| YesNo casing ("YES"→"Yes") | Not in E32-S4 scope (it's a different field group) |
| 4 missing taxonomy groups (Textiles-NF, Bitumen-f, Coatings-f, Plastics-f) | E32-S4 only normalizes sub-classification casing |

---

## 6. Proposed New Story: SF-First Validation Pipeline

### Story Scope

Redirect Path A's enum authority from BAR `register_enums.json` to SF picklists from `load_sf_field_schema()`. Ensure the correction loop provides SF-valid values to the LLM.

**Estimated effort:** 2-3 SP, MEDIUM risk
**Can slot into:** Sprint V3-2 (alongside E30-S5), V3-3, or V3-4

### 5 Files to Change

#### 1. `open_notebook/extractors/validators/acm_validator.py`

**Current (line 75):** `_load_enum_values()` calls `load_field_schema().enums` → reads `register_enums.json`

**Change:** Add an SF-aware enum resolution path. For SF-bound exports, resolve enum values against SF picklists instead of BAR. Options:
- (a) Replace `_load_enum_values()` to pull from `SFSchemaBundle.picklists` for fields that have SF equivalents
- (b) Add a `validate_enum_fields_sf()` variant that uses SF values, keep BAR path for BAR-only exports
- (c) Add SF picklist values as the primary authority in `_ENUM_FIELD_MAP`, falling back to BAR only for fields SF doesn't cover

**Recommended:** Option (c) — least disruptive, `_ENUM_FIELD_MAP` already maps field names to enum keys. Add a parallel `_SF_ENUM_FIELD_MAP` that maps field names to SF API names, and resolve from SF schema first.

#### 2. `open_notebook/extractors/normalizers/enums.py`

**Current:** `SAMPLE_RESULT_SYNONYMS` (line 17) maps to BAR canonical values (`"Positive"`, `"Negative"`, etc.)

**Change:** Add SF-specific result values:
- `"negative - treated as positive"` → `"Negative - Treated as Positive"`
- `"positive - non-friable"` → `"Positive - Non-friable"`
- `"positive - friable"` → `"Positive - Friable"`

**Also fix:** `CONDITION_SYNONYMS` already uses "Stable" (correct for SF). YesNo normalization needs adding — currently no synonym map for YesNo fields. BAR has `"YES"/"NO"`, SF has `"Yes"/"No"`.

#### 3. `prompts/acm/correction.jinja`

**Current (line 17):** Renders `issue.valid_values` which comes from BAR `register_enums.json`

**Change:** Ensure `valid_values` passed to the template contains SF picklist values, not BAR values. This is an upstream change (the template itself may not need modification — the data it receives needs to change).

**Alternatively:** Add SF-aware context to the prompt: "For Salesforce export, use these exact values: ..." alongside the BAR values.

#### 4. `open_notebook/graphs/acm_extraction.py`

**Current (line 1746-1748):** `validate_acm_record(record_dict)` in `validate_records_strict()` uses BAR enums.

**Change:** Pass an SF-mode flag or use the SF-aware validator when the extraction target is Salesforce. The correction loop (`correct_records()`, line 1818) should use SF-valid values for Layer 1 normalization and pass SF values to the LLM via correction prompt.

#### 5. `open_notebook/extractors/parsers/config_loader.py`

**Current:** `load_field_schema()` (line ~220) loads from `register_enums.json`. `load_sf_field_schema()` (separate function) loads SF schema.

**Change:** Add a unified enum resolution function that merges BAR + SF, with SF taking precedence for overlapping fields. Or: modify `load_field_schema()` to accept a `target="sf"` parameter that swaps enum sources.

### Specific Change Summary

| File | Lines Affected | Change Type |
|------|---------------|-------------|
| `acm_validator.py` | 48-77, 117-199 | Add SF enum resolution alongside BAR |
| `enums.py` | 17-29, new section | Add SF-specific SampleResult values, YesNo normalization |
| `correction.jinja` | 17 (data source change) | Ensure valid_values contains SF values |
| `acm_extraction.py` | 1746-1748, 1818-1946 | Pass SF context to validator and correction loop |
| `config_loader.py` | ~220-240 | Add unified enum resolution or SF-mode parameter |

---

## 7. Open Questions

1. **Should Path A (BAR) be disabled entirely or kept as fallback?**
   - If BAR export is still needed, keep both paths with a target flag
   - If SF is the only target, simplify to SF-only validation

2. **Should "Not Sampled"/"No Access" map to an SF value or be flagged for user input?**
   - These are valid BAR values with no SF equivalent
   - Options: map to a default SF value, flag as "requires user decision", or create synthetic SF mapping

3. **Should we move the 5 JSON files out of `docs/samplePDF/` into a proper config dir?**
   - They are runtime config, not documentation
   - Moving to `config/` or `open_notebook/config/` would be more accurate
   - Low priority — functional as-is, just misleading location

4. **Should the correction loop be SF-first or dual-mode?**
   - SF-first: always correct toward SF values (simplest)
   - Dual-mode: detect export target and correct accordingly (more flexible but more complex)

---

## 8. Audit Findings Status (F1-F8)

Updated from `V3/output/github-issue-e30s4-audit.md`:

| Finding | Severity | Status | Fixed By | Notes |
|---------|----------|--------|----------|-------|
| F1: "Good"→"Stable" | FIXED | ✅ Resolved | User + E30-S6 | Both register_enums.json and enums.py aligned |
| F2: Dual validation path | HIGH | ⚠️ Partially addressed | E30-S4 | SF chain validator exists (Path B) but Path A still uses BAR enums. **Correction loop still corrupts.** |
| F3: 4 missing SF groups | HIGH | ⚠️ Partially addressed | E30-S4/S6 | `_strip_t_prefix()` handles T-codes. 4 taxonomy groups still absent from JSONs. SF schema is authoritative via E30-S4. |
| F4: Product type casing | HIGH | ❌ NOT FIXED | E32-S4 (ready) | Story created, approach defined. Blocks on implementation. |
| F5: primary_classification rotated | MEDIUM | ⚠️ Not addressed | N/A | Code is safe (uses `product_group_header`). Comment gate recommended. |
| F6: Missing consultant action | LOW | ❌ Not fixed | N/A | Low priority — hardcoded fallback handles it. |
| F7: No BAR enum for ACM fields | MEDIUM | ✅ Mitigated | E30-S4 | SF schema is authoritative for ACM chain validation. |
| F8: SpecificUses gap | LOW | ✅ Deferred | N/A | Out of scope — will need fallback when Item_Name__c validation added. |
| **NEW: BAR correction loop corrupts SF data** | **CRITICAL** | **❌ NOT FIXED** | **New story needed** | **Path A runs upstream, correction loop feeds BAR-only values to LLM** |

---

## 9. Files to Pre-Read in Next Session

### Critical (must read before implementing)

| File | Why |
|------|-----|
| `open_notebook/extractors/validators/acm_validator.py` | Path A validation — the code that needs to change |
| `open_notebook/extractors/validators/sf_picklist_validator.py` | Path B — the correct model to follow |
| `open_notebook/extractors/normalizers/enums.py` | BAR synonym maps that need SF extensions |
| `open_notebook/extractors/parsers/config_loader.py` | Both `load_field_schema()` and `load_sf_field_schema()` |
| `prompts/acm/correction.jinja` | Correction prompt template |
| `open_notebook/graphs/acm_extraction.py` (lines 1635-1946) | Validation + correction loop |
| `docs/samplePDF/instructions-sample/register_enums.json` | BAR enum source (what we're replacing) |

### Context (read for understanding)

| File | Why |
|------|-----|
| `docs/sprint-artifacts/e32-s4-classifier-update-sf-taxonomy.md` | F4 fix approach (complementary story) |
| `V3/output/github-issue-e30s4-audit.md` | Full audit findings with status table |
| `V3/output/architecture-explainer.md` | Sections 6-7 cover runtime config and validation system |
| `open_notebook/extractors/parsers/field_config.py` | `SFSchemaBundle`, `SFDependencyChain`, `SFFieldDef` models |
| `docs/sprint-artifacts/v3-progress.md` | Current implementation progress |

---

## 10. Prompt Pack Position

### Where We Are

```
P0 ✅ → 01 ✅ → 02 ✅ → 03 ✅ → 04 ✅ → 05 ✅ → 06 ✅ → 07 ✅ → 08 ✅
                                                                        │
                                                                   08b ← NOT YET RUN
                                                                        │
                                                                   09 ✅ (sprint plan exists)
                                                                        │
                                                              10-15: Implementation cycle
                                                              E30-S1 ✅ E30-S2 ✅ E30-S3 ✅
                                                              E30-S4 ✅ E30-S6 ✅
                                                              SCHEMA_FREEZE ✅ (2026-03-03)
```

### What to Run Next

1. **Create SF-First Validation Pipeline story** (this document provides the scope)
2. **Run 08b readiness fixes** (`V3/prompts/08b-readiness-fixes.md`) — resolves 4 BMAD artifact issues from readiness check
3. **Verify sprint plan** — confirm 08b didn't invalidate sprint sequencing
4. **Continue implementation:**
   - E32-S4 (F4 casing fix) — ready for dev, can pull into current sprint
   - E30-S5 (data migration) — next on V3-2 critical path
   - E30-S8 (Anthropic Direct API) — V3-2, parallel with S5
   - New SF-First story — schedule based on priority assessment

### Implementation Order Recommendation

```
E32-S4 (F4 casing)  ←  can do now, 2 SP, no deps beyond E30-S4/S6 (done)
         │
SF-First story       ←  new, 2-3 SP, deps: E30-S4 (done)
         │
E30-S5 (migration)   ←  V3-2 critical path
E30-S8 (Anthropic)    ←  V3-2 parallel
```

E32-S4 and the SF-First story can run in parallel — they touch different files (sf_picklist_validator.py vs acm_validator.py/enums.py/acm_extraction.py).

---

## Confirmation: No Story Redos Needed

- **E30-S2** (BuildingRecord): Correct as implemented. No changes needed.
- **E30-S4** (SF Chain Validator): Correct as implemented. This IS the good path (Path B). The problem is in Path A, which is older code.
- **E30-S6** (BAR→SF Vocabulary): Correct as implemented. `_strip_t_prefix()` and vocabulary transition are fine.
- **E32-S4** (F4 Casing Fix): Still needed, approach validated, story file ready at `docs/sprint-artifacts/e32-s4-classifier-update-sf-taxonomy.md`.

---

*Document generated 2026-03-04. Sources: V3/output/github-issue-e30s4-audit.md, V3/output/architecture-explainer.md, V3/prompts/findings.md, V3/prompts/progress.md, acm_validator.py, sf_picklist_validator.py, enums.py, config_loader.py, correction.jinja, register_enums.json.*
