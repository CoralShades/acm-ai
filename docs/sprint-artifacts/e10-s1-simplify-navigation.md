# E10-S1: Simplify Navigation for ACM-AI Focus

## Story Info
- **Epic**: E10 — ACM-AI UI Simplification
- **Status**: done
- **Priority**: P0
- **Size**: S (Small)
- **Created**: 2025-12-19
- **Dependencies**: None
- **Blocks**: None
- **Tech Spec**: `docs/sprint-artifacts/tech-spec-e10-s1-ui-simplification.md`

## User Story

**As a** ACM compliance user,
**I want** the navigation to focus on ACM document management workflows,
**So that** I can work efficiently without irrelevant menu items.

## Acceptance Criteria

- [x] Hide "Notebooks" navigation item
- [x] Hide "Podcasts" navigation item
- [x] Hide "Transformations" navigation item
- [x] Hide "Advanced" navigation item
- [x] Keep Sources, ACM Register, Ask and Search, Models, Settings navigation
- [x] Navigation items hidden via feature flag or environment config
- [x] Hidden items easily re-enabled via configuration (no hard delete)
- [x] UI feels cohesive with reduced navigation (no empty groups)

## File Changes

| File | Action | Purpose |
|------|--------|---------|
| `frontend/src/config/navigation.ts` | CREATE | Typed NavItem/NavGroup interfaces with hideInAcm/acmOnly flags |
| `frontend/src/components/layout/AppSidebar.tsx` | MODIFY | Import navigation from config, filter by ACM mode |
| `frontend/.env.example` | MODIFY | Add NEXT_PUBLIC_ACM_MODE=true |

## Dev Agent Record
- **Completed**: 2026-02-22
- **Build**: PASS (ruff, frontend build)
- **Files verified**: navigation.ts, AppSidebar.tsx
- **Notes**: Navigation config with hideInAcm flags, environment-based ACM mode filtering.
