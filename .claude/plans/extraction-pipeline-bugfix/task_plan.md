# Extraction Pipeline Bugfix — Task Plan

## Context
Demo preparation for ACM-AI. Extraction pipeline returns 0 records due to
Pydantic validation errors + provider compatibility issues. See findings.md for
full root cause analysis.

## Phase 1: Fix Pydantic Validators (P0 — CRITICAL) — COMPLETE
- [x] 1.1 Update `validate_friable()` in `acm_schemas.py` to normalize N/A patterns to None
- [x] 1.2 Update `validate_material_condition()` in `acm_schemas.py` to normalize N/A patterns to None
- [x] 1.3 Update `validate_risk_status()` in `acm_schemas.py` to normalize N/A patterns to None (defensive)
- [x] 1.4 Update `validate_area_type()` in `acm_schemas.py` to normalize N/A patterns to None (defensive)
- [x] 1.5 Run existing tests: `pytest tests/test_bar_field_type_safety.py` — 13/13 PASSED
- [x] 1.6 Run full backend tests: `pytest tests/ -x` — 294 passed, 1 pre-existing failure
- [x] 1.7 Run linter: `ruff check .` — All checks passed

## Phase 2: Verify Fix (P0) — COMPLETE
- [x] 2.1 Confirm validators accept N/A values by checking test output
- [x] 2.2 Confirm no regressions in existing tests

## Phase 3: Record BMAD Issues — COMPLETE
- [x] 3.1 Created Epic 18: Production Hardening & Demo Stability
- [x] 3.2 Created E18-S1: Extraction Provider Compatibility (4 issues documented)
- [x] 3.3 Updated sprint-status.yaml

## Decisions
- D1: Only code fix is Bug 1 (validators). Bugs 2/3/4 are model config issues.
- D2: N/A normalization = return None (field is Optional, None is valid).
- D3: Apply N/A pattern to all 4 enum validators for consistency.
- D4: N/A patterns: "n/a", "na", "not applicable", "-", "none", plus any string
      containing "n/a" (catches "N/A (negative)", "N/A - not tested", etc.)
