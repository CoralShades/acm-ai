# Tech Spec: E14-S3 - Hide Brownfield Features from Navigation

> **Story:** E14-S3
> **Epic:** E14 - UX & Enterprise Readiness
> **Status:** Ready for Dev
> **Created:** 2026-02-08

---

## Overview

Remove Notebooks, Podcasts, and Transformations from sidebar navigation and command palette to streamline the ACM compliance workflow. Pages and components are preserved for backward compatibility and direct URL access.

---

## User Story

**As a** product owner
**I want** Podcasts, Transformations, and Notebooks hidden from navigation
**So that** the UI focuses on ACM compliance workflow

---

## Acceptance Criteria

- [ ] Podcasts removed from sidebar nav items
- [ ] Transformations removed from sidebar nav items
- [ ] Notebooks removed from sidebar nav items (pages still accessible via direct URL)
- [ ] Command palette entries for hidden features removed
- [ ] Create dialog no longer shows Notebook or Podcast options
- [ ] Code is preserved (not deleted) -- only nav entries removed

---

## Technical Design

### 1. AppSidebar.tsx - Remove Hidden Features from Navigation

**File:** `frontend/src/components/layout/AppSidebar.tsx`

#### 1.1 Update Navigation Array (lines 64-93)

Remove the following navigation items:
- **Notebooks** (line 76) from the "Process" section
- **Podcasts** (line 82) from the "Create" section
- **Transformations** (line 88) from the "Manage" section

**Before:**
```tsx
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
      { name: 'Notebooks', href: '/notebooks', icon: Book },  // REMOVE
      { name: 'Ask and Search', href: '/search', icon: Search },
    ],
  },
  {
    title: 'Create',
    items: [{ name: 'Podcasts', href: '/podcasts', icon: Mic }],  // REMOVE
  },
  {
    title: 'Manage',
    items: [
      { name: 'Models', href: '/models', icon: Bot },
      { name: 'Transformations', href: '/transformations', icon: Shuffle },  // REMOVE
      { name: 'Settings', href: '/settings', icon: Settings },
      { name: 'Advanced', href: '/advanced', icon: Wrench },
    ],
  },
]
```

**After:**
```tsx
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
      { name: 'Ask and Search', href: '/search', icon: Search },
    ],
  },
  // 'Create' section removed entirely (empty after Podcasts removal)
  {
    title: 'Manage',
    items: [
      { name: 'Models', href: '/models', icon: Bot },
      { name: 'Settings', href: '/settings', icon: Settings },
      { name: 'Advanced', href: '/advanced', icon: Wrench },
    ],
  },
]
```

#### 1.2 Simplify Create Button to Source-Only (lines 220-291)

Replace the dropdown Create button with a single "Upload Document" button that directly opens the source dialog.

**Before:**
```tsx
<DropdownMenu open={createMenuOpen} onOpenChange={setCreateMenuOpen}>
  <DropdownMenuTrigger asChild>
    <Button
      onClick={() => setCreateMenuOpen(true)}
      variant="default"
      size="sm"
      className="w-full justify-start bg-primary hover:bg-primary/90 text-primary-foreground border-0"
    >
      <Plus className="h-4 w-4 mr-2" />
      Create
    </Button>
  </DropdownMenuTrigger>

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

**After:**
```tsx
{/* Upload Document button - directly opens AddSourceDialog */}
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
        <FileText className="h-4 w-4" />
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
    <FileText className="h-4 w-4 mr-2" />
    Upload Document
  </Button>
)}
```

#### 1.3 Remove Unused Imports and State

**Remove these imports (lines 20-46):**
- `Book` (notebooks icon)
- `Mic` (podcasts icon)
- `Shuffle` (transformations icon)
- `Plus` (create dropdown icon)
- `DropdownMenu`, `DropdownMenuContent`, `DropdownMenuItem`, `DropdownMenuTrigger`

**Remove these state/hooks (lines 95-123):**
```tsx
// REMOVE:
const [createMenuOpen, setCreateMenuOpen] = useState(false)

// REMOVE from destructuring:
const { openSourceDialog, openNotebookDialog, openPodcastDialog } = useCreateDialogs()
// BECOMES:
const { openSourceDialog } = useCreateDialogs()

// REMOVE:
type CreateTarget = 'source' | 'notebook' | 'podcast'

