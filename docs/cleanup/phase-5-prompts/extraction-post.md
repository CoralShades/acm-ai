You are the EXTRACTION-POST specialist in a 6-agent Phase 5 audit for the ACM-AI SF reconciliation sprint. READ-ONLY review. No code changes, no commits.

Working directory is /mnt/d/ailocal/acm-ai. Branch `feat/sf-reconciliation-20260411`.

## Context to read

1. `docs/cleanup/assumptions-and-decisions.md` (especially DEC-006 RAG Option C)
2. `docs/cleanup/session-log-2026-04-11.md`
3. `docs/sprint-artifacts/full-audit-2026-04-11/rag-disposition-research.md` — prior RAG research that led to the surgical fix
4. `docs/sprint-artifacts/change-proposals/sprint-change-proposal-20260411-sf-reconciliation.md`
5. `git log --oneline main..HEAD` and `git show 5dc3ef30`

## Your domain: post-extraction

Consensus engine, corrective validation, provenance, export formatting.

Inspect: `open_notebook/extractors/consensus/matcher.py`, `engine.py`, `resolver.py`, `open_notebook/extractors/validators/acm_validator.py`, `open_notebook/graphs/acm_extraction.py` correction nodes (search for `_apply_field_correction`, `_llm_correct_records`, `correct_records`, `validate_records_strict`), `open_notebook/extractors/exporters/sf_export.py`, `prompts/acm/correction.jinja`.

## Questions to answer

1. Surgical fix at `acm_extraction.py:1806-1813` neutered Layer 2 LLM correction. Verify Layer 1 (deterministic synonym substitution) still runs. Does anything else depend on `_llm_correct_records` output that now just increments `failed`?
2. Is `prompts/acm/correction.jinja` now dead? No caller left?
3. Consensus engine: does its conflict resolution align with SF picklists? Does `ConsensusEngine` know about restricted picklists, or vote blindly?
4. Provenance tracking: compatible with new sf_export mapping? Does each SF field get a provenance trail?
5. `validate_records_strict`: where does it get valid values from — `config/sf-schema-snapshot.json` or stale in-code constants?

## Output

1. Write findings to `docs/cleanup/phase-5-audit-extraction-post.md`: Scope, Findings, Recommendations, References.
2. Print final ≤250-word summary starting with "=== EXTRACTION-POST SUMMARY ===".

Be specific. Exit cleanly when done.
