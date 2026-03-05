# Tech Spec: E33-S1 — Upload Wizard + Extraction Progress

**Story ID**: E33-S1
**Sprint**: V3-4
**Story Points**: 3
**Risk**: MEDIUM
**Type**: frontend

---

## 1. Overview

This story builds two new dedicated routes:

1. `/upload` — a 3-step wizard that accepts a PDF, lets the user choose an extraction mode, and triggers extraction.
2. `/extraction/[id]` — a full-page SSE-powered progress view that shows overall pipeline state and per-building completion cards while extraction runs, then auto-redirects to `/source/[id]` on completion.

Both routes sit inside the `(dashboard)` layout group (AppShell). The wizard replaces the dialog-based flow for uploading new SAMP documents.

**Why this is needed**: The existing upload path (`useCreateDialogs` -> `AddSourceDialog`) is a minimal dialog that does not trigger ACM extraction or provide visibility into the extraction pipeline. The dedicated page route gives users a clear, guided experience from file drop to results.

---

## 2. File Changes

| File | Action | Description |
|------|--------|-------------|
| `frontend/src/app/(dashboard)/upload/page.tsx` | Create | Upload wizard page — renders `<UploadWizard />` inside AppShell |
| `frontend/src/app/(dashboard)/extraction/[id]/page.tsx` | Create | Extraction progress page — renders `<ExtractionProgress />` inside AppShell |
| `frontend/src/components/acm/UploadWizard.tsx` | Create | 3-step wizard component with file drop, mode select, confirm+trigger |
| `frontend/src/components/acm/ExtractionProgress.tsx` | Create | Full-page progress wrapper: building cards + reuses `ExtractionProgressPanel` |
| `frontend/src/lib/hooks/useExtractionSSE.ts` | Create | Thin facade hook — wraps `useExtractionProgress` + `useAGUIStream` into a single composable API for the progress page |

No existing files require modification.

---

## 3. Implementation Notes

### 3.1 Route Placement

Both new routes go under `frontend/src/app/(dashboard)/` so they automatically inherit the `(dashboard)/layout.tsx` AppShell wrapping and any global providers (React Query, Zustand, Toaster).

```
frontend/src/app/(dashboard)/
  upload/
    page.tsx          ← NEW
  extraction/
    [id]/
      page.tsx        ← NEW
```

The `[id]` parameter in `/extraction/[id]` is the **source ID** (not command ID). The command ID is stored in `sessionStorage` with key `acm-extraction-{sourceId}`.

### 3.2 `useExtractionSSE` Hook

Location: `frontend/src/lib/hooks/useExtractionSSE.ts`

This hook is a thin composition wrapper. It does NOT replicate the SSE logic — it delegates to the two existing hooks:

```typescript
import { useExtractionProgress } from './use-extraction-progress'
import { useAGUIStream } from './use-agui-stream'

export interface ExtractionSSEResult {
  phase: ExtractionPhase
  pipelineState: PipelineRunState | null
  logEntries: string[]
  recordsCreated: number | undefined
  errorMessage: string | undefined
  commandId: string | null
  aguiStep: string | null
  aguiConnected: boolean
  reasoningText: string | undefined
  startTracking: (commandId: string) => void
  dismiss: () => void
}

export function useExtractionSSE(sourceId: string): ExtractionSSEResult
```

Internally:
1. Call `useExtractionProgress(sourceId)` — returns `phase`, `pipelineState`, `logEntries`, `recordsCreated`, `errorMessage`, `startTracking`, `dismiss`.
2. Derive the active `commandId` from `sessionStorage.getItem('acm-extraction-progress-{sourceId}')` (parsed JSON `.commandId`) when `phase === 'extracting'`.
3. Call `useAGUIStream(commandId)` — returns `currentStep`, `reasoningTokens`, `connected`.
4. Return all fields merged.

### 3.3 `UploadWizard` Component

Location: `frontend/src/components/acm/UploadWizard.tsx`

**State** (local React state, no Zustand store):
```typescript
type WizardStep = 1 | 2 | 3
const [step, setStep] = useState<WizardStep>(1)
const [file, setFile] = useState<File | null>(null)
const [mode, setMode] = useState<'standard' | 'ai_enhanced'>('standard')
const [isSubmitting, setIsSubmitting] = useState(false)
```

