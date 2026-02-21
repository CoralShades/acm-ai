# Navigation Redesign and Feature Cleanup Specification

> **Version:** 1.0
> **Date:** 2026-02-08
> **Status:** Draft
> **Epic:** E10 (UI Simplification) + E12 (Settings UI)

---

## 1. Current Navigation Structure

### 1.1 Sidebar Layout (AppSidebar.tsx)

The current sidebar at `frontend/src/components/layout/AppSidebar.tsx` uses a 4-section taxonomy with 11 navigation items:

```
ACM-AI (Logo + text)                    [Collapse btn]
-----------------------------------------------------
[Dashboard]                              (standalone)
-----------------------------------------------------
[+ Create]  (dropdown: Source, Notebook, Podcast)
-----------------------------------------------------
COLLECT
  Sources         -> /sources
  Documents       -> /documents
  ACM Register    -> /acm
-----------------------------------------------------
PROCESS
  Notebooks       -> /notebooks
  Ask and Search  -> /search
-----------------------------------------------------
CREATE
  Podcasts        -> /podcasts
-----------------------------------------------------
MANAGE
  Models          -> /models
  Transformations -> /transformations
  Settings        -> /settings
  Advanced        -> /advanced
-----------------------------------------------------
[Cmd+K hint]
[Theme Toggle]
[Sign Out]
```

### 1.2 Issues with Current Structure

| Issue | Impact |
|-------|--------|
| "Collect/Process/Create/Manage" taxonomy is confusing for ACM compliance officers | Users cannot intuitively find features |
| Podcasts, Transformations, Notebooks are irrelevant to ACM workflow | Clutters the UI with unused features |
| "Create" button offers Source/Notebook/Podcast dropdown | Should be a single "Upload Document" CTA |
| No extraction settings in navigation | Needed for E12 stories (Extraction, Parsers, Processing) |
| Sources and Documents are separate pages with overlapping purpose | Confusing - both deal with uploaded documents |
| Settings and Advanced are separate pages | Should be unified under a single settings area |
| Models page is standalone | Should be a section within settings |
| Middleware redirects `/` to `/notebooks` | Should redirect to Dashboard (`/`) |
| Command palette contains Notebooks, Podcasts, Transformations entries | Should match simplified nav |
| Sidebar store defaults have old section names (`Collect`, `Process`, `Create`, `Manage`) | Must update to new section names |

### 1.3 Current File Inventory

| File | Purpose | Lines |
|------|---------|-------|
| `components/layout/AppSidebar.tsx` | Sidebar navigation component | 466 |
| `components/layout/AppShell.tsx` | Layout shell with sidebar | 19 |
| `components/common/CommandPalette.tsx` | Cmd+K command palette | 282 |
| `lib/hooks/use-create-dialogs.tsx` | Create dialog context provider | 48 |
| `lib/stores/sidebar-store.ts` | Sidebar collapse/expand state | 45 |
| `middleware.ts` | Route redirects | 19 |
| `config/branding.ts` | App name, description, API info | 34 |
| `components/brand/Logo.tsx` | SVG logo component | 63 |

---

## 2. Target Navigation Structure

### 2.1 New Sidebar Layout

```
VAEA ACM-AI (VAEA ripple logo + text)   [Collapse btn]
-----------------------------------------------------
[Upload Document]  (primary CTA button, opens AddSourceDialog directly)
-----------------------------------------------------
WORKSPACE
  Dashboard        -> /
  Documents        -> /documents   (merged sources + documents)
  ACM Register     -> /acm
  Search           -> /search
-----------------------------------------------------
CONFIGURE
  Extraction       -> /settings/extraction    (E12-S1 placeholder)
  AI Models        -> /settings/models        (existing models page content)
  Parsers          -> /settings/parsers       (E12-S4 placeholder)
  Processing       -> /settings/processing    (E12-S3 placeholder)
  General          -> /settings               (existing settings + advanced merged)
-----------------------------------------------------
[VAEA Logo]
Powered by CoralShades
[Theme Toggle] [Sign Out]
```

