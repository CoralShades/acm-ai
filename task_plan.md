# Epic 14: UX & Enterprise Readiness - Story Execution Queue

> **Created:** 2026-02-08
> **Mode:** IMPLEMENTATION (Ralph Loop)
> **Branch:** lane-b
> **Worktree:** `/mnt/d/ailocal/acm-ai-frontend/`

---

## Story Queue

| # | Story | Priority | Tech Spec | Status |
|---|-------|----------|-----------|--------|
| 1 | E14-S1 | P0 | tech-spec-e14-s1-vaea-branding-design-tokens.md | done |
| 2 | E14-S3 | P0 | tech-spec-e14-s3-hide-brownfield-features.md | pending |
| 3 | E14-S2 | P0 | tech-spec-e14-s2-sidebar-navigation.md | pending |
| 4 | E14-S4 | P1 | tech-spec-e14-s4-skeleton-loading-screens.md | pending |
| 5 | E14-S5 | P1 | tech-spec-e14-s5-toast-system.md | pending |
| 6 | E14-S7 | P1 | tech-spec-e14-s7-unified-documents-view.md | pending |
| 7 | E14-S6 | P1 | tech-spec-e14-s6-wcag-accessibility.md | pending |
| 8 | E14-S8 | P2 | tech-spec-e14-s8-error-recovery-disconnect.md | pending |
| 9 | E14-S9 | P2 | tech-spec-e14-s9-keyboard-navigation.md | pending |
| 10 | E14-S10 | P2 | tech-spec-e14-s10-breadcrumb-navigation.md | pending |
| 11 | E14-S11 | P2 | tech-spec-e14-s11-pydantic-typescript-types.md | pending |

## Current Focus
- **Active Story:** E14-S3 (Hide Brownfield Features)
- **Phase:** 1 - PLAN

## Ordering Rationale
- S1 first: Foundational design tokens that all other stories depend on
- S3 before S2: S3 is independent; S2 depends on S1 token system
- S7 before S6: S6 (accessibility audit) benefits from all UI changes being in place
- P2 stories last: Lower priority, fewer dependencies