**Step 1 — Drop PDF Zone**:
- Use the native HTML `<input type="file" accept=".pdf" />` hidden behind a styled drag-and-drop `<div>`.
- Listen for `dragover`, `dragleave`, `drop` events on the drop zone div.
- Show file name + size once a file is selected.
- `onNext`: disabled until `file !== null`. Advances to step 2.
- Use `WizardStepHeader` (already exists at `@/components/acm/WizardStepHeader`) for the step indicator bar.

**Step 2 — Select Extraction Mode**:
- Two option cards:
  - **Standard** (`mode: 'standard'`): "Fast extraction using Docling table detection. Best for clean, well-formatted SAMP documents."
  - **AI-Enhanced** (`mode: 'ai_enhanced'`): "Slower. Uses AI reasoning to recover records from non-standard layouts and damaged tables."
- Visual radio-card selection pattern (border highlight on selected card).
- `onNext`: always enabled (default is `standard`). Advances to step 3.

**Step 3 — Confirm + Trigger**:
- Read-only summary card:
  - File name
  - File size (formatted: KB/MB)
  - Mode label
- "Extract" submit button triggers the two-step upload flow:
  1. `POST /api/sources` via `sourcesApi.create({ type: 'pdf', title: file.name, file })` → returns `SourceResponse` with `id`.
  2. `POST /api/acm/extract` via `acmApi.extract(sourceId)` — but pass `force: mode === 'ai_enhanced'` to signal AI-enhanced mode if needed. Returns `{ command_id }`.
  3. Store `command_id` in `sessionStorage` under key `acm-extraction-{sourceId}`.
  4. `router.push('/extraction/' + encodeURIComponent(sourceId))`.
- Non-fatal upload errors (network blip after source created) → `useToast().error(...)`.
- Fatal errors (source creation fails) → open `Dialog` (Radix UI) with error details + "Try Again" button.

**Cancel** on any step: `router.push('/jobs')`.

### 3.4 `ExtractionProgress` Component

Location: `frontend/src/components/acm/ExtractionProgress.tsx`

This component wraps `ExtractionProgressPanel` and adds:
1. A page-level progress percentage header (derived from `pipelineState`).
2. Building completion cards (AC3).
3. Auto-redirect to `/source/:id` on phase `'completed'`.
4. Error toast for non-fatal warnings (`phase === 'completed'` but `warningMessages.length > 0`).
5. Error modal (Radix `Dialog`) for fatal failure (`phase === 'failed'`).

**Props**:
```typescript
interface ExtractionProgressProps {
  sourceId: string
}
```

**Building Cards** (AC3):

`PipelineRunState` tracks `total_buildings` and stage metrics. The building-level breakdown is not currently in `PipelineRunState` — it does not have a `buildings` array. Use the available `pipelineState` fields to show aggregate cards grouped by stage:

- **Analyzing** — stages before `EXTRACT` are running or pending.
- **Extracting** — `EXTRACT` stage is `running`.
- **Validating** — `VALIDATE` or `CORRECT` stage is `running`.
- **Storing** — `STORE` stage is `running` or `complete`.

Since per-building granularity is not in the SSE payload, show a single summary card per active stage with count from `pipelineState.total_buildings`. If `total_buildings === 0`, omit the card section and show only the `ExtractionProgressPanel`.

When per-building data becomes available in the SSE stream (future story), the `PipelineRunState` type will have a `buildings` field — the component structure should be designed to accept `buildings?: BuildingProgress[]` as an optional prop for future extension without a rewrite.

**Auto-redirect**:
```typescript
useEffect(() => {
  if (phase === 'completed') {
    const timer = setTimeout(() => {
      router.push(`/source/${encodeURIComponent(sourceId)}`)
    }, 2000)  // 2-second pause so user can see "Extraction Complete"
    return () => clearTimeout(timer)
  }
}, [phase, sourceId, router])
```

**Fatal error modal** (Radix UI `Dialog`):
```tsx
<Dialog open={phase === 'failed'} onOpenChange={...}>
  <DialogContent>
    <DialogHeader>
      <DialogTitle>Extraction Failed</DialogTitle>
    </DialogHeader>
    <p>{errorMessage}</p>
    <DialogFooter>
      <Button onClick={() => router.push('/jobs')}>Back to Jobs</Button>
      <Button variant="outline" onClick={handleRetry}>Retry</Button>
    </DialogFooter>
  </DialogContent>
</Dialog>
```

### 3.5 `/upload/page.tsx`

