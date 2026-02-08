# Findings: UX Audit & Enterprise Readiness

> **Updated:** 2026-02-08
> **Project:** ACM-AI Frontend -> VAEA ACM-AI

---

## 1. Current Frontend Architecture

### Navigation Structure (Brownfield)
The sidebar has 4 sections with 11 nav items:
- **Collect:** Sources, Documents, ACM Register
- **Process:** Notebooks, Ask and Search
- **Create:** Podcasts
- **Manage:** Models, Transformations, Settings, Advanced

**Issues:**
- "Collect/Process/Create/Manage" taxonomy is confusing for ACM compliance officers
- Podcasts, Transformations, Notebooks are irrelevant to ACM workflow
- "Create" button offers Source/Notebook/Podcast - should be single "Upload Document"
- No extraction settings in navigation (needed for E12 stories)

### Current Pages
| Route | Purpose | Keep/Remove |
|-------|---------|-------------|
| `/` | Dashboard with bento grid stats | KEEP - redesign for VAEA |
| `/sources` | Source list (grid/table view) | KEEP - rename "Documents" |
| `/sources/[id]` | Source detail with ACM tab | KEEP - core workflow |
| `/documents` | Document library view | KEEP - merge with sources |
| `/acm` | Standalone ACM register view | KEEP - core feature |
| `/search` | Ask and search | KEEP - simplify |
| `/notebooks` | Notebook list | HIDE from nav |
| `/notebooks/[id]` | Notebook detail with chat | HIDE from nav |
| `/podcasts` | Podcast generation | HIDE from nav |
| `/models` | AI model configuration | KEEP -> move to Settings |
| `/transformations` | Text transformations | HIDE from nav |
| `/settings` | General settings | KEEP - expand for extraction |
| `/advanced` | System info, rebuild embeddings | KEEP -> merge into Settings |

### Component Quality Assessment
- **ACM Components (good):** Well-structured - ACMGrid, ACMToolbar, BuildingTabs, SiteConfigPanel, ACMCellViewer, ACMRecordDialog, ACMStatsCards, ACMExtractionBanner
- **Upload Components (good):** Multi-step wizard with FileDropzone, DocumentTypeStep, ProcessingOptionsStep, ReviewStep, UploadProgressStep
- **UI Components (good):** Full shadcn/ui library - 30+ base components
- **State Management (good):** Zustand stores (auth, navigation, sidebar, theme, upload, notebook-columns) + React Query hooks for server state
- **Loading (basic):** Simple LoadingSpinner, basic extraction banner with spinner. NO skeleton screens, NO multi-stage pipeline progress

### Extraction Status (Current)
The `useExtractionStatus` hook tracks: `idle -> extracting -> completed -> failed`
- Only shows a basic Alert banner with a spinning icon
- No visibility into WHICH stage is running
- No detail about what the AI is doing
- No progress percentage or time estimate

---

## 2. VAEA Brand Analysis

### Official Brand Colors
| Token | Hex | Usage |
|-------|-----|-------|
| Primary Teal | #01A09C / #53A69D | Primary action color |
| Deep Teal | #2A5951 / #01706D | Hover states, headings |
| Light Teal | #9AD9D9 / #75D4D0 | Backgrounds, soft accents |
| Green Accent | #A9D9AC / #95D60C | Success, environmental theme |
| Focus Ring | #EB787A | Accessibility focus indicator |
| Grey Background | #F2F2F2 | Page background |
| Charcoal | #1F1F1F / #4C4D52 | Primary text |
| VAEA Gradient | teal -> lime -> gold | Hero/accent gradient |

### Dark Mode Palette (from sample)
| Token | Hex |
|-------|-----|
| Page BG | #0F1F1D |
| Surface | #162B28 |
| Text Primary | #E6F2F1 |
| Text Secondary | #B8D9D6 |
| Border | #244743 |
| Brand Primary | #9AD9D9 |
| Brand Hover | #A9D9AC |

### Government Design Patterns
- Left-border accent cards (6px teal border)
- System font stack (no custom fonts - accessibility)
- 12px border radius (modern but professional)
- Subtle shadows: `0 4px 12px rgba(42, 89, 81, 0.08)`
- Aboriginal/Torres Strait Islander acknowledgment in footer
- Accessibility: WCAG 2.1 AA minimum for government

### Brand Assets Collected
- `VAEA_Ripple2_FavIcon_0.png` - Square icon (ripple pattern)
- `VAEA-Ripple2-Logo_Print.png` - Full logo with text
- `favicon.ico` - Browser favicon
- `CS_Logo.svg` - CoralShades vendor logo (for footer)
- `CS_Favicon.svg` - CoralShades vendor icon

