# Implemented Changes (E20)

## Commit

- `893c70f` — `feat(web): link marketing and app navigation with Vercel domain contract`

## Code Changes

### Marketing -> App Linking

- `marketing-site/src/lib/site-urls.ts`
- `marketing-site/src/components/Navigation.tsx`
- `marketing-site/src/components/landing/Hero.tsx`
- `marketing-site/src/components/Footer.tsx`
- `marketing-site/.env.local.example`

Behavior:
- `Open App` CTA is now present in header, hero, and footer.
- CTA target is env-driven via `NEXT_PUBLIC_APP_URL` with default `https://demo.vaea.coralshades.ai`.

### App -> Marketing Linking

- `frontend/src/lib/site-urls.ts`
- `frontend/src/config/navigation.ts`
- `frontend/src/components/layout/AppSidebar.tsx`
- `frontend/src/components/common/CommandPalette.tsx`
- `frontend/.env.example`

Behavior:
- Sidebar has external links: `Visit Landing`, `Documentation`.
- Command palette has matching external commands.
- URLs use `NEXT_PUBLIC_MARKETING_URL` and derived docs URL.

### Env/Docs

- `.env.example`
- `docs/marketing-site/deployment.md`

Added/updated:
- Cross-site URL env contract.
- Vercel two-project setup (`marketing-site` + `frontend`) and domain mapping.

## BMAD Artifact Updates

- `_bmad-output/project-planning-artifacts/acm-ai/03-prd.md` (v1.6, FR-1100 section)
- `_bmad-output/project-planning-artifacts/acm-ai/04-architecture.md` (v1.3, multi-project topology)
- `_bmad-output/project-planning-artifacts/acm-ai/05-epics-and-stories.md` (Epic 20 added)
- `_bmad-output/project-planning-artifacts/acm-ai/bmm-workflow-status.yaml` (updated)
- `docs/sprint-artifacts/sprint-status.yaml` (Epic 20 done)
- `docs/sprint-artifacts/e20-s1-marketing-to-app-linking.md` (new)
- `docs/sprint-artifacts/e20-s2-app-to-marketing-navigation-cutover.md` (new)
- `task_plan.md`, `findings.md`, `progress.md` (planning-with-files logs)

## Validation Results

### Passed

- `marketing-site`: `npm run lint`
- `frontend`: `npm run lint`

### Blocked in Environment

- `marketing-site`: `npm run build` failed with `spawn EPERM`.
- `frontend`: `npm run build` failed with `spawn EPERM`.
- `git push` failed due network connectivity to GitHub (`Could not connect to server`).
- `vercel deploy --prod --yes` failed due network to `vercel.com` and local `spawn EPERM`.

## Notes

- This repo has many unrelated modified/untracked files. Commit `893c70f` intentionally includes only the E20 integration and BMAD updates listed above.
