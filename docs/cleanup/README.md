# ACM-AI Cleanup — Session Log

Working artifacts for the SF reconciliation cleanup sprint that started
2026-04-11 on branch `feat/sf-reconciliation-20260411`.

This directory captures assumptions, decisions, subagent reports, and
manifests produced during multi-phase cleanup. It is intentionally
separate from `docs/sprint-artifacts/` (which holds canonical sprint
state) and `docs/sprint-artifacts/full-audit-2026-04-11/` (which holds
the raw SF audit data + Phase 1 findings).

## Contents

- `README.md` — this file
- `session-log-2026-04-11.md` — chronological session narrative, decisions, escape hatches
- `assumptions-and-decisions.md` — durable decisions made during the interview rounds
- `phase-4-doc-cleanup-manifest.md` — deletion manifest from the Phase 4 subagent
- `phase-6-sprint-change-proposal.md` — (if produced) link to the final SCP

## Canonical SCP location

The final Sprint Change Proposal lives at:
`docs/sprint-artifacts/change-proposals/sprint-change-proposal-20260411-sf-reconciliation.md`

This directory holds working notes only; the SCP is the authoritative
change-control document.

## Branch state at session start

```
feat/sf-reconciliation-20260411 (4 commits ahead of main)
  444a66f9  fix(sf-export): rewrite field mappings + hash-based External_ID
  7ad8a871  chore(audit): add picklists.json
  5dc3ef30  feat(sf): Phase 2a — schema snapshot + BAR→SF mapping + RAG fix
  ebfabef0  chore: snapshot before SF reconciliation (Phase 1 audit)
```
