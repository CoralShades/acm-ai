You are the OBSERVABILITY specialist in a 6-agent Phase 5 audit for the ACM-AI SF reconciliation sprint. READ-ONLY review. No code changes, no trace queries.

Working directory is /mnt/d/ailocal/acm-ai. Branch `feat/sf-reconciliation-20260411`.

## Context to read

1. `docs/cleanup/assumptions-and-decisions.md`
2. `docs/cleanup/session-log-2026-04-11.md`
3. `docs/sprint-artifacts/change-proposals/sprint-change-proposal-20260411-sf-reconciliation.md`
4. `.claude/skills/acm-observability/SKILL.md` (or invoke `/skill acm-observability`)
5. `git log --oneline main..HEAD` + `git show 5dc3ef30`

## Your domain: observability wiring

6-tool observability stack: Langfuse (self-hosted), LangSmith (cloud), LangGraph API (local), Logfire (Pydantic via OTel), erdantic, JSON Crack.

Inspect: `open_notebook/observability/langfuse_config.py`, `logfire_config.py`, `langfuse_bridge.py`, `open_notebook/graphs/acm_extraction.py` (where callbacks are injected — do NOT edit per CLAUDE.md), `commands/acm_commands.py`.

## Questions to answer

1. Did Phase 2a (surgical RAG fix at `acm_extraction.py:1806-1813`) break any Langfuse span emission? The old code emitted `pl.info("[PIPELINE] Prompt template: acm/correction")`, the new code doesn't. Is that a regression or correctly removed?
2. `logfire_config.py` `instrument_pydantic()` safety: run `uv run pytest tests/test_observability_config_smoke.py -v` and report. Verify include set is limited to ACM domain models (the 48K-span regression guardrail).
3. Callback placement rule: verify no graph node in `acm_extraction.py` now has a callback from the rewrite.
4. PipelineEventBus stage progress: still emitted correctly after the correction-stage neutering, or did the fix drop a required event?
5. Does `langfuse_tracing()` still work if Langfuse is disabled (`LANGFUSE_ENABLED=false`)?

## Output

1. Write findings to `docs/cleanup/phase-5-audit-observability.md`: Scope, Findings, Recommendations, References.
2. Print final ≤250-word summary starting with "=== OBSERVABILITY SUMMARY ===".

Do not modify any observability code. Do not query live Langfuse traces. Pure static review. Exit cleanly.
