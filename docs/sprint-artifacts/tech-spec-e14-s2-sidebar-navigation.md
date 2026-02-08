# Tech Spec: E14-S2 - Redesign Sidebar Navigation

> **Story:** E14-S2
> **Epic:** E14 - UX & Enterprise Readiness
> **Status:** Ready for Dev
> **Created:** 2026-02-08

---

## Overview

Redesign the AppSidebar component to simplify navigation from 4 sections (Collect/Process/Create/Manage) to 2 sections (WORKSPACE/CONFIGURE), replace the Create dropdown with a single "Upload Document" button, and integrate VAEA branding assets. This aligns the UI with ACM compliance workflows and removes unused features from navigation while preserving their routes.

---

## User Story

**As a** compliance officer
**I want** a simplified navigation with WORKSPACE and CONFIGURE sections
**So that** I can easily find ACM-related features

---

## Acceptance Criteria

- [ ] Sidebar sections changed to WORKSPACE (Dashboard, Documents, ACM Register, Search) and CONFIGURE (Extraction, AI Models, Parsers, Processing, General)
- [ ] "Upload Document" primary CTA button at top of sidebar (replaces Create dropdown)
- [ ] Dashboard moved into WORKSPACE section (removed as standalone item)
- [ ] VAEA logo (Ripple2) replaces custom shield SVG in Logo component
- [ ] CoralShades footer with VAEA logo, "Powered by CoralShades" text
- [ ] Theme toggle and sign out in sidebar footer (unchanged behavior)
- [ ] CONFIGURE section collapsed by default
- [ ] Sidebar store updated with new section names
- [ ] Root redirect changed from `/notebooks` to `/` (Dashboard)

---

## Technical Design

### 1. Navigation Data Structure Update

**File:** `frontend/src/components/layout/AppSidebar.tsx`

Replace the current 4-section navigation array (lines 64-93) with a streamlined 2-section structure:

```tsx
// NEW: Import additional icons for CONFIGURE section
import {
  LayoutDashboard,
  Search,
  Settings,
  LogOut,
  ChevronLeft,
  ChevronDown,
  Menu,
  FileText,
  Upload,        // NEW: for Upload Document button
  Command,
  FileWarning,
  Library,
  Bot,
  FlaskConical,    // NEW: Extraction icon
  FileCode,        // NEW: Parsers icon
  Cog,             // NEW: Processing icon
  SlidersHorizontal, // NEW: General settings icon
} from 'lucide-react'

// REMOVE unused icons:
// - Book (notebooks)
// - Mic (podcasts)
// - Shuffle (transformations)
// - Wrench (advanced)
// - Plus (replaced by Upload)

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

**Key changes:**
- 4 sections → 2 sections
- 11 navigation items → 9 navigation items
- Dashboard moved from standalone into Workspace section
- Sources merged into Documents
- Notebooks, Podcasts, Transformations removed from navigation
- Models moved to `/settings/models`
- Advanced merged into `/settings` (General)

---

### 2. Replace Create Dropdown with Upload Document Button

**File:** `frontend/src/components/layout/AppSidebar.tsx`

Replace the DropdownMenu Create button (lines 220-291) with a direct Upload Document button:

```tsx
{/* BEFORE: Dashboard standalone item (lines 183-218) - REMOVE THIS */}

{/* NEW: Upload Document CTA (replaces Create dropdown) */}
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

**Remove from imports and usage:**
- `DropdownMenu`, `DropdownMenuContent`, `DropdownMenuItem`, `DropdownMenuTrigger` components
- `createMenuOpen` state and `setCreateMenuOpen`
- `handleCreateSelection` function
- `CreateTarget` type
- `openNotebookDialog`, `openPodcastDialog` from `useCreateDialogs()` (only keep `openSourceDialog`)

---

### 3. Sidebar Store Section Updates

**File:** `frontend/src/lib/stores/sidebar-store.ts`

Update default expanded sections (lines 17-22):

```tsx
// BEFORE
expandedSections: {
  Collect: true,
  Process: true,
  Create: true,
  Manage: false,
},

// AFTER
expandedSections: {
  Workspace: true,
  Configure: false, // Collapsed by default for compliance officers
},
```

**Migration note:** Users with persisted localStorage state from old section names will see new sections default to expanded via the `?? true` fallback in AppSidebar. Old keys are harmless and will be overwritten on first user interaction.

---

### 4. VAEA Branding Integration

#### 4.1 Update branding.ts

**File:** `frontend/src/config/branding.ts`

Replace existing BRANDING object with VAEA-specific branding:

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

#### 4.2 Update Logo Component

**File:** `frontend/src/components/brand/Logo.tsx`

Replace custom shield SVG with VAEA Ripple2 logo:

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

/**
 * VAEA ACM-AI Logo Component
 *
 * Uses VAEA Ripple2 branding assets
 */
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

#### 4.3 Add VAEA Footer to Sidebar

**File:** `frontend/src/components/layout/AppSidebar.tsx`

Update footer section (lines 392-461) to include VAEA vendor attribution:

```tsx
{/* Footer */}
<div className={cn(
  'border-t border-sidebar-border p-3 space-y-2',
  isCollapsed && 'px-2'
)}>
  {/* VAEA vendor attribution - NEW */}
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

  {/* Command Palette hint - UNCHANGED */}
  {!isCollapsed && (
    <div className="px-3 py-1.5 text-xs text-sidebar-foreground/60 rounded-md bg-sidebar-accent/30">
      <div className="flex items-center justify-between">
        <span className="flex items-center gap-1.5">
          <Command className="h-3 w-3" />
          Quick actions
        </span>
        <kbd className="pointer-events-none inline-flex h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground">
          {isMac ? <span className="text-xs">⌘</span> : <span>Ctrl+</span>}
          K
        </kbd>
      </div>
    </div>
  )}

  {/* Theme toggle and Sign out - UNCHANGED logic, updated layout */}
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

#### 4.4 Copy Brand Assets

**Action:** Copy VAEA brand assets to frontend public directory

Source files (from `docs/vaea-assets/`):
- `VAEA_Ripple2_FavIcon_0.png` → `frontend/public/brand/vaea-favicon.png`
- `VAEA-Ripple2-Logo_Print.png` → `frontend/public/brand/vaea-logo.svg` (convert to SVG if possible, or use PNG)

Note: CoralShades assets (`cs-logo.svg`, `cs-favicon.svg`) need to be provided or created.

---

### 5. Middleware Redirect Update

**File:** `frontend/src/middleware.ts`

Update root redirect and add redirects for merged routes:

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

  // REMOVED: Root redirect to /notebooks
  // Dashboard is now at / and is the natural landing page

  return NextResponse.next()
}

export const config = {
  matcher: [
    '/((?!api|_next/static|_next/image|favicon.ico|brand).*)',
  ],
}
```

**Key changes:**
- Remove `if (pathname === '/') { redirect to /notebooks }` logic
- Add redirects for merged routes: `/sources`, `/advanced`, `/models`
- Update matcher to exclude `/brand` directory (for logo assets)

---

### 6. Remove Standalone Dashboard Item

**File:** `frontend/src/components/layout/AppSidebar.tsx`

**Remove lines 183-218** (Dashboard standalone item above Create button)

Dashboard is now rendered as the first item in the WORKSPACE section through the normal section iteration, so the standalone rendering is redundant.

---

## File Changes

| File | Change | Description |
|------|--------|-------------|
| `frontend/src/components/layout/AppSidebar.tsx` | Modify | Update navigation array, replace Create dropdown, update footer, remove Dashboard standalone |
| `frontend/src/lib/stores/sidebar-store.ts` | Modify | Update `expandedSections` default to `{Workspace: true, Configure: false}` |
| `frontend/src/config/branding.ts` | Modify | Add VAEA branding with vendor/client structure |
| `frontend/src/components/brand/Logo.tsx` | Modify | Replace shield SVG with Image component using VAEA Ripple2 icon |
| `frontend/src/middleware.ts` | Modify | Remove root redirect to `/notebooks`, add redirects for `/sources`, `/advanced`, `/models` |
| `frontend/public/brand/vaea-favicon.png` | Create | Copy from `docs/vaea-assets/VAEA_Ripple2_FavIcon_0.png` |
| `frontend/public/brand/vaea-logo.svg` | Create | Convert/copy from `docs/vaea-assets/VAEA-Ripple2-Logo_Print.png` |
| `frontend/public/brand/cs-logo.svg` | Create | CoralShades logo for footer attribution |
| `frontend/public/brand/cs-favicon.svg` | Create | CoralShades icon (if needed) |

---

## Dependencies

### Required Before This Story
- **E14-S1**: VAEA design tokens and theme variables must be implemented first
- VAEA brand assets must be provided (Ripple2 logo files)
- CoralShades logo assets must be provided

### Unblocks After This Story
- **E14-S3**: Dashboard redesign (requires new navigation structure)
- **E12-S1, E12-S3, E12-S4**: Settings placeholder pages (routes defined in CONFIGURE section)

### External Dependencies
- None (uses existing components and libraries)

---

## Testing Strategy

### Unit Tests
No new unit tests required. Existing component tests should be updated if they reference old navigation structure.

### Manual Testing Checklist

**Sidebar Behavior:**
- [ ] Sidebar renders with WORKSPACE and CONFIGURE sections
- [ ] WORKSPACE section expanded by default
- [ ] CONFIGURE section collapsed by default
- [ ] All 9 navigation items render with correct icons
- [ ] Active page highlights correctly
- [ ] Sidebar collapse/expand toggles correctly
- [ ] Collapsed mode shows icons with tooltips
- [ ] Upload Document button opens AddSourceDialog

**Navigation:**
- [ ] Dashboard link (`/`) works and highlights when active
- [ ] Documents link (`/documents`) works
- [ ] ACM Register link (`/acm`) works
- [ ] Search link (`/search`) works
- [ ] Settings sub-routes render (Extraction, Models, Parsers, Processing, General)

