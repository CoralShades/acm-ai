# Sprint Change Proposal: Epic 14 - UX & Enterprise Readiness

> **Date:** 2026-02-08
> **Proposer:** Lane B (Frontend)
> **Target File:** `docs/sprint-artifacts/sprint-status.yaml`
> **Status:** Pending SM Review

---

## Summary

Add Epic 14: UX & Enterprise Readiness (11 stories) to the sprint tracking system.
This epic was created as part of the UX Audit & Enterprise Readiness initiative, which is
a Lane B (frontend-only) effort with zero cross-lane dependencies.

## Reason for Change

- UX Audit identified 30 findings requiring remediation
- Government compliance mandates professional VAEA branding
- WCAG 2.1 AA accessibility is a government requirement
- Navigation simplification needed for ACM compliance focus
- Enterprise readiness features (skeletons, toasts, error recovery) required

## Spec References

| Document | Content |
|----------|---------|
| `docs/ux-audit.md` | 30 findings with severity ratings |
| `docs/design-system.md` | VAEA color tokens, component variants |
| `docs/ui-ux-spec.md` | Information architecture, wireframes |
| `docs/navigation-cleanup-spec.md` | Sidebar redesign, route merging |
| `docs/state-loading-spec.md` | Loading states, error recovery |
| `docs/ag-ui-pipeline-spec.md` | Pipeline visualization |

## Proposed YAML Addition

Add the following block to `development_status:` in `sprint-status.yaml`, after Epic 13:

```yaml
  # Epic 14: UX & Enterprise Readiness (P0/P1) - NEW 2026-02-08
  # 0/11 stories complete
  # Owner: Lane B (Frontend)
  # Dependencies: E14-S1 is foundational for all visual stories
  epic-14: backlog
  e14-s1-vaea-branding-design-tokens: drafted
  e14-s2-sidebar-navigation-redesign: drafted
  e14-s3-hide-brownfield-features: drafted
  e14-s4-shimmer-skeleton-loading: drafted
  e14-s5-toast-system-enhancement: drafted
  e14-s6-wcag-accessibility-fixes: drafted
  e14-s7-merge-sources-documents: drafted
  e14-s8-error-recovery-handling: drafted
  e14-s9-keyboard-navigation: drafted
  e14-s10-breadcrumb-navigation: drafted
  e14-s11-pydantic-typescript-pipeline: drafted
  epic-14-retrospective: optional
```

## Summary Statistics Update

Update the SUMMARY comment block at the bottom of sprint-status.yaml:

```yaml
# SUMMARY:
# ========
# Total Epics: 14 (6 done, 3 in-progress, 5 backlog)
# Total Stories: 84
# Stories Done: 50 (60%)
# Stories Review: 1 (E1-S11)
# Stories Ready-for-dev: 1 (E1-S12)
# Stories Drafted: 2 (E9-S3, E10-S1)
# Stories Backlog: 30 (existing 19 + 11 new E14 stories)
#
# Last Updated: 2026-02-08
#
# COMPLETED EPICS: E3, E4, E6, E7, E8
# IN-PROGRESS EPICS: E1 (10/19), E2 (7/8), E5 (2/4), E9 (2/3)
# BACKLOG EPICS: E10 (0/1), E11 (0/2), E12 (0/4), E13 (0/3), E14 (0/11)
#
# KEY CHANGES (2026-02-08 - UX Audit & Enterprise Readiness):
# ==============================================================
# - NEW Epic 14: UX & Enterprise Readiness (11 stories, Lane B)
#   - E14-S1: VAEA Branding & Design Tokens (P0)
#   - E14-S2: Sidebar Navigation Redesign (P0)
#   - E14-S3: Hide Brownfield Features (P0)
#   - E14-S4: Shimmer Skeleton Loading (P1)
#   - E14-S5: Toast System Enhancement (P1)
#   - E14-S6: WCAG 2.1 AA Accessibility (P1)
#   - E14-S7: Merge Sources/Documents (P1)
#   - E14-S8: Error Recovery Handling (P2)
#   - E14-S9: Keyboard Navigation (P2)
#   - E14-S10: Breadcrumb Navigation (P2)
#   - E14-S11: Pydantic-to-TypeScript Pipeline (P2)
```

## Impact Assessment

| Aspect | Impact |
|--------|--------|
| Lane A Stories | No impact - E14 has zero Lane A dependencies |
| Existing Epics | No modifications to E1-E13 |
| Sprint Velocity | E14 estimated at 12-17 days (Lane B capacity) |
| Cross-Lane Coordination | None required for E14 stories |

## Implementation Sequence

### Wave 1: Foundation (P0)
1. E14-S1 -- VAEA design tokens (foundational)
2. E14-S3 -- Hide brownfield features
3. E14-S2 -- Sidebar navigation redesign

### Wave 2: Loading & Feedback (P1)
4. E14-S4 -- Shimmer skeleton screens
5. E14-S5 -- Toast system enhancement
6. E14-S7 -- Merge sources/documents pages

### Wave 3: Accessibility & Polish (P1/P2)
7. E14-S6 -- WCAG 2.1 AA fixes
8. E14-S8 -- Error recovery patterns
9. E14-S9 + E14-S10 -- Keyboard nav + breadcrumbs

### Wave 4: Advanced (P2)
10. E14-S11 -- Pydantic-to-TypeScript pipeline

## Dependency Graph

```
E14-S1 (Design Tokens)     [No dependency - START HERE]
  ├── E14-S2 (Navigation)
  ├── E14-S4 (Skeletons)
  ├── E14-S5 (Toasts)
  └── E14-S6 (Accessibility)

E14-S3 (Hide Features)     [No dependency]
E14-S7 (Merge Documents)   [No dependency]
E14-S8 (Error Recovery)    [No dependency]
E14-S9 (Keyboard Nav)      [No dependency]
E14-S10 (Breadcrumbs)      [No dependency]
E14-S11 (Type Generation)  [No dependency]
```

---

**Action Required:** SM to review and apply the YAML changes to `sprint-status.yaml`.