---

## 3. Extraction Pipeline Stages (for AG-UI)

From sprint change proposals, the full extraction pipeline:

```
STAGE -1: STRUCTURE ANALYSIS (E1-S16..S19)
+-- TOC Extraction & Document Structure
+-- Building Inventory Compilation
+-- Page-Level Section Tagging
+-- Document Metadata Extraction

STAGE 0: PREFLIGHT
+-- Format detection (Prensa/Greencap/Generic)
+-- Content hash & dedup check
+-- Parser selection

STAGE 0.5: AGENTIC ORCHESTRATOR (E1-S20)
+-- Section analysis
+-- Tool selection (MinerU/Docling/Regex)
+-- Dynamic routing per section

STAGE 1: EXTRACT
+-- Verbatim extraction with provenance
+-- Page, table ID, row/column, bounding box
+-- Raw ACM items output

STAGE 2: INTERPRET
+-- Field mapping (consultant -> BAR)
+-- Value normalization (synonyms -> enums)
+-- Product classification (taxonomy)
+-- Business rule application

STAGE 2.5: CORRECTIVE VALIDATION (E1-S15)
+-- Schema validation
+-- LLM re-extraction on failure
+-- Max 3 correction attempts

STAGE 3: ENRICH & STORE
+-- Contextual embedding enrichment (E1-S14)
+-- Parent document sections (E11-S1)
+-- SurrealDB storage
+-- Vector embedding generation
```

Each stage should be visualized in the UI with:
- Stage name and icon
- Status: pending / running / complete / failed
- Duration timer
- Expandable detail showing agent decisions
- Record count (where applicable)

---

## 4. Features to Hide/Remove

### Components to Hide from Navigation
| Component | Directory | Action |
|-----------|-----------|--------|
| Podcasts page | `app/(dashboard)/podcasts/` | Remove from sidebar |
| Podcast components | `components/podcasts/` | Keep code, remove nav entry |
| Transformations page | `app/(dashboard)/transformations/` | Remove from sidebar |
| Transformation components | `components/(dashboard)/transformations/` | Keep code, remove nav entry |
| Notebooks page | `app/(dashboard)/notebooks/` | Remove from sidebar |
| Notebook components | `components/notebooks/` | Keep code, remove nav entry |

### Navigation Redesign Target
```
VAEA ACM-AI
---------------------
[Upload Document]  (primary CTA)
---------------------
WORKSPACE
  Dashboard
  Documents         (merged sources + documents)
  ACM Register
  Search
---------------------
CONFIGURE
  Extraction        (E12-S1)
  AI Models         (existing models page)
  Parsers           (E12-S4)
  Processing        (E12-S3)
  General           (existing settings + advanced merged)
---------------------
[VAEA Logo]
Powered by CoralShades
[Theme Toggle] [Sign Out]
```

---

## 5. Enterprise Readiness Gaps

### Current Gaps
1. **No skeleton loading** - Just a spinner, no content placeholders
2. **No pipeline progress** - Basic "extracting..." banner, no stage visibility
3. **No offline/disconnect handling** - ConnectionGuard exists but basic
4. **No session timeout** - Auth check on mount only
5. **No WCAG audit** - Color contrast, focus management, aria labels incomplete
6. **No breadcrumbs** - Deep pages have no context
7. **No toast system for long ops** - Using Alert inline only
8. **No keyboard shortcuts beyond Cmd+K** - CommandPalette exists but limited
9. **No export progress** - No feedback during BAR Excel generation
10. **No batch operation feedback** - Bulk actions have no progress

### Priority Fixes for Enterprise
1. Multi-stage pipeline visualization (AG-UI) - P0
2. VAEA branding + design tokens - P0
3. Skeleton loading screens - P1
4. Navigation simplification - P1
5. Toast/notification system enhancement - P1
6. WCAG 2.1 AA accessibility - P1
7. Error recovery patterns - P2
8. Keyboard navigation - P2

---

## 6. Dual-Persona UX Considerations

### Compliance Officer (Non-technical)
- Simple upload -> wait -> review -> export flow
- Clear risk indicators (color-coded, large text)
- Minimal configuration options (use defaults)
- PDF viewer with highlighted citations
- One-click BAR Excel export

### Asbestos Consultant (Technical)
- Bulk document processing
- Parser configuration management
- Extraction method tuning
- Knowledge graph exploration
- Advanced search with filters
- Record editing and validation

