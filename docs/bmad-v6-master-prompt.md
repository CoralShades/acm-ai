# BMAD v6 Master Prompt: UX & Enterprise Readiness Implementation

> **Version:** 6.0
> **Created:** 2026-02-08
> **Target Branch:** `lane-b` (Frontend worktree)
> **Worktree:** `/mnt/d/ailocal/acm-ai-frontend/`
> **Purpose:** Guide implementation of Epic 14 (UX & Branding) and integration with existing Epics 10-13

---

## Instructions for Claude Code / BMAD Agents

You are implementing the **UX Audit & Enterprise Readiness** initiative for the ACM-AI frontend. This is a **Lane B (frontend-only)** effort on the `lane-b` branch. You must:

1. **ADD** Epic 14 and its 11 stories to the existing epics-and-stories document as a NEW epic
2. **MODIFY** the PRD to add new frontend requirements (FR-700 series: UX & Branding) without overwriting any existing requirements
3. **EXTEND** the architecture document with new frontend components and design system sections
4. **UPDATE** the sprint-status.yaml to include Epic 14 stories (Lane A owns this file -- create a change proposal instead if you cannot directly edit)
5. **NEVER** overwrite or remove existing epics, stories, requirements, or architecture decisions
6. **FOLLOW** the concurrent-workflow-protocol.md for cross-lane coordination

---

## Specification Documents (Source of Truth)

All specifications are in `/mnt/d/ailocal/acm-ai-frontend/docs/`. Read these BEFORE implementing:

| Document | Size | Key Content |
|----------|------|-------------|
| `ux-audit.md` | 38KB | 30 findings with severity ratings, current-vs-ideal user flows, page-by-page review |
| `design-system.md` | 45KB | VAEA color tokens (hex + OKLCH), light/dark mode, component variants, AG Grid theme, migration checklist |
| `ui-ux-spec.md` | 47KB | Information architecture, 6 user flow diagrams, ASCII wireframes, dual-persona UX, responsive breakpoints |
| `ag-ui-pipeline-spec.md` | 53KB | 7-stage pipeline visualization, SSE event schema, CopilotKit integration, TypeScript interfaces, Pydantic models |
| `state-loading-spec.md` | 65KB | Zustand store audits, 3 new stores, skeleton screen components, shimmer CSS, toast patterns, error recovery |
| `navigation-cleanup-spec.md` | 31KB | Before/after AppSidebar code, route merging, command palette cleanup, VAEA branding changes |
| `implementation-priorities.md` | 6KB | P0-P3 priority matrix, 5-wave implementation sequence, dependency graph |

Supporting files:
| File | Content |
|------|---------|
| `findings.md` | Research synthesis: AG-UI protocol, pydantic-to-typescript, enterprise UI patterns |
| `task_plan.md` | Original 10-phase task plan |
| `progress.md` | Session log with timestamps and deliverable tracking |

---

## Epic 14: UX & Branding (NEW)

### Epic Summary

**Title:** UX & Enterprise Readiness
**Priority:** P0/P1 (mixed -- see per-story priority)
**Owner:** Lane B (Frontend)
**Dependency:** E14-S1 (Design Tokens) is foundational -- all other E14 stories depend on it
**Total Stories:** 11
**Estimated Effort:** 12-17 days

### Stories

#### E14-S1: Apply VAEA Branding and Design Tokens (P0)
**As a** government client
**I want** the application to use VAEA's official branding
**So that** it meets government presentation standards

