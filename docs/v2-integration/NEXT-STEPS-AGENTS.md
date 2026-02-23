# Next Steps for AI Agents

This file is the session-start runbook for follow-on agents.

## Current State (as of 2026-02-23)

| Item | Status |
|------|--------|
| `git push origin release` | ✅ Done — HEAD is `f730640` |
| Vercel project A (`acm-marketing-site`) | ✅ `prj_pM0jSF8SLL6xheNPTqt0TWmAasYU` |
| Vercel project B (`frontend`) | ✅ `prj_7uWhAMwVWvnKte9HfhxkKBNlbMRz` |
| Domain `vaea.coralshades.ai` → marketing | ✅ Assigned |
| Domain `demo.vaea.coralshades.ai` → frontend | ✅ Assigned |
| `NEXT_PUBLIC_APP_URL` on marketing | ✅ Set |
| `NEXT_PUBLIC_MARKETING_URL` on frontend | ✅ Set |
| Frontend deploy to production | ✅ **LIVE** at `demo.vaea.coralshades.ai` |
| Marketing deploy to production | ✅ **LIVE** at `vaea.coralshades.ai` |
| Cross-link verification | ✅ "Open App" ↔ "Visit Landing" both correct |
| Legacy alias 301 redirects | ✅ Done (verified 2026-02-23) |

## Session Start Checklist

1. Confirm branch and baseline:
```bash
git rev-parse --abbrev-ref HEAD   # should be: release
git log --oneline -n 5
```
2. Verify commits exist:
```bash
git show --stat 893c70f  # E20 integration
git show --stat 78c537c  # marketing-site source files
git show --stat 1bc26b5  # shadcn + package.json
```
3. Check live URLs:
```bash
curl -sI https://demo.vaea.coralshades.ai | head -5   # should be 200
curl -sI https://vaea.coralshades.ai | head -5         # should be 200 when build done
```

## Priority Work Queue

### ✅ DONE: Production Routing Verified

Both sites live and cross-linked:
- `https://vaea.coralshades.ai` — marketing landing page ✅
- Marketing `Open App` button → `https://demo.vaea.coralshades.ai` ✅
- Frontend sidebar `Visit Landing` → `https://vaea.coralshades.ai` ✅
- Frontend sidebar `Documentation` → `https://vaea.coralshades.ai/docs` ✅

### ✅ DONE: Legacy Alias 301 Redirects

Both Vercel auto-generated aliases now redirect to canonical domains (verified with HTTP 301):
- `frontend-two-alpha-37.vercel.app` → `https://demo.vaea.coralshades.ai/`
- `acm-marketing-site.vercel.app` → `https://vaea.coralshades.ai/`

Set via `PATCH /v9/projects/{id}/domains/{alias}` Vercel API with `{redirect, redirectStatusCode: 301}`.

### P1: Canonical URL Metadata

After domain cutover is stable:
- Add `<link rel="canonical" href="https://vaea.coralshades.ai/...">` to marketing-site layout.
- Add canonical URL to frontend layout pointing to `https://demo.vaea.coralshades.ai`.

### P2: Integration Test Assertions

Add lightweight test that asserts:
- Marketing CTA href matches `NEXT_PUBLIC_APP_URL`
- App sidebar and command palette expose marketing links with correct `NEXT_PUBLIC_MARKETING_URL`

## Vercel Project IDs (for API)

```bash
VERCEL_TOKEN=vcp_...  # already in .env
MKTG_ID=prj_pM0jSF8SLL6xheNPTqt0TWmAasYU
FRONT_ID=prj_7uWhAMwVWvnKte9HfhxkKBNlbMRz
```

Trigger a new deploy manually:
```bash
# Use check_deploys.py to monitor
python3 _debug/check_deploys.py
```

## BMAD Tracking Protocol

If any follow-up change is made, keep these in sync:

- `_bmad-output/project-planning-artifacts/acm-ai/03-prd.md`
- `_bmad-output/project-planning-artifacts/acm-ai/04-architecture.md`
- `_bmad-output/project-planning-artifacts/acm-ai/05-epics-and-stories.md`
- `docs/sprint-artifacts/sprint-status.yaml`
- `_bmad-output/project-planning-artifacts/acm-ai/bmm-workflow-status.yaml`
- `task_plan.md`, `findings.md`, `progress.md`

## Known Risks / Caveats

1. Marketing-site npm build may still fail — check Vercel dashboard for READY state.
2. `spawn EPERM` on Windows prevents local `npm run build`; use WSL or the Vercel API for deployments.
3. Repo contains unrelated in-progress/untracked files; avoid broad `git add .`.
4. `VERCEL_TOKEN` is in the shell environment (loaded from `.env`) — not committed to git.

## Recommended Follow-Up Stories

1. Add a lightweight integration test that asserts:
- marketing CTA points to `NEXT_PUBLIC_APP_URL`
- app sidebar and command palette expose marketing links
2. Add explicit Vercel redirect rules for legacy app aliases (301) in dashboard or project config.
3. Add canonical URL metadata review for both projects after domain cutover.

## Known Risks / Caveats

1. Build/deploy commands were blocked by current environment constraints (`spawn EPERM`, network restrictions).
2. Repo contains unrelated in-progress/untracked files; avoid broad `git add .` in follow-on sessions.
