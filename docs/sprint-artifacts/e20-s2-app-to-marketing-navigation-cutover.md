# E20-S2: App to Marketing Navigation + Domain Cutover Contract

## Story Info
- **Epic**: E20 — Marketing-App Cross-Site Navigation & Domain Cutover
- **Status**: done
- **Priority**: P0
- **Created**: 2026-02-23

## Description
Add app-side links back to marketing landing/docs and define deployment environment contract for Vercel root-domain + demo-subdomain topology.

## Acceptance Criteria
- [x] Sidebar contains `Visit Landing` and `Documentation` links.
- [x] Command palette includes landing/docs external commands.
- [x] URL source is `NEXT_PUBLIC_MARKETING_URL`.
- [x] Env examples include cross-site URL variables.
- [x] Deployment docs include Vercel two-project domain mapping.

## Key Files
- `frontend/src/config/navigation.ts`
- `frontend/src/components/layout/AppSidebar.tsx`
- `frontend/src/components/common/CommandPalette.tsx`
- `frontend/src/lib/site-urls.ts`
- `frontend/.env.example`
- `.env.example`
- `docs/marketing-site/deployment.md`
