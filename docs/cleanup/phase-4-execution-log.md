# Phase 4 Doc Cleanup — Execution Log

**Date:** 2026-04-11
**Executor:** parent session (Opus 4.6)
**Manifest source:** `docs/cleanup/phase-4-doc-cleanup-manifest.md`
**Subagent:** Sonnet (Phase 4 audit agent, run_in_background)

## Executed deletions (19 files, 4,587 lines removed)

### Category 1 — Old sprint-artifact reports (7 files)
```
docs/sprint-artifacts/reports/bug-extraction-status-tracking-gap.md
docs/sprint-artifacts/reports/demo-extraction-report-2026-02-22.md
docs/sprint-artifacts/reports/nfr-assessment-pr21-pr22.md
docs/sprint-artifacts/reports/phase4-ui-bug-report.md
docs/sprint-artifacts/reports/post-merge-review-consolidated-report.md
docs/sprint-artifacts/reports/prd-cross-check-2026-02-21.md
docs/sprint-artifacts/reports/ralph-sprint-verification-2026-02-22.md
```
All pre-2026-03-01, historical only, superseded by sprint-status.yaml and the 2026-02-22 retrospective. No cross-references from MEMORY.md or canonical docs.

### Category 4 — BAR-only / fabricated-field docs (2 files)
```
docs/sprint-artifacts/e30-s2-building-record-table-domain-model.md
docs/sprint-artifacts/prompt-packs/2026-03-19-mcs11-remaining-building-room-id-audit-fix.md
```
Both referenced BAR fields (`est_building_size_m2`, `daily_duration`, `level_of_activity`, `mobile_plant`) or fabricated SF field names (`Room_ID__c`) that don't exist in the live SF schema. Stories are done; docs are historical.

### Category 5 — Root-level scratch files (10 files)
```
findings.md                         (chat debug session 2026-03-31)
progress.md                         (chat debug session 2026-03-31)
task_plan.md                        (chat debug session 2026-03-31)
findings-ACM-FeatureComplete.md     (feature-complete 2026-02-22; superseded by retrospective)
task_plan-ACM-FeatureComplet.md     (feature-complete 2026-02-22)
progress--ACM-FeatureComplet.md     (feature-complete 2026-02-22; has encoding artifacts)
acm-page-test.mjs                   (one-off Playwright script, not in tests/)
acm-page-test2.mjs                  (second one-off Playwright script)
check_out.txt                       (empty 0-byte file)
pytest_out.txt                      (transient pytest output capture)
```
All transient session artifacts that should never have been tracked. None are referenced by source code or the test suite.

## SKIPPED: Category 2 — Superseded change proposals (4 files)

**Why skipped:** Subagent recommended deleting 4 SCPs claiming they were "superseded by later SCPs". However, cross-reference against `MEMORY.md` showed 3 of the 4 are explicitly listed as **canonical**:

| Agent's proposed deletion | MEMORY.md status | Decision |
|---|---|---|
| `sprint-change-proposal-20260204.md` | ✅ Listed as canonical ("Victorian BAR Format Expansion") | KEEP |
| `sprint-change-proposal-2026-02-07.md` | ✅ Listed as canonical ("RAG Strategy Alignment (E1-S13..S15, Epic 11)") | KEEP |
| `sprint-change-proposal-20260220-extraction-monitor-ux.md` | ✅ Listed as canonical ("Extraction Monitor + UX (E15, E16)") | KEEP |
| `sprint-change-proposal-20260222-extraction-quality.md` | ❌ Not in MEMORY.md | KEEP (defer to user — avoid partial delete of chain) |

**Principle applied:** A subagent's judgment about "supersession" is not sufficient grounds to delete files explicitly enshrined as canonical in MEMORY.md. Memory was updated on 2026-02-21 when these SCPs were consolidated into the current directory structure. If any of these truly became superseded later, the user should update MEMORY.md first and then re-run the audit.

**Follow-up for user:** If you want Category 2 deletions, update MEMORY.md to remove the entries you consider stale, then re-run Phase 4 or delete manually. Alternatively, confirm explicitly in a future session that these SCPs should be removed despite the memory listing.

## Also NOT executed (borderline items deferred to user)

From the manifest's Category 7 (~9 files, ~280 KB):

| File | Manifest recommendation |
|---|---|
| `batch_fix_services.py` | Move to `scripts/`, not delete |
| `mcp_port_summary.md` | Move to `docs/` subdirectory |
| `start_docs.md` | Move to `docs/getting-started/` or `docs/development/` |
| `broadmeadows_register.json` | Move to `tests/fixtures/` |
| `broadmeadows_text_mid.json` | Move to `tests/fixtures/` |
| `source_dump.json` | 0-byte file, probably safe but confirm |
| `files.zip` | 15 KB, unknown provenance — inspect before deleting |
| `broadmeadows-police-station-samp.pdf` | 1.8 MB, possibly duplicates `docs/samplePDF/` — verify |
| `docs/sprint-artifacts/e33-s2-building-grid-item-grid-two-view.md` + 6 other BAR-review docs | Review-needed per manifest Category 4 |

These are deferred because they're either (a) moves rather than deletions, (b) require inspection the session couldn't do safely, or (c) have tooling dependencies not verified.

## Dead-link fix — not executed

Manifest Category 3 found 1 dead link in `docs/index.md` (`e2e-testing/README.md`). This is an edit action, not a deletion. Deferred to user — the docs/index.md file is a generic Open Notebook portal and may need broader update along with the SF reconciliation work.

## Disk savings

| Category | Files | ~Size |
|---|---|---|
| Executed | 19 | ~310 KB (4,587 text lines) |
| Skipped (Cat 2) | 4 | ~75 KB |
| Deferred (borderline) | 9 | ~280 KB |
| **Total firm candidates from manifest** | 32 | ~665 KB |

## Next time

If the Phase 4 agent runs again, give it an explicit `MEMORY.md is authoritative for canonical SCPs — do not recommend deleting any SCP listed there` instruction. The agent's manifest quality was good but it didn't know about the memory contract.
