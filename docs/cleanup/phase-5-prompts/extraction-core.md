You are the EXTRACTION-CORE specialist in a 6-agent Phase 5 audit for the ACM-AI SF reconciliation sprint. READ-ONLY review. No code changes, no commits.

Working directory is /mnt/d/ailocal/acm-ai. You are on branch `feat/sf-reconciliation-20260411` (8 commits ahead of main).

## Context to read first (in order)

1. `docs/cleanup/assumptions-and-decisions.md` — 20 durable decisions DEC-001..DEC-020
2. `docs/cleanup/session-log-2026-04-11.md` — narrative of Phases 1-6
3. `docs/sprint-artifacts/full-audit-2026-04-11/PHASE-1-FINDINGS.md` — SF gap matrix
4. `docs/sprint-artifacts/change-proposals/sprint-change-proposal-20260411-sf-reconciliation.md`
5. `git log --oneline main..HEAD` and `git show 5dc3ef30` + `git show 444a66f9`

## Your domain: extraction core

Inspect: `open_notebook/graphs/acm_extraction.py` (surgical RAG fix at line 1806-1813), `open_notebook/extractors/row_segmenter.py`, `row_extractor.py`, `schema_inference.py`, `open_notebook/domain/acm_row_schemas.py`, `acm_row_mappers.py`, `open_notebook/domain/acm.py`, `open_notebook/extractors/exporters/sf_export.py`.

## Questions to answer

1. Did the surgical RAG fix leave dead references? `_llm_correct_records()` is not called — any other callers? Imports to clean up?
2. Are there fields extracted by `row_segmenter.py`/`row_extractor.py`/`schema_inference.py` that do NOT map to a valid SF field per `config/sf-schema-snapshot.json`? List them for E38-S2.
3. Trace: extraction → BuildingRecord → sf_export. What's the chain, are there gaps?
4. Non-SF fields on ACMRecord/BuildingRecord that the extraction pipeline sets but sf_export does NOT export?
5. Run `uv run pytest tests/test_sf_export_contract.py -v` and report.

## Output

1. Write findings to `docs/cleanup/phase-5-audit-extraction-core.md` with sections: Scope, Findings, Recommendations (critical/high/medium/low), References (file:line).
2. Print a final ≤250-word summary to stdout. Start with "=== EXTRACTION-CORE SUMMARY ===" so the parent can grep for it.

Be specific with file:line refs. No speculation — if you can't verify, say so. When done, exit cleanly.
