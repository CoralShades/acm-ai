# Implemented Changes (E20 + Deploy Session)

## Commits

### E20 Integration (previous session)
- `893c70f` — `feat(web): link marketing and app navigation with Vercel domain contract`

### Deploy Session (2026-02-23)
- `27ff481` — `Merge remote-tracking branch 'origin/release' into release` (conflict resolution: sprint-status.yaml, E18+E19+E20 merged)
- `78c537c` — `feat(web): add marketing-site source files and v2 integration docs` (84 files — full marketing-site Next.js project committed to git)
- `1bc26b5` — `chore: add shadcn to root devDependencies`

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
- `marketing-site/.gitignore` (added `.source/` and `!.env.local.example` rules)

Added/updated:
- Cross-site URL env contract.
- Vercel two-project setup (`marketing-site` + `frontend`) and domain mapping.

## Vercel Configuration (completed 2026-02-23 via API)

### Project A: `acm-marketing-site`
- **Vercel ID**: `prj_pM0jSF8SLL6xheNPTqt0TWmAasYU`
- **Root Directory**: `marketing-site`
- **Framework**: Next.js
- **Git repo**: `CoralShades/acm-ai` → branch `release`
- **Domain**: `vaea.coralshades.ai` ✅ assigned
- **Env vars**: `NEXT_PUBLIC_APP_URL=https://demo.vaea.coralshades.ai` ✅

### Project B: `frontend`
- **Vercel ID**: `prj_7uWhAMwVWvnKte9HfhxkKBNlbMRz`
- **Root Directory**: `frontend`
- **Framework**: Next.js
- **Git repo**: `CoralShades/acm-ai` → branch `release`
- **Domain**: `demo.vaea.coralshades.ai` ✅ assigned
- **Env vars**: `NEXT_PUBLIC_MARKETING_URL=https://vaea.coralshades.ai` ✅

## BMAD Artifact Updates

- `_bmad-output/project-planning-artifacts/acm-ai/03-prd.md` (v1.6, FR-1100 section)
- `_bmad-output/project-planning-artifacts/acm-ai/04-architecture.md` (v1.3, multi-project topology)
- `_bmad-output/project-planning-artifacts/acm-ai/05-epics-and-stories.md` (Epic 20 added)
- `_bmad-output/project-planning-artifacts/acm-ai/bmm-workflow-status.yaml` (updated)
- `docs/sprint-artifacts/sprint-status.yaml` (E18 done, E19 done, E20 done — merged conflict)
- `docs/sprint-artifacts/e20-s1-marketing-to-app-linking.md` (new)
- `docs/sprint-artifacts/e20-s2-app-to-marketing-navigation-cutover.md` (new)
- `task_plan.md`, `findings.md`, `progress.md` (planning-with-files logs)

## Validation Results

### Passed

- `marketing-site`: `npm run lint` (previous session)
- `frontend`: `npm run lint` (previous session)
- `git push origin release`: ✅ pushed (3 new commits on 2026-02-23)
- `demo.vaea.coralshades.ai` (frontend): ✅ **LIVE** — sidebar shows "Visit Landing" → `https://vaea.coralshades.ai`
- `vaea.coralshades.ai` (marketing): ⏳ build in progress (commit `1bc26b5`)

### Blocked in Previous Session (now resolved)

- `git push` was blocked by non-fast-forward (remote had new commits) → fixed by `git merge origin/release` + conflict resolution.
- `marketing-site` files were never committed to git → fixed in `78c537c` (84 files).
- `vercel deploy --prod --yes` was blocked by `spawn EPERM` → replaced with Vercel REST API calls.

## Notes

- Vercel projects were created/configured entirely via the Vercel REST API (token from `.env`).
- `vaea.coralshades.ai` was previously on the `frontend` project and was migrated to `acm-marketing-site`.
- `demo.vaea.coralshades.ai` is newly assigned to the `frontend` project.
- The `release` branch is the source of truth for both Vercel projects.
- `marketing-site/.gitignore` excludes `.source/` (Fumadocs cache), `.next/`, `.env*` and allows `.env.local.example`.
