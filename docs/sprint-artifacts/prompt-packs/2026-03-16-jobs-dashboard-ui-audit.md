# Session: Audit & fix Jobs Dashboard UI/UX — cards, filters, job card overflow & metadata icons

## Skills to Load

```
/uncodixfy — prevent generic AI/Codex UI patterns; enforce Linear/Stripe/GitHub-level design
/ui-ux-pro-max — UI/UX design intelligence; 50 styles, 21 palettes, component architecture
/frontend-design — production-grade frontend interfaces with high design quality
/baseline-ui — Tailwind CSS validation, typography scale, a11y checks, layout anti-patterns
/e2e-test — self-healing E2E testing with Playwright + agent-browser
/dogfood — systematic QA/exploratory testing; produce structured bug reports with repro evidence
/verification-before-completion — verify work before claiming done
/planning-with-files — persistent markdown plan for session continuity
/find-skills — discover additional skills if needed mid-session
```

---

## Prerequisites

Before starting this session, verify:

- SurrealDB running: `docker ps | grep acm-ai-db`
- API running: `curl http://localhost:5055/health`
- Frontend running: `curl http://localhost:8503` (Next.js dev server)
- Branch: `git checkout ACMV3` (or create feature branch `feat/jobs-dashboard-ui-redesign`)
- File exists: `frontend/src/app/(dashboard)/jobs/page.tsx`
- File exists: `frontend/src/components/jobs/JobCard.tsx`

---

## Project Glossary

Key terms for this session. Refer to these definitions when interpreting code or instructions.

| Term | Definition |
|------|-----------|
| JobCard | React component (`frontend/src/components/jobs/JobCard.tsx`) rendering individual job/source cards with status, metadata, and actions. |
| SourceListResponse | TypeScript interface (`frontend/src/lib/types/api.ts:21-45`) representing a source record from the API — includes `title`, `review_status`, `building_count`, `insights_count`, `asset`, `command_id`. |
| FILTER_OPTIONS | Constant array in `jobs/page.tsx:27-34` defining the filter pill buttons. Currently 6 options including `building_review` and `acm_review`. |
| JobStatusPill | Component rendering colored status badges for job review states. |
| PipelineEventBus | Pub/sub bus emitting events to the SSE endpoint during extraction runs. Powers extraction progress bars in JobCard. |
| useSourcesPaginated | React Query hook wrapping `GET /sources` with limit/offset pagination and sort. Powers the jobs list. |
| useExtractionStatus | Hook polling `/commands/jobs/{commandId}` every 3s for active extractions. Returns stage info and progress percent. |
| shadcn/ui | Component library (Card, Button, Input, DropdownMenu) following Radix UI + Tailwind CSS patterns. |
| VAEA color vars | CSS custom properties (`--vaea-teal-*`, `--vaea-gold`) for brand-consistent theming. |
| Subagent | Claude Code session spawned via Task tool for parallel work. Model: `sonnet` for complex, `haiku` for simple. |
| Context7 MCP | MCP server fetching live library documentation via `resolve-library-id` + `query-docs`. |
| Plan mode | Session starts by reading/writing `task_plan.md` to prevent scope creep. |

---

## Current State

- Branch: ACMV3 (last commit: `121b4e0b docs: update multi-format audit progress`)
- Sprint: V3-8, 6 stories remaining (E35-S3..S8)
- Dashboard stat cards: 6 cards in `lg:grid-cols-6` layout — Total Jobs, Extracting, In Review, Published, Buildings, ACM Records
- Filter options: 6 options — All, Extracting, Pending, Buildings, Records, Published
- JobCard title: `line-clamp-2` with `text-sm font-medium` — reported as overflowing card boundary
- JobCard metadata: Only shows relative date + building/record counts as text; no PDF metadata icons
- Backend `SourceListResponse` has no `page_count` or `file_size` fields currently
- Frontend port: **8503** (Next.js dev, configured in package.json)

---

## Key Files

Files this session will read or modify. Verify all paths exist before starting.