### 2.2 Design Rationale

- **WORKSPACE** groups the daily-use pages for compliance officers and consultants
- **CONFIGURE** groups all configuration/admin pages under a single section
- Hidden features (Notebooks, Podcasts, Transformations) keep their routes accessible via direct URL but are removed from navigation
- "Upload Document" replaces the multi-option "Create" dropdown since document upload is the primary entry point for ACM workflow
- All settings-related pages are consolidated under `/settings/*` routes

---

## 3. AppSidebar.tsx Changes

### 3.1 Navigation Array (Before)

```tsx
// Current navigation definition (lines 64-93)
const navigation: NavSection[] = [
  {
    title: 'Collect',
    items: [
      { name: 'Sources', href: '/sources', icon: FileText },
      { name: 'Documents', href: '/documents', icon: Library },
      { name: 'ACM Register', href: '/acm', icon: FileWarning },
    ],
  },
  {
    title: 'Process',
    items: [
      { name: 'Notebooks', href: '/notebooks', icon: Book },
      { name: 'Ask and Search', href: '/search', icon: Search },
    ],
  },
  {
    title: 'Create',
    items: [{ name: 'Podcasts', href: '/podcasts', icon: Mic }],
  },
  {
    title: 'Manage',
    items: [
      { name: 'Models', href: '/models', icon: Bot },
      { name: 'Transformations', href: '/transformations', icon: Shuffle },
      { name: 'Settings', href: '/settings', icon: Settings },
      { name: 'Advanced', href: '/advanced', icon: Wrench },
    ],
  },
]
```

### 3.2 Navigation Array (After)

```tsx
import {
  LayoutDashboard,
  Search,
  Settings,
  LogOut,
  ChevronLeft,
  ChevronDown,
  Menu,
  FileText,
  Upload,
  Command,
  FileWarning,
  Library,
  Bot,
  FlaskConical,    // new: Extraction
  FileCode,        // new: Parsers
  Cog,             // new: Processing
  SlidersHorizontal, // new: General settings
} from 'lucide-react'

const navigation: NavSection[] = [
  {
    title: 'Workspace',
    items: [
      { name: 'Dashboard', href: '/', icon: LayoutDashboard },
      { name: 'Documents', href: '/documents', icon: Library },
      { name: 'ACM Register', href: '/acm', icon: FileWarning },
      { name: 'Search', href: '/search', icon: Search },
    ],
  },
  {
    title: 'Configure',
    items: [
      { name: 'Extraction', href: '/settings/extraction', icon: FlaskConical },
      { name: 'AI Models', href: '/settings/models', icon: Bot },
      { name: 'Parsers', href: '/settings/parsers', icon: FileCode },
      { name: 'Processing', href: '/settings/processing', icon: Cog },
      { name: 'General', href: '/settings', icon: SlidersHorizontal },
    ],
  },
]
```

### 3.3 Create Button Redesign (Before)

```tsx
// Current: DropdownMenu with Source/Notebook/Podcast options (lines 221-291)
<DropdownMenu open={createMenuOpen} onOpenChange={setCreateMenuOpen}>
  {/* ... trigger ... */}
  <DropdownMenuContent>
    <DropdownMenuItem onSelect={() => handleCreateSelection('source')}>
      <FileText /> Source
    </DropdownMenuItem>
    <DropdownMenuItem onSelect={() => handleCreateSelection('notebook')}>
      <Book /> Notebook
    </DropdownMenuItem>
    <DropdownMenuItem onSelect={() => handleCreateSelection('podcast')}>
      <Mic /> Podcast
    </DropdownMenuItem>
  </DropdownMenuContent>
</DropdownMenu>
```

### 3.4 Create Button Redesign (After)

