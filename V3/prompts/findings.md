# V3 MinerU Audit — Findings

**Date:** 2026-03-02
**Auditor:** Claude Opus 4.6
**Sources:** User's component research, PyPI/GitHub verification, Party Mode plan, Tech Research output

---

## Summary

The tech research (Step 02) and party mode plan (Step 03) contain **several material inaccuracies** about MinerU that affect E31 story scoping, risk assessment, and architectural decisions. The user's own research is significantly more accurate than both agent-generated documents.

---

## Finding 1: CRITICAL — Torch Version Constraint is WRONG

| Source | Claim | Actual (pyproject.toml master) |
|--------|-------|-------------------------------|
| Tech research | `torch >= 2.2, < 2.7` | `torch>2.6.0,<3` |
| Party mode plan (Q3) | `torch 2.10 vs mineru constraint <2.7` | `torch>2.6.0,<3` |
| Party mode Risk R1 | "MinerU 2.x torch constraint blocks main-venv" | **NO CONFLICT** |

**Your torch 2.10.0+cu126 IS COMPATIBLE** with MinerU 2.7.6 (`2.10 > 2.6` and `2.10 < 3`).

**Impact:**
- Risk R1 (Medium likelihood, High impact) in the party plan is **ELIMINATED**
- The 3 SP contingency for subprocess bridge in E31-S1 is likely unnecessary
- E31-S1 can be simplified from "Install MinerU in main venv OR subprocess bridge" to just direct installation
- Party mode Q3 resolution is outdated

---

## Finding 2: CRITICAL — Three Distinct MinerU Components Not Differentiated

The user's research correctly identifies THREE separate things that the tech research and party plan conflate into "MinerU 2.x":

| Component | Package | Backend | PaddlePaddle? | VRAM | Best For |
|-----------|---------|---------|:------------:|:----:|----------|
| **Pipeline** | `mineru[pipeline]` | Traditional models (PaddleOCR-based) | Unclear (may use paddleocr2torch internally) | ~6 GB | Fast, reliable, fine-tunable |
| **VLM** | `mineru[vlm]` or `mineru-vl-utils` | MinerU 2.5 vision-language model (1.2B params) | **NO** — pure transformers/PyTorch | ~10 GB (FP16) | Highest accuracy, no OCR pipeline |
| **Hybrid** | `mineru[core]` | Pipeline + VLM combined | Mixed | ~10 GB | DEFAULT since v2.7.0 — best of both |

**Neither the tech research nor party plan discusses which MinerU backend to use.** They assume "MinerU" is one thing. The party plan should specify: pipeline, VLM, or hybrid.

**Impact:**
- E31-S1 needs a backend selection decision
- VLM backend has NO PaddlePaddle dependency at all — simplest integration
- Hybrid is the DEFAULT since v2.7.0 and likely the best choice
- Architecture may differ significantly based on backend choice

---

## Finding 3: MODERATE — paddleocr2torch Status is Misrepresented

| Source | Claim | Actual |
|--------|-------|--------|
| Tech research | "MinerU 2.x replaced paddlepaddle-gpu with paddleocr2torch" | Neither paddlepaddle NOR paddleocr2torch appears in current pyproject.toml dependencies |
| Tech research | "paddleocr2torch" listed as a dependency | NOT in pyproject.toml. Pipeline extra only has: ultralytics, doclayout_yolo, PyYAML |
| Party plan | "PaddlePaddle isolation: Subprocess bridge (not Docker)" | May not be needed at all |

**What actually happened:** The `mineru` package v2.7.6 pyproject.toml shows `torch>2.6.0,<3` as the main dependency. The [pipeline] extra adds ultralytics + doclayout_yolo. PaddleOCR models may be loaded through a different mechanism than direct paddlepaddle or paddleocr2torch imports.

**Impact:**
- The entire "PaddlePaddle isolation" discussion in the party plan may be irrelevant
- Need to verify at install time what actually gets pulled in transitively
- The `pip install mineru --dry-run` test in E31-S1 remains important but for different reasons

---

## Finding 4: HIGH — MinerU 2.5 VLM Option Not Considered