// REMOVE:
const handleCreateSelection = (target: CreateTarget) => {
  setCreateMenuOpen(false)
  if (target === 'source') {
    openSourceDialog()
  } else if (target === 'notebook') {
    openNotebookDialog()
  } else if (target === 'podcast') {
    openPodcastDialog()
  }
}
```

---

### 2. CommandPalette.tsx - Remove Hidden Features

**File:** `frontend/src/components/common/CommandPalette.tsx`

#### 2.1 Update navigationItems Array (lines 33-42)

Remove Notebooks, Podcasts, Transformations from navigation commands.

**Before:**
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

**After:**
```tsx
const navigationItems = [
  { name: 'Sources', href: '/sources', icon: FileText, keywords: ['files', 'documents', 'upload'] },
  { name: 'Ask and Search', href: '/search', icon: Search, keywords: ['find', 'query'] },
  { name: 'Models', href: '/models', icon: Bot, keywords: ['ai', 'llm', 'providers', 'openai', 'anthropic'] },
  { name: 'Settings', href: '/settings', icon: Settings, keywords: ['preferences', 'config', 'options'] },
  { name: 'Advanced', href: '/advanced', icon: Wrench, keywords: ['debug', 'system', 'tools'] },
]
```

#### 2.2 Update createItems Array (lines 44-48)

Remove Notebook and Podcast creation options.

**Before:**
```tsx
const createItems = [
  { name: 'Create Source', action: 'source', icon: FileText },
  { name: 'Create Notebook', action: 'notebook', icon: Book },
  { name: 'Create Podcast', action: 'podcast', icon: Mic },
]
```

**After:**
```tsx
const createItems = [
  { name: 'Upload Document', action: 'source', icon: FileText },
]
```

#### 2.3 Remove Notebooks CommandGroup (lines 205-224)

Delete the entire `<CommandGroup heading="Notebooks">` block that displays notebook quick-links.

**Remove:**
```tsx
{/* Notebooks */}
<CommandGroup heading="Notebooks">
  {notebooksLoading ? (
    <CommandItem disabled>
      <Loader2 className="h-4 w-4 animate-spin" />
      <span>Loading notebooks...</span>
    </CommandItem>
  ) : notebooks && notebooks.length > 0 ? (
    notebooks.map((notebook) => (
      <CommandItem
        key={notebook.id}
        value={`notebook ${notebook.name} ${notebook.description || ''}`}
        onSelect={() => handleNavigate(`/notebooks/${notebook.id}`)}
      >
        <Book className="h-4 w-4" />
        <span>{notebook.name}</span>
      </CommandItem>
    ))
  ) : null}
</CommandGroup>
```

#### 2.4 Simplify handleCreate (lines 117-123)

Remove notebook and podcast handling.

**Before:**
```tsx
const handleCreate = useCallback((action: string) => {
  handleSelect(() => {
    if (action === 'source') openSourceDialog()
    else if (action === 'notebook') openNotebookDialog()
    else if (action === 'podcast') openPodcastDialog()
  })
}, [handleSelect, openSourceDialog, openNotebookDialog, openPodcastDialog])
```

**After:**
```tsx
const handleCreate = useCallback((action: string) => {
  handleSelect(() => {
    if (action === 'source') openSourceDialog()
  })
}, [handleSelect, openSourceDialog])
```

#### 2.5 Remove Unused Imports and Hooks

**Remove these imports (lines 8-31):**
- `Book`
- `Mic`
- `Shuffle`
- `Loader2`

**Remove hook usage (line 62):**
```tsx
// REMOVE:
const { data: notebooks, isLoading: notebooksLoading } = useNotebooks(false)

// REMOVE import:
import { useNotebooks } from '@/lib/hooks/use-notebooks'
```

**Update useCreateDialogs destructuring (line 60):**
```tsx
// BEFORE:
const { openSourceDialog, openNotebookDialog, openPodcastDialog } = useCreateDialogs()

