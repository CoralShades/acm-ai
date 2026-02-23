# Extraction Pipeline Bugfix — Progress Log

## Session: 2026-02-22 ~7:15 PM AEDT

### Phase 0: Root Cause Investigation (COMPLETE)
- [x] Read worker logs — identified 3 distinct bugs
- [x] Traced Bug 1 to `acm_schemas.py` validators (lines 216-250)
- [x] Traced Bugs 2/3 to provider routing (Google Vertex / Amazon Bedrock)
- [x] Read orchestrator.py, document_structure.py, page_tagger.py, utils.py
- [x] Confirmed model provisioning flow: model_manager -> default_extraction -> provider
- [x] Documented all findings in findings.md

### Phase 1: Fix Pydantic Validators (COMPLETE)
- [x] 1.1 Added `_is_na()` helper and `_NA_PATTERNS` constant
- [x] 1.2 Updated `validate_friable()` — N/A -> None
- [x] 1.3 Updated `validate_material_condition()` — N/A -> None
- [x] 1.4 Updated `validate_risk_status()` — N/A -> None (defensive)
- [x] 1.5 Updated `validate_area_type()` — N/A -> None (defensive)

### Phase 2: Verify Fix (COMPLETE)
- [x] BAR field type safety tests: 13/13 PASSED
- [x] Full test suite: 294 passed, 1 pre-existing failure (token limit, not related)
- [x] Ruff linter: All checks passed
- [x] Pre-existing failure: `test_broadmeadows_e2e.py` — model token limit issue (Bug 4)

### Phase 3: Record BMAD Issues (COMPLETE)
- [x] Created Epic 18: Production Hardening & Demo Stability
- [x] Created E18-S1 story: Extraction Provider Compatibility
  - Issue 1: Google Vertex AI rejects anthropic-beta header
  - Issue 2: Amazon Bedrock rejects integer min/max in JSON schema
  - Issue 3: Output token limits causing truncation (hardcoded fallbacks)
  - Issue 4: Model routing should prefer compatible providers
- [x] Updated sprint-status.yaml with Epic 18 and E18-S1
- [x] Story file: `docs/sprint-artifacts/e18-s1-extraction-provider-compatibility.md`

### Summary of Changes
| File | Change |
|------|--------|
| `open_notebook/extractors/acm_schemas.py` | Added `_is_na()` helper, updated 4 validators to normalize N/A -> None |
| `docs/sprint-artifacts/e18-s1-extraction-provider-compatibility.md` | NEW — BMAD story for provider issues |
| `docs/sprint-artifacts/sprint-status.yaml` | Added Epic 18, E18-S1 |