The user's research identifies MinerU 2.5 VLM as "the game-changer":
- 1.2B-parameter vision-language model
- NO PaddlePaddle, NO paddleocr2torch — pure transformers/PyTorch
- Claims to outperform GPT-4o, Gemini-2.5 Pro on OmniDocBench
- ~2.4 GB VRAM in FP16, ~1.2 GB in INT8
- Separate install: `pip install "mineru-vl-utils[transformers]"`
- Processes page **images**, not PDF text streams (different approach than Docling)
- GGUF quantized versions available

**Neither the tech research nor party plan evaluates VLM as an extraction option.**

The party plan's consensus layer design assumes both providers output HTML/markdown tables. If VLM outputs structured markdown from page images, the `NormalizedExtractionResult` normalization step is different.

**Impact:**
- VLM could be a superior "second provider" — truly different extraction approach (vision-based vs structure-based), which maximizes consensus layer value
- Integration effort may be different (image rendering + VLM inference vs PDF parsing)
- The `ExtractionProvider` adapter interface may need to accommodate image-based extraction
- E31-S1 should evaluate VLM backend alongside pipeline backend

---

## Finding 5: MODERATE — Alexander Benchmark Target is Conflated

The user's research states clearly:
> "Alexander: 0/43 due to the completionState wrapper parsing bug (Epic 27, not Docling-related). The pre-existing baseline was 52 records extracted (9 over-extracted vs 43 ground truth)."

The party plan states:
> E31-S6: "Alexander: >= 42/43 (cross-page stitching improvement)"

**These are two different problems:**
1. Alexander's 0/43 is from the completionState JSON unwrapping bug in the orchestrator path — MinerU has ZERO effect on this
2. Cross-page stitching would help if tables span pages, but Alexander's issue is parsing, not extraction

**Impact:**
- E31-S6 benchmark target for Alexander is based on a false premise
- Fixing the completionState bug (which should be in E30 or E32 scope) would likely get Alexander close to 43/43 independently
- MinerU's value for Alexander is in ADDITIONAL accuracy improvements beyond the bug fix, not the primary fix
- The benchmark story needs to separate: (a) completionState fix baseline and (b) MinerU improvement delta

---

## Finding 6: LOW-MODERATE — CUDA 12.8+ Requirement Needs Verification

One source (DeepWiki) claims MinerU requires "Compute Capability 7.0+ (Volta+), CUDA 12.8+". The user has CUDA 12.6.

**This needs verification:**
- RTX 4090 is Compute Capability 8.9 (Ada Lovelace) — well above 7.0
- CUDA 12.6 vs 12.8 requirement is unclear — MinerU 2.5.3 release notes mention "fixed pipeline backend compatibility with torch 2.8.0" which suggests CUDA 12.x support is being actively maintained
- The pyproject.toml says `torch>2.6.0,<3` — torch 2.10 with CUDA 12.6 should work as torch handles CUDA compatibility internally

**Impact:**
- Probably fine but should be verified in the E31-S1 validation story
- Not a planning-level risk unless CUDA 12.8 is a hard requirement

---

## Finding 7: LOW — v2.7.0 Changed Default Backend to Hybrid

MinerU v2.7.0 (Dec 2025) made hybrid the DEFAULT backend, combining pipeline + VLM. The party plan and tech research were both written against an assumption of "MinerU = pipeline backend only."