```tsx
// New: Single "Upload Document" button that opens AddSourceDialog directly
<div className={cn('mb-4', isCollapsed ? 'px-0' : 'px-0')}>
  {isCollapsed ? (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button
          onClick={() => openSourceDialog()}
          variant="default"
          size="sm"
          className="w-full justify-center px-2 bg-primary hover:bg-primary/90 text-primary-foreground border-0"
          aria-label="Upload Document"
        >
          <Upload className="h-4 w-4" />
        </Button>
      </TooltipTrigger>
      <TooltipContent side="right">Upload Document</TooltipContent>
    </Tooltip>
  ) : (
    <Button
      onClick={() => openSourceDialog()}
      variant="default"
      size="sm"
      className="w-full justify-start bg-primary hover:bg-primary/90 text-primary-foreground border-0"
    >
      <Upload className="h-4 w-4 mr-2" />
      Upload Document
    </Button>
  )}
</div>
```

### 3.5 Dashboard Link Removal

The standalone Dashboard link (lines 183-218) should be **removed** since Dashboard is now the first item in the WORKSPACE section. It will be rendered through the normal section iteration.

### 3.6 Footer Redesign (Before)

```tsx
// Current footer (lines 392-461)
{/* Command Palette hint */}
{/* ThemeToggle */}
{/* Sign Out button */}
```

### 3.7 Footer Redesign (After)

```tsx
{/* Footer */}
<div className={cn(
  'border-t border-sidebar-border p-3 space-y-2',
  isCollapsed && 'px-2'
)}>
  {/* VAEA vendor attribution */}
  {!isCollapsed && (
    <div className="px-3 py-2 text-center">
      <img
        src="/brand/vaea-logo.svg"
        alt="VAEA"
        className="h-6 mx-auto mb-1 opacity-60"
      />
      <p className="text-[10px] text-sidebar-foreground/40">
        Powered by CoralShades
      </p>
    </div>
  )}

  {/* Command Palette hint */}
  {!isCollapsed && (
    <div className="px-3 py-1.5 text-xs text-sidebar-foreground/60 rounded-md bg-sidebar-accent/30">
      <div className="flex items-center justify-between">
        <span className="flex items-center gap-1.5">
          <Command className="h-3 w-3" />
          Quick actions
        </span>
        <kbd className="pointer-events-none inline-flex h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground">
          {isMac ? <span className="text-xs">&#8984;</span> : <span>Ctrl+</span>}
          K
        </kbd>
      </div>
    </div>
  )}

  <div className={cn(
    'flex',
    isCollapsed ? 'justify-center' : 'justify-start gap-2'
  )}>
    {isCollapsed ? (
      <Tooltip>
        <TooltipTrigger asChild>
          <div><ThemeToggle iconOnly /></div>
        </TooltipTrigger>
        <TooltipContent side="right">Theme</TooltipContent>
      </Tooltip>
    ) : (
      <>
        <ThemeToggle />
        <Button
          variant="outline"
          size="sm"
          className="flex-1 justify-start gap-2"
          onClick={logout}
        >
          <LogOut className="h-4 w-4" />
          Sign Out
        </Button>
      </>
    )}
  </div>

  {isCollapsed && (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button
          variant="outline"
          className="w-full justify-center"
          onClick={logout}
          aria-label="Sign out"
        >
          <LogOut className="h-4 w-4" />
        </Button>
      </TooltipTrigger>
      <TooltipContent side="right">Sign Out</TooltipContent>
    </Tooltip>
  )}
</div>
```

### 3.8 Import Cleanup

Remove unused imports:
- `Book` (notebooks icon)
- `Mic` (podcasts icon)
- `Shuffle` (transformations icon)
- `Wrench` (advanced icon)
- `Plus` (create dropdown icon)
- `DropdownMenu`, `DropdownMenuContent`, `DropdownMenuItem`, `DropdownMenuTrigger`

