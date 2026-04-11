# Phase 5 — Post-Code 6-Agent Audit Plan

> **Sub-skills consulted:** `dispatching-parallel-agents`, `acm-observability`
> **Model policy:** Sonnet only (CLAUDE.md agent-teams rule — never opus for team members)
> **Branch under review:** `feat/sf-reconciliation-20260411` at commit `1eefac1e` (8 commits ahead of main)

## Goal

Independent verification that Phase 1-4 + 6 + 3A landed cleanly and nothing
critical was missed. Each specialist reviews a distinct domain in
parallel; findings feed the final SCP revision.

## Agents (dispatched in parallel, run_in_background=true)

| # | Agent | Domain | Key question |
|---|---|---|---|
| 1 | `acm-extraction-core` | Extraction pipeline + row schemas | Did the surgical RAG fix + sf_export rewrite break any extraction path? Are there other non-SF fields still live in the core? |
| 2 | `acm-extraction-pre` | Document structure, TOC, building inventory, metadata | Does pre-extraction still work post-rewrite? Any reliance on deleted fields? |
| 3 | `acm-extraction-post` | Consensus, corrective validation, provenance | Is the post-extraction pipeline still coherent after E1-S15 Layer 2 was neutered? Consensus engine assumptions still hold? |
| 4 | `acm-schema-expert` | SurrealDB migrations, Pydantic models, field schema | Does the DB schema still align with the SF snapshot? Any migration needed for E38-S2? |
| 5 | `acm-observability-debugger` | Langfuse, Logfire, LangGraph state inspection | Did the Phase 2a/2b changes break any observability wiring? `instrument_pydantic` include set still safe? |
| 6 | `acm-rag-strategist` | RAG / retrieval / corrective loop | Given that E1-S15 Layer 2 LLM correction is disabled, does the overall RAG posture (E1-S14 contextual embeddings + search tools) still make sense? |

## Common context each agent receives

- Branch: `feat/sf-reconciliation-20260411`
- Phase 1 findings: `docs/sprint-artifacts/full-audit-2026-04-11/PHASE-1-FINDINGS.md`
- Assumptions/decisions: `docs/cleanup/assumptions-and-decisions.md` (DEC-001..DEC-020)
- Session narrative: `docs/cleanup/session-log-2026-04-11.md`
- Final SCP: `docs/sprint-artifacts/change-proposals/sprint-change-proposal-20260411-sf-reconciliation.md`
- Runtime config: `config/sf-schema-snapshot.json`, `config/bar_to_sf_mapping.yaml`
- New test surface: `tests/` (55 tests)

## Common instructions

1. READ-ONLY review. No code changes, no file deletions.
2. Use `git log --oneline main..HEAD` to see the 8 commits.
3. Use `git show <sha>` to inspect specific changes.
4. Write findings to `docs/cleanup/phase-5-audit-<agent-slug>.md` with these sections:
   - Scope (what you examined)
   - Findings (what's correct, what's concerning, what's missing)
   - Recommendations (ordered by severity: critical / high / medium / low)
   - References (file:line for every claim)
5. Return a ≤250-word summary to the parent session.

## Aggregation

After all 6 complete, parent session writes
`docs/cleanup/phase-5-aggregate-report.md` consolidating findings by
severity, plus a delta-to-SCP section listing any items that should be
appended to the E38 epic.

## Context budget guard

Each agent gets a strict ≤250-word response cap so aggregation fits in
context. Full findings stay in the per-agent MD files; the parent
session reads those directly only if a summary flags something
critical.
