---
epic: Epic 21
story_id: E21-S4
title: Raw Table Preview + Extraction Input Quality Fix
status: done
---

As a compliance officer,
I want to inspect raw extracted table content and improve extraction input quality,
So that missing ACM rows can be diagnosed and extraction accuracy can improve without prompt churn.

Acceptance Criteria:
- [x] Added content normalizer for Docling split-value patterns before extraction prompt input.
- [x] Added raw tables endpoint: `GET /api/acm/jobs/{source_id}/raw-tables`.
- [x] Endpoint returns `acm_table_section` rows when available and falls back to Docling markdown table parsing.
- [x] Added unit/integration coverage for normalizer and raw tables endpoint.
- [x] Preserved fallback behavior and existing extraction graph topology.

Implementation Notes:
- `open_notebook/extractors/normalizers/content.py` added with targeted line-break fixes (e.g. `Same as\n34511-039001`, `Assumed\npositive`, split sample numbers).
- Normalization is wired into both extraction paths:
  - `open_notebook/graphs/acm_extraction.py` (`prepare_context`)
  - `open_notebook/extractors/orchestrator.py` (`orchestrate_extraction`)
- `api/models.py` includes `RawTableResponse` model.
- `api/routers/acm.py` includes raw table endpoint and fallback table parsing helpers.

Validation Notes (2026-02-26):
- Broadmeadows (`source:z2a59rp36ur25znpaavr`): **17/31** after two extraction attempts (target `>= 28/31` not met).
- Alexander (`source:ubbsh2i0b6ypy64vs1hh`): **52** records extracted (no complete regression to zero; historical expectation of 54 not reached in this run).
- Raw table preview endpoint returns payload for Broadmeadows (large `acm_table_section` content, truncated in CLI output).

Follow-up:
- Prompt-only ceiling remains for Broadmeadows reference/unsampled rows; additional structural extraction strategy is still required to reach `>= 28/31`.