```tsx
'use client'
import { AppShell } from '@/components/layout/AppShell'
import { UploadWizard } from '@/components/acm/UploadWizard'
import { ErrorBoundary } from '@/components/common/ErrorBoundary'
import { PageErrorFallback } from '@/components/common/PageErrorFallback'

export default function UploadPage() {
  return (
    <ErrorBoundary fallback={(props) => <PageErrorFallback {...props} pageName="Upload" reloadUrl="/jobs" />}>
      <AppShell>
        <UploadWizard />
      </AppShell>
    </ErrorBoundary>
  )
}
```

### 3.6 `/extraction/[id]/page.tsx`

```tsx
'use client'
import { use } from 'react'
import { AppShell } from '@/components/layout/AppShell'
import { ExtractionProgress } from '@/components/acm/ExtractionProgress'
import { ErrorBoundary } from '@/components/common/ErrorBoundary'
import { PageErrorFallback } from '@/components/common/PageErrorFallback'

export default function ExtractionPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params)
  return (
    <ErrorBoundary fallback={(props) => <PageErrorFallback {...props} pageName="Extraction" reloadUrl="/jobs" />}>
      <AppShell>
        <ExtractionProgress sourceId={decodeURIComponent(id)} />
      </AppShell>
    </ErrorBoundary>
  )
}
```

### 3.7 sessionStorage Strategy for Reload Resilience

`useExtractionProgress` already persists to `sessionStorage` under key `acm-extraction-progress-{sourceId}` (with `commandId`, `phase`, `pipelineState`, `logEntries`).

The `ExtractionProgress` component mounts and on first render reads this key to restore in-flight state. If `commandId` is found and `phase === 'extracting'`, call `startTracking(commandId)` in a mount-time `useEffect` — identical to the pattern in `jobs/[id]/extract/page.tsx` (line 56-89).

The upload wizard additionally writes to a second key `acm-extraction-{sourceId}` (simpler string, just the commandId) for compatibility with the existing `extract/page.tsx` fallback path.

### 3.8 Non-Fatal Toast vs Fatal Modal Decision Tree

| Condition | Response |
|-----------|----------|
| Source creation fails (step 3) | Fatal modal: "Could not upload file" + try again |
| Extraction trigger fails after source created | Non-fatal toast: error + link to `/jobs/{sourceId}` |
| `phase === 'failed'` on progress page | Fatal modal with error message + retry/back-to-jobs |
| `phase === 'completed'` with stage errors in pipeline | Non-fatal toast: "Extraction complete with warnings" |

### 3.9 Responsive Layout (AC7)

Both pages use `min-w-[1024px]` as the AppShell provides the global sidebar. The wizard is centered with `max-w-2xl mx-auto`. The progress page is full-width with `max-w-4xl mx-auto px-6`.

Building cards grid: `grid gap-4 sm:grid-cols-2 lg:grid-cols-3` — matches the stage card grid already in `ExtractionProgressPanel`.

---

## 4. Acceptance Criteria Verification

| AC | How it is met |
|----|---------------|
| AC1: 3-step wizard | `UploadWizard` renders step 1 (drop zone), step 2 (mode radio cards), step 3 (confirm + trigger). `WizardStepHeader` shows `Step N of 3`. |
| AC2: SSE progress page with % and stage label | `ExtractionProgress` renders `ExtractionProgressPanel` (already has progress bar + stage pills). Overall percentage computed as `(completedStages / totalStages) * 100` in `ExtractionProgressPanel`. |
| AC3: Building cards with name/count/status | Cards derived from `pipelineState` stage status: aggregate card per active stage group. `total_buildings` from `PipelineRunState` provides the count. Status maps to extracting/validating/complete/error via stage status. |
| AC4: Route flow `/upload` → `/extraction/:id` → `/source/:id` | Wizard triggers `router.push('/extraction/' + sourceId)` after extraction starts. `ExtractionProgress` calls `router.push('/source/' + sourceId)` on `phase === 'completed'` after 2s delay. |
| AC5: Error toast for non-fatal issues | `useToast().error(...)` called for extraction trigger failure and for completed-with-warnings state. |
| AC6: Error modal for fatal issues | Radix UI `Dialog` shown when `phase === 'failed'` or source creation throws. |
| AC7: Responsive 1024px+ | `max-w-2xl` centered wizard, `max-w-4xl` progress page, responsive grid for building cards. |
| AC8: Unit tests for wizard step transitions | See test plan below. |

---

## 5. Test Plan (AC8)

File: `frontend/src/components/acm/__tests__/UploadWizard.test.tsx`

