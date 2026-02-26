---
epic: Epic 22
story_id: E22-S1
title: Schema Resilience - Normalize Instead of Reject
status: drafted
---

As a system,
I want field validators to normalize unexpected LLM values instead of rejecting entire buildings,
So that extraction does not lose records due to minor enum mismatches.

Acceptance Criteria:
- [ ] `risk_status` validator normalizes `"Moderate"` -> `"Medium"` instead of raising `ValueError`
- [ ] ALL `field_validator` logic in `ACMExtractionRecord` and `acm_validator.py` follows a normalize-or-passthrough pattern
- [ ] No field validator raises `ValueError` for unexpected but close values; it normalizes and logs
- [ ] `data_issues` captures normalization events (for example, `"Normalized risk_status: Moderate -> Medium"`)
- [ ] All existing tests still pass

Technical Notes:
- Reuse shared enum normalization utilities from `open_notebook/extractors/normalizers/enums.py` and avoid duplicated mapping logic
- Apply the same normalization contract in schema-level and validator-level paths so behavior is consistent regardless of entrypoint
- Preserve auditability by logging normalization decisions and recording them in `data_issues`

Key Files:
- open_notebook/extractors/acm_schemas.py
- open_notebook/extractors/validators/acm_validator.py
- open_notebook/extractors/normalizers/enums.py

Guard Rails:
- Do not drop or reject otherwise valid records because of minor enum label variance
- Do not remove strict handling for structurally invalid payloads (this story only changes enum/value resilience)
- Keep scope limited to normalization and observability behavior in extraction validators
