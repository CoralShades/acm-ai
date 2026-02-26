You are implementing E22-S5: Extraction Streaming & Navigation Polish.
You are Amelia (Developer). Primarily frontend, with optional backend investigation.

## MANDATORY PRE-READ — Read ALL before writing ANY code

### Your story:
- docs/sprint-artifacts/e22-s5-extraction-streaming-polish.md

### Extraction UI components:
- frontend/src/app/(dashboard)/jobs/[id]/extract/page.tsx
- frontend/src/components/acm/ExtractionProgressPanel.tsx
- frontend/src/components/acm/RawExtractionTable.tsx
- frontend/src/components/acm/ExtractionThinkingPanel.tsx

### SSE hooks:
- frontend/src/hooks/use-extraction-progress.ts — PipelineLogger SSE
- frontend/src/hooks/use-extraction-status.ts — polling status

### Backend SSE emitters:
- api/routers/extraction_events.py — SSE endpoint
- open_notebook/extractors/pipeline_logger.py — what events are emitted

### Backend pipeline (READ ONLY — understand when records are saved):
- open_notebook/graphs/acm_extraction.py — find the save_records node
- Search for: "def save_records" and understand when records appear in DB

### API for fetching records:
- api/routers/acm.py — find the GET records endpoint
- frontend/src/hooks/use-acm-records.ts

## THE PROBLEM

From user testing screenshots:

**Image 3**: During extraction, the page shows "Extracting: Processing...",
"Raw Extracted Records • Streaming", "Waiting for records..." — but 0 records.
The grid is empty the entire time extraction runs.

**Image 2**: AFTER extraction completes, all 16 records appear at once.

**Root cause**: The pipeline saves ALL records in a single batch at the end
(save_records node). There are NO intermediate saves. So there are literally
no records in the database to display until the final save completes.

The SSE stream (PipelineLogger) emits STAGE events (stage:entered, stage:completed)
but NOT individual record events. The frontend "Streaming" badge is misleading.

## FIX APPROACH

### Option A: Frontend Only (RECOMMENDED — do this)

Improve the user experience without changing the backend pipeline.
The goal is to give MEANINGFUL progress feedback even though records
arrive in a batch at the end.

### Option B: Backend Enhancement (OPTIONAL — only if time permits)

Modify the backend to save records per-building instead of all-at-once,
emitting SSE events as each building completes.

## IMPLEMENTATION TASKS

### Task 1: Enhance Stage Progress Display (Option A)

File: `frontend/src/app/(dashboard)/jobs/[id]/extract/page.tsx`
and: `frontend/src/components/acm/ExtractionProgressPanel.tsx`

The current ExtractionProgressPanel shows stage pills. Make them MORE prominent:

```tsx
// Show the pipeline stages with clear visual progression:
const STAGES = [
  { id: 'structure', label: 'Document Analysis', icon: FileSearch },
  { id: 'preflight', label: 'Format Detection', icon: Settings },
  { id: 'inventory', label: 'Building Inventory', icon: Building },
  { id: 'extract', label: 'Extracting Records', icon: Table },
  { id: 'validate', label: 'Validation', icon: CheckCircle },
  { id: 'correct', label: 'Corrective Loop', icon: RefreshCw },
  { id: 'save', label: 'Saving Records', icon: Database },
]

// For each stage:
// - Before: gray, dimmed
// - Current: animated pulse, teal color, spinner icon
// - Completed: green checkmark
// - Show elapsed time for current stage
```

Add a prominent text description of what's happening:
```tsx
{currentStage === 'extract' && (
  <p className="text-sm text-muted-foreground mt-2">
    AI is analyzing each building's asbestos records... This typically takes 60-90 seconds.
    Records will appear when processing is complete.
  </p>
)}
```

### Task 2: Remove Misleading "Streaming" Badge

File: `frontend/src/components/acm/RawExtractionTable.tsx`

The "• Streaming" green badge next to "Raw Extracted Records" is misleading
because records don't actually stream in. Change it:

- During extraction: Show "• Processing" with amber/orange color
- When extraction stage reaches "save": Show "• Saving..." with teal color
- When extraction completes: Show "• Complete" with green color + record count
- When waiting: Show "• Waiting for records..." (gray, no animation)

### Task 3: Auto-Fetch Records When Extraction Completes

The extraction status hook should detect when extraction completes,
then immediately trigger a fetch of the records.

```tsx
// In the extract page or RawExtractionTable:
const { status, stage } = useExtractionStatus(sourceId)
const queryClient = useQueryClient()

useEffect(() => {
  if (status === 'completed' || stage === 'save') {
    // Immediately fetch records
    queryClient.invalidateQueries({ queryKey: ['acm-records', sourceId] })
  }
}, [status, stage])

// Also: start polling records every 5 seconds once we're in the 'save' stage
useEffect(() => {
  if (stage === 'save' || status === 'completed') {
    const interval = setInterval(() => {
      queryClient.invalidateQueries({ queryKey: ['acm-records', sourceId] })
    }, 5000)
    return () => clearInterval(interval)
  }
}, [stage, status])
```