Remove unused state/hooks:
- `createMenuOpen` state and `setCreateMenuOpen`
- `handleCreateSelection` function
- `CreateTarget` type
- `openNotebookDialog`, `openPodcastDialog` from `useCreateDialogs()` (only keep `openSourceDialog`)

---

## 4. Features to Hide from Navigation

### 4.1 Features Affected

These features are **hidden from navigation only**. Their routes remain accessible via direct URL, and their code is preserved.

| Feature | Nav Entry Removed | Route Still Works | Components Kept |
|---------|-------------------|-------------------|-----------------|
| Podcasts | Yes | `/podcasts` works if visited directly | `components/podcasts/*` |
| Transformations | Yes | `/transformations` works if visited directly | `components/(dashboard)/transformations/*` |
| Notebooks | Yes | `/notebooks`, `/notebooks/[id]` work if visited directly | `components/notebooks/*` |

### 4.2 Files Affected

**No file deletions.** The following files are left untouched but no longer linked from sidebar or command palette:

- `app/(dashboard)/podcasts/page.tsx`
- `app/(dashboard)/transformations/page.tsx`
- `app/(dashboard)/transformations/components/*`
- `app/(dashboard)/notebooks/page.tsx`
- `app/(dashboard)/notebooks/[id]/page.tsx`
- `app/(dashboard)/notebooks/components/*`
- `components/podcasts/*`
- `components/notebooks/*`

### 4.3 use-create-dialogs.tsx Changes

The `CreateDialogsProvider` currently renders three dialogs:
- `AddSourceDialog` -- **KEEP**
- `CreateNotebookDialog` -- **KEEP** (still usable via direct URL)
- `GeneratePodcastDialog` -- **KEEP** (still usable via direct URL)

No changes needed to this file since the dialogs should still work for direct-URL access. However, the `openNotebookDialog` and `openPodcastDialog` functions are no longer called from the sidebar or command palette.

---

## 5. Command Palette Cleanup

### 5.1 File: `components/common/CommandPalette.tsx`

### 5.2 navigationItems Array (Before)

```tsx
const navigationItems = [
  { name: 'Sources', href: '/sources', icon: FileText, keywords: ['files', 'documents', 'upload'] },
  { name: 'Notebooks', href: '/notebooks', icon: Book, keywords: ['notes', 'research', 'projects'] },
  { name: 'Ask and Search', href: '/search', icon: Search, keywords: ['find', 'query'] },
  { name: 'Podcasts', href: '/podcasts', icon: Mic, keywords: ['audio', 'episodes', 'generate'] },
  { name: 'Models', href: '/models', icon: Bot, keywords: ['ai', 'llm', 'providers', 'openai', 'anthropic'] },
  { name: 'Transformations', href: '/transformations', icon: Shuffle, keywords: ['prompts', 'templates', 'actions'] },
  { name: 'Settings', href: '/settings', icon: Settings, keywords: ['preferences', 'config', 'options'] },
  { name: 'Advanced', href: '/advanced', icon: Wrench, keywords: ['debug', 'system', 'tools'] },
]
```

### 5.3 navigationItems Array (After)

```tsx
const navigationItems = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard, keywords: ['home', 'overview', 'stats'] },
  { name: 'Documents', href: '/documents', icon: Library, keywords: ['files', 'sources', 'upload', 'samp'] },
  { name: 'ACM Register', href: '/acm', icon: FileWarning, keywords: ['asbestos', 'register', 'records'] },
  { name: 'Search', href: '/search', icon: Search, keywords: ['find', 'query', 'ask'] },
  { name: 'Extraction', href: '/settings/extraction', icon: FlaskConical, keywords: ['extract', 'pipeline'] },
  { name: 'AI Models', href: '/settings/models', icon: Bot, keywords: ['ai', 'llm', 'providers', 'openai', 'anthropic'] },
  { name: 'Settings', href: '/settings', icon: SlidersHorizontal, keywords: ['preferences', 'config', 'options', 'advanced'] },
]
```

