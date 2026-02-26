# Epic 22: Post Phase 6+7 Remediation & Feature Completion
# Sprint Plan — 2026-02-26
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Context

Phase 6+7 (Epic 21) completed loading states, layout consistency, and SSE wiring.
However 10 issues remain from user testing with annotated screenshots:

| # | Issue | Severity | Session |
|---|-------|----------|---------|
| 1 | risk_status 'Moderate' kills entire building extraction | P0 Backend | S1 |
| 2 | Dashboard missing sidebar/header/footer | P0 Frontend | S2 |
| 3 | PDF preview missing in Job Detail page | P1 Feature | S3 |
| 4 | Chat widget missing in Job Detail page | P1 Feature | S3 |
| 5 | Source layout not replicated in Jobs | P1 Feature | S3 |
| 6 | Building tabs missing in ACM Register + Job ACM Records | P1 Feature | S4 |
| 7 | Live streaming doesn't stream (records appear after completion) | P1 UX | S5 |
| 8 | Unicode arrow \u2192 rendering as text on buttons | P2 Bug | S3 |
| 9 | Building tab overlap/spacing in review wizard | P2 UX | S4 |
| 10 | No loading state during Next.js page compilation | P2 UX | S5 |

## Execution Order

```
Session 0: BMAD Planning (Bob/SM)        → 15 min   → docs only
Session 1: Schema Resilience (Backend)    → 20 min   → Python only
Session 2: Dashboard Layout Fix           → 25 min   → Frontend only
Session 3: Job Detail Redesign            → 60 min   → Frontend only (LARGEST)
Session 4: Building Tabs Everywhere       → 35 min   → Frontend only
Session 5: Streaming + Navigation Polish  → 40 min   → Frontend (+ optional backend)
                                          ─────────
                                    Total: ~3.5 hours
```

**Rule: Open a FRESH Claude Code session for each session. Close the previous one.**

## Prompt Files

Each session has a standalone prompt file. Copy-paste the ENTIRE file into Claude Code CLI.

| Session | File | Stories |
|---------|------|---------|
| 0 | `e22-session0-bmad-planning.md` | Creates E22 SCP + 5 story files |
| 1 | `e22-session1-schema-resilience.md` | E22-S1 |
| 2 | `e22-session2-dashboard-layout.md` | E22-S2 |
| 3 | `e22-session3-job-detail-redesign.md` | E22-S3 |
| 4 | `e22-session4-building-tabs.md` | E22-S4 |
| 5 | `e22-session5-streaming-polish.md` | E22-S5 |
