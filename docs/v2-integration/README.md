# V2 Integration Handoff

This folder contains the handoff package for the marketing-app integration and Vercel domain cutover work.

## Contents

- `IMPLEMENTED-CHANGES.md`: What was implemented, all commits, Vercel config, and validation status.
- `NEXT-STEPS-AGENTS.md`: Current state table, startup checklist, and remaining P0/P1 tasks.

## Commits (release branch)

| SHA | Description |
|-----|-------------|
| `893c70f` | `feat(web): link marketing and app navigation with Vercel domain contract` |
| `27ff481` | `Merge remote-tracking branch 'origin/release' into release` (sprint-status conflict resolved) |
| `78c537c` | `feat(web): add marketing-site source files and v2 integration docs` (84 files) |
| `1bc26b5` | `chore: add shadcn to root devDependencies` |
| `b8cb4a3` | `docs(v2-integration): update handoff docs with deploy session results` |
| `0c6cbbd` | `fix(marketing): add explicit type annotation to footerLinks to fix TS union error` |

## Current Live State

| URL | Status | Project |
|-----|--------|---------|
| `https://demo.vaea.coralshades.ai` | ✅ **LIVE** | `frontend` (`prj_7uWhAMwVWvnKte9HfhxkKBNlbMRz`) |
| `https://vaea.coralshades.ai` | ⏳ TS fix pushed, build queued | `acm-marketing-site` (`prj_pM0jSF8SLL6xheNPTqt0TWmAasYU`) |

## Scope Covered

- Marketing site links to app via `Open App` (header, hero, footer).
- App links back to marketing landing/docs (sidebar, command palette).
- Env contract fully configured on Vercel:
  - `NEXT_PUBLIC_APP_URL=https://demo.vaea.coralshades.ai` (marketing project)
  - `NEXT_PUBLIC_MARKETING_URL=https://vaea.coralshades.ai` (frontend project)
- `vaea.coralshades.ai` moved from `frontend` project to `acm-marketing-site` project.
- `demo.vaea.coralshades.ai` added to `frontend` project.
- BMAD artifacts updated (`PRD`, `Architecture`, `Epics/Stories`, `Sprint Status`, `Workflow Status`).
- `sprint-status.yaml` merge conflict resolved: E18 + E19 + E20 all marked done.