**Redirects:**
- [ ] `/sources` redirects to `/documents`
- [ ] `/advanced` redirects to `/settings`
- [ ] `/models` redirects to `/settings/models`
- [ ] Root `/` renders Dashboard (no redirect to `/notebooks`)

**Branding:**
- [ ] VAEA Ripple2 logo displays in sidebar header
- [ ] Logo collapses to icon-only mode correctly
- [ ] Footer shows VAEA logo and "Powered by CoralShades" text
- [ ] Theme toggle and sign out buttons work

**Hidden Features:**
- [ ] `/notebooks` route still accessible via direct URL
- [ ] `/podcasts` route still accessible via direct URL
- [ ] `/transformations` route still accessible via direct URL
- [ ] These routes do not appear in sidebar navigation

**Responsive:**
- [ ] Sidebar behavior correct on desktop (1280px+)
- [ ] Sidebar behavior correct on tablet (768px-1279px)
- [ ] Upload button works in both collapsed and expanded states

### Build Verification
```bash
cd frontend
npm run build  # Must pass without errors
```

### Story Verification Protocol
Per CLAUDE.md Story Verification Protocol:
1. Run `npm run build` - must pass
2. Verify all 9 files in File Changes table exist after changes
3. Take browser snapshot of sidebar in expanded and collapsed states
4. Save screenshots to `docs/sprint-artifacts/e14-s2-evidence/`

---

## Estimated Complexity

**Story Points:** 5

**Time Estimate:** 4-6 hours

**Complexity Breakdown:**
- Navigation array update: 1 hour (straightforward data structure change)
- Upload Document button replacement: 1 hour (remove dropdown logic, add button)
- Branding updates (Logo, branding.ts, footer): 2 hours (asset integration, Image component setup)
- Sidebar store update: 30 minutes (change default section names)
- Middleware redirects: 30 minutes (add redirect map)
- Testing and verification: 1-2 hours (manual testing, screenshot evidence)

**Risk Factors:**
- **Low risk:** Pure UI change, no business logic affected
- **Low risk:** Hidden features remain functional via direct URLs
- **Medium risk:** Brand asset conversion (PNG to SVG for logo) may require design tool
- **Low risk:** Existing users with old localStorage keys will see sections expanded (acceptable behavior)

---

## Implementation Notes

### Code Removal Checklist
Remove from `AppSidebar.tsx`:
- [ ] Dashboard standalone rendering block (lines 183-218)
- [ ] Create dropdown DropdownMenu component (lines 220-291)
- [ ] `createMenuOpen` state
- [ ] `handleCreateSelection` function
- [ ] `CreateTarget` type
- [ ] Unused icon imports: `Book`, `Mic`, `Shuffle`, `Wrench`, `Plus`
- [ ] Unused hook calls: `openNotebookDialog`, `openPodcastDialog`

### Import Additions
Add to `AppSidebar.tsx`:
- [ ] `Upload` icon from lucide-react
- [ ] `FlaskConical` icon (Extraction)
- [ ] `FileCode` icon (Parsers)
- [ ] `Cog` icon (Processing)
- [ ] `SlidersHorizontal` icon (General)

### Brand Asset Preparation
1. Convert `VAEA-Ripple2-Logo_Print.png` to SVG if possible (for scalability)
2. Optimize PNG favicon to appropriate size (192x192 or 512x512 for manifest)
3. Create or obtain CoralShades logo SVG files
4. Place all assets in `frontend/public/brand/` directory

### localStorage Migration
Users with existing `sidebar-storage` localStorage keys will have stale section names:
```json
{
  "expandedSections": {
    "Collect": true,
    "Process": true,
    "Create": true,
    "Manage": false
  }
}
```

New code will ignore these keys and use `?? true` fallback. New sections will be:
```json
{
  "expandedSections": {
    "Workspace": true,
    "Configure": false
  }
}
```

On first user interaction (toggle section), new keys will be persisted and old keys effectively replaced.

### Router Structure After Changes
```
/ ──────────────────→ Dashboard (no redirect)
/documents ─────────→ Documents page (merged sources+documents)
/sources ───────────→ 307 redirect to /documents
/acm ───────────────→ ACM Register
/search ────────────→ Search
/settings ──────────→ Settings page (General tab)
/settings/extraction → Extraction settings placeholder (E12-S1)
/settings/models ───→ AI Models configuration
/settings/parsers ──→ Parsers placeholder (E12-S4)
/settings/processing → Processing placeholder (E12-S3)
/advanced ──────────→ 307 redirect to /settings
/models ────────────→ 307 redirect to /settings/models
/notebooks ─────────→ Hidden, but route still works
/podcasts ──────────→ Hidden, but route still works
/transformations ───→ Hidden, but route still works
```

---

## References

- **Spec:** `docs/navigation-cleanup-spec.md` Section 3 (Navigation redesign)
- **Spec:** `docs/ui-ux-spec.md` Section 4.1 (Sidebar specification)
- **Epic:** Epic 14 - UX & Enterprise Readiness
- **Depends On:** E14-S1 (VAEA design tokens)
- **Related:** E12-S1, E12-S3, E12-S4 (CONFIGURE section placeholders)

---

*End of Tech Spec*
