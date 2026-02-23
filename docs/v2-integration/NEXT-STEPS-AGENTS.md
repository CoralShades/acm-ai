# Next Steps for AI Agents

This file is the session-start runbook for follow-on agents.

## Session Start Checklist

1. Confirm branch and baseline:
```bash
git rev-parse --abbrev-ref HEAD
git log --oneline -n 5
git status --short
```
2. Verify integration commit exists:
```bash
git show --name-only --oneline 893c70f
```
3. Read handoff docs:
- `docs/v2-integration/README.md`
- `docs/v2-integration/IMPLEMENTED-CHANGES.md`
- `docs/v2-integration/NEXT-STEPS-AGENTS.md`

## Priority Work Queue

### P0: Publish and Deploy

1. Push branch:
```bash
git push
```
2. Ensure Vercel projects are configured:
- Project A root directory: `marketing-site`
- Project B root directory: `frontend`
3. Apply domains:
- Marketing: `vaea.coralshades.ai`
- App: `demo.vaea.coralshades.ai`
4. Set Vercel env vars:
- Marketing: `NEXT_PUBLIC_APP_URL=https://demo.vaea.coralshades.ai`
- Frontend: `NEXT_PUBLIC_MARKETING_URL=https://vaea.coralshades.ai`
5. Deploy:
```bash
cd marketing-site && vercel deploy --prod --yes
cd ../frontend && vercel deploy --prod --yes
```

### P0: Verify Production Routing

1. Root domain serves marketing.
2. Marketing `Open App` links to demo subdomain.
3. App sidebar links return to landing/docs on root domain.
4. Confirm no broken internal app routes.

## Local Validation Commands

Use `cmd /c` on this machine to bypass PowerShell script policy for npm/vercel wrappers.

```bash
cd marketing-site
cmd /c npm run lint
cmd /c npm run build

cd ../frontend
cmd /c npm run lint
cmd /c npm run build
```

If `spawn EPERM` persists:
- retry in elevated shell,
- ensure antivirus/policy is not blocking child process spawn,
- retry using `npx next build` as a diagnostic.

## BMAD Tracking Protocol

If any follow-up change is made, keep these in sync:

- `_bmad-output/project-planning-artifacts/acm-ai/03-prd.md`
- `_bmad-output/project-planning-artifacts/acm-ai/04-architecture.md`
- `_bmad-output/project-planning-artifacts/acm-ai/05-epics-and-stories.md`
- `docs/sprint-artifacts/sprint-status.yaml`
- `_bmad-output/project-planning-artifacts/acm-ai/bmm-workflow-status.yaml`
- `task_plan.md`, `findings.md`, `progress.md`

## Recommended Follow-Up Stories

1. Add a lightweight integration test that asserts:
- marketing CTA points to `NEXT_PUBLIC_APP_URL`
- app sidebar and command palette expose marketing links
2. Add explicit Vercel redirect rules for legacy app aliases (301) in dashboard or project config.
3. Add canonical URL metadata review for both projects after domain cutover.

## Known Risks / Caveats

1. Build/deploy commands were blocked by current environment constraints (`spawn EPERM`, network restrictions).
2. Repo contains unrelated in-progress/untracked files; avoid broad `git add .` in follow-on sessions.