// AFTER:
const { openSourceDialog } = useCreateDialogs()
```

#### 2.6 Update hasCommandMatch Logic (lines 131-150)

Remove notebooks from the command match check.

**Before:**
```tsx
const hasCommandMatch = useMemo(() => {
  if (!queryLower) return false
  return (
    navigationItems.some(item =>
      item.name.toLowerCase().includes(queryLower) ||
      item.keywords.some(k => k.includes(queryLower))
    ) ||
    createItems.some(item =>
      item.name.toLowerCase().includes(queryLower)
    ) ||
    themeItems.some(item =>
      item.name.toLowerCase().includes(queryLower) ||
      item.keywords.some(k => k.includes(queryLower))
    ) ||
    (notebooks?.some(nb =>
      nb.name.toLowerCase().includes(queryLower) ||
      (nb.description && nb.description.toLowerCase().includes(queryLower))
    ) ?? false)
  )
}, [queryLower, notebooks])
```

**After:**
```tsx
const hasCommandMatch = useMemo(() => {
  if (!queryLower) return false
  return (
    navigationItems.some(item =>
      item.name.toLowerCase().includes(queryLower) ||
      item.keywords.some(k => k.includes(queryLower))
    ) ||
    createItems.some(item =>
      item.name.toLowerCase().includes(queryLower)
    ) ||
    themeItems.some(item =>
      item.name.toLowerCase().includes(queryLower) ||
      item.keywords.some(k => k.includes(queryLower))
    )
  )
}, [queryLower])
```

---

### 3. AddButton.tsx - Remove Notebook Option (Optional)

**File:** `frontend/src/components/common/AddButton.tsx`

**Note:** This component is used on the sources list page. While not explicitly in the sidebar, it offers a dropdown with Notebook creation. For consistency, remove the Notebook option.

#### 3.1 Simplify to Source-Only Button

**Before (lines 40-60 and 72-94):**
```tsx
<DropdownMenu>
  <DropdownMenuTrigger asChild>
    <Button variant={variant} size={size} className={className}>
      <Plus className="h-4 w-4" />
    </Button>
  </DropdownMenuTrigger>
  <DropdownMenuContent align="start" side="right">
    <DropdownMenuItem onClick={handleAddSource} className="gap-2">
      <FileText className="h-4 w-4" />
      Source
    </DropdownMenuItem>
    <DropdownMenuItem onClick={handleAddNotebook} className="gap-2">
      <Book className="h-4 w-4" />
      Notebook <span className="text-xs text-muted-foreground ml-auto">Coming soon</span>
    </DropdownMenuItem>
  </DropdownMenuContent>
</DropdownMenu>
```

**After:**
```tsx
{/* Direct button - no dropdown needed for single action */}
<Button
  variant={variant}
  size={size}
  className={className}
  onClick={handleAddSource}
>
  <Plus className="h-4 w-4" />
  {!iconOnly && <span className="ml-2">Add Source</span>}
