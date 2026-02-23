# V2 Integration Handoff

This folder contains the handoff package for the marketing-app integration and Vercel domain cutover work completed on the release branch.

## Contents

- `IMPLEMENTED-CHANGES.md`: What was implemented, where, and validation status.
- `NEXT-STEPS-AGENTS.md`: Exact startup checklist and task list for the next AI agent sessions.

## Primary Commit

- `893c70f` — `feat(web): link marketing and app navigation with Vercel domain contract`

## Scope Covered

- Marketing site links to app via `Open App` (header, hero, footer).
- App links back to marketing landing/docs (sidebar, command palette).
- Env contract added:
  - `NEXT_PUBLIC_APP_URL` (marketing)
  - `NEXT_PUBLIC_MARKETING_URL` (frontend)
- BMAD artifacts updated (`PRD`, `Architecture`, `Epics/Stories`, `Sprint Status`, `Workflow Status`).
