# Task Plan — Feature Complete

Updated: 2026-02-22 (Final Reconciliation)
Source of truth: `docs/sprint-artifacts/sprint-status.yaml`

---

## Project Summary

- **Total Stories**: 122
- **Done**: 112 (92%)
- **Archived**: 10 (E8)
- **Completed Epics**: E1, E2, E3, E4, E5, E6, E7, E9, E10, E11, E12, E13, E14, E15, E16, E17 (16/17)
- **Archived Epics**: E8

**All feature stories are complete.** The project is feature-complete.

---

## Deferred Items

1. **Test coverage**: No test coverage for new backend endpoints (source_bulk.py, graph.py, settings.py stage models)
2. **DocumentActions dropdown**: Individual document action dropdown component not created (functionality exists in BulkActions.tsx)
3. **Runtime ACM mode toggle**: Settings UI toggle for ACM mode not implemented (env-var control works)
4. **Epic retrospectives**: All optional, none completed

---

## 2026-02-23 Release Task: Cross-Site Navigation + Domain Cutover

- [x] Add marketing -> app `Open App` CTAs (header, hero, footer) using `NEXT_PUBLIC_APP_URL`
- [x] Add app -> marketing links in sidebar + command palette using `NEXT_PUBLIC_MARKETING_URL`
- [x] Update env examples (`frontend/.env.example`, `marketing-site/.env.local.example`, root `.env.example`)
- [x] Update deployment docs with two-project Vercel domain mapping
- [x] Update BMAD planning artifacts (PRD, architecture, epics/stories, sprint status, workflow status)

## 2026-02-23 Hotfix: Frontend → Railway API Connection

**Problem:** `demo.vaea.coralshades.ai` shows "Unable to Connect to API Server"

**Root Cause (2 failures):**
1. `/config` endpoint returns `{"apiUrl":"https://frontend-two-alpha-37.vercel.app\n"}` — old alias (now 301) with trailing newline
2. Next.js rewrites proxy `/api/*` to `INTERNAL_API_URL` (default `http://localhost:5055`) — no backend on Vercel serverless → 502

**Railway backend is healthy:** `https://acm-ai-production.up.railway.app/health` → `{"status":"healthy"}`

**Fix (Option B — complete):**
- [x] Delete wrong `API_URL` env var (id: `Iz5u0YCzlx5B56IN`) from Vercel frontend project
- [x] Set `API_URL=https://acm-ai-production.up.railway.app` (production target)
- [x] Delete wrong `INTERNAL_API_URL` env var (id: `4Nt9hezDYxDllvyU`)
- [x] Set `INTERNAL_API_URL=https://acm-ai-production.up.railway.app` (build-time rewrite target)
- [x] Trigger Vercel rebuild (rewrites baked at build time) → `dpl_85ypYezPpK8r3z85BdymJoc9BYJf` → READY
- [x] Verify: `curl https://demo.vaea.coralshades.ai/config` returns Railway URL
- [x] Verify: `curl https://demo.vaea.coralshades.ai/api/config` returns 200 (when Railway up)
- [x] Verify: browser loads app without connection error

**Secondary fix — Railway watch patterns:**
- [x] Added `watchPatterns` to `railway.toml` — docs/frontend pushes no longer trigger backend rebuilds
- [x] Verify Railway recovers after current build cycle

**Tertiary fix — OOM crash loop:**
- [x] Increased Railway memory allocation (dashboard)
- [x] Staggered supervisor startup: worker waits 10s after API (reduces peak memory)
- [x] Added Python malloc tuning env vars in Dockerfile.api
- [x] Full E2E verification passed — all 5 endpoints return correct data

---

## Sprint History

### Final Reconciliation (2026-02-22): 7 stories verified & marked done
E10-S1, E9-S3, E12-S2, E12-S3, E12-S4, E13-S2, E13-S3
(All were implemented in prior Ralph sprint but tracking artifacts never updated)

### Epic 17 (2026-02-22): 6 stories implemented
E17-S1..S6 (AG-UI extraction, A2A agent card, OpenRouter models)

### Ralph Sprint (2026-02-22): 11 stories completed
E2-S8, E2-S11, E16-S3, E1-S23, E5-S3, E16-S1, E12-S1, E13-S1, E15-S2, E5-S4, E11-S2

### Bug Triage (2026-02-21): 10 stories completed
7 bug fixes + E1-S28/S29/S30 (model capabilities, dynamic token limits)