**Read (reference):**
- `frontend/src/lib/types/api.ts` — SourceListResponse type definition (lines 21-45)
- `frontend/src/lib/hooks/use-sources-paginated.ts` — paginated source list hook
- `frontend/src/lib/hooks/use-extraction-status.ts` — extraction polling hook
- `frontend/src/lib/api/sources.ts` — sources API client
- `frontend/src/components/ui/card.tsx` — shadcn Card primitives
- `frontend/src/components/ui/button.tsx` — shadcn Button primitives
- `frontend/src/components/jobs/JobStatusPill.tsx` — status badge component
- `api/routers/sources.py` — backend source list endpoint
- `open_notebook/domain/models.py` — Source domain model

**Modify:**
- `frontend/src/app/(dashboard)/jobs/page.tsx` — dashboard stat cards + filter options
- `frontend/src/components/jobs/JobCard.tsx` — card layout, title overflow, metadata icons
- `frontend/src/lib/types/api.ts` — add `page_count`, `file_size` to SourceListResponse
- `api/routers/sources.py` — include page_count/file_size in list response serialization
- `open_notebook/domain/models.py` — add page_count/file_size fields if not present (or expose from existing data)

**Possibly Create:**
- `frontend/src/components/jobs/JobMetadataIcons.tsx` — reusable metadata icon row component (if warranted)

---

## Plan

Read `docs/sprint-artifacts/task_plan.md` before starting. Update it as you work.

### Task Plan Reference
- task_plan.md: `docs/sprint-artifacts/task_plan.md`
- findings.md: `docs/sprint-artifacts/findings.md`
- progress.md: `docs/sprint-artifacts/progress.md`

### Implementation Steps

#### Phase 1: Dashboard Cards Redesign (Subagent: frontend-cards)

1. **Remove Buildings & ACM Records stat cards** — `jobs/page.tsx:184-196`
   - Delete the last 2 `<Card>` blocks (Buildings, ACM Records)
   - Change grid from `lg:grid-cols-6` to `lg:grid-cols-4` (or `sm:grid-cols-2 lg:grid-cols-4`)
   - Remove `totalBuildings` and `totalRecords` from the `stats` useMemo (lines 84-91)
   - Update the loading skeleton grid to match (line 108: `lg:grid-cols-4` already correct)

2. **Verify visual balance** — ensure 4 cards fill the row cleanly without orphan gaps on all breakpoints

#### Phase 2: Filter Redesign (Subagent: frontend-filters)

3. **Simplify FILTER_OPTIONS** — `jobs/page.tsx:27-34`
   - Current: `['all', 'extracting', 'pending_review', 'building_review', 'acm_review', 'published']`
   - Target: `['all', 'extracting', 'pending_review', 'acm_review', 'published']`
   - Remove `building_review` option (or merge it into an existing filter)
   - Rename labels: `pending_review` → "Pending", `acm_review` → "Records"
   - Update the `JobFilter` type union to remove `'building_review'`

4. **Update filter logic** — `jobs/page.tsx:60-72`
   - If `building_review` sources still exist in DB, decide: fold into "Pending" or "Records"?
   - Ensure no sources become invisible after filter removal

#### Phase 3: Job Card UI Bug Fixes (Subagent: frontend-jobcard)

5. **Fix filename/title overflow** — `JobCard.tsx:121-126`
   - Current: `line-clamp-2` in a flex container with `min-w-0` — but card itself may not constrain width
   - Fix: ensure the card has `overflow-hidden` and title container uses `truncate` or proper `min-w-0` chain
   - Add `break-words` or `overflow-wrap: anywhere` as safety net
   - Test with very long filenames (60+ chars, no spaces) and multi-word filenames
   - Ensure the three-dot menu remains clickable (not blocked by overflow)

6. **Add metadata icons to JobCard** — `JobCard.tsx:196-214`
   - Add icon row between status pill and "Uploaded X ago" text
   - Icons to display (conditional — only show if data available):
     - `FileText` icon + page count (e.g., "24 pages")
     - `HardDrive` icon + file size (e.g., "2.4 MB")
     - `FileType` icon + document type indicator (PDF badge)
   - Use `lucide-react` icons, `text-xs text-muted-foreground` styling
   - Layout: horizontal flex with `gap-3`, each item is `flex items-center gap-1`

#### Phase 4: Backend Wiring (Subagent: backend-metadata)

7. **Expose PDF metadata in source list API** — `api/routers/sources.py`
   - Check if `page_count` / `file_size` are already stored on the Source model or acm_table_section
   - If stored: add to serialization in the list endpoint response
   - If NOT stored: add fields to Source model, populate during upload/extraction
   - Ensure backward compatibility (fields are optional)

