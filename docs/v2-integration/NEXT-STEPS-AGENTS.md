# Next Steps for AI Agents

This file is the session-start runbook for follow-on agents.

## Current State (as of 2026-02-23)

| Item | Status |
|------|--------|
| `git push origin release` | ✅ Done — HEAD is `1bc26b5` |
| Vercel project A (`acm-marketing-site`) | ✅ Created — `prj_pM0jSF8SLL6xheNPTqt0TWmAasYU` |
| Vercel project B (`frontend`) | ✅ Exists — `prj_7uWhAMwVWvnKte9HfhxkKBNlbMRz` |
| Domain `vaea.coralshades.ai` → marketing | ✅ Assigned |
| Domain `demo.vaea.coralshades.ai` → frontend | ✅ Assigned |
| `NEXT_PUBLIC_APP_URL` on marketing | ✅ Set |
| `NEXT_PUBLIC_MARKETING_URL` on frontend | ✅ Set |
| Frontend deploy to production | ✅ **LIVE** at `demo.vaea.coralshades.ai` |
| Marketing deploy to production | ⏳ Build in progress / verify complete |

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

### P0: Verify Marketing-Site Build ⏳

Check if the latest Vercel build succeeded:
```bash
python3 _debug/check_deploys.py  # state should be READY
```

If still ERROR — check build logs on Vercel dashboard:
- `https://vercel.com/coralshades-projects/acm-marketing-site`
- Common issue: TypeScript errors or missing peer deps in `marketing-site/package.json`

### P0: Verify Production Routing ⏳

1. `https://vaea.coralshades.ai` — should serve the marketing landing page
2. Marketing `Open App` button → should navigate to `https://demo.vaea.coralshades.ai`
3. `https://demo.vaea.coralshades.ai` — app sidebar `Visit Landing` link → `https://vaea.coralshades.ai`
4. `https://demo.vaea.coralshades.ai` — app sidebar `Documentation` link → `https://vaea.coralshades.ai/docs`

### P1: Legacy Alias 301 Redirects

Add 301 redirects from legacy app aliases (e.g. `frontend-two-alpha-37.vercel.app`) to `demo.vaea.coralshades.ai`.
Can be done in `marketing-site/vercel.json` or Vercel dashboard redirects.

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