### 5.4 createItems Array (Before)

```tsx
const createItems = [
  { name: 'Create Source', action: 'source', icon: FileText },
  { name: 'Create Notebook', action: 'notebook', icon: Book },
  { name: 'Create Podcast', action: 'podcast', icon: Mic },
]
```

### 5.5 createItems Array (After)

```tsx
const createItems = [
  { name: 'Upload Document', action: 'source', icon: Upload },
]
```

### 5.6 Notebooks Group Removal

Remove the entire `<CommandGroup heading="Notebooks">` block (lines 205-224) that lists notebooks for quick navigation. This removes the `useNotebooks` import and the `notebooks`/`notebooksLoading` state.

### 5.7 handleCreate Simplification

```tsx
// Before
const handleCreate = useCallback((action: string) => {
  handleSelect(() => {
    if (action === 'source') openSourceDialog()
    else if (action === 'notebook') openNotebookDialog()
    else if (action === 'podcast') openPodcastDialog()
  })
}, [handleSelect, openSourceDialog, openNotebookDialog, openPodcastDialog])

// After
const handleCreate = useCallback((action: string) => {
  handleSelect(() => {
    if (action === 'source') openSourceDialog()
  })
}, [handleSelect, openSourceDialog])
```

### 5.8 Import Cleanup

Remove: `Book`, `Mic`, `Shuffle`, `Wrench`, `Loader2`
Add: `LayoutDashboard`, `Library`, `FileWarning`, `Upload`, `FlaskConical`, `SlidersHorizontal`
Remove: `useNotebooks` hook import

---

## 6. Route Merging Specification

### 6.1 Sources + Documents -> `/documents`

**Current state:**
- `/sources` -- Source list with grid/table view, search, sort, bulk delete (fully featured)
- `/documents` -- Document library with Library tab and Processing tab (simpler view)

**Target state:**
- `/documents` -- Unified page combining the best of both:
  - Library tab (from documents page) with DocumentLibrary component
  - Processing tab (from documents page) with ProcessingStatus component
  - Retain sources page's grid/table toggle, search, sort, infinite scroll, bulk operations
  - Retain sources page's empty state with "Upload Document" CTA

**Implementation approach:**
1. Enhance `/documents/page.tsx` to incorporate source list features (search, sort, view toggle, bulk ops)
2. Keep `/sources/page.tsx` as-is for backward compatibility
3. Add redirect from `/sources` to `/documents` (see Section 9)
4. The `/sources/[id]` detail page remains at its current route (no redirect needed, it is a deep link)

### 6.2 Settings + Advanced + Models -> `/settings`

**Current state:**
- `/settings` -- SettingsForm with Content Processing, Embedding, File Management cards
- `/advanced` -- SystemInfo + RebuildEmbeddings
- `/models` -- ProviderStatus, DefaultModelsSection, ModelTypeSection

**Target state:**
- `/settings` -- Tabbed settings page with tabs:
  - **General** (default) -- Current SettingsForm content
  - **Advanced** -- Current SystemInfo + RebuildEmbeddings content
  - **AI Models** -- Current models page content (ProviderStatus, DefaultModelsSection, ModelTypeSection)

**Implementation approach:**
1. Refactor `/settings/page.tsx` to use `<Tabs>` component
2. Import `SettingsForm`, `SystemInfo`, `RebuildEmbeddings` from current locations
3. Create a new `SettingsModelsTab` component that wraps the models page content
4. Add redirects from `/advanced` and `/models` to `/settings` (see Section 9)

### 6.3 New Settings Sub-Routes

Create placeholder pages for future epic stories:

| Route | File | Epic Story | Placeholder Content |
|-------|------|------------|---------------------|
| `/settings/extraction` | `app/(dashboard)/settings/extraction/page.tsx` | E12-S1 | "Extraction settings coming soon" card |
| `/settings/models` | `app/(dashboard)/settings/models/page.tsx` | (existing) | Redirect to `/settings?tab=models` or render models content |
| `/settings/parsers` | `app/(dashboard)/settings/parsers/page.tsx` | E12-S4 | "Parser configuration coming soon" card |
| `/settings/processing` | `app/(dashboard)/settings/processing/page.tsx` | E12-S3 | "Processing settings coming soon" card |

**Placeholder page template:**

```tsx
'use client'

import { AppShell } from '@/components/layout/AppShell'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Construction } from 'lucide-react'

export default function ExtractionSettingsPage() {
  return (
    <AppShell>
      <div className="flex-1 overflow-y-auto">
        <div className="p-6">
          <div className="max-w-4xl">
            <h1 className="text-2xl font-bold mb-6">Extraction Settings</h1>
            <Card>
              <CardHeader>
                <div className="flex items-center gap-3">
                  <Construction className="h-6 w-6 text-muted-foreground" />
                  <div>
                    <CardTitle>Coming Soon</CardTitle>
                    <CardDescription>
                      Extraction pipeline configuration will be available in a future update.
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  This page will allow you to configure extraction rules, field mappings,
                  and validation settings for ACM register extraction.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </AppShell>
  )
}
```

---

## 7. VAEA Branding Changes

### 7.1 branding.ts (Before)

```tsx
export const BRANDING = {
  name: 'ACM-AI',
  fullName: 'ACM-AI - Asbestos Register Management',
  tagline: 'AI-powered compliance document analysis',
  description: 'Analyze and manage Asbestos Containing Material registers with AI assistance',
  keywords: ['ACM', 'asbestos', 'SAMP', 'compliance', 'AI', 'register', 'management'],
  api: {
    title: 'ACM-AI API',
    description: 'API for ACM-AI - Asbestos Containing Material Register Analysis',
    version: '1.0.0',
  },
} as const
```

### 7.2 branding.ts (After)

```tsx
export const BRANDING = {
  /** Short application name */
  name: 'VAEA ACM-AI',

  /** Full application name with description */
  fullName: 'VAEA ACM-AI - Asbestos Register Management',

  /** Brief tagline for the application */
  tagline: 'AI-powered compliance document analysis',

  /** Longer description for metadata and marketing */
  description: 'Analyze and manage Asbestos Containing Material registers with AI assistance',

  /** SEO keywords */
  keywords: ['VAEA', 'ACM', 'asbestos', 'SAMP', 'compliance', 'AI', 'register', 'management'],

  /** Vendor information */
  vendor: {
    name: 'CoralShades',
    logo: '/brand/cs-logo.svg',
    icon: '/brand/cs-favicon.svg',
  },

  /** Client/organization information */
  client: {
    name: 'VAEA',
    logo: '/brand/vaea-logo.svg',
    icon: '/brand/vaea-favicon.png',
  },

  /** API information */
  api: {
    title: 'VAEA ACM-AI API',
    description: 'API for VAEA ACM-AI - Asbestos Containing Material Register Analysis',
    version: '1.0.0',
  },
} as const

export type BrandingConfig = typeof BRANDING
```

### 7.3 Logo.tsx Changes

The Logo component must be updated to use the VAEA ripple logo instead of the custom shield SVG.

```tsx
'use client'

import { cn } from '@/lib/utils'
import { BRANDING } from '@/config/branding'
import Image from 'next/image'

interface LogoProps {
  variant?: 'full' | 'icon'
  className?: string
  iconClassName?: string
}

export function Logo({ variant = 'full', className, iconClassName }: LogoProps) {
  const icon = (
    <Image
      src={BRANDING.client.icon}
      alt={BRANDING.client.name}
      width={32}
      height={32}
      className={cn('w-8 h-8', iconClassName)}
    />
  )

  if (variant === 'icon') {
    return <div className={className}>{icon}</div>
  }

  return (
    <div className={cn('flex items-center gap-2', className)}>
      {icon}
      <span className="font-semibold text-lg text-foreground">{BRANDING.name}</span>
    </div>
  )
}

export default Logo
```