8. **Update SourceListResponse type** — `frontend/src/lib/types/api.ts`
   - Add: `page_count?: number` and `file_size?: number` (optional)
   - These feed the metadata icons in step 6

#### Phase 5: Verification & QA (Subagent: qa-verifier)

9. **Build verification**
   - `cd frontend && npm run build` — must pass
   - `cd frontend && npm run lint` — must pass
   - `uv run ruff check .` — must pass (if backend changed)
   - `uv run pytest tests/ -x` — must pass (if backend changed)

10. **Visual verification (dogfood)**
    - Navigate to `http://localhost:8503/jobs`
    - Screenshot: 4 stat cards render correctly (no Buildings/ACM Records)
    - Screenshot: Filter pills show exactly 5 options (All, Extracting, Pending, Records, Published)
    - Screenshot: Job card with long filename — title truncates, menu remains clickable
    - Screenshot: Job card with metadata icons (page count, file size)
    - Test responsive: check at mobile (375px), tablet (768px), desktop (1280px)
    - Verify extraction progress bar still works on extracting cards

---

## Agent Strategy

```
Strategy: SUBAGENT-DISPATCH
Use the Task tool to dispatch independent work items in parallel.
All subagents use model: "sonnet" (team context).

┌─────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR (you)                            │
│  Reads plan, dispatches subagents, synthesizes results           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  PARALLEL WAVE 1 (independent frontend changes):                 │
│  ┌──────────────────────┐  ┌──────────────────────┐             │
│  │ frontend-cards        │  │ frontend-filters     │             │
│  │ (Phase 1)             │  │ (Phase 2)            │             │
│  │ Remove 2 stat cards,  │  │ Simplify filters     │             │
│  │ fix grid to 4-col     │  │ to 5 options,        │             │
│  │ in jobs/page.tsx      │  │ update filter logic   │             │
│  └──────────────────────┘  └──────────────────────┘             │
│                                                                  │
│  PARALLEL WAVE 2 (after Wave 1 merges — shared file edits):     │
│  ┌──────────────────────┐  ┌──────────────────────┐             │
│  │ frontend-jobcard      │  │ backend-metadata     │             │
│  │ (Phase 3)             │  │ (Phase 4)            │             │
│  │ Fix title overflow,   │  │ Expose page_count +  │             │
│  │ add metadata icons    │  │ file_size in API     │             │
│  │ in JobCard.tsx         │  │ response             │             │
│  └──────────────────────┘  └──────────────────────┘             │
│                                                                  │
│  SEQUENTIAL (after all waves):                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ qa-verifier (Phase 5)                                     │   │
│  │ Build check, lint, dogfood visual verification,           │   │
│  │ responsive screenshots, E2E extraction progress test      │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘

Subagent details:

1. frontend-cards (Wave 1, parallel):
   subagent_type: "frontend-specialist"
   model: "sonnet"
   Task: Remove Buildings + ACM Records stat cards from jobs/page.tsx.
         Change grid to lg:grid-cols-4. Remove totalBuildings/totalRecords
         from stats useMemo. Update loading skeleton grid.

2. frontend-filters (Wave 1, parallel):
   subagent_type: "frontend-specialist"
   model: "sonnet"
   Task: Simplify FILTER_OPTIONS in jobs/page.tsx to 5 options:
         All, Extracting, Pending, Records, Published. Remove
         'building_review' from JobFilter type. Update filter logic
         to fold building_review sources into nearest status.

3. frontend-jobcard (Wave 2, after Wave 1):
   subagent_type: "frontend-specialist"
   model: "sonnet"
   Task: Fix title overflow in JobCard.tsx (add overflow-hidden,
         break-words). Add metadata icon row with page count,
         file size, PDF type badge using lucide-react icons.
         Apply /uncodixfy + /baseline-ui rules.

4. backend-metadata (Wave 2, parallel with frontend-jobcard):
   subagent_type: "backend-specialist"
   model: "sonnet"
   Task: Expose page_count and file_size in GET /sources response.
         Check if data exists on Source model or acm_table_section.
         Add optional fields to response serialization. Update
         SourceListResponse type in frontend types.

5. qa-verifier (Sequential, after all waves):
   subagent_type: "qa-specialist"
   model: "sonnet"
   Task: Run npm build + lint + ruff check + pytest.
         Use agent-browser to navigate to /jobs, take screenshots
         at 3 viewports. Verify: 4 stat cards, 5 filter pills,
         no title overflow, metadata icons visible.
         Run /dogfood on the jobs page.
```

