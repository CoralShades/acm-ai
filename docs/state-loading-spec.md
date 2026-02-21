# State Management and Loading Patterns Specification

> **Version:** 1.0
> **Date:** 2026-02-08
> **Status:** Draft
> **Applies to:** ACM-AI / VAEA Frontend

---

## Table of Contents

1. [Zustand Store Audit](#1-zustand-store-audit)
2. [React Query Hook Audit](#2-react-query-hook-audit)
3. [New Store Proposals](#3-new-store-proposals)
4. [Skeleton Screen Specifications](#4-skeleton-screen-specifications)
5. [Shimmer Animation CSS](#5-shimmer-animation-css)
6. [Multi-Stage Pipeline Progress](#6-multi-stage-pipeline-progress)
7. [Toast and Notification System](#7-toast-and-notification-system)
8. [Optimistic Update Patterns](#8-optimistic-update-patterns)
9. [Error Boundary and Recovery Patterns](#9-error-boundary-and-recovery-patterns)

---

## 1. Zustand Store Audit

The application uses 6 Zustand stores for client-side state. Three use the `persist` middleware with `localStorage`, one uses `sessionStorage`, and two are ephemeral (in-memory only).

### 1.1 auth-store

**File:** `src/lib/stores/auth-store.ts`
**Persistence:** `localStorage` (key: `auth-storage`)
**Partialize:** Only `token` and `isAuthenticated` are persisted.

```typescript
interface AuthState {
  // Persisted
  isAuthenticated: boolean
  token: string | null

  // Ephemeral
  isLoading: boolean
  error: string | null
  lastAuthCheck: number | null
  isCheckingAuth: boolean
  hasHydrated: boolean
  authRequired: boolean | null

  // Actions
  setHasHydrated: (state: boolean) => void
  checkAuthRequired: () => Promise<boolean>
  login: (password: string) => Promise<boolean>
  logout: () => void
  checkAuth: () => Promise<boolean>
}
```

**Observations:**
- Hydration-aware via `hasHydrated` flag and `onRehydrateStorage` callback.
- Auth check throttled to 30-second intervals via `lastAuthCheck`.
- `checkAuthRequired` makes a fetch to `/api/auth/status` to determine if auth is enabled.
- Login tests credentials against `/api/notebooks` GET endpoint (not a dedicated auth endpoint).

**Enhancement needed:** Session timeout support. Currently no periodic re-check after initial auth verification. The `lastAuthCheck` throttle prevents rapid re-checks but does not enforce token expiry.

### 1.2 theme-store

**File:** `src/lib/stores/theme-store.ts`
**Persistence:** `localStorage` (key: `theme-storage`)
**Partialize:** Only `theme` is persisted.

```typescript
type Theme = 'light' | 'dark' | 'system'

interface ThemeState {
  theme: Theme
  setTheme: (theme: Theme) => void
  getSystemTheme: () => 'light' | 'dark'
  getEffectiveTheme: () => 'light' | 'dark'
}
```

**Observations:**
- System theme detection via `window.matchMedia`.
- Immediate DOM update on theme change (`classList` and `data-theme`).
- Convenience `useTheme()` hook wrapping the store.
- No issues. Clean implementation.

### 1.3 sidebar-store

**File:** `src/lib/stores/sidebar-store.ts`
**Persistence:** `localStorage` (key: `sidebar-storage`)
**Partialize:** Entire state persisted (default behavior).

```typescript
interface SidebarState {
  isCollapsed: boolean
  expandedSections: Record<string, boolean>
  toggleCollapse: () => void
  setCollapsed: (collapsed: boolean) => void
  toggleSection: (sectionTitle: string) => void
  setSectionExpanded: (sectionTitle: string, expanded: boolean) => void
}
```

**Observations:**
- Default sections: `Collect: true`, `Process: true`, `Create: true`, `Manage: false`.
- Section keys are hardcoded strings (will need updating when navigation is redesigned to `WORKSPACE` / `CONFIGURE`).
- No mobile-responsive handling (should coordinate with `useMediaQuery` to auto-collapse on small screens).

### 1.4 navigation-store

**File:** `src/lib/stores/navigation-store.ts`
**Persistence:** `sessionStorage` (key: `navigation-storage`)
**Custom storage adapter:** Wraps `sessionStorage` with try/catch for SSR safety.

```typescript
interface NavigationState {
  returnTo?: {
    path: string
    label: string
    preserveState?: {
      scrollPosition?: number
      highlightItemId?: string
      timestamp?: number
    }
  }
  setReturnTo: (path: string, label: string, preserveState?: object) => void
  clearReturnTo: () => void
  getReturnPath: () => string
  getReturnLabel: () => string
}
```

**Observations:**
- Stale context detection: auto-clears after 1 hour.
- Default fallback: `/sources` with label `Back to Sources`.
- Convenience `useNavigation()` hook wrapping the store.
- Scroll position and highlight item ID support for return-to-context navigation.

### 1.5 upload-store

**File:** `src/lib/stores/upload-store.ts`
**Persistence:** None (ephemeral).

```typescript
interface ProcessingOptions {
  enableAcmExtraction: boolean
  enableEmbeddings: boolean
  transformations: string[]
  notebookIds: string[]
  processingMode: 'sync' | 'async'
}

interface UploadStore {
  files: UploadFile[]
  options: ProcessingOptions
  addFiles: (files: File[]) => void
  removeFile: (id: string) => void
  updateFile: (id: string, updates: Partial<UploadFile>) => void
  clearFiles: () => void
  setDocumentType: (id: string, type: UploadFile['documentType']) => void
  setOptions: (updates: Partial<ProcessingOptions>) => void
  resetOptions: () => void
}
```

**Observations:**
- File IDs generated via `nanoid()`.
- `MAX_FILES` cap applied in `addFiles`.
- Default processing mode is `async`.
- No progress tracking for individual file uploads (handled externally by the upload service).

### 1.6 notebook-columns-store

**File:** `src/lib/stores/notebook-columns-store.ts`
**Persistence:** `localStorage` (key: `notebook-columns-storage`)
**Partialize:** Entire state persisted.

```typescript
interface NotebookColumnsState {
  sourcesCollapsed: boolean
  notesCollapsed: boolean
  toggleSources: () => void
  toggleNotes: () => void
  setSources: (collapsed: boolean) => void
  setNotes: (collapsed: boolean) => void
}
```

**Observations:**
- Controls the three-column layout in the notebook detail page.
- Both columns default to expanded.
- Will be hidden from main navigation but the store remains functional for when users access notebook pages directly.

### 1.7 Store Summary Table

| Store | Persistence | Storage Key | Partialize | Hydration-Aware |
|-------|-------------|-------------|------------|-----------------|
| auth-store | localStorage | `auth-storage` | `token`, `isAuthenticated` | Yes (`onRehydrateStorage`) |
| theme-store | localStorage | `theme-storage` | `theme` | No (implicit via persist) |
| sidebar-store | localStorage | `sidebar-storage` | Full state | No |
| navigation-store | sessionStorage | `navigation-storage` | Full state | No |
| upload-store | None | N/A | N/A | N/A |
| notebook-columns-store | localStorage | `notebook-columns-storage` | Full state | No |

---

## 2. React Query Hook Audit

### 2.1 Global Defaults

**File:** `src/lib/api/query-client.ts`

```typescript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,       // 5 minutes
      gcTime: 10 * 60 * 1000,          // 10 minutes (garbage collection)
      retry: 2,
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: 1,
    },
  },
})
```

### 2.2 Query Key Registry

**Central keys** (`query-client.ts`):
```typescript
const QUERY_KEYS = {
  notebooks: ['notebooks'],
  notebook: (id) => ['notebooks', id],
  notes: (notebookId?) => ['notes', notebookId],
  note: (id) => ['notes', id],
  sources: (notebookId?) => ['sources', notebookId],
  source: (id) => ['sources', id],
  settings: ['settings'],
  sourceChatSessions: (sourceId) => ['source-chat', sourceId, 'sessions'],
  sourceChatSession: (sourceId, sessionId) => ['source-chat', sourceId, 'sessions', sessionId],
  notebookChatSessions: (notebookId) => ['notebook-chat', notebookId, 'sessions'],
  notebookChatSession: (sessionId) => ['notebook-chat', 'sessions', sessionId],
  podcastEpisodes: ['podcasts', 'episodes'],
  podcastEpisode: (episodeId) => ['podcasts', 'episodes', episodeId],
  episodeProfiles: ['podcasts', 'episode-profiles'],
  speakerProfiles: ['podcasts', 'speaker-profiles'],
}
```

**ACM keys** (`use-acm.ts`):
```typescript
const ACM_QUERY_KEYS = {
  records: (sourceId, params?) => ['acm', 'records', sourceId, params],
  record: (recordId) => ['acm', 'records', 'detail', recordId],
  stats: (sourceId?) => ['acm', 'stats', sourceId],
}
```

**Site config keys** (`use-site-config.ts`):
```typescript
const SITE_CONFIG_QUERY_KEYS = {
  config: (sourceId) => ['site-config', sourceId],
  templates: (limit?) => ['site-config', 'templates', limit],
  agencies: (department?) => ['site-config', 'agencies', department],
}
```

**Model keys** (`use-models.ts`):
```typescript
const MODEL_QUERY_KEYS = {
  models: ['models'],
  model: (id) => ['models', id],
  defaults: ['models', 'defaults'],
  providers: ['models', 'providers'],
}
```

**Transformation keys** (`use-transformations.ts`):
```typescript
const TRANSFORMATION_QUERY_KEYS = {
  transformations: ['transformations'],
  transformation: (id) => ['transformations', id],
  defaultPrompt: ['transformations', 'default-prompt'],
}
```

### 2.3 Hook-by-Hook Audit

#### ACM Domain (`use-acm.ts`)

| Hook | Type | Stale Time | Refetch Interval | Notes |
|------|------|------------|------------------|-------|
| `useACMRecords` | query | 30s | - | Enabled when `source_id` present |
| `useACMRecord` | query | default (5m) | - | Single record detail |
| `useACMStats` | query | 60s | - | Aggregate risk counts |
| `useCreateACMRecord` | mutation | - | - | Invalidates records list + stats |
| `useUpdateACMRecord` | mutation | - | - | Invalidates record + list + stats |
| `useDeleteACMRecord` | mutation | - | - | Invalidates list + stats |
| `useExtractACM` | mutation | - | - | Triggers extraction, reports `command_id` |
| `useExportACMCsv` | mutation | - | - | Downloads blob as CSV |
| `useExportACMExcel` | mutation | - | - | Downloads blob as XLSX |

#### ACM Summary (`use-acm-summary.ts`)

| Hook | Type | Notes |
|------|------|-------|
| `useACMSummary` | wrapper | Wraps `useACMStats`, normalizes field names |

#### Extraction Status (`use-extraction-status.ts`)

| Hook | Type | Stale Time | Refetch Interval | Notes |
|------|------|------------|------------------|-------|
| `useExtractionStatus` | custom (query + state) | 0 | 3s (while extracting) | Polls job status, sessionStorage-backed |

**Key detail:** Uses `sessionStorage` keyed as `acm-extraction-{sourceId}` to survive tab navigation. Phases: `idle -> extracting -> completed -> failed`. Invalidates ACM records and stats on completion.

#### Site Config (`use-site-config.ts`)

| Hook | Type | Stale Time | Notes |
|------|------|------------|-------|
| `useSiteConfig` | query | 60s | Per-source configuration |
| `useSiteConfigTemplates` | query | 5m | Template list |
| `useAgencies` | query | 5m | Autocomplete list |
| `useSaveSiteConfig` | mutation | - | Invalidates config + templates + agencies |
| `useApplyConfigTemplate` | mutation | - | Invalidates config |

#### Sources (`use-sources.ts`)

| Hook | Type | Stale Time | Refetch Interval | Notes |
|------|------|------------|------------------|-------|
| `useSources` | query | 5s | - | `refetchOnWindowFocus: true` |
| `useSource` | query | 30s | - | `refetchOnWindowFocus: true` |
| `useCreateSource` | mutation | - | - | Invalidates sources (active refetch) |
| `useUpdateSource` | mutation | - | - | Invalidates all sources |
| `useDeleteSource` | mutation | - | - | Invalidates all sources |
| `useFileUpload` | mutation | - | - | Invalidates notebook sources |
| `useSourceStatus` | query | 0 | 2s (while active) | Conditional polling based on status |
| `useRetrySource` | mutation | - | - | Invalidates status + sources |
| `useAddSourcesToNotebook` | mutation | - | - | Uses `Promise.allSettled` |
| `useRemoveSourceFromNotebook` | mutation | - | - | Invalidates sources |

#### Notebooks (`use-notebooks.ts`)

| Hook | Type | Stale Time | Notes |
|------|------|------------|-------|
| `useNotebooks` | query | default (5m) | Supports `archived` filter |
| `useNotebook` | query | default (5m) | Single notebook detail |
| `useCreateNotebook` | mutation | - | Invalidates notebooks list |
| `useUpdateNotebook` | mutation | - | Invalidates list + detail |
| `useDeleteNotebook` | mutation | - | Invalidates list |

#### Notes (`use-notes.ts`)

| Hook | Type | Stale Time | Notes |
|------|------|------------|-------|
| `useNotes` | query | default (5m) | Requires `notebookId` |
| `useNote` | query | default (5m) | Optional `enabled` control |
| `useCreateNote` | mutation | - | Invalidates notebook notes |
| `useUpdateNote` | mutation | - | Invalidates all notes + specific note |
| `useDeleteNote` | mutation | - | Invalidates all `['notes']` |

#### Search (`use-search.ts`)

| Hook | Type | Notes |
|------|------|-------|
| `useSearch` | mutation | Post-processes results with `final_score`, sorts descending |

#### Ask (`use-ask.ts`)

| Hook | Type | Notes |
|------|------|-------|
| `useAsk` | custom (useState + SSE) | Streaming SSE parser; phases: strategy -> answer -> final_answer -> complete |

#### Source Chat (`useSourceChat.ts`)

| Hook | Type | Notes |
|------|------|-------|
| Sessions list | query | Key: `['sourceChatSessions', sourceId]` |
| Current session | query | Key: `['sourceChatSession', sourceId, sessionId]` |
| Create/Update/Delete session | mutations | Invalidate session queries |
| `sendMessage` | custom SSE stream | Optimistic user message, streaming AI response |

#### Notebook Chat (`useNotebookChat.ts`)

| Hook | Type | Notes |
|------|------|-------|
| Sessions list | query | Uses `QUERY_KEYS.notebookChatSessions` |
| Current session | query | Uses `QUERY_KEYS.notebookChatSession` |
| Create/Update/Delete session | mutations | Standard pattern |
| `sendMessage` | custom (async, not streaming) | Builds context from selected sources/notes |

#### Models (`use-models.ts`)

| Hook | Type | Stale Time | Notes |
|------|------|------------|-------|
| `useModels` | query | default (5m) | All models list |
| `useModel` | query | default (5m) | Single model detail |
| `useCreateModel` | mutation | - | Invalidates models list |
| `useDeleteModel` | mutation | - | Invalidates models + defaults |
| `useModelDefaults` | query | default (5m) | Default model assignments |
| `useUpdateModelDefaults` | mutation | - | Invalidates defaults |
| `useProviders` | query | default (5m) | Provider list |

#### Settings (`use-settings.ts`)

| Hook | Type | Stale Time | Notes |
|------|------|------------|-------|
| `useSettings` | query | default (5m) | Global settings |
| `useUpdateSettings` | mutation | - | Invalidates settings |

#### Insights (`use-insights.ts`)

| Hook | Type | Stale Time | Notes |
|------|------|------------|-------|
| `useInsight` | query | 30s | Single insight with optional `enabled` |

#### Processing Status (`use-processing-status.ts`)

| Hook | Type | Stale Time | Refetch Interval | Notes |
|------|------|------------|------------------|-------|
| `useProcessingStatus` | query | 0 | 3s (active) / 15s (idle) | Groups sources by status |

#### Podcasts (`use-podcasts.ts`)

| Hook | Type | Refetch Interval | Notes |
|------|------|------------------|-------|
| `usePodcastEpisodes` | query | 15s (while active) | Groups by status |
| `useDeletePodcastEpisode` | mutation | - | |
| `useEpisodeProfiles` | query | - | |
| `useCreate/Update/Delete/DuplicateEpisodeProfile` | mutations | - | |
| `useSpeakerProfiles` | query | - | Computes usage map |
| `useCreate/Update/Delete/DuplicateSpeakerProfile` | mutations | - | |
| `useGeneratePodcast` | mutation | - | |

#### Transformations (`use-transformations.ts`)

| Hook | Type | Notes |
|------|------|-------|
| `useTransformations` | query | List all |
| `useTransformation` | query | Single with optional enabled |
| `useCreate/Update/DeleteTransformation` | mutations | Standard pattern |
| `useExecuteTransformation` | mutation | No success invalidation |
| `useDefaultPrompt` | query | |
| `useUpdateDefaultPrompt` | mutation | Invalidates default prompt |

#### Utility Hooks

| Hook | File | Type | Purpose |
|------|------|------|---------|
| `useAuth` | `use-auth.ts` | wrapper | Wraps auth-store with router navigation |
| `useToast` | `use-toast.ts` | wrapper | Wraps Sonner `toast.error` / `toast.success` |
| `useNavigation` | `use-navigation.ts` | wrapper | Wraps navigation-store |
| `useDebouncedValue` | `use-debounced-value.ts` | utility | Generic debounce with configurable delay |
| `useLocalStorage` | `use-local-storage.ts` | utility | SSR-safe localStorage read/write |
| `useSessionStorage` | `use-session-storage.ts` | utility | SSR-safe sessionStorage read/write |
| `useMediaQuery` | `use-media-query.ts` | utility | Viewport matching, `useIsDesktop`, `useGridColumns` |
| `useModalManager` | `use-modal-manager.ts` | utility | URL-param-based modal state |
| `useCreateDialogs` | `use-create-dialogs.tsx` | context | Global create dialogs (Source, Notebook, Podcast) |
| `useVersionCheck` | `use-version-check.ts` | effect | One-time version check with dismissible toast |

---

## 3. New Store Proposals

### 3.1 Pipeline Progress Store

Tracks multi-stage extraction pipeline progress for one or more concurrent jobs. Replaces the simple `useExtractionStatus` hook with rich stage-level visibility.

```typescript
// src/lib/stores/pipeline-progress-store.ts
import { create } from 'zustand'

export type PipelineStageStatus = 'pending' | 'running' | 'completed' | 'failed' | 'skipped'

export interface PipelineStage {
  id: string
  name: string
  status: PipelineStageStatus
  startedAt?: string
  completedAt?: string
  durationMs?: number
  detail?: string              // e.g. "Extracting 4 tables from pages 3-7"
  recordCount?: number         // e.g. 12 records extracted
  errorMessage?: string
}

export interface PipelineJob {
  jobId: string
  sourceId: string
  sourceName: string
  status: 'running' | 'completed' | 'failed' | 'cancelled'
  stages: PipelineStage[]
  currentStageIndex: number
  startedAt: string
  completedAt?: string
  totalRecords?: number
}

interface PipelineProgressState {
  jobs: Record<string, PipelineJob>

  // Actions
  startJob: (jobId: string, sourceId: string, sourceName: string, stages: string[]) => void
  updateStage: (jobId: string, stageId: string, update: Partial<PipelineStage>) => void
  advanceStage: (jobId: string, stageId: string) => void
  completeJob: (jobId: string, totalRecords?: number) => void
  failJob: (jobId: string, errorMessage: string) => void
  dismissJob: (jobId: string) => void
  clearCompleted: () => void

  // Selectors
  getActiveJobs: () => PipelineJob[]
  getJob: (jobId: string) => PipelineJob | undefined
}

export const usePipelineProgressStore = create<PipelineProgressState>((set, get) => ({
  jobs: {},

  startJob: (jobId, sourceId, sourceName, stageNames) => {
    const stages: PipelineStage[] = stageNames.map((name, i) => ({
      id: `stage-${i}`,
      name,
      status: i === 0 ? 'running' : 'pending',
    }))

    set((state) => ({
      jobs: {
        ...state.jobs,
        [jobId]: {
          jobId,
          sourceId,
          sourceName,
          status: 'running',
          stages,
          currentStageIndex: 0,
          startedAt: new Date().toISOString(),
        },
      },
    }))
  },

  updateStage: (jobId, stageId, update) => {
    set((state) => {
      const job = state.jobs[jobId]
      if (!job) return state
      return {
        jobs: {
          ...state.jobs,
          [jobId]: {
            ...job,
            stages: job.stages.map((s) =>
              s.id === stageId ? { ...s, ...update } : s
            ),
          },
        },
      }
    })
  },

  advanceStage: (jobId, nextStageId) => {
    set((state) => {
      const job = state.jobs[jobId]
      if (!job) return state
      const now = new Date().toISOString()
      const updatedStages = job.stages.map((s) => {
        if (s.status === 'running') {
          return { ...s, status: 'completed' as const, completedAt: now }
        }
        if (s.id === nextStageId) {
          return { ...s, status: 'running' as const, startedAt: now }
        }
        return s
      })
      const nextIndex = updatedStages.findIndex((s) => s.id === nextStageId)
      return {
        jobs: {
          ...state.jobs,
          [jobId]: {
            ...job,
            stages: updatedStages,
            currentStageIndex: nextIndex >= 0 ? nextIndex : job.currentStageIndex,
          },
        },
      }
    })
  },

  completeJob: (jobId, totalRecords) => {
    set((state) => {
      const job = state.jobs[jobId]
      if (!job) return state
      const now = new Date().toISOString()
      return {
        jobs: {
          ...state.jobs,
          [jobId]: {
            ...job,
            status: 'completed',
            completedAt: now,
            totalRecords,
            stages: job.stages.map((s) =>
              s.status === 'running'
                ? { ...s, status: 'completed' as const, completedAt: now }
                : s
            ),
          },
        },
      }
    })
  },

  failJob: (jobId, errorMessage) => {
    set((state) => {
      const job = state.jobs[jobId]
      if (!job) return state
      return {
        jobs: {
          ...state.jobs,
          [jobId]: {
            ...job,
            status: 'failed',
            stages: job.stages.map((s) =>
              s.status === 'running'
                ? { ...s, status: 'failed' as const, errorMessage }
                : s
            ),
          },
        },
      }
    })
  },

  dismissJob: (jobId) => {
    set((state) => {
      const { [jobId]: _, ...rest } = state.jobs
      return { jobs: rest }
    })
  },

  clearCompleted: () => {
    set((state) => {
      const activeJobs: Record<string, PipelineJob> = {}
      for (const [id, job] of Object.entries(state.jobs)) {
        if (job.status === 'running') {
          activeJobs[id] = job
        }
      }
      return { jobs: activeJobs }
    })
  },

  getActiveJobs: () => {
    return Object.values(get().jobs).filter((j) => j.status === 'running')
  },

  getJob: (jobId) => {
    return get().jobs[jobId]
  },
}))
```

**Pipeline stage names** (from extraction pipeline):
```typescript
const EXTRACTION_STAGES = [
  'Structure Analysis',
  'Preflight',
  'Agentic Orchestration',
  'Extract',
  'Interpret',
  'Corrective Validation',
  'Enrich & Store',
]
```

### 3.2 Notification Store

Persistent notifications for background jobs that survive navigation. Distinct from transient toasts.

```typescript
// src/lib/stores/notification-store.ts
import { create } from 'zustand'

export type NotificationLevel = 'info' | 'success' | 'warning' | 'error'

export interface AppNotification {
  id: string
  level: NotificationLevel
  title: string
  message: string
  timestamp: string
  read: boolean
  actionLabel?: string
  actionHref?: string
  sourceId?: string        // link to related source
  jobId?: string           // link to related pipeline job
  autoDismissMs?: number   // 0 = persistent until manually dismissed
}

interface NotificationState {
  notifications: AppNotification[]
  unreadCount: number

  // Actions
  add: (notification: Omit<AppNotification, 'id' | 'timestamp' | 'read'>) => string
  markRead: (id: string) => void
  markAllRead: () => void
  dismiss: (id: string) => void
  dismissAll: () => void
}

export const useNotificationStore = create<NotificationState>((set, get) => ({
  notifications: [],
  unreadCount: 0,

  add: (notification) => {
    const id = `notif-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`
    const entry: AppNotification = {
      ...notification,
      id,
      timestamp: new Date().toISOString(),
      read: false,
    }
    set((state) => ({
      notifications: [entry, ...state.notifications].slice(0, 50), // cap at 50
      unreadCount: state.unreadCount + 1,
    }))
    return id
  },

  markRead: (id) => {
    set((state) => {
      const wasUnread = state.notifications.find((n) => n.id === id && !n.read)
      return {
        notifications: state.notifications.map((n) =>
          n.id === id ? { ...n, read: true } : n
        ),
        unreadCount: wasUnread ? state.unreadCount - 1 : state.unreadCount,
      }
    })
  },

  markAllRead: () => {
    set((state) => ({
      notifications: state.notifications.map((n) => ({ ...n, read: true })),
      unreadCount: 0,
    }))
  },

  dismiss: (id) => {
    set((state) => {
      const wasDismissed = state.notifications.find((n) => n.id === id)
      return {
        notifications: state.notifications.filter((n) => n.id !== id),
        unreadCount:
          wasDismissed && !wasDismissed.read
            ? state.unreadCount - 1
            : state.unreadCount,
      }
    })
  },

  dismissAll: () => {
    set({ notifications: [], unreadCount: 0 })
  },
}))
```

### 3.3 Feature Flags Store

Controls dual-persona mode (Compliance Officer vs Asbestos Consultant) and feature visibility.

```typescript
// src/lib/stores/feature-flags-store.ts
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export type UserMode = 'simple' | 'advanced'

interface FeatureFlagsState {
  mode: UserMode
  flags: {
    showPipelineDetails: boolean     // expanded pipeline stages
    showParserConfig: boolean        // parser configuration UI
    showKnowledgeGraph: boolean      // knowledge graph explorer
    showBulkOperations: boolean      // bulk document actions
    showAdvancedSearch: boolean      // advanced search filters
    showRecordEditing: boolean       // inline ACM record editing
  }

  // Actions
  setMode: (mode: UserMode) => void
  toggleFlag: (flag: keyof FeatureFlagsState['flags']) => void
  setFlag: (flag: keyof FeatureFlagsState['flags'], value: boolean) => void
}

const SIMPLE_FLAGS = {
  showPipelineDetails: false,
  showParserConfig: false,
  showKnowledgeGraph: false,
  showBulkOperations: false,
  showAdvancedSearch: false,
  showRecordEditing: false,
}

const ADVANCED_FLAGS = {
  showPipelineDetails: true,
  showParserConfig: true,
  showKnowledgeGraph: true,
  showBulkOperations: true,
  showAdvancedSearch: true,
  showRecordEditing: true,
}

export const useFeatureFlagsStore = create<FeatureFlagsState>()(
  persist(
    (set) => ({
      mode: 'simple',
      flags: SIMPLE_FLAGS,

      setMode: (mode) => {
        set({
          mode,
          flags: mode === 'advanced' ? ADVANCED_FLAGS : SIMPLE_FLAGS,
        })
      },

      toggleFlag: (flag) => {
        set((state) => ({
          flags: { ...state.flags, [flag]: !state.flags[flag] },
        }))
      },

      setFlag: (flag, value) => {
        set((state) => ({
          flags: { ...state.flags, [flag]: value },
        }))
      },
    }),
    {
      name: 'feature-flags-storage',
      partialize: (state) => ({ mode: state.mode, flags: state.flags }),
    }
  )
)
```

---

## 4. Skeleton Screen Specifications

### 4.1 Design Principles

1. **Match content layout:** Skeleton shapes must mirror the dimensions of the actual content to prevent Cumulative Layout Shift (CLS).
2. **Accessibility:** Mark skeleton containers with `aria-busy="true"` and add a visually hidden `<span>` with `role="status"` announcing "Loading content".
3. **Progressive reveal:** Skeletons should fade out as real content fades in using a brief opacity transition (150ms).
4. **No spinners in skeletons:** Skeleton screens replace spinners at the page and component level. The `LoadingSpinner` component is reserved for inline loading indicators (buttons, form submissions).

### 4.2 Base Skeleton Component

The existing `Skeleton` component (`src/components/ui/skeleton.tsx`) uses `animate-pulse` with `bg-muted`. This will be enhanced with a shimmer variant (see Section 5).

```typescript
// Enhanced skeleton with shimmer support
interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'pulse' | 'shimmer'
}

function Skeleton({ className, variant = 'shimmer', ...props }: SkeletonProps) {
  return (
    <div
      className={cn(
        'rounded-md bg-muted',
        variant === 'shimmer' ? 'animate-shimmer' : 'animate-pulse',
        className
      )}
      {...props}
    />
  )
}
```

### 4.3 Page-Level Skeleton Specifications

#### Dashboard Page Skeleton

```typescript
// src/components/skeletons/DashboardSkeleton.tsx

export function DashboardSkeleton() {
  return (
    <div className="space-y-6 p-6" aria-busy="true">
      <span className="sr-only" role="status">Loading dashboard</span>

      {/* Page title */}
      <Skeleton className="h-8 w-48" />

      {/* Stats cards row - 4 bento cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="rounded-xl border p-6 space-y-3">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-8 w-16" />
            <Skeleton className="h-3 w-32" />
          </div>
        ))}
      </div>

      {/* Risk chart + recent sources */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Risk donut chart placeholder */}
        <div className="rounded-xl border p-6 space-y-4">
          <Skeleton className="h-5 w-32" />
          <Skeleton className="h-48 w-48 rounded-full mx-auto" />
        </div>

        {/* Recent sources list */}
        <div className="rounded-xl border p-6 space-y-4">
          <Skeleton className="h-5 w-40" />
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="flex items-center gap-3">
              <Skeleton className="h-10 w-10 rounded" />
              <div className="flex-1 space-y-2">
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-3 w-1/2" />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
```

#### Documents Page Skeleton

```typescript
// src/components/skeletons/DocumentsSkeleton.tsx

export function DocumentsSkeleton() {
  return (
    <div className="space-y-6 p-6" aria-busy="true">
      <span className="sr-only" role="status">Loading documents</span>

      {/* Header with title + filters */}
      <div className="flex items-center justify-between">
        <Skeleton className="h-8 w-40" />
        <div className="flex gap-2">
          <Skeleton className="h-9 w-32" />
          <Skeleton className="h-9 w-24" />
          <Skeleton className="h-9 w-9" />
        </div>
      </div>

      {/* Filter bar */}
      <div className="flex gap-2">
        <Skeleton className="h-8 w-20 rounded-full" />
        <Skeleton className="h-8 w-24 rounded-full" />
        <Skeleton className="h-8 w-28 rounded-full" />
      </div>

      {/* Document cards grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="rounded-xl border p-4 space-y-3">
            <div className="flex items-start justify-between">
              <Skeleton className="h-10 w-10 rounded" />
              <Skeleton className="h-5 w-16 rounded-full" />
            </div>
            <Skeleton className="h-5 w-3/4" />
            <Skeleton className="h-3 w-full" />
            <Skeleton className="h-3 w-2/3" />
            <div className="flex gap-2 pt-2">
              <Skeleton className="h-6 w-16 rounded-full" />
              <Skeleton className="h-6 w-20 rounded-full" />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
```

#### ACM Register Page Skeleton

```typescript
// src/components/skeletons/ACMRegisterSkeleton.tsx

export function ACMRegisterSkeleton() {
  return (
    <div className="space-y-4 p-6" aria-busy="true">
      <span className="sr-only" role="status">Loading ACM register</span>

      {/* Stats cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="rounded-lg border p-4 space-y-2">
            <Skeleton className="h-3 w-20" />
            <Skeleton className="h-7 w-12" />
          </div>
        ))}
      </div>

      {/* Toolbar: search + building tabs + actions */}
      <div className="flex items-center gap-3">
        <Skeleton className="h-9 w-64" />
        <div className="flex gap-1">
          <Skeleton className="h-8 w-20 rounded-full" />
          <Skeleton className="h-8 w-24 rounded-full" />
          <Skeleton className="h-8 w-28 rounded-full" />
        </div>
        <div className="ml-auto flex gap-2">
          <Skeleton className="h-9 w-9" />
          <Skeleton className="h-9 w-9" />
        </div>
      </div>

      {/* AG Grid skeleton: header + 10 rows, 8 columns */}
      <div className="rounded-lg border overflow-hidden">
        {/* Header row */}
        <div className="flex border-b bg-muted/30 p-2 gap-2">
          {Array.from({ length: 8 }).map((_, i) => (
            <Skeleton
              key={i}
              className="h-4 flex-1"
              style={{ maxWidth: i === 0 ? 40 : undefined }}
            />
          ))}
        </div>
        {/* Data rows */}
        {Array.from({ length: 10 }).map((_, row) => (
          <div key={row} className="flex border-b p-3 gap-2">
            {Array.from({ length: 8 }).map((_, col) => (
              <Skeleton
                key={col}
                className={cn('h-4 flex-1', col === 0 && 'max-w-[40px]')}
              />
            ))}
          </div>
        ))}
      </div>
    </div>
  )
}
```

#### Search Page Skeleton

```typescript
// src/components/skeletons/SearchSkeleton.tsx

export function SearchSkeleton() {
  return (
    <div className="max-w-4xl mx-auto space-y-6 p-6" aria-busy="true">
      <span className="sr-only" role="status">Loading search</span>

      {/* Search input */}
      <Skeleton className="h-12 w-full rounded-lg" />

      {/* Model selectors */}
      <div className="flex gap-3">
        <Skeleton className="h-9 w-40" />
        <Skeleton className="h-9 w-40" />
        <Skeleton className="h-9 w-40" />
      </div>

      {/* Results placeholder */}
      <div className="space-y-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="rounded-lg border p-4 space-y-2">
            <Skeleton className="h-5 w-2/3" />
            <Skeleton className="h-3 w-full" />
            <Skeleton className="h-3 w-full" />
            <Skeleton className="h-3 w-1/2" />
          </div>
        ))}
      </div>
    </div>
  )
}
```

#### Settings Page Skeleton

```typescript
// src/components/skeletons/SettingsSkeleton.tsx

export function SettingsSkeleton() {
  return (
    <div className="max-w-2xl mx-auto space-y-8 p-6" aria-busy="true">
      <span className="sr-only" role="status">Loading settings</span>

      <Skeleton className="h-8 w-32" />

      {/* Settings sections */}
      {Array.from({ length: 4 }).map((_, section) => (
        <div key={section} className="space-y-4">
          <Skeleton className="h-5 w-48" />
          <div className="rounded-lg border p-4 space-y-4">
            {Array.from({ length: 3 }).map((_, field) => (
              <div key={field} className="space-y-2">
                <Skeleton className="h-4 w-32" />
                <Skeleton className="h-9 w-full" />
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}
```

### 4.4 Component-Level Skeletons

#### Card Skeleton (reusable)

```typescript
export function CardSkeleton({ lines = 3 }: { lines?: number }) {
  return (
    <div className="rounded-xl border p-4 space-y-3">
      <div className="flex items-center gap-3">
        <Skeleton className="h-10 w-10 rounded" />
        <div className="flex-1 space-y-1">
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-3 w-1/2" />
        </div>
      </div>
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton key={i} className="h-3 w-full" />
      ))}
    </div>
  )
}
```

#### Grid Row Skeleton (for AG Grid)

```typescript
export function GridRowSkeleton({ columns = 8 }: { columns?: number }) {
  return (
    <div className="flex border-b p-3 gap-2">
      {Array.from({ length: columns }).map((_, i) => (
        <Skeleton key={i} className="h-4 flex-1" />
      ))}
    </div>
  )
}
```

---

## 5. Shimmer Animation CSS

### 5.1 CSS Keyframes

Add to `src/app/globals.css`:

```css
@keyframes shimmer {
  0% {
    background-position: -200% 0;
  }
  100% {
    background-position: 200% 0;
  }
}
```

### 5.2 Tailwind Configuration

Add to `tailwind.config.ts` under `theme.extend.animation` and `theme.extend.keyframes`:

```typescript
// tailwind.config.ts
export default {
  theme: {
    extend: {
      animation: {
        shimmer: 'shimmer 2s linear infinite',
      },
      keyframes: {
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
      },
    },
  },
}
```

### 5.3 Shimmer Utility Class

```css
/* globals.css */
.animate-shimmer {
  background: linear-gradient(
    90deg,
    hsl(var(--muted)) 25%,
    hsl(var(--muted-foreground) / 0.08) 50%,
    hsl(var(--muted)) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 2s linear infinite;
}
```

### 5.4 Dark Mode Variant

The shimmer gradient automatically adapts through CSS custom properties (`--muted` and `--muted-foreground`). No separate dark mode definition needed because these variables change per theme.

### 5.5 Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  .animate-shimmer {
    animation: none;
    background: hsl(var(--muted));
  }
}
```

---

## 6. Multi-Stage Pipeline Progress

### 6.1 Pipeline Progress Component

Displays the current state of an extraction pipeline job with expandable stage details.

```typescript
// src/components/pipeline/PipelineProgress.tsx

import { usePipelineProgressStore, PipelineJob, PipelineStage } from '@/lib/stores/pipeline-progress-store'
import { Check, Loader2, AlertCircle, Circle, ChevronDown } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useState } from 'react'

interface PipelineProgressProps {
  jobId: string
  compact?: boolean      // collapsed single-line view for sidebar
}

export function PipelineProgress({ jobId, compact = false }: PipelineProgressProps) {
  const job = usePipelineProgressStore((s) => s.getJob(jobId))
  const dismissJob = usePipelineProgressStore((s) => s.dismissJob)
  const [expanded, setExpanded] = useState(false)

  if (!job) return null

  const completedCount = job.stages.filter((s) => s.status === 'completed').length
  const progressPercent = Math.round((completedCount / job.stages.length) * 100)
  const currentStage = job.stages.find((s) => s.status === 'running')

  if (compact) {
    return (
      <div className="flex items-center gap-2 text-sm px-3 py-2">
        <Loader2 className="h-4 w-4 animate-spin text-primary" />
        <span className="truncate">
          {currentStage?.name ?? 'Processing'}
        </span>
        <span className="text-muted-foreground ml-auto">{progressPercent}%</span>
      </div>
    )
  }

  return (
    <div className="rounded-lg border bg-card p-4 space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <StatusIcon status={job.status === 'running' ? 'running' : job.status} />
          <span className="font-medium text-sm">{job.sourceName}</span>
        </div>
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-muted-foreground hover:text-foreground"
        >
          <ChevronDown
            className={cn('h-4 w-4 transition-transform', expanded && 'rotate-180')}
          />
        </button>
      </div>

      {/* Progress bar */}
      <div className="h-2 bg-muted rounded-full overflow-hidden">
        <div
          className={cn(
            'h-full rounded-full transition-all duration-500',
            job.status === 'failed' ? 'bg-destructive' : 'bg-primary'
          )}
          style={{ width: `${progressPercent}%` }}
        />
      </div>

      {/* Current stage label */}
      <div className="text-sm text-muted-foreground">
        {currentStage
          ? `Step ${job.currentStageIndex + 1}/${job.stages.length}: ${currentStage.name}`
          : job.status === 'completed'
            ? `Completed - ${job.totalRecords ?? 0} records extracted`
            : 'Processing...'}
      </div>

      {/* Expanded stage list */}
      {expanded && (
        <div className="space-y-1 pt-2 border-t">
          {job.stages.map((stage) => (
            <StageRow key={stage.id} stage={stage} />
          ))}
        </div>
      )}

      {/* Actions */}
      {(job.status === 'completed' || job.status === 'failed') && (
        <div className="flex justify-end gap-2 pt-2">
          <button
            onClick={() => dismissJob(jobId)}
            className="text-sm text-muted-foreground hover:text-foreground"
          >
            Dismiss
          </button>
          {job.status === 'completed' && (
            <a
              href={`/sources/${job.sourceId}`}
              className="text-sm text-primary hover:underline"
            >
              View Results
            </a>
          )}
        </div>
      )}
    </div>
  )
}

function StageRow({ stage }: { stage: PipelineStage }) {
  return (
    <div className="flex items-center gap-2 py-1 text-sm">
      <StatusIcon status={stage.status} size="sm" />
      <span
        className={cn(
          stage.status === 'running' && 'font-medium',
          stage.status === 'pending' && 'text-muted-foreground',
          stage.status === 'failed' && 'text-destructive'
        )}
      >
        {stage.name}
      </span>
      {stage.detail && (
        <span className="text-muted-foreground ml-auto text-xs">{stage.detail}</span>
      )}
      {stage.durationMs !== undefined && stage.status === 'completed' && (
        <span className="text-muted-foreground ml-auto text-xs">
          {formatDuration(stage.durationMs)}
        </span>
      )}
    </div>
  )
}

function StatusIcon({ status, size = 'md' }: { status: string; size?: 'sm' | 'md' }) {
  const cls = size === 'sm' ? 'h-3.5 w-3.5' : 'h-4 w-4'
  switch (status) {
    case 'completed':
      return <Check className={cn(cls, 'text-green-600')} />
    case 'running':
      return <Loader2 className={cn(cls, 'animate-spin text-primary')} />
    case 'failed':
      return <AlertCircle className={cn(cls, 'text-destructive')} />
    default:
      return <Circle className={cn(cls, 'text-muted-foreground')} />
  }
}

function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`
  const seconds = Math.round(ms / 1000)
  if (seconds < 60) return `${seconds}s`
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  return `${minutes}m ${remainingSeconds}s`
}
```

### 6.2 Integration with AG-UI Events

When AG-UI (CopilotKit) is integrated, the pipeline progress store will be driven by real-time events instead of polling:

```typescript
// Future integration pattern (AG-UI)
import { useCopilotAction } from '@copilotkit/react-core'
import { usePipelineProgressStore } from '@/lib/stores/pipeline-progress-store'

function useExtractionPipeline(sourceId: string) {
  const store = usePipelineProgressStore()

  useCopilotAction({
    name: 'extraction_progress',
    handler: async (event) => {
      const { jobId, stage, status, detail, recordCount } = event.parameters

      switch (status) {
        case 'stage_started':
          store.advanceStage(jobId, stage)
          break
        case 'stage_detail':
          store.updateStage(jobId, stage, { detail })
          break
        case 'stage_completed':
          store.updateStage(jobId, stage, {
            status: 'completed',
            recordCount,
          })
          break
        case 'job_completed':
          store.completeJob(jobId, recordCount)
          break
        case 'job_failed':
          store.failJob(jobId, detail ?? 'Extraction failed')
          break
      }
    },
  })
}
```

### 6.3 Fallback Polling Pattern

Until AG-UI is available, the existing polling approach via `useExtractionStatus` continues to work. The pipeline progress store can be updated from the polling hook:

```typescript
// Bridge: polling -> pipeline progress store
function useExtractionWithProgress(sourceId: string) {
  const extraction = useExtractionStatus(sourceId)
  const store = usePipelineProgressStore()

  useEffect(() => {
    if (extraction.phase === 'extracting') {
      // Show a simplified single-stage progress
      store.startJob(`poll-${sourceId}`, sourceId, 'Document', ['Processing'])
    } else if (extraction.phase === 'completed') {
      store.completeJob(`poll-${sourceId}`, extraction.recordsCreated)
    } else if (extraction.phase === 'failed') {
      store.failJob(`poll-${sourceId}`, extraction.errorMessage ?? 'Failed')
    }
  }, [extraction.phase])

  return extraction
}
```

---

## 7. Toast and Notification System

### 7.1 Current State

The `useToast` hook wraps Sonner with a simplified API:

```typescript
// Current: only supports success + error
toast({ title, description, variant: 'default' | 'destructive' })
```

The Sonner `<Toaster>` component is already configured with theme awareness.

### 7.2 Enhanced Toast Patterns

#### Promise-Based Toasts for Extraction Jobs

```typescript
import { toast } from 'sonner'

// In extraction trigger handler:
function handleExtract(sourceId: string) {
  const extractPromise = acmApi.extract(sourceId)

  toast.promise(extractPromise, {
    loading: 'Starting ACM extraction...',
    success: (result) => `Extraction started: ${result.message}`,
    error: 'Failed to start extraction',
  })
}
```

#### Long-Running Job Progress Toast

```typescript
// For background jobs with progress updates
function startExtractionToast(jobId: string, sourceName: string) {
  const toastId = toast.loading(`Processing "${sourceName}"...`, {
    description: 'Stage 1/7: Structure Analysis',
    duration: Infinity,  // persist until explicitly dismissed
  })

  return {
    updateProgress: (stage: string, current: number, total: number) => {
      toast.loading(`Processing "${sourceName}"...`, {
        id: toastId,
        description: `Stage ${current}/${total}: ${stage}`,
      })
    },
    complete: (recordCount: number) => {
      toast.success(`Extraction complete`, {
        id: toastId,
        description: `${recordCount} records extracted from "${sourceName}"`,
        action: {
          label: 'View Results',
          onClick: () => window.location.assign(`/sources/${jobId}`),
        },
        duration: 10000,
      })
    },
    fail: (error: string) => {
      toast.error(`Extraction failed`, {
        id: toastId,
        description: error,
        action: {
          label: 'Retry',
          onClick: () => handleExtract(jobId),
        },
        duration: 15000,
      })
    },
  }
}
```

#### Risk-Aware Toast Variants

```typescript
// Custom styled toasts for risk levels
function riskToast(level: 'high' | 'medium' | 'low', message: string) {
  const borderClass = {
    high: 'border-l-4 border-l-red-500',
    medium: 'border-l-4 border-l-amber-500',
    low: 'border-l-4 border-l-green-500',
  }[level]

  toast(message, {
    className: borderClass,
    duration: level === 'high' ? Infinity : 5000,
    closeButton: level === 'high',
  })
}
```

#### Action Toasts for Human-in-the-Loop

```typescript
// Toast with review action for extraction validation
toast.info('Extraction needs review', {
  description: '3 records have low confidence scores',
  duration: Infinity,
  closeButton: true,
  action: {
    label: 'Review Now',
    onClick: () => {
      router.push(`/sources/${sourceId}?tab=acm&filter=low-confidence`)
    },
  },
})
```

### 7.3 Enhanced useToast Hook

```typescript
// src/lib/hooks/use-toast.ts (enhanced)
import { toast as sonnerToast } from 'sonner'

type ToastVariant = 'default' | 'destructive' | 'warning' | 'info'

interface ToastProps {
  title?: string
  description?: string
  variant?: ToastVariant
  duration?: number
  action?: {
    label: string
    onClick: () => void
  }
  closeButton?: boolean
}

export function useToast() {
  return {
    toast: ({ title, description, variant = 'default', duration, action, closeButton }: ToastProps) => {
      const options = { description, duration, action, closeButton }

      switch (variant) {
        case 'destructive':
          return sonnerToast.error(title || 'Error', options)
        case 'warning':
          return sonnerToast.warning(title || 'Warning', options)
        case 'info':
          return sonnerToast.info(title || 'Info', options)
        default:
          return sonnerToast.success(title || 'Success', options)
      }
    },
    promise: sonnerToast.promise,
    loading: sonnerToast.loading,
    dismiss: sonnerToast.dismiss,
  }
}
```

---

## 8. Optimistic Update Patterns

### 8.1 Pattern: Optimistic Create with Rollback

```typescript
// Example: Creating an ACM record optimistically
export function useCreateACMRecordOptimistic() {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: (data: ACMRecordCreateRequest) => acmApi.create(data),

    onMutate: async (newRecord) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({
        queryKey: ['acm', 'records', newRecord.source_id],
      })

      // Snapshot previous value
      const previousRecords = queryClient.getQueryData(
        ['acm', 'records', newRecord.source_id]
      )

      // Optimistically add the new record
      queryClient.setQueryData(
        ['acm', 'records', newRecord.source_id],
        (old: any) => {
          if (!old) return old
          const optimisticRecord = {
            ...newRecord,
            id: `temp-${Date.now()}`,
            created: new Date().toISOString(),
            updated: new Date().toISOString(),
          }
          return {
            ...old,
            records: [...(old.records || []), optimisticRecord],
            total: (old.total || 0) + 1,
          }
        }
      )

      return { previousRecords }
    },

    onError: (_error, variables, context) => {
      // Rollback on error
      if (context?.previousRecords) {
        queryClient.setQueryData(
          ['acm', 'records', variables.source_id],
          context.previousRecords
        )
      }
      toast({
        title: 'Error',
        description: 'Failed to create ACM record',
        variant: 'destructive',
      })
    },

    onSettled: (_data, _error, variables) => {
      // Always refetch to sync with server
      queryClient.invalidateQueries({
        queryKey: ['acm', 'records', variables.source_id],
      })
      queryClient.invalidateQueries({
        queryKey: ACM_QUERY_KEYS.stats(variables.source_id),
      })
    },

    onSuccess: () => {
      toast({
        title: 'Success',
        description: 'ACM record created successfully',
      })
    },
  })
}
```

### 8.2 Pattern: Optimistic Delete

```typescript
export function useDeleteACMRecordOptimistic() {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: ({ recordId }: { recordId: string; sourceId: string }) =>
      acmApi.delete(recordId),

    onMutate: async ({ recordId, sourceId }) => {
      await queryClient.cancelQueries({
        queryKey: ['acm', 'records', sourceId],
      })

      const previousRecords = queryClient.getQueryData(
        ['acm', 'records', sourceId]
      )

      // Optimistically remove the record
      queryClient.setQueryData(
        ['acm', 'records', sourceId],
        (old: any) => {
          if (!old) return old
          return {
            ...old,
            records: (old.records || []).filter((r: any) => r.id !== recordId),
            total: Math.max(0, (old.total || 0) - 1),
          }
        }
      )

      return { previousRecords }
    },

    onError: (_error, { sourceId }, context) => {
      if (context?.previousRecords) {
        queryClient.setQueryData(
          ['acm', 'records', sourceId],
          context.previousRecords
        )
      }
      toast({
        title: 'Error',
        description: 'Failed to delete ACM record',
        variant: 'destructive',
      })
    },

    onSettled: (_data, _error, { sourceId }) => {
      queryClient.invalidateQueries({
        queryKey: ['acm', 'records', sourceId],
      })
      queryClient.invalidateQueries({
        queryKey: ACM_QUERY_KEYS.stats(sourceId),
      })
    },

    onSuccess: () => {
      toast({
        title: 'Success',
        description: 'ACM record deleted',
      })
    },
  })
}
```

### 8.3 Pattern: Optimistic Update

```typescript
export function useUpdateACMRecordOptimistic() {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: ({ recordId, data }: { recordId: string; sourceId: string; data: ACMRecordUpdateRequest }) =>
      acmApi.update(recordId, data),

    onMutate: async ({ recordId, sourceId, data }) => {
      await queryClient.cancelQueries({
        queryKey: ['acm', 'records', sourceId],
      })

      const previousRecords = queryClient.getQueryData(
        ['acm', 'records', sourceId]
      )

      // Optimistically update the record
      queryClient.setQueryData(
        ['acm', 'records', sourceId],
        (old: any) => {
          if (!old) return old
          return {
            ...old,
            records: (old.records || []).map((r: any) =>
              r.id === recordId ? { ...r, ...data, updated: new Date().toISOString() } : r
            ),
          }
        }
      )

      return { previousRecords }
    },

    onError: (_error, { sourceId }, context) => {
      if (context?.previousRecords) {
        queryClient.setQueryData(
          ['acm', 'records', sourceId],
          context.previousRecords
        )
      }
      toast({
        title: 'Error',
        description: 'Failed to update ACM record',
        variant: 'destructive',
      })
    },

    onSettled: (_data, _error, { recordId, sourceId }) => {
      queryClient.invalidateQueries({
        queryKey: ACM_QUERY_KEYS.record(recordId),
      })
      queryClient.invalidateQueries({
        queryKey: ['acm', 'records', sourceId],
      })
      queryClient.invalidateQueries({
        queryKey: ACM_QUERY_KEYS.stats(sourceId),
      })
    },

    onSuccess: () => {
      toast({
        title: 'Success',
        description: 'ACM record updated',
      })
    },
  })
}
```

### 8.4 When to Use Optimistic Updates

| Operation | Use Optimistic? | Rationale |
|-----------|----------------|-----------|
| ACM record create/update/delete | Yes | Low-latency feel for grid editing |
| Source upload | No | Server-side processing required |
| Extraction trigger | No | Long-running background job |
| Settings update | Yes | Immediate feedback expected |
| Source delete | Yes | Instant removal from list |
| Notebook CRUD | Yes | Fast UI response |
| Note CRUD | Yes | Fast UI response |
| Chat message send | Already optimistic | Current pattern adds user message before server response |
| Site config save | No | Validation on server required |

---

## 9. Error Boundary and Recovery Patterns

### 9.1 Current ErrorBoundary

**File:** `src/components/common/ErrorBoundary.tsx`

The existing class component catches render errors and shows a card with:
- Error icon
- "Something went wrong" message
- Error details in development mode (`process.env.NODE_ENV === 'development'`)
- "Try Again" button (resets boundary state)
- "Refresh Page" button (full page reload)
- Supports custom `fallback` component via props

**Observations:**
- Does not report errors to any monitoring service.
- No route-level boundaries (only the global one in root layout).
- The `useErrorBoundary` hook simply re-throws errors (forces the nearest boundary to catch).

### 9.2 Route-Level Error Boundaries

Each major page should have its own error boundary to prevent a single broken page from crashing the entire application.

```typescript
// Example: ACM page with route-level error boundary
// src/app/(dashboard)/acm/page.tsx

import { ErrorBoundary } from '@/components/common/ErrorBoundary'
import { ACMRegisterContent } from '@/components/acm/ACMRegisterContent'

function ACMErrorFallback({ error, resetError }: { error?: Error; resetError: () => void }) {
  return (
    <div className="p-6 text-center space-y-4">
      <h2 className="text-lg font-medium">Failed to load ACM Register</h2>
      <p className="text-sm text-muted-foreground">{error?.message}</p>
      <button onClick={resetError} className="btn-primary">
        Retry
      </button>
    </div>
  )
}

export default function ACMPage() {
  return (
    <ErrorBoundary fallback={ACMErrorFallback}>
      <ACMRegisterContent />
    </ErrorBoundary>
  )
}
```

### 9.3 API Error Recovery with React Query

React Query already provides retry logic (2 retries for queries, 1 for mutations). Additional patterns:

```typescript
// Custom retry logic for specific error codes
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: (failureCount, error) => {
        const axiosError = error as { response?: { status?: number } }
        const status = axiosError?.response?.status

        // Never retry auth errors
        if (status === 401 || status === 403) return false

        // Never retry validation errors
        if (status === 422) return false

        // Retry server errors up to 2 times
        if (status && status >= 500) return failureCount < 2

        // Default: retry up to 2 times
        return failureCount < 2
      },
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 10000),
    },
  },
})
```

### 9.4 Enhanced ConnectionGuard

The existing `ConnectionGuard` checks connectivity on mount only. Enhancements:

```typescript
// Periodic health check while app is active
export function ConnectionGuard({ children }: { children: React.ReactNode }) {
  const [error, setError] = useState<ConnectionError | null>(null)
  const [isChecking, setIsChecking] = useState(true)

  const checkConnection = useCallback(async () => {
    // ... existing check logic ...
  }, [])

  // Check on mount
  useEffect(() => {
    checkConnection()
  }, [checkConnection])

  // Periodic health check every 30 seconds
  useEffect(() => {
    if (error) return // don't poll while showing error overlay

    const interval = setInterval(async () => {
      try {
        const config = await getConfig()
        if (config.dbStatus === 'offline') {
          setError({
            type: 'database-offline',
            details: { message: 'Database connection lost' },
          })
        }
      } catch {
        setError({
          type: 'api-unreachable',
          details: { message: 'Connection to server lost' },
        })
      }
    }, 30000)

    return () => clearInterval(interval)
  }, [error])

  // Online/offline browser events
  useEffect(() => {
    const handleOffline = () => {
      setError({
        type: 'api-unreachable',
        details: { message: 'Your device appears to be offline' },
      })
    }
    const handleOnline = () => {
      checkConnection()
    }

    window.addEventListener('offline', handleOffline)
    window.addEventListener('online', handleOnline)
    return () => {
      window.removeEventListener('offline', handleOffline)
      window.removeEventListener('online', handleOnline)
    }
  }, [checkConnection])

  // ... render logic ...
}
```

### 9.5 Session Timeout Handling

Enhancement to the auth store to periodically validate the session:

```typescript
// In the dashboard layout, add session check interval
useEffect(() => {
  if (!isAuthenticated || authRequired === false) return

  const interval = setInterval(async () => {
    const valid = await checkAuth()
    if (!valid) {
      toast.warning('Session expired', {
        description: 'Please log in again',
        duration: Infinity,
        action: {
          label: 'Log In',
          onClick: () => router.push('/login'),
        },
      })
    }
  }, 5 * 60 * 1000) // Check every 5 minutes

  return () => clearInterval(interval)
}, [isAuthenticated, authRequired])
```

### 9.6 Form Validation Errors (React Hook Form + Zod)

Pattern for consistent form error display:

```typescript
// Reusable form field error display
import { FieldError } from 'react-hook-form'

interface FieldErrorMessageProps {
  error?: FieldError
}

function FieldErrorMessage({ error }: FieldErrorMessageProps) {
  if (!error) return null
  return (
    <p className="text-sm text-destructive mt-1" role="alert">
      {error.message}
    </p>
  )
}
```

Zod schema validation that surfaces friendly messages:

```typescript
import { z } from 'zod'

const siteConfigSchema = z.object({
  school_name: z.string().min(1, 'School name is required'),
  school_number: z.string().regex(/^\d{4}$/, 'Must be a 4-digit school number'),
  department: z.enum(['education', 'health', 'other'], {
    errorMap: () => ({ message: 'Please select a department' }),
  }),
  assessment_date: z.string().refine(
    (val) => !isNaN(Date.parse(val)),
    'Please enter a valid date'
  ),
})
```

### 9.7 Error Recovery Summary

| Error Type | Current Handling | Enhancement |
|------------|-----------------|-------------|
| Render crash | Global ErrorBoundary | Add route-level boundaries |
| API unreachable | ConnectionGuard (mount only) | Add periodic health check + online/offline events |
| API 4xx | Toast error | Retry logic exempt for 401/403/422 |
| API 5xx | Toast error (retry 2x) | Exponential backoff with max 10s |
| Session expired | `checkAuth` on mount | Periodic 5-minute check with re-login prompt |
| Form validation | Per-field Zod errors | Consistent `FieldErrorMessage` component |
| Extraction failure | Banner with error message | Toast with retry action button |
| Offline state | Not handled | Browser `offline`/`online` events |

---

## Appendix: File Locations

| Artifact | Path |
|----------|------|
| Zustand stores | `src/lib/stores/*.ts` |
| React Query hooks | `src/lib/hooks/*.ts` |
| Query client config | `src/lib/api/query-client.ts` |
| Loading components | `src/components/common/LoadingSpinner.tsx` |
| Error boundary | `src/components/common/ErrorBoundary.tsx` |
| Connection guard | `src/components/common/ConnectionGuard.tsx` |
| Skeleton component | `src/components/ui/skeleton.tsx` |
| Toast provider | `src/components/ui/sonner.tsx` |
| Skeleton screens (new) | `src/components/skeletons/*.tsx` |
| Pipeline progress (new) | `src/components/pipeline/PipelineProgress.tsx` |
| Pipeline store (new) | `src/lib/stores/pipeline-progress-store.ts` |
| Notification store (new) | `src/lib/stores/notification-store.ts` |
| Feature flags store (new) | `src/lib/stores/feature-flags-store.ts` |