### 7.4 Brand Assets to Place

Copy these files to `frontend/public/brand/`:

| Source Asset | Target Path | Usage |
|-------------|-------------|-------|
| `VAEA_Ripple2_FavIcon_0.png` | `/brand/vaea-favicon.png` | App icon, Logo component |
| `VAEA-Ripple2-Logo_Print.png` | `/brand/vaea-logo.svg` | Sidebar footer |
| `favicon.ico` | `/favicon.ico` (replace existing) | Browser tab |
| `CS_Logo.svg` | `/brand/cs-logo.svg` | "Powered by" footer |
| `CS_Favicon.svg` | `/brand/cs-favicon.svg` | Vendor icon (if needed) |

### 7.5 Favicon and Metadata

Update `frontend/src/app/layout.tsx` metadata:
```tsx
export const metadata: Metadata = {
  title: 'VAEA ACM-AI',
  description: BRANDING.description,
  icons: {
    icon: '/brand/vaea-favicon.png',
  },
}
```

Update `frontend/public/manifest.json`:
```json
{
  "name": "VAEA ACM-AI",
  "short_name": "VAEA ACM-AI",
  "icons": [
    { "src": "/brand/vaea-favicon.png", "sizes": "192x192", "type": "image/png" }
  ]
}
```

---

## 8. Sidebar Store Changes

### 8.1 File: `lib/stores/sidebar-store.ts`

Update default expanded sections to match new section names:

```tsx
// Before
expandedSections: {
  Collect: true,
  Process: true,
  Create: true,
  Manage: false,
},

// After
expandedSections: {
  Workspace: true,
  Configure: false,
},
```

**Migration note:** Users with persisted sidebar state from `localStorage` key `sidebar-storage` will have stale section names. The new sections will default to the fallback `?? true` behavior in AppSidebar.tsx, so they will appear expanded. This is acceptable behavior -- old keys are harmless and will be overwritten on first toggle.

---

## 9. Migration Plan and Backwards Compatibility

### 9.1 Route Redirects

Add redirects in `middleware.ts` for removed/merged routes:

```tsx
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

const REDIRECTS: Record<string, string> = {
  '/sources': '/documents',
  '/advanced': '/settings',
  '/models': '/settings/models',
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  // Handle route redirects for merged pages
  if (pathname in REDIRECTS) {
    return NextResponse.redirect(new URL(REDIRECTS[pathname], request.url))
  }

  // Note: Remove the old / -> /notebooks redirect
  // Dashboard is now at / and is the natural landing page

  return NextResponse.next()
}

export const config = {
  matcher: [
    '/((?!api|_next/static|_next/image|favicon.ico|brand).*)',
  ],
}
```

### 9.2 Important: Preserve Deep Links

These routes must **NOT** be redirected because they are deep links used in the app:

- `/sources/[id]` -- Source detail page with ACM tab (keep as-is)
- `/notebooks/[id]` -- Notebook detail page (hidden but accessible)
- `/search?q=...&mode=...` -- Search with parameters (keep as-is)

### 9.3 Feature Gating (Not Needed)

Hidden features (Notebooks, Podcasts, Transformations) do NOT need feature flags. They are simply removed from navigation. Their routes continue to work for any user who has a direct link.

### 9.4 Phased Rollout

| Phase | Changes | Risk |
|-------|---------|------|
| Phase 1 | Navigation array update, Create button simplification, Command palette cleanup | Low - UI only |
| Phase 2 | Route merging (sources+documents, settings+advanced+models) | Medium - page content changes |
| Phase 3 | Branding update (Logo, branding.ts, favicon, footer) | Low - cosmetic only |
| Phase 4 | New placeholder pages (extraction, parsers, processing) | Low - new pages only |

