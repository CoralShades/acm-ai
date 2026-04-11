You are the RAG-STRATEGIST specialist in a 6-agent Phase 5 audit for the ACM-AI SF reconciliation sprint. READ-ONLY review. No code changes.

Working directory is /mnt/d/ailocal/acm-ai. Branch `feat/sf-reconciliation-20260411`.

## Context to read

1. `docs/cleanup/assumptions-and-decisions.md` (especially DEC-005 literal-only, DEC-006 RAG Option C, DEC-020 E1-S14 is chat-only)
2. `docs/cleanup/session-log-2026-04-11.md`
3. `docs/sprint-artifacts/full-audit-2026-04-11/rag-disposition-research.md` — prior RAG research
4. `docs/sprint-artifacts/change-proposals/sprint-change-proposal-20260411-sf-reconciliation.md`
5. `git log --oneline main..HEAD` + `git show 5dc3ef30`

## Your domain: RAG strategy

E1-S14 contextual embeddings, E1-S15 corrective RAG (now half-disabled), hybrid search, parent-document retrieval, Epic 11 alignment.

Inspect: `open_notebook/graphs/acm_extraction.py` around line 1811, `open_notebook/graphs/` chat/search tools, `open_notebook/extractors/contextual/` (if exists), `open_notebook/domain/acm.py` (`ACMRecord.enriched_text` + `embedding`), `tests/test_observability_config_smoke.py` (Phase 3A new), chat/search tool modules.

## Questions to answer

1. With E1-S15 Layer 2 disabled, is E1-S14 (contextual embeddings) still producing useful embeddings? Verify S14 only writes to `enriched_text`/`embedding` and NOT to SF-bound fields.
2. Chat-side retrieval: does chat still use vector search over `ACMRecord.embedding`? Verify the embedding write path is intact.
3. `_llm_correct_records()` dead code: any other code path that references it? Recommend its removal in E38-S2.
4. Corrective RAG Layer 1 (deterministic synonym substitution): still running and producing corrections? Give a "layer 1 intact" or "layer 1 broken because X" verdict.
5. Epic 11 RAG stories: any still relying on the LLM correction path?
6. STRATEGIC: given the new literal-only rule, does the project still need hybrid search + corrective RAG + parent-document retrieval, or is a simpler retrieval path sufficient?

## Output

1. Write findings to `docs/cleanup/phase-5-audit-rag-strategist.md`: Scope, Findings, Recommendations, References, Strategic verdict.
2. Print final ≤250-word summary starting with "=== RAG-STRATEGIST SUMMARY ===".

Be direct. If the RAG stack is over-engineered for current scope, say so. Exit cleanly.
