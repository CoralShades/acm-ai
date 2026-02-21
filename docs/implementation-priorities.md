# Implementation Priorities: VAEA ACM-AI Frontend

> **Created:** 2026-02-08
> **Context:** UX Audit & Enterprise Readiness initiative
> **Worktree:** `/mnt/d/ailocal/acm-ai-frontend/` (lane-b branch)

---

## Priority Matrix

### P0 - Critical (Must-have for enterprise launch)

| # | Item | Effort | Sprint Stories | Rationale |
|---|------|--------|---------------|-----------|
| 1 | **VAEA Branding + Design Tokens** | 2-3 days | New: E14-S1 | Government client requirement; all UI flows through brand tokens |
| 2 | **Navigation Simplification** | 1-2 days | New: E14-S2 | Current Collect/Process/Create/Manage taxonomy confuses compliance officers |
| 3 | **Feature Cleanup** | 0.5 day | New: E14-S3 | Remove Podcasts/Transformations/Notebooks from nav; streamline Create button |
| 4 | **Multi-Stage Pipeline Visualization** | 3-5 days | E12-S1, E12-S2 | Core differentiator; user requested full pipeline transparency |
| 5 | **Extraction Status Upgrade** | 2-3 days | E12-S2 | Replace basic `idle/extracting/completed/failed` with 8-stage pipeline view |

### P1 - High (Required for government-grade UX)

| # | Item | Effort | Sprint Stories | Rationale |
|---|------|--------|---------------|-----------|
| 6 | **Skeleton Loading Screens** | 1-2 days | New: E14-S4 | Every page needs shimmer skeletons; enterprise standard |
| 7 | **Toast System Enhancement** | 1 day | New: E14-S5 | Promise-based toasts for extraction, export, and long-running operations |
| 8 | **WCAG 2.1 AA Accessibility** | 2-3 days | New: E14-S6 | Government mandate; color contrast, focus management, aria labels |
| 9 | **Settings Consolidation** | 1-2 days | E12-S1, E12-S3, E12-S4 | Merge Models + Advanced + Settings into tabbed interface |
| 10 | **Documents Page Merge** | 1 day | New: E14-S7 | Merge `/sources` + `/documents` into unified Documents view |

### P2 - Medium (Enterprise polish)

| # | Item | Effort | Sprint Stories | Rationale |
|---|------|--------|---------------|-----------|
| 11 | **Error Recovery Patterns** | 1-2 days | New: E14-S8 | Enhanced ConnectionGuard, session timeout, offline handling |
| 12 | **Keyboard Navigation** | 1 day | New: E14-S9 | Expand CommandPalette, add grid navigation shortcuts |
| 13 | **Breadcrumbs** | 0.5 day | New: E14-S10 | Context for deep pages (source detail, ACM register) |
| 14 | **Export Progress Feedback** | 0.5 day | Part of E5-S2 | Progress indicator during BAR Excel generation |
| 15 | **Pydantic-to-TypeScript Pipeline** | 0.5 day | New: E14-S11 | Auto-generate frontend types from backend models |

### P3 - Nice-to-have (Future enhancements)

| # | Item | Effort | Sprint Stories | Rationale |
|---|------|--------|---------------|-----------|
| 16 | **AG-UI CopilotKit Full Integration** | 5-7 days | E11-S2 (partial) | Replace polling with AG-UI streaming; thinking steps viz |
| 17 | **Knowledge Graph Visualization** | 3-5 days | E13-S2, E13-S3 | React Flow for building→room→ACM entity relationships |
| 18 | **Storybook Documentation** | 2-3 days | New | Component library docs for development team |
| 19 | **Framer Motion Animations** | 1-2 days | New | Layout animations, gesture interactions for pipeline viz |
| 20 | **Batch Operation Progress** | 1 day | Part of E9-S3 | Progress indicator for bulk document operations |

---

## Sprint Story Mapping

### Existing Stories Affected

| Story | Epic | Current Status | UX Audit Impact |
|-------|------|---------------|-----------------|
| E12-S1 | Settings UI | backlog | Extraction settings page → integrate into Settings tab |
| E12-S2 | Settings UI | backlog | Parser display → integrate into Settings tab |
| E12-S3 | Settings UI | backlog | Processing config → integrate into Settings tab |
| E12-S4 | Settings UI | backlog | Parser config from backend → cross-lane handoff |
| E13-S2 | Knowledge Graph | backlog | Graph exploration page → use React Flow |
| E13-S3 | Knowledge Graph | backlog | Graph browsing UI → ACM hierarchy visualization |
| E5-S2 | Export | done | Excel export → add progress feedback |
| E9-S3 | Bulk Operations | done | Bulk actions → add progress indicator |