All phases can be done in a single PR if desired, but splitting into phases allows for easier review.

---

## 10. Implementation Checklist

### Files to Modify

- [ ] `frontend/src/components/layout/AppSidebar.tsx` -- Navigation redesign
- [ ] `frontend/src/components/common/CommandPalette.tsx` -- Remove hidden features
- [ ] `frontend/src/lib/stores/sidebar-store.ts` -- Update section defaults
- [ ] `frontend/src/config/branding.ts` -- VAEA branding
- [ ] `frontend/src/components/brand/Logo.tsx` -- VAEA logo
- [ ] `frontend/src/middleware.ts` -- Route redirects
- [ ] `frontend/src/app/layout.tsx` -- Metadata/favicon
- [ ] `frontend/public/manifest.json` -- App name/icon

### Files to Create

- [ ] `frontend/public/brand/vaea-favicon.png`
- [ ] `frontend/public/brand/vaea-logo.svg`
- [ ] `frontend/public/brand/cs-logo.svg`
- [ ] `frontend/public/brand/cs-favicon.svg`
- [ ] `frontend/src/app/(dashboard)/settings/extraction/page.tsx` -- Placeholder
- [ ] `frontend/src/app/(dashboard)/settings/parsers/page.tsx` -- Placeholder
- [ ] `frontend/src/app/(dashboard)/settings/processing/page.tsx` -- Placeholder
- [ ] `frontend/src/app/(dashboard)/settings/models/page.tsx` -- Models content or redirect

### Files Unchanged (Hidden features kept intact)

- `frontend/src/app/(dashboard)/podcasts/page.tsx`
- `frontend/src/app/(dashboard)/transformations/*`
- `frontend/src/app/(dashboard)/notebooks/*`
- `frontend/src/components/podcasts/*`
- `frontend/src/components/notebooks/*`
- `frontend/src/lib/hooks/use-create-dialogs.tsx` (dialogs still work via direct URL)

### Verification Steps

1. `npm run build` must pass
2. All new routes return 200
3. Redirect routes (sources, advanced, models) return 307/308
4. Hidden feature routes (notebooks, podcasts, transformations) still return 200
5. Deep links (`/sources/[id]`, `/notebooks/[id]`) still work
6. Sidebar renders correctly in both collapsed and expanded states
7. Command palette shows only WORKSPACE + CONFIGURE items
8. "Upload Document" button opens AddSourceDialog
9. VAEA logo and branding display correctly
10. Dark mode renders correctly with new footer

---

## Appendix A: Component Dependency Map

```
AppShell
  └── AppSidebar (modified)
        ├── Logo (modified - VAEA branding)
        ├── useSidebarStore (modified - new sections)
        ├── useCreateDialogs (simplified - source only)
        ├── ThemeToggle (unchanged)
        └── useAuth (unchanged)

DashboardLayout
  ├── CreateDialogsProvider (unchanged)
  ├── CommandPalette (modified)
  └── ModalProvider (unchanged)
```

## Appendix B: Removed vs Preserved Functionality

| Functionality | Status | Notes |
|--------------|--------|-------|
| Upload documents | PRESERVED | Primary CTA, unchanged behavior |
| View sources list | REDIRECTED | `/sources` -> `/documents` |
| View source detail | PRESERVED | `/sources/[id]` unchanged |
| ACM register view | PRESERVED | `/acm` unchanged |
| Search/Ask | PRESERVED | `/search` unchanged |
| Create notebook | HIDDEN | Route works, removed from nav + palette |
| View notebooks | HIDDEN | Route works, removed from nav + palette |
| Generate podcast | HIDDEN | Route works, removed from nav + palette |
| Transformations | HIDDEN | Route works, removed from nav + palette |
| Models config | MOVED | `/models` -> `/settings/models` |
| Settings | PRESERVED | `/settings` stays, gains tabs |
| Advanced tools | MERGED | `/advanced` -> `/settings` (Advanced tab) |