### Task 4: Show Provider Error in Extraction Log

From the user's logs, there's a provider schema/compat error:
```
Provider schema/compat error detected (Error code: 400 - compiled grammar is too large)
Falling back to direct invocation with manual JSON parsing.
```

And a validation error:
```
risk_status must be one of ['High', 'Low', 'Medium'], got 'Moderate'
```

These errors should be visible in the Extraction Log tab, not hidden.
Check if ExtractionProgressPanel shows error events from SSE.
If not, add error display:

```tsx
{errors.length > 0 && (
  <div className="mt-4 space-y-2">
    <h4 className="text-sm font-medium text-destructive">Extraction Warnings</h4>
    {errors.map((error, i) => (
      <div key={i} className="text-xs bg-destructive/10 text-destructive p-2 rounded">
        {error.message}
      </div>
    ))}
  </div>
)}
```

### Task 5: Global Navigation Loading Indicator

When clicking between pages, Next.js compiles the page and shows nothing.
Add a top-of-page progress bar.

Option 1 — Use Next.js router events:
```tsx
// In frontend/src/app/(dashboard)/layout.tsx or a global component:
import { usePathname } from 'next/navigation'
import { useEffect, useState, useTransition } from 'react'

// Or use NProgress-style thin bar at top of page
// Check if nprogress is already in package.json
```

Option 2 — Simple CSS approach:
```tsx
// Create a NavigationProgress component
export function NavigationProgress() {
  const pathname = usePathname()
  const [loading, setLoading] = useState(false)
  
  useEffect(() => {
    setLoading(true)
    const timeout = setTimeout(() => setLoading(false), 500)
    return () => clearTimeout(timeout)
  }, [pathname])
  
  if (!loading) return null
  
  return (
    <div className="fixed top-0 left-0 right-0 z-50 h-0.5 bg-primary/20">
      <div className="h-full bg-primary animate-[progress_1s_ease-in-out_infinite]" 
           style={{ width: '60%' }} />
    </div>
  )
}
```

Add to the dashboard layout so it appears on every page navigation.

### Task 6: (OPTIONAL — Option B Backend) Per-Building Record Saving

IF you have time and want true streaming, modify the backend:

File: `open_notebook/graphs/acm_extraction.py` — find `save_records` node

Currently it saves ALL buildings' records at once. Change to:
1. Save records per-building as each building completes
2. Emit an SSE event: `building:records_saved` with building name and count
3. Frontend detects this event and fetches new records

This is complex and touches the backend pipeline. Only do this if the
frontend-only fixes (Tasks 1-5) are done and working.

### Task 7: Verification

```bash
cd frontend
npm run build    # MUST pass
npm run lint     # MUST pass
```

Manual checks:
- Upload a PDF and watch extraction page
- Stage pills should animate through progression
- "Streaming" badge should say "Processing" during extraction
- Records should appear as soon as extraction completes (no manual refresh)
- Navigation between pages should show progress indicator
- Extraction errors should be visible in the log

### Task 8: Update BMAD Artifacts

Update docs/sprint-artifacts/sprint-status.yaml:
```yaml
e22-s5-extraction-streaming-polish: done  # 2026-02-26: Enhanced stage progress, removed misleading Streaming badge, auto-fetch on completion, navigation progress bar, error display
```

If all E22 stories are done:
```yaml
epic-22: done  # All 5 stories complete
```

Update _bmad-output/project-planning-artifacts/acm-ai/bmm-workflow-status.yaml:
```
# 2026-02-26: Epic 22 Post-Audit Remediation — COMPLETE
#   - E22-S1: Schema resilience (normalize instead of reject)
#   - E22-S2: Dashboard layout fix (sidebar restoration)
#   - E22-S3: Job detail redesign (source layout with PDF + chat)
#   - E22-S4: Building tabs everywhere (reusable component)
#   - E22-S5: Extraction streaming polish (progress feedback + navigation)
```

### Task 9: Git Commit

```bash
git add frontend/ docs/ _bmad-output/
git commit -m "feat(e22-s5): extraction progress polish + navigation indicator

- Enhanced stage progress display with icons and descriptions
- Replaced misleading 'Streaming' badge with accurate status indicators
- Auto-fetch records when extraction completes (no manual refresh)
- Provider/validation errors now visible in Extraction Log
- Global navigation progress bar during page transitions
- Epic 22 complete"
```

## GUARD RAILS
- Do NOT modify the extraction pipeline graph (unless doing Option B)
- Do NOT modify LLM prompts
- Do NOT change how SSE events are emitted (PipelineLogger is the production path)
- Do NOT install heavy new packages — keep it lightweight
- The "Streaming" badge removal is important — don't promise streaming when it's batch
- FOCUS on honest, helpful progress feedback rather than fake streaming
