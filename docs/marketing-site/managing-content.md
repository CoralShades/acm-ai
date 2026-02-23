# Managing Content

How to update the marketing site's data, text, and visual content.

## Data Files

All dynamic data is centralized in two TypeScript files. Edit these to update stats, pipeline stages, and project metrics site-wide.

### `src/lib/sprint-data.ts`

| Export | Used By | What It Controls |
|--------|---------|-----------------|
| `velocityData` | Status page sparkline | Sprint velocity over time |
| `projectStats` | Stats counter, Status page | Numeric metrics (stories, epics, accuracy, etc.) |
| `barColumns` | Spreadsheet demo | BAR column definitions for the demo table |
| `techStack` | Architecture section | Technology layer/purpose table |
| `pipelineStages` | Pipeline preview, Demo pipeline | 7-stage extraction pipeline definitions |
| `logLines` | Demo pipeline section | Terminal log simulation lines |
| `gridRows` | Spreadsheet demo | Sample ACM register data rows |

### `src/lib/epic-data.ts`

| Export | Used By | What It Controls |
|--------|---------|-----------------|
| `epics` | Status page, Roadmap | 16 completed epic definitions with story counts |
| `futureEpics` | Roadmap page | E18-E20 planned epic cards |
| `audienceData` | StakeholderTabs, StakeholdersSection | Director/CTO/CEO/Client value propositions |

## Updating Statistics

To update project-wide statistics (e.g., after completing new stories):

1. Edit `src/lib/sprint-data.ts`:
   ```typescript
   export const projectStats = {
     totalStories: 123,     // ← Update count
     completedStories: 113, // ← Update count
     accuracy: 96,          // ← Update percentage
     // ...
   };
   ```

2. The following components auto-update:
   - Landing page StatsCounter
   - Status page progress rings
   - Demo ProgressSection charts

## Updating the Landing Page

### Hero Section (`src/components/landing/Hero.tsx`)
- Headline text and subheadline are hardcoded in JSX
- Counter row values come from `projectStats` in sprint-data.ts
- CTA button text/links are inline

### How It Works (`src/components/landing/HowItWorks.tsx`)
- 3 cards with icons, titles, descriptions — edit the `steps` array
- Lottie animation URLs are in the component (with SVG fallbacks)

### Pipeline Preview (`src/components/landing/PipelinePreview.tsx`)
- Uses `pipelineStages` from sprint-data.ts
- Glass-morphism cards with staggered animations

### Stats Counter (`src/components/landing/StatsCounter.tsx`)
- Uses `projectStats` from sprint-data.ts
- AnimatedCounter triggers on scroll via IntersectionObserver

### Stakeholder Tabs (`src/components/landing/StakeholderTabs.tsx`)
- Uses `audienceData` from epic-data.ts
- 4 tabs: Director, CTO, CEO, Client
- Each tab has title, subtitle, features array, metric, CTA

### Live Status Strip (`src/components/landing/LiveStatusStrip.tsx`)
- Fetches from `/api/github/stats`, `/api/vercel/status`, `/api/railway/status`
- SWR with 60-second refresh
- Shows skeleton loaders while fetching

## Updating the Demo Page

The demo page has 8 sections, each in its own component under `src/components/demo/`:

| Section | Component | Data Source |
|---------|-----------|-------------|
| Overview | `OverviewSection.tsx` | Inline data |
| Pipeline | `PipelineSection.tsx` | `pipelineStages`, `logLines` from sprint-data.ts |
| Spreadsheet | `SpreadsheetSection.tsx` | `gridRows`, `barColumns` from sprint-data.ts |
| Chat | `ChatSection.tsx` | Inline chat messages, `highRiskItems` array |
| Export | `ExportSection.tsx` | Inline format definitions |
| Progress | `ProgressSection.tsx` | `velocityData`, `projectStats` from sprint-data.ts |
| Architecture | `ArchitectureSection.tsx` | `techStack` from sprint-data.ts, inline diagram data |
| Stakeholders | `StakeholdersSection.tsx` | `audienceData` from epic-data.ts |

### Demo Sidebar (`DemoSidebar.tsx`)
- Section list is defined in the `sections` array at the top of the file
- Keyboard shortcuts (1-8) map to section indices
- Active section is tracked via IntersectionObserver

## Updating the Status Page

`src/app/status/page.tsx` is a single large component that:
- Fetches live data from API routes using SWR
- Displays project stats from `projectStats` and `velocityData`
- Shows epic progress from `epics` array
- All chart data is derived from these data sources

## Updating the Roadmap Page

`src/app/roadmap/page.tsx` contains:
- Phase definitions (inline `phases` array with epic IDs, dates, colors)
- Milestone entries (inline `milestones` array)
- Future epic cards from `futureEpics` in epic-data.ts
- To add a new completed phase, add to the `phases` array and map its epic IDs
