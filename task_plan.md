# Task Plan: UX Audit & Enterprise Readiness - ACM-AI Frontend

> **Created:** 2026-02-08
> **Status:** PLANNING
> **Worktree:** `/mnt/d/ailocal/acm-ai-frontend/` (lane-b branch)
> **Client:** VAEA (Victorian Asbestos Eradication Agency)
> **Vendor:** CoralShades (footer branding)

---

## Goal

Transform the brownfield ACM-AI frontend from an Open Notebook fork into an enterprise-ready, VAEA-branded document intelligence application. The primary use case is: **Upload asbestos risk assessment PDF -> AI extracts & tabulates ACM data -> Review/validate -> Export BAR-compliant Excel**.

---

## User Answers (Clarification)

| Question | Answer |
|----------|--------|
| Branding | VAEA government branding with CoralShades vendor attribution |
| Target Users | Both: Government compliance officers + Asbestos consultants |
| Agent Visibility | Full transparency - show every pipeline stage live |
| Features to Remove | Podcasts, Transformations, Notes/Notebooks |
| Brand Assets | VAEA logo (teal ripple), favicon, color palette, CS_Logo.svg vendor mark |

---

## Phases

### Phase 0: Research & Discovery `status: in_progress`
- [x] Audit current frontend structure (sidebar, pages, components)
- [x] Read all sprint change proposals for context
- [x] Collect VAEA brand assets and color palette
- [x] Fetch VAEA website design patterns
- [ ] Complete AG-UI / CopilotKit protocol research
- [ ] Complete design system best practices research
- [ ] Document all findings

### Phase 1: UX Audit & Current State Analysis `status: pending`
- [ ] Create comprehensive UX audit document
  - Navigation structure assessment
  - Page-by-page review (all 15+ routes)
  - Component quality assessment
  - Accessibility audit (WCAG 2.1 AA for government)
  - Performance baseline
- [ ] Identify brownfield debt (unused features, dead code)
- [ ] Map current user flows vs ideal user flows
- [ ] Document pain points and friction areas

### Phase 2: UI/UX Specification `status: pending`
- [ ] Define information architecture (IA)
  - Simplified navigation (remove Podcasts, Transformations, Notebooks)
  - Core flows: Upload -> Process -> Review -> Export
  - Secondary flows: Dashboard, Search, Settings, Knowledge Graph
- [ ] Create user flow diagrams for each use case
  - UC-1: Upload PDF and extract ACM data
  - UC-2: Review and validate extracted records
  - UC-3: Export BAR-compliant Excel
  - UC-4: Search and query ACM data
  - UC-5: Configure extraction settings
  - UC-6: View knowledge graph
- [ ] Define page layouts and wireframe specs
- [ ] Define interaction patterns and micro-interactions
- [ ] Define responsive behavior (desktop-first, tablet-responsive)

### Phase 3: Design System & Tokens `status: pending`
- [ ] Create VAEA-branded design token system
  - Color tokens (light + dark mode)
  - Typography scale (government-appropriate)
  - Spacing scale
  - Border radius tokens
  - Shadow/elevation tokens
  - Animation/transition tokens
- [ ] Define component variants
  - Buttons: primary (teal), secondary (outline), ghost, destructive
  - Cards: default, accent (left-border), stat, alert
  - Badges: risk-high (red), risk-medium (amber), risk-low (green), risk-presumed (purple)
  - Status indicators: processing, complete, failed, idle
- [ ] Define icon system (Lucide subset + custom risk icons)
- [ ] Dark mode specification (VAEA dark teal palette)
- [ ] AG Grid theme (VAEA-branded)
- [ ] Gradient specifications (VAEA ripple gradient)

### Phase 4: Agent Pipeline Transparency (AG-UI) `status: pending`
- [ ] Design pipeline visualization component
  - Stage -1: Document Structure Analysis
  - Stage 0: Preflight checks
  - Stage 0.5: Agentic Orchestrator
  - Stage 1: Extract (MinerU/Docling)
  - Stage 2: Interpret (normalize, classify)
  - Stage 2.5: Corrective validation
  - Stage 3: Enrich (contextual embedding)
  - Output: Store + Index