**Impact:**
- If we install `mineru[all]`, we get the hybrid backend by default
- Hybrid uses both pipeline (fast, traditional) and VLM (accurate, vision-based)
- This may be the ideal configuration for ACM-AI — fast for simple tables, VLM for complex ones
- GPU VRAM: ~10 GB for hybrid (fits alongside Docling on RTX 4090's 24 GB)

---

## Cross-Reference: Party Mode Plan Changes Needed

| Section | Issue | Severity |
|---------|-------|----------|
| Topic 1, row "MinerU 2.x torch constraint" | Wrong constraint. Should be `>2.6.0,<3`. No conflict with torch 2.10 | **CRITICAL** |
| Topic 1, row "PaddlePaddle isolation" | May not be needed. Current pyproject.toml has no paddle dependency | **HIGH** |
| Topic 1, row "GPU sharing" | Timing estimates may differ if using VLM or hybrid backend | MODERATE |
| Topic 1, row "Implement now vs later" | Correct decision (Docling + MinerU), but needs backend specification | MODERATE |
| Risk R1 | "MinerU 2.x torch constraint blocks main-venv" — ELIMINATED | **CRITICAL** |
| Risk R3 | "Consensus layer adds latency" — timing estimates need backend-specific numbers | LOW |
| Q3 resolution | "If torch 2.10 conflicts" — it doesn't. Remove subprocess bridge contingency | **HIGH** |
| E31-S1 | "Install MinerU in main venv (or subprocess bridge if torch conflict)" — simplify to direct install + backend selection | **HIGH** |
| E31-S6 | "Alexander: >= 42/43 (cross-page stitching improvement)" — conflates completionState bug with extraction quality | **MODERATE** |
| Section 10 | Consensus layer assumes HTML/markdown output from both providers. VLM outputs structured markdown from images — different normalization | MODERATE |

---

## Cross-Reference: Tech Research Changes Needed

| Section | Issue | Severity |
|---------|-------|----------|
| Section 5, "MinerU 2.x torch constraint" | Claims `torch >= 2.2, < 2.7` — wrong, actual is `>2.6.0,<3` | **CRITICAL** |
| Section 5, "paddleocr2torch" dependency | Claims it's a listed dependency — not in current pyproject.toml | **HIGH** |
| Section 5, integration pattern | Shows `from mineru import MinerUDocumentConverter` — may not be the correct API for v2.7.6 | MODERATE |
| Section 6, comparison matrix | "PyTorch conflict: No" — correct conclusion but wrong reasoning (it's not because of paddleocr2torch, it's because torch constraint was updated) | MODERATE |
| Section 11, dependency analysis | "CRITICAL RISK: torch version constraint" — this risk doesn't exist with current pyproject.toml | **CRITICAL** |
| Missing | No discussion of pipeline vs VLM vs hybrid backends | **HIGH** |
| Missing | No evaluation of MinerU 2.5 VLM as a distinct extraction option | **HIGH** |

---

## Recommendation

These findings do NOT break the prompt pack flow. The corrections should be fed into the **still-open Party Mode session** as a follow-up message (like the previous continuation prompt pattern). Steps 04-15 are unaffected because they reference Party Mode output — fixing the plan at Step 03 propagates corrections downstream automatically.

---
---

# Audit: `instructions-sample` Files Are Runtime Dependencies — Salesforce Picklist Mismatches

**Date:** 2026-03-03
**Auditor:** Claude Opus 4.6
**Context:** E30-S4 (Dependent Picklist Validator) is in active development. This audit ensures the data files it depends on are correct for Salesforce target.
**Constraint:** NO CODE CHANGES — findings only. Active dev session ongoing.

---

## CRITICAL DISCOVERY: These Files Are Not Documentation

The files in `docs/samplePDF/instructions-sample/` are **loaded at runtime** by production code. They are not reference docs — they are live config:

| File | Loaded By | How |
|------|-----------|-----|
| `register_enums.json` | `config_loader.py:222` → `acm_validator.py:75` | `json.load()` → cached in `_FIELD_SCHEMA` → used by `validate_enum_fields()` |
| `register_row.schema.json` | `config_loader.py:221` | `json.load()` → field definitions, required fields, column mappings |
| `register_taxonomy.nonfriable.json` | `taxonomy.py:64` | `json.load()` → cached in `_NONFRIABLE_TAXONOMY` → used by `classify_product()` |
| `register_taxonomy.friable.json` | `taxonomy.py:71` | `json.load()` → cached in `_FRIABLE_TAXONOMY` → used by `classify_product()` |
| `consultant_wording_rules.json` | `recommendations.py:86` | `json.load()` → regex patterns for hygienist action normalization |

**Any mismatch between these files and Salesforce picklist values will cause:**
- Silent validation failures (records flagged as invalid when they're correct for SF)
- Silent pass-throughs (records pass validation but fail SF import)
- Missed records (valid data rejected by wrong enum lists)
- Incorrect classification (wrong product group/type assigned)

---

## F1: FIXED — Condition "Good" → "Stable"

| Layer | Value | Status |
|-------|-------|--------|
| `register_enums.json` | ~~"Good"~~ → "Stable" | ✅ User fixed |
| `enums.py` line 33 | `"good": "Stable"` | ✅ Already aligned |
| Salesforce `Condition__c` | "Stable" | ✅ Ground truth |

**No remaining issue.** Both the JSON and the hardcoded normalizer agree on "Stable".

---

## F2: HIGH — Dual Validation Path Creates Divergence Risk for E30-S4

The existing validation pipeline has TWO independent enum validation paths:

```
Path A (current): record → enums.py normalizer → acm_validator.validate_enum_fields()
                                                        ↓
                                              register_enums.json (BAR values)

Path B (E30-S4):  record → sf_picklist_validator.validate_acm_chain()
                                        ↓
                              SFSchemaBundle.dependencies (SF values)
```

**Risk:** If `register_enums.json` and the SF schema disagree on ANY value, a record can:
- Pass Path A but fail Path B (or vice versa)
- Get normalized to a BAR value by Path A, then fail SF chain validation in Path B

**Specific conflicts E30-S4 must handle:**

| Field | `register_enums.json` value | SF picklist value | Conflict? |
|-------|---------------------------|-------------------|-----------|
| Sample Result | "Not Sampled" | *(not in SF picklist)* | ❌ YES — will pass BAR validation, fail SF |
| Sample Result | "No Access" | *(not in SF picklist)* | ❌ YES — same |
| Sample Result | *(absent)* | "Negative - Treated as Positive" | ❌ YES — SF value has no BAR equivalent |
| YesNo | "YES" / "NO" | "Yes" / "No" | ❌ YES — case mismatch |
| Condition | "Stable" | "Stable" | ✅ Now aligned |

**E30-S4 action:** The `SalesforcePicklistValidator` must be authoritative for SF-bound data. When Path A (BAR) and Path B (SF) disagree, Path B wins for SF export. Document this precedence.

---

## F3: HIGH — Taxonomy JSONs Missing 4 Salesforce ACM_Classification Groups

The taxonomy files loaded by `taxonomy.py` are incomplete vs Salesforce:

| SF `ACM_Classification__c` Value | In taxonomy JSON? | Impact |
|----------------------------------|-------------------|--------|
| Textiles *(non-friable)* | ❌ NO | `get_product_types("Textiles")` returns `[]` — no valid sub-classifications |
| Bitumen products (f) | ❌ NO | `get_product_groups("Friable")` won't include this group |
| Coatings (f) | ❌ NO | Same |
| Reinforced plastics/resins (f) | ❌ NO | Same |

**Runtime impact in `taxonomy.py`:**
- `get_product_groups("Friable")` returns 6 groups, SF has 9 → 3 valid SF groups invisible to validator
- `get_product_types("Textiles", friability="Non-friable")` → returns `[]` → classified as "no match"
- `classify_product()` hardcodes Textiles as Friable-only (lines 524-527) — non-friable textile items get misclassified

**E30-S4 action:** The SF schema (from `load_sf_field_schema()`) will have all 18 groups. But if `classify_product()` assigns a group BEFORE validation, it may assign the wrong group for these 4 missing cases.

---

## F4: HIGH — Product Type Name Casing Mismatch (Taxonomy vs SF Picklist)

`taxonomy.py` `CLASSIFICATION_PATTERNS` (lines 139-579) output Title Case product types. Salesforce `ACM_Sub_Classification__c` uses sentence case:

| `classify_product()` output | SF `ACM_Sub_Classification__c` picklist | Match? |
|-----------------------------|----------------------------------------|--------|
| "Flat Sheeting" | "Flat sheeting" | ❌ |
| "Corrugated Roof Sheeting" | "Corrugated roof sheeting" | ❌ |
| "Ceiling Tiles" | "Ceiling tiles" | ❌ |
| "Vinyl Tiles" | "Vinyl tiles" | ❌ |
| "Ridge Capping" | "Ridge capping" | ❌ |
| "Clutch Plates" | "Clutch plates" | ❌ |
| "Brake pads" | "Brake pads" | ✅ |
| "Mastic" | "Mastic" | ✅ |

**E30-S4 tech spec says AC4: "Strict case-sensitive matching"**. This means every Title Case product type from `classify_product()` will FAIL the SF chain validator when checked against the actual SF picklist values.

**E30-S4 action:** Either:
- (a) Fix `CLASSIFICATION_PATTERNS` to use SF-exact casing (many lines to change), OR
- (b) Add a case-normalization step between classification and SF validation, OR
- (c) Make chain validation case-insensitive (contradicts AC4)

---

## F5: MEDIUM — Taxonomy JSON `primary_classification` Field Is Rotated

Both `register_taxonomy.nonfriable.json` and `register_taxonomy.friable.json` have `primary_classification` shifted by one position:

| pc_code | `primary_classification` (WRONG) | `product_group_header` (CORRECT) |
|---------|----------------------------------|----------------------------------|
| T1 (nf) | "Bitumen products" | "T1 Cement products" |
| T2 (nf) | "Cement products" | "T2 Bitumen products" |
| T3 (nf) | "Coatings" | "T3 Vinyl products" |
| T1 (f) | "Cement products (f)" | "T1 Cement products" |
| T2 (f) | "Gasket products (f)" | "T2 Vinyl products" |

**Current code is safe:** `taxonomy.py:128` uses `group.get("product_group_header")` not `primary_classification`. But any future code (including E30-S4) that reads `primary_classification` will get wrong group names.

**E30-S4 action:** If the SF chain validator ever looks up taxonomy by `primary_classification`, it will get wrong results. Ensure it uses `product_group_header` or, better, the SF schema directly.

---

## F6: MEDIUM — `consultant_wording_rules.json` Missing One Canonical Action

The code in `acm_extraction.py:380` references patterns from this file. The heuristic rules reference (Section 12) documents 7 canonical actions. The JSON file has only 6:

| Action | In JSON? | In code? |
|--------|----------|----------|
| `maintain_in_situ` | ✅ | ✅ |
| `remove_prior_to_refurb_or_demolition` | ✅ | ✅ |
| `restrict_access_immediately` | ✅ | ✅ |
| `remedial_within_months` | ✅ | ✅ |
| `confirm_status_sampling` | ✅ | ✅ |
| `height_or_access_restriction` | ✅ | ✅ |
| `leave_undisturbed_and_manage` | ❌ NO | ✅ (hardcoded in code) |

**Impact:** Low — `recommendations.py` falls back to hardcoded `DEFAULT_PATTERNS` when JSON patterns don't match, so the missing action IS handled. But the JSON is incomplete as a source of truth.

---

## F7: MEDIUM — `register_row.schema.json` Has No Enum Constraint on ACM Fields

BAR columns AA ("ACM Product Group") and AC ("ACM Product Type") are defined as plain `string|null` — no `enum` constraint:

```json
"ACM Product Group": { "type": ["string", "null"], "description": "Excel column AA" }
"ACM Product Type": { "type": ["string", "null"], "description": "Excel column AC" }
```

This means `config_loader.py` provides NO validation for these critical fields from the BAR schema. **All ACM classification validation depends entirely on the taxonomy JSON files (F3, F4, F5 above) or the SF schema (E30-S4).**

---

## F8: LOW — 16 `SpecificUses` Values Not in SF `Item_Name__c` Picklist

`register_enums.json` `SpecificUses` has ~320 values. SF `Item_Name__c` has 294. These 16+ values exist in the BAR enum but NOT in Salesforce:

`Above door`, `Adj to Heating Coils`, `Backing panel box lining`, `Electrical cabinet`, `Electrical cabinet door lining`, `Furnace door seal`, `Manhole cover`, `Motor room - Debris on floor`, `Old electrical cables`, `On floor`, `On ground`, `On shelf`, `Settled on surfaces`, `Strapping (Walls/ceiling etc.)`, `Strapping to eave lining`, `Suspect Cement Sheet`

**Impact:** Low for E30-S4 (which focuses on dependent chains, not Item_Name validation). But if `Item_Name__c` validation is added later, these will need a fallback mapping.

---

## Summary: E30-S4 Must-Know Items

| Finding | Severity | E30-S4 Action Required |
|---------|----------|----------------------|
| F2: Dual validation path divergence | HIGH | Document Path B (SF) takes precedence over Path A (BAR) for SF export |
| F3: 4 missing SF groups in taxonomy | HIGH | SF schema from `load_sf_field_schema()` must be authoritative, not taxonomy JSONs |
| F4: Product type casing mismatch | HIGH | Decide: fix patterns, add normalization, or relax case-sensitivity |
| F5: Taxonomy `primary_classification` rotated | MEDIUM | Never use `primary_classification` — use `product_group_header` or SF schema |
| F1: Condition "Stable" | FIXED | No action needed |
| F6: Missing consultant action | LOW | No E30-S4 impact |
| F7: No BAR enum for ACM fields | MEDIUM | SF schema is the only source of truth for ACM field validation |
| F8: SpecificUses/Item_Name gap | LOW | Not in E30-S4 scope |