Use React Testing Library + Jest (project's existing test setup).

### Test Cases

**WizardStep transitions:**

```
test: "Step 1 — Next button disabled when no file selected"
  Render UploadWizard
  Find the WizardStepHeader Next button
  Assert: button has attribute disabled

test: "Step 1 — Next button enabled after file selected"
  Render UploadWizard
  Simulate file drop / file input change with a mock PDF File object
  Assert: Next button is no longer disabled

test: "Step 1 — Clicking Next advances to Step 2"
  Render UploadWizard with a file already loaded (state override or interaction)
  Click Next
  Assert: screen contains "Select Extraction Mode" heading or Step 2 content

test: "Step 2 — Mode defaults to 'standard'"
  Render UploadWizard, advance to step 2
  Assert: Standard mode card has aria-checked="true" (or selected class)

test: "Step 2 — Selecting AI-Enhanced updates mode"
  Render UploadWizard, advance to step 2
  Click AI-Enhanced card
  Assert: AI-Enhanced card has selected state

test: "Step 2 — Next advances to Step 3"
  Render UploadWizard, advance to step 2
  Click Next
  Assert: Step 3 content visible (file name summary, Extract button)

test: "Step 3 — Shows file name in confirmation summary"
  Render UploadWizard, advance to step 3 with file named 'test.pdf'
  Assert: 'test.pdf' visible in DOM

test: "Cancel button on any step calls router.push('/jobs')"
  Mock useRouter
  Render UploadWizard
  Click Cancel
  Assert: router.push called with '/jobs'

test: "Step 3 — Extract button triggers source creation then extraction"
  Mock sourcesApi.create to return { id: 'source:test123' }
  Mock acmApi.extract to return { command_id: 'cmd:abc' }
  Mock useRouter
  Render UploadWizard, advance to step 3
  Click Extract
  Assert: sourcesApi.create called with FormData containing the file
  Assert: acmApi.extract called with 'source:test123'
  Assert: router.push called with '/extraction/source%3Atest123'

test: "Step 3 — Source creation failure shows error modal"
  Mock sourcesApi.create to throw
  Render UploadWizard, advance to step 3
  Click Extract
  Assert: Dialog with 'Could not upload file' (or similar) is visible
```

### Testing Infrastructure Notes

- Use `vi.mock` (Vitest) or `jest.mock` for `sourcesApi` and `acmApi`.
- Mock `next/navigation` `useRouter` to capture `push` calls.
- For file drop simulation: create a `new File(['pdf content'], 'test.pdf', { type: 'application/pdf' })` and fire a `change` event on the hidden file input.

---

## 6. Key Implementation Patterns to Follow

Looking at `frontend/src/app/(dashboard)/jobs/[id]/extract/page.tsx` as the reference implementation:

1. **AppShell wrapping**: Always wrap page content in `<AppShell>` inside the `(dashboard)` group.
2. **ErrorBoundary pattern**: Wrap inner content component in `<ErrorBoundary>` with `<PageErrorFallback>`.
3. **Next.js 15 async params**: Use `use(params)` in the default export, pass decoded `id` to content component.
4. **sessionStorage restore on mount**: `useEffect` with `// eslint-disable-next-line react-hooks/exhaustive-deps` comment when intentionally running only on mount.
5. **Routing**: `useRouter` from `next/navigation`, `encodeURIComponent` on source IDs before putting them in URLs.
6. **Client directive**: All page files and components that use hooks must have `'use client'` at the top.

---

## 7. Import Paths Reference

| Symbol | Import From |
|--------|-------------|
| `AppShell` | `@/components/layout/AppShell` |
| `WizardStepHeader` | `@/components/acm/WizardStepHeader` |
| `ExtractionProgressPanel` | `@/components/acm/ExtractionProgressPanel` |
| `ExtractionPhase` | `@/lib/hooks/use-extraction-progress` |
| `PipelineRunState`, `PIPELINE_STAGE_ORDER` | `@/lib/types/pipeline` |
| `useExtractionProgress` | `@/lib/hooks/use-extraction-progress` |
| `useAGUIStream` | `@/lib/hooks/use-agui-stream` |
| `useToast` | `@/lib/hooks/use-toast` |
| `sourcesApi` | `@/lib/api/sources` |
| `acmApi` | `@/lib/api/acm` |
| `Dialog`, `DialogContent`, `DialogHeader`, `DialogTitle`, `DialogFooter` | `@/components/ui/dialog` |
| `ErrorBoundary` | `@/components/common/ErrorBoundary` |
| `PageErrorFallback` | `@/components/common/PageErrorFallback` |
| `useRouter`, `useParams` | `next/navigation` |