### Approach
- Default view optimized for compliance officers
- "Advanced" toggles/tabs reveal consultant features
- Settings pages only in "Configure" section (not in main flow)
- Pipeline transparency is opt-in detail (collapsed by default, expandable)

---

## 7. Technology Research Findings (from Agent Teams)

### AG-UI Protocol (CopilotKit)
- **Status**: Production-ready, backed by Google, LangChain, AWS, Microsoft
- **Core capabilities**: Streaming chat, thinking steps visualization, frontend tool calls, human-in-the-loop interrupts, shared state, tool output streaming
- **Packages**: `@copilotkit/react-core`, `@copilotkit/react-ui`, `@copilotkit/runtime` (frontend), `copilotkit` (Python backend)
- **Integration**: Works directly with LangGraph (already in use at `open_notebook/graphs/acm_extraction.py`)
- **Key hooks**: `useCopilotAction` for extraction actions, replaces polling-based `useExtractionStatus`
- **Impact**: Replace 3-second polling with real-time streaming; show LLM reasoning for product classification

### Pydantic-to-TypeScript Pipeline
- **Recommended tool**: `pydantic-to-typescript` (mature, Pydantic V2 compatible)
- **Alternative**: `datamodel-code-generator` (for OpenAPI schema sync)
- **Usage**: `pydantic2ts --module open_notebook.domain.acm --output frontend/src/lib/types/acm-generated.ts`
- **CI/CD**: GitHub Action watches `open_notebook/domain/*.py` changes, auto-generates and commits TypeScript types
- **Impact**: Single source of truth, catches API contract mismatches at build time

### Skeleton Loading (Enterprise Pattern)
- **Shimmer animation**: CSS keyframes with `background-position` animation (2s linear infinite)
- **ACM-specific**: Grid skeleton matching 8-column layout with 10 shimmer rows
- **Key principle**: Skeleton dimensions must match actual content to prevent CLS (Cumulative Layout Shift)
- **Accessibility**: `aria-busy="true"` and screen reader announcements required

### Toast/Notification Enhancement (Sonner)
- **Promise-based**: `toast.promise()` for extraction jobs (loading → success → error)
- **Manual progress**: `toast.loading()` with `id` for SSE/WebSocket progress updates
- **Human-in-the-loop**: Action buttons in toasts for review workflows
- **Risk-aware**: Custom `className` with `border-l-4 border-risk-high` for alert variants
- **Persistent**: `duration: Infinity` for critical alerts and background job tracking

### Knowledge Graph (React Flow)
- **Package**: `reactflow@11` (latest stable)
- **ACM hierarchy**: School → Building → Room → ACM Item nodes with risk-color edges
- **Custom nodes**: Building nodes show record count + high-risk count
- **Performance**: Virtualization for 1000+ nodes, viewport-based lazy loading

### Animation Strategy
- **CSS**: Hover effects, skeleton loaders, spinners, simple transitions
- **Framer Motion**: Layout animations, gesture interactions, complex orchestration, physics-based movement
- **Motion.dev**: 8KB alternative for performance-critical scenarios

### Design System (Tailwind 4 CSS-First)
- **@theme vs :root**: Use `@theme` for utility class generation, `:root` for CSS-only variables
- **OKLCH**: Already in use - perceptual uniformity for color adjustments
- **v4 benefits**: 5x faster full builds, 100x faster incremental (Rust engine), runtime theming
- **Radix UI update**: Unified `radix-ui` single package (Feb 2026) replaces per-component `@radix-ui/react-*`

---

## 8. Current Component Inventory Summary

### By Domain
| Domain | Components | Files | Quality |
|--------|-----------|-------|---------|
| ACM | 11 | 11 | Good - well-structured, clear separation |
| Upload | 6 | 7 (+ types) | Good - wizard pattern with dropzone |
| UI (shadcn) | 36 | 38 (+ wizard/) | Good - full library |
| Common | 10 | 10 | Good - CommandPalette, ErrorBoundary, etc. |
| Source | 10 | 10 | Good - detail, chat, insights panels |
| Documents | 7 | 7 | Good - library view with filters |
| Podcasts | 7 | 7 | HIDE - not ACM relevant |
| Notebooks | 3 | 3 | HIDE - not ACM relevant |
| Dashboard | 2 | 2 | Redesign for VAEA |
| Layout | 2 | 2 | Redesign sidebar |
| Auth | 1 | 1 | Keep |

### API Modules (15 files)
All at `frontend/src/lib/api/`: client, acm, sources, notebooks, notes, chat, source-chat, search, models, transformations, podcasts, insights, embedding, settings, query-client

### Hooks (25+)
ACM-specific (4), General domain (11), Utility (10+)