- [ ] Design real-time status updates via WebSocket/SSE
- [ ] Design tool/agent detail panel (expandable)
- [ ] Define Pydantic model -> TypeScript type generation pipeline
- [ ] Design error recovery UI (corrective RAG feedback)

### Phase 5: State Management & Loading Patterns `status: pending`
- [ ] Audit and document all Zustand stores
- [ ] Audit and document all React Query hooks
- [ ] Define loading state patterns:
  - Skeleton screens (page-level, component-level)
  - Pipeline progress (multi-stage with live updates)
  - Optimistic updates for CRUD operations
  - Error boundaries with retry
- [ ] Define toast/notification system for:
  - Extraction started/completed/failed
  - Export ready for download
  - Settings saved
  - Long-running operation updates

### Phase 6: Feature Cleanup & Navigation Redesign `status: pending`
- [ ] Remove/hide from navigation:
  - Podcasts section + all podcast components
  - Transformations section + all transformation components
  - Notes/Notebooks section (keep notebook shell if needed for chat)
- [ ] Redesign sidebar navigation:
  - **Primary:** Dashboard, Documents, ACM Register, Search
  - **Configure:** Settings (extraction, models, parsers, processing)
  - **Footer:** VAEA logo, CoralShades vendor mark, theme toggle, sign out
- [ ] Redesign "Create" button -> "Upload Document" (single action)
- [ ] Simplify command palette (remove podcast/notebook/transform actions)

### Phase 7: VAEA Branding Implementation `status: pending`
- [ ] Replace all brand assets:
  - Logo: VAEA Ripple2 logo (header, sidebar, login)
  - Favicon: VAEA favicon
  - App name: "VAEA ACM-AI" or "VAEA Asbestos Register Manager"
- [ ] Apply VAEA color palette to design tokens
  - Primary: #53A69D (teal-300) / #01A09C (from website)
  - Dark: #2A5951 (teal-700)
  - Light: #9AD9D9 (teal-100)
  - Accent: #A9D9AC (green-200)
  - Background: #F2F2F2 (grey-50)
- [ ] Apply VAEA gradient (teal -> lime -> gold) for accents
- [ ] Add CoralShades vendor attribution in footer
- [ ] Government-appropriate typography (system fonts or approved typeface)
- [ ] Aboriginal/Torres Strait Islander acknowledgment (if required)

### Phase 8: Enterprise Readiness `status: pending`
- [ ] Accessibility compliance (WCAG 2.1 AA)
  - Color contrast ratios
  - Keyboard navigation
  - Screen reader support
  - Focus indicators (VAEA coral red focus ring)
- [ ] Error handling patterns
  - Global error boundary
  - API error recovery
  - Offline/disconnected state
  - Session timeout handling
- [ ] Performance optimization
  - Code splitting per route
  - Image optimization
  - Bundle analysis
- [ ] Security patterns
  - CSP headers
  - Auth state management
  - Session handling

### Phase 9: Documentation & Handoff `status: pending`
- [ ] Complete UI/UX specification document
- [ ] Design system documentation
- [ ] Component inventory
- [ ] Implementation priority guide
- [ ] Create implementation stories for sprint backlog

---

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Design system approach | CSS custom properties + Tailwind | Already using Tailwind 4 + CSS vars; VAEA tokens map cleanly |
| Agent visibility | Full pipeline transparency | User requested; shows every extraction stage live |
| Features removed | Podcasts, Transformations, Notebooks | Not part of ACM compliance use case |
| Navigation model | Simplified 2-section sidebar | Primary (core workflow) + Configure (settings) |
| Client branding | VAEA + CoralShades vendor | Government agency primary, vendor secondary |
| Dark mode | VAEA dark teal palette | Already have dark tokens from sample CSS |
| Animation | CSS transitions + Tailwind animate | Enterprise = subtle, not flashy |

---

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
| CS_Logo.svg too large (185k tokens) | 1 | Skip reading; it's a vector logo file for display |
| (none yet) | | |

---

## Dependencies
- VAEA brand assets: `docs/vaea-assets/` (collected)
- Sprint change proposals: Read and understood
- AG-UI protocol research: In progress (agent)
- Frontend component audit: In progress (agent)