**Acceptance Criteria:**
- [ ] CSS custom properties defined for VAEA color palette (light + dark mode)
- [ ] Tailwind 4 `@theme inline` configured with VAEA tokens
- [ ] OKLCH color space used for all brand colors
- [ ] VAEA logo (`VAEA-Ripple2-Logo_Print.png`) replaces current logo
- [ ] VAEA favicon replaces current favicon
- [ ] CoralShades vendor attribution in sidebar footer
- [ ] Focus ring color set to VAEA coral (#EB787A) for accessibility
- [ ] Government design patterns: left-border accent cards, system font stack, 12px border-radius

**Spec Reference:** `design-system.md` Sections 1-6, 14 (Migration Checklist)

**Key Files to Modify:**
- `frontend/src/app/globals.css` -- Replace `:root` and `.dark` token blocks
- `frontend/tailwind.config.ts` -- Update `@theme inline` section
- `frontend/src/config/branding.ts` -- Update brand config
- `frontend/src/components/brand/Logo.tsx` -- Replace with VAEA logo
- `frontend/public/` -- Replace logo.svg, icon.svg, favicon, manifest.json

---

#### E14-S2: Redesign Sidebar Navigation (P0)
**As a** compliance officer
**I want** a simplified navigation with WORKSPACE and CONFIGURE sections
**So that** I can easily find ACM-related features

**Acceptance Criteria:**
- [ ] Sidebar sections changed to WORKSPACE (Dashboard, Documents, ACM Register, Search) and CONFIGURE (Extraction, AI Models, Parsers, Processing, General)
- [ ] "Upload Document" primary CTA button at top of sidebar
- [ ] Create button dropdown replaced with single "Upload Document" action
- [ ] VAEA logo and CoralShades footer in sidebar
- [ ] Theme toggle and sign out in sidebar footer

**Spec Reference:** `navigation-cleanup-spec.md` Section 3, `ui-ux-spec.md` Section 3
**Depends On:** E14-S1 (needs VAEA tokens for sidebar styling)

**Key Files to Modify:**
- `frontend/src/components/layout/AppSidebar.tsx`
- `frontend/src/lib/stores/navigation-store.ts`
- `frontend/src/components/common/AddButton.tsx`

---

#### E14-S3: Hide Brownfield Features from Navigation (P0)
**As a** product owner
**I want** Podcasts, Transformations, and Notebooks hidden from navigation
**So that** the UI focuses on ACM compliance workflow

**Acceptance Criteria:**
- [ ] Podcasts removed from sidebar nav items
- [ ] Transformations removed from sidebar nav items
- [ ] Notebooks removed from sidebar nav items (pages still accessible via direct URL)
- [ ] Command palette entries for hidden features removed
- [ ] Create dialog no longer shows Notebook or Podcast options
- [ ] Code is preserved (not deleted) -- only nav entries removed

**Spec Reference:** `navigation-cleanup-spec.md` Section 4

**Key Files to Modify:**
- `frontend/src/components/layout/AppSidebar.tsx`
- `frontend/src/components/common/CommandPalette.tsx`
- `frontend/src/components/common/AddButton.tsx` or create dialog

---

#### E14-S4: Add Shimmer Skeleton Loading Screens (P1)
**As a** user
**I want** skeleton loading placeholders on every page
**So that** I see content structure immediately instead of a blank screen

**Acceptance Criteria:**
- [ ] Skeleton screen for Dashboard (bento grid layout)
- [ ] Skeleton screen for Documents page (card grid + filters)
- [ ] Skeleton screen for ACM Register (toolbar + AG Grid rows)
- [ ] Skeleton screen for Source Detail (panels layout)
- [ ] Skeleton screen for Search page
- [ ] Shimmer animation with CSS keyframes (2s linear infinite)
- [ ] Dark mode adaptation (lighter shimmer on dark surfaces)
- [ ] `aria-busy="true"` and screen reader announcements
- [ ] Zero CLS (skeleton dimensions match actual content)

**Spec Reference:** `state-loading-spec.md` Section 4

---

#### E14-S5: Enhance Toast System with Promise-Based Patterns (P1)
**As a** user
**I want** informative toast notifications during long operations
**So that** I know what's happening with extraction, export, and processing

**Acceptance Criteria:**
- [ ] Sonner `toast.promise()` used for extraction start/complete/fail
- [ ] Sonner `toast.promise()` used for Excel/CSV export
- [ ] Loading toast with manual ID for SSE/polling progress updates
- [ ] Risk-aware toast variants (border-l-4 with risk colors)
- [ ] Persistent toasts (`duration: Infinity`) for critical alerts
- [ ] Action buttons in toasts for human-in-the-loop workflows

**Spec Reference:** `state-loading-spec.md` Section 6

---

#### E14-S6: WCAG 2.1 AA Accessibility Audit and Fixes (P1)
**As a** government application
**I want** WCAG 2.1 AA compliance
**So that** the application meets government accessibility mandates

**Acceptance Criteria:**
- [ ] All interactive elements have visible focus indicators (VAEA coral ring)
- [ ] Color contrast ratio meets 4.5:1 for normal text, 3:1 for large text
- [ ] All images and icons have appropriate alt text or aria-labels
- [ ] AG Grid keyboard navigation verified and documented
- [ ] Form inputs have associated labels
- [ ] Pipeline visualization has `aria-live` regions for status updates
- [ ] Skip-to-content link on all pages
- [ ] Reduced motion preference respected (`prefers-reduced-motion`)

**Spec Reference:** `ux-audit.md` Finding ACC-01, `design-system.md` Section 8

---

#### E14-S7: Merge Sources and Documents into Unified View (P1)
**As a** user
**I want** a single Documents page instead of separate Sources and Documents views
**So that** I have one place to find all my uploaded files

**Acceptance Criteria:**
- [ ] `/sources` and `/documents` merged into unified `/documents` route
- [ ] `/sources` redirects to `/documents` via middleware
- [ ] `/sources/[id]` continues to work (source detail page)
- [ ] Grid/table/list view toggle preserved
- [ ] All document filters available
- [ ] Bulk actions preserved

**Spec Reference:** `navigation-cleanup-spec.md` Section 5

---

#### E14-S8: Improve Error Recovery and Disconnect Handling (P2)
**As a** user
**I want** graceful handling of connection drops and errors
**So that** I don't lose my work or get confused when something fails

**Acceptance Criteria:**
- [ ] Enhanced `ConnectionGuard` with reconnection attempts
- [ ] Session timeout detection with re-authentication prompt
- [ ] Offline indicator banner
- [ ] Route-level error boundaries on all dashboard pages
- [ ] Retry logic in API client for transient failures
- [ ] Network status check on window focus

**Spec Reference:** `state-loading-spec.md` Section 8

---

#### E14-S9: Expand Keyboard Navigation and Shortcuts (P2)
**As a** power user
**I want** keyboard shortcuts for common actions
**So that** I can work efficiently without a mouse

**Acceptance Criteria:**
- [ ] Command palette (Cmd+K) entries for all primary actions
- [ ] AG Grid keyboard navigation (arrow keys, Enter to expand)
- [ ] Escape to close dialogs/panels
- [ ] Tab navigation through pipeline stages
- [ ] Shortcut cheat sheet accessible via `?` key

**Spec Reference:** `ux-audit.md` Finding NAV-03

---

#### E14-S10: Add Breadcrumb Navigation for Deep Pages (P2)
**As a** user viewing a source detail page
**I want** breadcrumb navigation showing my location
**So that** I can easily navigate back to the parent page

**Acceptance Criteria:**
- [ ] Breadcrumb component created following VAEA design tokens
- [ ] Breadcrumbs shown on: Source detail, ACM Register (within source), Notebook detail
- [ ] Links are functional (clicking "Documents" goes to documents list)
- [ ] Responsive: truncated with ellipsis on mobile

**Spec Reference:** `ui-ux-spec.md` Section 7

---

#### E14-S11: Set Up Pydantic-to-TypeScript Type Generation (P2)
**As a** developer
**I want** TypeScript types auto-generated from Python Pydantic models
**So that** frontend and backend types are always in sync

**Acceptance Criteria:**
- [ ] `scripts/generate_types.py` created
- [ ] Generates TypeScript interfaces from ACMRecord, ACMExtractionOutput, etc.
- [ ] Output to `frontend/src/lib/types/generated/`
- [ ] `npm run generate:types` script in package.json
- [ ] CI workflow detects type drift on PRD model changes

**Spec Reference:** `ag-ui-pipeline-spec.md` Section 7

---

## PRD Additions (FR-700 Series: UX & Branding)

Add these to the existing PRD as a NEW section `2.8 UX & Enterprise Readiness (FR-700 Series)`:

```markdown
### 2.8 UX & Enterprise Readiness (FR-700 Series)

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-701 | System shall use VAEA government branding (teal palette, logo, favicon) | P0 | All brand colors match VAEA specification |
| FR-702 | Navigation shall use WORKSPACE + CONFIGURE taxonomy | P0 | Sidebar redesigned per navigation-cleanup-spec |
| FR-703 | Brownfield features (Podcasts, Transformations, Notebooks) shall be hidden from navigation | P0 | Features inaccessible from nav but code preserved |
| FR-704 | All pages shall display skeleton loading placeholders during data fetch | P1 | Zero CLS, shimmer animation, aria-busy |
| FR-705 | Toast notifications shall provide promise-based feedback for long operations | P1 | Extraction/export shows loading→success→error toasts |
| FR-706 | Application shall meet WCAG 2.1 AA accessibility standards | P1 | Color contrast, focus management, aria labels verified |
| FR-707 | Sources and Documents pages shall be merged into unified Documents view | P1 | Single /documents route with redirect from /sources |
| FR-708 | Application shall gracefully handle connection drops and session timeouts | P2 | Reconnection, offline indicator, timeout prompt |
| FR-709 | Keyboard navigation shall support all primary workflows | P2 | Command palette, grid nav, dialog shortcuts |
| FR-710 | Deep pages shall display breadcrumb navigation | P2 | Source detail, ACM register breadcrumbs |
| FR-711 | TypeScript types shall be auto-generated from Python Pydantic models | P2 | generate_types.py script, CI drift detection |
```

---

## Architecture Additions

Add a new section `6. Frontend Design System Architecture` to the architecture document:

### 6.1 VAEA Design Token System

```
CSS Custom Properties (:root / .dark)
    └── Tailwind 4 @theme inline
        └── Component-level tokens (shadcn/ui variants)
            └── AG Grid theme overrides
```

- **Color Space:** OKLCH for perceptual uniformity
- **Token Layers:** Brand → Semantic → Component
- **Dark Mode:** Class-based toggle (`.dark` class on `<html>`)
- **Reference:** `design-system.md`

### 6.2 Pipeline Visualization Architecture

```
Browser ──SSE──> FastAPI ──Events──> LangGraph Nodes
                    │
    PipelineEventEmitter (asyncio.Queue per subscriber)
```

- **Transport:** SSE (Phase 1), AG-UI/CopilotKit (Phase 2)
- **State:** Zustand `pipeline-progress-store`
- **Fallback:** 3-second polling via existing `useExtractionStatus`
- **Reference:** `ag-ui-pipeline-spec.md`

### 6.3 State Management Extensions

Three new Zustand stores:
1. `pipeline-progress-store` -- Multi-stage extraction tracking
2. `notification-store` -- Persistent background job alerts
3. `feature-flags-store` -- Dual-persona mode (simple vs advanced)

- **Reference:** `state-loading-spec.md`

---

## Implementation Sequence

### Wave 1: Foundation (Days 1-3) -- P0
1. **E14-S1** -- VAEA design tokens (CSS custom properties, Tailwind 4 @theme)
2. **E14-S3** -- Hide Podcasts/Transformations/Notebooks from nav
3. **E14-S2** -- Redesign sidebar to WORKSPACE + CONFIGURE

### Wave 2: Loading & Feedback (Days 4-6) -- P1
4. **E14-S4** -- Shimmer skeleton screens for all pages
5. **E14-S5** -- Toast system enhancement (Sonner promise patterns)
6. **E14-S7** -- Merge sources + documents pages

### Wave 3: Pipeline Visualization (Days 7-11) -- P0/P1
7. **E12-S1 + E12-S3 + E12-S4** -- Settings consolidation (cross-lane dependency)
8. Pipeline visualization component (from `ag-ui-pipeline-spec.md`)
9. Extraction status upgrade to multi-stage

### Wave 4: Accessibility & Polish (Days 12-15) -- P1/P2
10. **E14-S6** -- WCAG 2.1 AA fixes
11. **E14-S8** -- Error recovery patterns
12. **E14-S9 + E14-S10** -- Keyboard nav + breadcrumbs

### Wave 5: Advanced Features (Days 16+) -- P2/P3
13. **E14-S11** -- Pydantic-to-TypeScript pipeline
14. AG-UI CopilotKit full integration (E11-S2)
15. Knowledge Graph React Flow (E13-S2, E13-S3)

---

## Dependency Graph

```
E14-S1 (Design Tokens)                           [No dependency - START HERE]
  ├── E14-S2 (Navigation) ──── depends on ──── E14-S3 (Feature Cleanup)
  ├── E14-S4 (Skeletons)
  ├── E14-S5 (Toasts)
  └── E14-S6 (Accessibility)

E14-S7 (Merge Documents)                          [No dependency]

E12-S4 (Parser Config Backend)  [Lane A]
  └── E12-S1 (Extraction Settings UI)  [Lane B]
  └── E12-S3 (Processing Config UI)  [Lane B]

E1-S16..S19 (Pre-extraction Pipeline)  [Lane A]
  └── Pipeline Visualization Component  [Lane B]

E13-S1 (Knowledge Graph Schema)  [Lane A]
  └── E13-S2 → E13-S3 (Graph Explorer UI)  [Lane B]
```

---

## Sprint Status Update (Change Proposal)

Since Lane A owns `sprint-status.yaml`, create a change proposal for the SM to apply:

```yaml
# CHANGE PROPOSAL: Add Epic 14 to sprint-status.yaml
# Date: 2026-02-08
# Reason: UX Audit & Enterprise Readiness initiative
# Lane: B (Frontend)

  # Epic 14: UX & Enterprise Readiness (P0/P1)
  # 0/11 stories complete
  epic-14: backlog
  e14-s1-vaea-branding-design-tokens: backlog
  e14-s2-sidebar-navigation-redesign: backlog
  e14-s3-hide-brownfield-features: backlog
  e14-s4-shimmer-skeleton-loading: backlog
  e14-s5-toast-system-enhancement: backlog
  e14-s6-wcag-accessibility-fixes: backlog
  e14-s7-merge-sources-documents: backlog
  e14-s8-error-recovery-handling: backlog
  e14-s9-keyboard-navigation: backlog
  e14-s10-breadcrumb-navigation: backlog
  e14-s11-pydantic-typescript-pipeline: backlog
  epic-14-retrospective: optional
```

---

## Cross-Lane Coordination Notes

| When Lane A Completes | Lane B Can Start | Notes |
|-----------------------|------------------|-------|
| E1-S11 merged | E12-S4 (Parser Config UI) | Parser display config needed |
| E1-S16..S19 done | Pipeline Visualization | Need backend event emission |
| E13-S1 done | E13-S2, E13-S3 (Graph UI) | Need SurrealDB graph schema |
| -- | E14-S1 through E14-S11 | **No Lane A dependency** for all E14 stories |

Epic 14 can begin immediately -- it has zero cross-lane dependencies.

---

## BMAD Workflow Commands

To start implementing stories, use these BMAD workflows:

```bash
# Create tech spec for a story
/bmad-bmm-create-story E14-S1

# Implement a story with TDD
/bmad-bmm-dev-story E14-S1

# Check implementation readiness
/bmad-bmm-check-implementation-readiness

# Run sprint status
/bmad-bmm-sprint-status

# Create sprint change proposal (for Lane A coordination) - Only After everything is done
/bmad-bmm-correct-course
```

---

## Critical Rules

1. **Read specs before coding.** Every story has a "Spec Reference" pointing to the exact section in the spec documents. Read that section FIRST.
2. **Don't overwrite existing code patterns.** The codebase has established patterns (React Query, Zustand, shadcn/ui). Follow them.
3. 
4. **Build verification required.** Run `cd frontend && npm run build` after every story. Use MCP tools to take a screenshot of the build output. A build failure = incomplete story.
5. **Browser verification for UI stories.** Navigate to the affected page and verify elements exist.
6. **Keep brownfield code.** When hiding features (E14-S3), remove nav entries only. Do NOT delete page files or components.
7. **Lane B only.** Do not modify files owned by Lane A (migrations, sprint-status.yaml, backend Python code). Create change proposals instead.
8. **VAEA tokens are foundational.** E14-S1 MUST be completed before any other E14 story that involves visual changes.
9. **Conventional commits.** Use `feat:`, `fix:`, `refactor:`, `docs:` prefixes.
10. **One story per feature branch.** Branch from `lane-b` as `feature/e14-s1`, merge back to `lane-b`.
11. **Test on both light and dark mode.** VAEA has explicit dark mode tokens -- verify both.