</Button>
```

**Remove:**
- `DropdownMenu`, `DropdownMenuContent`, `DropdownMenuItem`, `DropdownMenuTrigger` imports
- `Book` icon import
- `ChevronDown` icon import
- `handleAddNotebook` function (lines 33-35)

---

### 4. Preserve Hidden Features

**IMPORTANT:** The following files are **NOT** deleted or modified:

#### 4.1 Routes (Pages Still Accessible via Direct URL)

- `frontend/src/app/(dashboard)/notebooks/page.tsx`
- `frontend/src/app/(dashboard)/notebooks/[id]/page.tsx`
- `frontend/src/app/(dashboard)/podcasts/page.tsx`
- `frontend/src/app/(dashboard)/transformations/page.tsx`

#### 4.2 Components (Still Functional)

- `frontend/src/components/notebooks/*` (all components)
- `frontend/src/components/podcasts/*` (all components)
- `frontend/src/app/(dashboard)/transformations/components/*` (all components)

#### 4.3 Dialogs (Still Rendered for Direct URL Access)

**File:** `frontend/src/lib/hooks/use-create-dialogs.tsx` (UNCHANGED)

The `CreateDialogsProvider` continues to render all three dialogs:
```tsx
<CreateDialogsContext.Provider value={{ openSourceDialog, openNotebookDialog, openPodcastDialog }}>
  {children}
  <AddSourceDialog open={sourceDialogOpen} onOpenChange={setSourceDialogOpen} />
  <CreateNotebookDialog open={notebookDialogOpen} onOpenChange={setNotebookDialogOpen} />
  <GeneratePodcastDialog open={podcastDialogOpen} onOpenChange={setPodcastDialogOpen} />
</CreateDialogsContext.Provider>
```

This ensures that if a user navigates directly to `/notebooks` or `/podcasts`, the create dialogs still work.

---

## File Changes

| File | Change Type | Description |
|------|-------------|-------------|
| `frontend/src/components/layout/AppSidebar.tsx` | Modify | Remove Notebooks, Podcasts, Transformations from navigation array; simplify Create button to source-only; remove unused imports/state |
| `frontend/src/components/common/CommandPalette.tsx` | Modify | Remove Notebooks, Podcasts, Transformations from navigation commands and create items; remove Notebooks group; simplify handleCreate |
| `frontend/src/components/common/AddButton.tsx` | Modify (Optional) | Convert dropdown to direct button for source creation only |

**Files Preserved (Not Modified):**
- All route files in `app/(dashboard)/notebooks/*`, `app/(dashboard)/podcasts/*`, `app/(dashboard)/transformations/*`
- All components in `components/notebooks/*`, `components/podcasts/*`
- `lib/hooks/use-create-dialogs.tsx` (dialogs remain functional for direct access)

---

## Dependencies

**Prerequisites:**
- None - this is a pure UI cleanup story

**Blocks:**
- None - other Epic 14 stories are independent

**Related Stories:**
- E14-S1 (Sidebar Redesign) - this story complements the navigation restructure
- E14-S2 (Branding Update) - can be done in parallel

---

## Testing

### Unit/Component Testing

No new tests required. Existing tests should pass after removal.

**Regression checks:**
1. Sidebar renders without errors
2. Command palette opens and filters commands correctly
3. Upload Document button opens AddSourceDialog
4. No console errors about missing icons or imports

### Manual Testing

**Test 1: Sidebar Navigation**
- [ ] Dashboard, Sources, Documents, ACM Register visible under "Collect"
- [ ] Ask and Search visible under "Process"
- [ ] Models, Settings, Advanced visible under "Manage"
- [ ] NO Notebooks, Podcasts, or Transformations visible
- [ ] "Upload Document" button works (opens AddSourceDialog)

**Test 2: Command Palette (⌘K)**
- [ ] Typing "notebook" shows NO results
- [ ] Typing "podcast" shows NO results
- [ ] Typing "transformation" shows NO results
- [ ] Create section shows only "Upload Document"
- [ ] Navigation section shows only visible pages

**Test 3: Direct URL Access (Backward Compatibility)**
- [ ] `/notebooks` still loads (page accessible)
- [ ] `/notebooks/[existing-id]` still loads
- [ ] `/podcasts` still loads
- [ ] `/transformations` still loads
- [ ] These pages can still trigger create dialogs internally

**Test 4: AddButton Component (if modified)**
- [ ] AddButton on sources page opens AddSourceDialog directly
- [ ] No dropdown menu appears

### Build Verification

```bash
cd frontend
npm run build
```

**Expected:**
- ✅ Build passes with no errors
- ✅ No TypeScript errors about missing imports
- ✅ No unused variable warnings

---

## Estimated Complexity

**Story Points:** 2

**Effort Breakdown:**
- AppSidebar changes: 30 minutes (navigation array, create button, imports)
- CommandPalette changes: 30 minutes (arrays, groups, logic)
- AddButton changes: 15 minutes (optional cleanup)
- Testing: 30 minutes (manual verification of all nav areas)

**Risk Level:** Low
- Pure UI changes, no data model or API changes
- All code preserved, only navigation references removed
- Easy to revert by restoring navigation arrays

---

## Implementation Notes

### Code Preservation Strategy

This story follows a **"hide, don't delete"** approach:
- Navigation entries are removed from arrays
- Routes remain functional for direct access
- Components remain in codebase
- Dialogs remain available for programmatic use

This allows:
1. **Future re-enablement** by simply adding items back to navigation arrays
2. **Deep linking** from external sources (bookmarks, documentation, etc.)
3. **Gradual migration** for users with existing workflows

### Feature Flag Alternative (Not Required)

While not needed for this story, a future enhancement could add a feature flag:
```tsx
const ENABLE_BROWNFIELD_FEATURES = process.env.NEXT_PUBLIC_ENABLE_BROWNFIELD === 'true'

const navigation: NavSection[] = [
  // ...
  {
    title: 'Process',
    items: [
      ...(ENABLE_BROWNFIELD_FEATURES ? [{ name: 'Notebooks', href: '/notebooks', icon: Book }] : []),
      { name: 'Ask and Search', href: '/search', icon: Search },
    ],
  },
]
```

This is **not required** for E14-S3 but documents the pattern for future use.

---

## Verification Checklist

Before marking this story complete:

- [ ] `npm run build` passes
- [ ] All hidden features removed from sidebar navigation
- [ ] All hidden features removed from command palette
- [ ] Create button simplified to source-only
- [ ] Direct URLs (`/notebooks`, `/podcasts`, `/transformations`) still work
- [ ] No TypeScript errors
- [ ] No console warnings about unused variables
- [ ] Screenshot of new sidebar saved to `docs/sprint-artifacts/e14-s3-sidebar-after.png`
- [ ] Screenshot of new command palette saved to `docs/sprint-artifacts/e14-s3-command-palette-after.png`

---

## References

- **Navigation Cleanup Spec:** `/mnt/d/ailocal/acm-ai-frontend/docs/navigation-cleanup-spec.md` Section 4
- **Current Sidebar:** `/mnt/d/ailocal/acm-ai-frontend/frontend/src/components/layout/AppSidebar.tsx`
- **Current Command Palette:** `/mnt/d/ailocal/acm-ai-frontend/frontend/src/components/common/CommandPalette.tsx`
- **Story:** E14-S3 from Epic 14 (UX & Enterprise Readiness)
