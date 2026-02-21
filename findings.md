# Findings: Bug Triage Investigation + Sprint Artifact Cleanup

## Last Updated: 2026-02-21 (Bug Triage Plan Findings)
## Originally Created: 2026-02-09

---

## Bug Triage Investigation (2026-02-21)

### Bug #1+9: Multi-Model Compatibility — RESOLVED

**Root Cause:** 15+ hardcoded `max_tokens` values throughout the extraction pipeline, with the critical path using `"haiku" in str(model_id).lower()` to select token limits. This tested against SurrealDB record IDs (e.g., `model:h2ucwvxqwo76y7vqw1bz`) rather than actual model names, making the check always fail.

**Fix:** Created model capabilities system (E1-S28) with migration 20 adding `max_output_tokens`, `context_window`, `supports_structured_output`, `supports_tool_calling`, `embedding_dimensions` fields to the `model` table. Provider-default fallback lookup tables in `Model` class. Dynamic token limit replacement in critical extraction path (E1-S29). Embedding dimension validation (E1-S30).

**Impact:** All models (qwen, deepseek, llama, gemini, Claude, GPT) now get appropriate token limits automatically.

### Bug #2: Blank Loading Spinner — RESOLVED

**Root Cause:** Triple blocking pattern: Zustand hydration → `checkAuthRequired()` API call → generic `<LoadingSpinner />`. Users saw blank screen for 1-3 seconds.

**Fix:** Replaced spinner with skeleton layout matching dashboard structure. Cached `authRequired` in Zustand persist store.

### Bug #3/5: No Post-Upload Navigation — RESOLVED

**Root Cause:** Both `AddSourceDialog` and `UploadProgressStep` navigated to generic `/sources` list regardless of upload count.

**Fix:** Smart navigation — single file → `/sources/{id}`, multiple → `/sources` list.

### Bug #4/6: Extraction Progress Panel Colors — RESOLVED

**Root Cause:** Hardcoded Tailwind colors (`bg-blue-500`, etc.) instead of VAEA design system tokens.

**Fix:** Replaced with semantic tokens (`bg-primary`, `bg-destructive`, `bg-emerald-500`).

### Bug #7: Column Naming Regressions — RESOLVED

**Root Cause:** Victorian BAR terminology not applied consistently. "Building ID" should be "Building Code", separate material columns should be merged, risk_status is external.

**Fix:** Renamed columns in grid + CSV + Excel exports. Merged `material_description`/`acm_product_type` with fallback valueGetter.

### Bug #8: Negative Results Regression — RESOLVED

**Root Cause:** `_create_row_from_cells()` in `acm_extractor.py:631-645` silently dropped negative records missing product/material_description (returned `None`), while assumed-positive records got "Unknown" placeholders.

**Investigation:** Git history confirmed prompts correctly instruct negative inclusion (commits a6721fc, 18c6baf). No filtering code in `validate_records()`. Structural risk was only in row creation logic.

**Fix:** Extended "Unknown" placeholder treatment to "Negative" and "Assumed Negative" results.

### Bug #10: Query Data Undefined — RESOLVED

**Root Cause:** `getConfigTemplates()` returned `undefined` when API has no templates property.

**Fix:** Added `?? []` null guard.

### Bug #11: UI/UX Polish + VAEA Branding — RESOLVED

**Fix:** App name → "VAEA | ACM AI", manifest updated, command palette height increased, TabsList overflow-x-auto.

**Deferred:** Favicon conversion from `docs/vaea-assets/VAEA_Ripple2_FavIcon_0.png` — needs image processing tools.

### Anthropic Model ID Typo — RESOLVED

**Found during investigation:** `model_provisioning.py` had `"claude-haiku-3-5-20241022"` instead of `"claude-3-5-haiku-20241022"`. Fixed in E1-S28.

---

## Sprint Artifact Cleanup (2026-02-21)

### Root Cause of Duplication
`_bmad/bmm/config.yaml` does not exist. All BMAD workflows use `{config_source}:implementation_artifacts` which falls back to `_bmad-output/implementation-artifacts/`. The team manually created stories in `docs/sprint-artifacts/` which became more up-to-date and complete.

### Canonical Location Decision
`docs/sprint-artifacts/` is the single source of truth for:
- Sprint status YAML
- All tech-specs and story spec files
- Sprint change proposals (in `change-proposals/` subfolder)
- Historical reports (in `reports/` subfolder)

---

## Historical: Bug Investigation + E2E Test Design (2026-02-09)

### Bug 1: Source Not Found - RESOLVED
Stale API process. Killed and restarted.

### Bug 2: AG Grid RowGroupingModule Error #200 - RESOLVED
Changed default `enableGrouping` from `true` to `false` in ACMGrid.tsx.

### Bug 3: E2E PDF Extraction Test - PENDING
Research completed, implementation not yet started.