### New Stories Recommended (Epic 14: UX & Branding)

| Story | Title | Priority | Effort |
|-------|-------|----------|--------|
| E14-S1 | Apply VAEA branding and design tokens | P0 | 2-3 days |
| E14-S2 | Redesign sidebar navigation (WORKSPACE + CONFIGURE) | P0 | 1-2 days |
| E14-S3 | Hide brownfield features from navigation | P0 | 0.5 day |
| E14-S4 | Add shimmer skeleton loading screens | P1 | 1-2 days |
| E14-S5 | Enhance toast system with promise-based patterns | P1 | 1 day |
| E14-S6 | WCAG 2.1 AA accessibility audit and fixes | P1 | 2-3 days |
| E14-S7 | Merge sources and documents into unified view | P1 | 1 day |
| E14-S8 | Improve error recovery and disconnect handling | P2 | 1-2 days |
| E14-S9 | Expand keyboard navigation and shortcuts | P2 | 1 day |
| E14-S10 | Add breadcrumb navigation for deep pages | P2 | 0.5 day |
| E14-S11 | Set up pydantic-to-typescript type generation | P2 | 0.5 day |

**Total new stories: 11** | **Total effort: ~12-17 days**

---

## Implementation Sequence

### Wave 1: Foundation (Days 1-3)
1. E14-S1: VAEA design tokens (CSS custom properties, Tailwind 4 @theme)
2. E14-S3: Hide Podcasts/Transformations/Notebooks from nav
3. E14-S2: Redesign sidebar to WORKSPACE + CONFIGURE

### Wave 2: Loading & Feedback (Days 4-6)
4. E14-S4: Shimmer skeleton screens for all pages
5. E14-S5: Toast system enhancement (Sonner promise patterns)
6. E14-S7: Merge sources + documents pages

### Wave 3: Pipeline Viz (Days 7-11)
7. E12-S1 + E12-S3 + E12-S4: Settings consolidation with extraction/parser/processing tabs
8. Pipeline visualization component (part of E12-S2)
9. Extraction status upgrade to multi-stage

### Wave 4: Accessibility & Polish (Days 12-15)
10. E14-S6: WCAG 2.1 AA fixes (contrast, focus, aria)
11. E14-S8: Error recovery patterns
12. E14-S9 + E14-S10: Keyboard nav + breadcrumbs

### Wave 5: Advanced Features (Days 16+)
13. E14-S11: Pydantic-to-TypeScript pipeline
14. AG-UI CopilotKit full integration
15. Knowledge Graph (React Flow)

---

## Dependencies

```
E14-S1 (Design Tokens)
  └── E14-S2 (Navigation) - needs tokens for VAEA-styled sidebar
  └── E14-S4 (Skeletons) - needs tokens for skeleton colors
  └── E14-S6 (Accessibility) - needs tokens for focus ring color

E14-S3 (Feature Cleanup)
  └── E14-S2 (Navigation) - cleanup before redesign

E12-S4 (Parser Config - Backend)  [Lane A]
  └── E12-S1 (Extraction Settings UI)  [Lane B]
  └── E12-S3 (Processing Config UI)  [Lane B]

E1-S16..S19 (Pre-extraction Pipeline)  [Lane A]
  └── Pipeline Visualization Component  [Lane B]

E13-S1 (Knowledge Graph Schema)  [Lane A]
  └── E13-S2 (Graph Explorer UI)  [Lane B]
```

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| VAEA color discrepancy (sample vs production) | Medium | High | Clarify with stakeholder which palette to use |
| AG-UI protocol complexity | Medium | Medium | Start with SSE-based pipeline viz, add CopilotKit later |
| Inter-worktree conflicts | Low | Medium | Follow concurrent-workflow-protocol.md |
| Accessibility gaps discovered late | Medium | High | Start WCAG audit in Wave 1, fix throughout |
| Settings consolidation complexity | Low | Medium | Tab-based approach keeps existing code intact |

---

## Specification Documents

All specifications produced by the UX Audit team are in `/mnt/d/ailocal/acm-ai-frontend/docs/`:

| Document | Purpose | Status |
|----------|---------|--------|
| `ux-audit.md` | Comprehensive UX audit findings | In progress |
| `design-system.md` | VAEA design tokens and component variants | In progress |
| `ui-ux-spec.md` | User flows, page layouts, interaction patterns | In progress |
| `ag-ui-pipeline-spec.md` | AG-UI pipeline visualization design | In progress |
| `state-loading-spec.md` | State management and loading patterns | In progress |
| `navigation-cleanup-spec.md` | Navigation redesign and feature cleanup | In progress |
| `implementation-priorities.md` | This document - priority matrix and sprint mapping | Complete |