---

## Context7 Directives

Run these at session start to load current library documentation:

1. resolve-library-id for "lucide-react" → query-docs for "available icons FileText HardDrive FileType"
2. resolve-library-id for "tailwindcss" → query-docs for "line-clamp overflow-hidden break-words truncate"
3. resolve-library-id for "ag-grid-react" → query-docs for "column auto-sizing row height"

---

## Design Rules (/uncodixfy + /ui-ux-pro-max enforcement)

Apply these rules to ALL frontend changes in this session:

### Anti-Patterns to AVOID
- No gratuitous gradients, glows, or glass-morphism on stat cards
- No rounded-full on rectangular cards (rounded-xl is fine)
- No excessive padding that wastes space (keep cards compact)
- No icon-only buttons without aria-labels
- No color-only status indicators (always pair with text or shape)

### Patterns to FOLLOW
- **Stat cards**: Clean, minimal — label + large number + subtle color accent. Linear/Stripe style.
- **Filter pills**: Consistent height, rounded-full is OK for pills, clear active state with brand color
- **Job cards**: Tight vertical rhythm, metadata as secondary text with icons, clear visual hierarchy
- **Icons**: 14-16px (`w-3.5 h-3.5` or `w-4 h-4`), `text-muted-foreground`, never decorative-only
- **Overflow**: Always `min-w-0` on flex children containing text, `truncate` or `line-clamp-N` on text
- **Spacing**: Use 4px increments (Tailwind `gap-1`, `gap-2`, `gap-3`, `gap-4`)
- **Typography**: `text-xs` for metadata, `text-sm` for body, `text-base`+ for headings only

### Responsive Behavior
- Mobile (< 640px): 1 column cards, stack all stat cards vertically, filter pills wrap
- Tablet (640-1024px): 2 column cards, 2-col stat cards
- Desktop (> 1024px): 3-4 column cards, 4-col stat cards in a single row

---

## Verification Checklist

Run these commands in order before marking the session complete. All must pass.

- [ ] `cd frontend && npm run lint` — Frontend lint (0 errors)
- [ ] `cd frontend && npm run build` — Frontend build (0 errors)
- [ ] `uv run ruff check .` — Python lint (0 errors, if backend modified)
- [ ] `uv run pytest tests/ -x` — Backend tests (all pass, if backend modified)
- [ ] Visual: Navigate to `http://localhost:8503/jobs` — page loads without errors
- [ ] Visual: Stat cards show exactly 4 cards (Total Jobs, Extracting, In Review, Published)
- [ ] Visual: No "Buildings" or "ACM Records" stat cards visible
- [ ] Visual: Filter pills show exactly 5 options (All, Extracting, Pending, Records, Published)
- [ ] Visual: Job card with 80-char filename — title truncates cleanly, no overflow
- [ ] Visual: Three-dot menu on job card is always clickable (not blocked by title overflow)
- [ ] Visual: Metadata icons (page count, file size) appear on cards with available data
- [ ] Visual: Cards at mobile width (375px) — single column, no horizontal scroll
- [ ] Visual: Extraction progress bar still animates on extracting cards
- [ ] Console: No React errors/warnings in browser DevTools console

---

## Files Summary

| Operation | Count | Files |
|-----------|-------|-------|
| MODIFY | 4-5 | `jobs/page.tsx`, `JobCard.tsx`, `api.ts`, `sources.py`, possibly `models.py` |
| NEW | 0-1 | `JobMetadataIcons.tsx` (only if icon row is complex enough to extract) |
| MOVE | 0 | — |
| DELETE | 0 | — |

---

## Commit Template

When work is complete, use this commit message structure:

```
feat(ui): redesign Jobs Dashboard — simplify cards, filters, fix overflow & add metadata icons

- Remove Buildings and ACM Records stat cards; keep 4 workflow-status cards
- Simplify filter pills to 5 options (All/Extracting/Pending/Records/Published)
- Fix job card title overflow blocking interaction with menu
- Add PDF metadata icons (page count, file size) to job cards
- Expose page_count/file_size in source list API response

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```
