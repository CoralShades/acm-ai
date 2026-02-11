# Tech Spec: E14-S9 - Expand Keyboard Navigation and Shortcuts

> **Story:** E14-S9
> **Epic:** E14 - UX & Enterprise Readiness
> **Status:** Ready for Dev
> **Created:** 2026-02-08

---

## Overview

Expand keyboard navigation beyond the existing Cmd+K (command palette) and Ctrl+F (search filter) shortcuts to include shortcuts for common actions, AG Grid navigation enhancements, Escape key handling for dialogs/panels, and a keyboard shortcut cheat sheet accessible via `?` key.

This addresses **UX Audit Finding NAV-03** ("Limited keyboard navigation") and **ENT-07** ("Limited keyboard shortcuts") from `docs/ux-audit.md`.

---

## User Story

**As a** power user
**I want** keyboard shortcuts for common actions
**So that** I can work efficiently without a mouse

---

## Acceptance Criteria

- [ ] Command palette (Cmd+K) entries for all primary actions (upload, export, navigate to pages, toggle theme)
- [ ] AG Grid keyboard navigation (arrow keys, Enter to expand groups, Tab to cycle cells)
- [ ] Escape key closes dialogs, panels, cell viewer, and command palette
- [ ] Tab key navigation cycles through pipeline stage cards
- [ ] Shortcut cheat sheet accessible via `?` key (shows modal with all shortcuts)
- [ ] Visual feedback for keyboard focus (existing focus ring styles preserved)

---

## Technical Design

### 1. Command Palette Expansion

**File:** `frontend/src/components/common/CommandPalette.tsx`

The command palette already exists with Cmd+K trigger and basic navigation/create/theme commands. Expand it with ACM-specific actions.

#### 1.1 Add New Command Categories

**Current state:**
- Navigation: Sources, Ask and Search, Models, Settings, Advanced (5 items after E14-S3)
- Create: Upload Document (1 item after E14-S3)
- Theme: Light/Dark/System (3 items)

**Additions:**

```tsx
// After existing navigationItems (line 42)
const actionItems = [
  {
    name: 'Upload Document',
    action: 'upload',
    icon: Upload,
    keywords: ['add', 'import', 'pdf', 'file']
  },
  {
    name: 'Export ACM to CSV',
    action: 'export-csv',
    icon: FileText,
    keywords: ['download', 'save', 'export']
  },
  {
    name: 'Export ACM to Excel',
    action: 'export-excel',
    icon: FileSpreadsheet,
    keywords: ['download', 'save', 'bar', 'xlsx']
  },
  {
    name: 'Extract ACM Records',
    action: 'extract',
    icon: Sparkles,
    keywords: ['ai', 'analyze', 'process', 'run']
  },
  {
    name: 'Add ACM Record',
    action: 'add-record',
    icon: Plus,
    keywords: ['create', 'new', 'manual']
  },
]

const viewItems = [
  {
    name: 'Dashboard',
    href: '/',
    icon: LayoutDashboard,
    keywords: ['home', 'overview', 'stats']
  },
  {
    name: 'ACM Register',
    href: '/acm',
    icon: FileWarning,
    keywords: ['records', 'grid', 'data', 'table']
  },
]
```

**Location:** Insert after line 42 (after `navigationItems` definition)

#### 1.2 Add Action Handler

```tsx
// After handleTheme callback (line 127)
const handleAction = useCallback((action: string) => {
  handleSelect(() => {
    // Actions are dispatched via custom events that components can listen to
    // This decouples the command palette from specific page contexts
    const event = new CustomEvent('acm-command', {
      detail: { action }
    })
    window.dispatchEvent(event)
  })
}, [handleSelect])
```

**Location:** Insert after line 127

**Rationale:** Using custom events allows the command palette to remain context-agnostic. Components like `ACMTab.tsx` or `ACMSpreadsheet` pages can listen for these events and execute actions only when they're the active page.

#### 1.3 Add CommandGroups to CommandList

```tsx
{/* After Navigation group (line 203) */}

{/* Quick Actions */}
<CommandGroup heading="Actions">
  {actionItems.map((item) => (
    <CommandItem
      key={item.action}
      value={`${item.name} ${item.keywords.join(' ')}`}
      onSelect={() => handleAction(item.action)}
    >
      <item.icon className="h-4 w-4" />
      <span>{item.name}</span>
    </CommandItem>
  ))}
</CommandGroup>

{/* Quick Views */}
<CommandGroup heading="Go to">
  {viewItems.map((item) => (
    <CommandItem
      key={item.href}
      value={`${item.name} ${item.keywords.join(' ')}`}
      onSelect={() => handleNavigate(item.href)}
    >
      <item.icon className="h-4 w-4" />
      <span>{item.name}</span>
    </CommandItem>
  ))}
</CommandGroup>
```

**Location:** Insert after the Navigation CommandGroup (after line 203)

#### 1.4 Update Imports

```tsx
// Add to existing icon imports (lines 16-31)
import {
  Book,
  Search,
  // ... existing imports ...
  Upload,        // NEW
  FileSpreadsheet, // NEW
  Sparkles,      // NEW
  LayoutDashboard, // NEW
  FileWarning,   // NEW
} from 'lucide-react'
```

**Note:** The command palette is already set up to ignore commands when focus is inside editable elements (lines 67-75), so shortcuts won't trigger when typing in forms.

---

### 2. AG Grid Keyboard Navigation

**File:** `frontend/src/components/acm/ACMGrid.tsx`

The grid already has basic keyboard support via `onCellKeyDown` (lines 306-329). Enhance it with additional keyboard actions.

#### 2.1 Enhance Cell Key Handler

**Current state:** Enter key opens cell viewer (lines 306-329)

**Additions:**

```tsx
// Replace onCellKeyDown callback (lines 306-329)
const onCellKeyDown = useCallback(
  (event: CellKeyDownEvent<ACMRecord>) => {
    const keyboardEvent = event.event as KeyboardEvent
    const key = keyboardEvent?.key

    if (!key || !event.data) return

    // Enter key: Open cell citation viewer or edit record
    if (key === 'Enter' && !event.node.group) {
      const field = event.colDef?.field
      const recordId = event.data.id

      // If Actions column or no field/ID, do nothing
      if (field && event.colDef?.headerName !== 'Actions' && recordId) {
        if (onCellSelect) {
          onCellSelect({
            recordId,
            field: field,
            value: event.value,
            pageNumber: event.data.page_number,
            record: event.data,
          })
        } else {
          onEdit(event.data)
        }
      }
    }

    // Space key: Expand/collapse group row
    if (key === ' ' && event.node.group) {
      keyboardEvent.preventDefault() // Prevent page scroll
      event.node.setExpanded(!event.node.expanded)
    }

    // E key: Edit record (when not in group row)
    if (key === 'e' && !event.node.group && event.data.id) {
      keyboardEvent.preventDefault()
      onEdit(event.data)
    }

    // Delete key: Delete record (when not in group row)
    if (key === 'Delete' && !event.node.group && event.data.id) {
      keyboardEvent.preventDefault()
      onDelete(event.data)
    }
  },
  [onEdit, onCellSelect, onDelete]
)
```

**Location:** Replace lines 306-329

**Keyboard Shortcuts Added:**
- **Enter**: Open cell citation viewer (existing)
- **Space**: Expand/collapse group row (NEW)
- **E**: Edit selected record (NEW)
- **Delete**: Delete selected record (NEW)
- **Arrow keys**: Native AG Grid navigation (already supported)
- **Tab**: Cycle through cells (native AG Grid behavior)

#### 2.2 Add Keyboard Hint to Grid Footer

Add a small help text below the grid to indicate keyboard shortcuts are available.

```tsx
// After closing </AgGridReact> tag (line 388)
{/* Keyboard navigation hint */}
<div className="text-xs text-muted-foreground mt-2 flex items-center gap-4">
  <span>Arrow keys to navigate</span>
  <span>Enter to view</span>
  <span>E to edit</span>
  <span>Space to expand/collapse</span>
  <span>? for all shortcuts</span>
</div>
```

**Location:** Insert after line 388 (after the closing `</AgGridReact>` tag, before closing `</div>`)

---

### 3. Global Keyboard Shortcuts

**File:** `frontend/src/components/common/KeyboardShortcutSheet.tsx` (NEW FILE)

Create a new component that listens for the `?` key and displays a modal with all available keyboard shortcuts.

#### 3.1 Create KeyboardShortcutSheet Component

```tsx
'use client'

import { useEffect, useState } from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'

interface Shortcut {
  keys: string[]
  description: string
  category: 'global' | 'grid' | 'navigation' | 'actions'
}

const shortcuts: Shortcut[] = [
  // Global shortcuts
  { keys: ['?'], description: 'Show keyboard shortcuts', category: 'global' },
  { keys: ['Cmd', 'K'], description: 'Open command palette', category: 'global' },
  { keys: ['Esc'], description: 'Close dialogs and panels', category: 'global' },

  // Navigation shortcuts
  { keys: ['G', 'D'], description: 'Go to Dashboard', category: 'navigation' },
  { keys: ['G', 'S'], description: 'Go to Sources', category: 'navigation' },
  { keys: ['G', 'A'], description: 'Go to ACM Register', category: 'navigation' },
  { keys: ['G', 'M'], description: 'Go to Models', category: 'navigation' },

  // Action shortcuts (via Command Palette)
  { keys: ['Cmd', 'K', 'then type "upload"'], description: 'Upload document', category: 'actions' },
  { keys: ['Cmd', 'K', 'then type "extract"'], description: 'Extract ACM records', category: 'actions' },
  { keys: ['Cmd', 'K', 'then type "export"'], description: 'Export ACM data', category: 'actions' },

  // Grid shortcuts (when grid is focused)
  { keys: ['↑', '↓', '←', '→'], description: 'Navigate grid cells', category: 'grid' },
  { keys: ['Enter'], description: 'View cell citation', category: 'grid' },
  { keys: ['Space'], description: 'Expand/collapse group', category: 'grid' },
  { keys: ['E'], description: 'Edit selected record', category: 'grid' },
  { keys: ['Delete'], description: 'Delete selected record', category: 'grid' },
  { keys: ['Tab'], description: 'Cycle through cells', category: 'grid' },
  { keys: ['Ctrl', 'F'], description: 'Focus search filter', category: 'grid' },
]

const categoryLabels: Record<Shortcut['category'], string> = {
  global: 'Global',
  navigation: 'Navigation',
  actions: 'Actions',
  grid: 'Grid Navigation',
}

function KeyboardKey({ children }: { children: string }) {
  return (
    <Badge
      variant="outline"
      className="font-mono text-xs px-2 py-0.5 bg-muted"
    >
      {children}
    </Badge>
  )
}

export function KeyboardShortcutSheet() {
  const [open, setOpen] = useState(false)

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignore if user is typing in an input/textarea
      const target = e.target as HTMLElement
      if (
        target &&
        (target.isContentEditable ||
          ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName))
      ) {
        return
      }

      // Shift+? (question mark) to open shortcuts
      if (e.key === '?' && e.shiftKey) {
        e.preventDefault()
        setOpen(true)
      }

      // Escape to close
      if (e.key === 'Escape' && open) {
        setOpen(false)
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [open])

  const categorizedShortcuts = shortcuts.reduce((acc, shortcut) => {
    if (!acc[shortcut.category]) {
      acc[shortcut.category] = []
    }
    acc[shortcut.category].push(shortcut)
    return acc
  }, {} as Record<Shortcut['category'], Shortcut[]>)

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Keyboard Shortcuts</DialogTitle>
          <DialogDescription>
            Use these shortcuts to navigate and perform actions quickly
          </DialogDescription>
        </DialogHeader>

        <ScrollArea className="h-[400px] pr-4">
          <div className="space-y-6">
            {Object.entries(categorizedShortcuts).map(([category, items]) => (
              <div key={category}>
                <h3 className="text-sm font-semibold mb-3">
                  {categoryLabels[category as Shortcut['category']]}
                </h3>
                <div className="space-y-2">
                  {items.map((shortcut, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between py-2 border-b last:border-0"
                    >
                      <span className="text-sm">{shortcut.description}</span>
                      <div className="flex gap-1">
                        {shortcut.keys.map((key, keyIndex) => (
                          <KeyboardKey key={keyIndex}>{key}</KeyboardKey>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>

        <div className="text-xs text-muted-foreground mt-4">
          Press <KeyboardKey>?</KeyboardKey> anytime to show this dialog
        </div>
      </DialogContent>
    </Dialog>
  )
}
```

**Location:** Create new file at `frontend/src/components/common/KeyboardShortcutSheet.tsx`

#### 3.2 Register KeyboardShortcutSheet in Layout

**File:** `frontend/src/app/(dashboard)/layout.tsx`

Add the `KeyboardShortcutSheet` component to the layout so it's available on all dashboard pages.

```tsx
// Add import (near other component imports)
import { KeyboardShortcutSheet } from '@/components/common/KeyboardShortcutSheet'

// Add component to layout (inside the main layout return)
<div className="flex min-h-screen">
  {/* Existing sidebar and content */}
  <AppSidebar />
  <div className="flex-1">
    {children}
  </div>

  {/* Global keyboard shortcut sheet */}
  <KeyboardShortcutSheet />
</div>
```

**Note:** The exact line numbers depend on the current `layout.tsx` structure. Place it at the root level alongside other global components like `CommandPalette` (which is already in the layout from the CreateDialogsProvider).

---

### 4. Escape Key Handling for Dialogs/Panels

**Files:**
- `frontend/src/components/ui/dialog.tsx` (already supports Escape via Radix UI)
- `frontend/src/components/ui/sheet.tsx` (already supports Escape via Radix UI)
- `frontend/src/components/acm/ACMCellViewer.tsx` (needs Escape handler)

#### 4.1 Verify Radix UI Escape Handling

**Current state:** Both `dialog.tsx` and `sheet.tsx` use Radix UI primitives (`@radix-ui/react-dialog`), which have **built-in Escape key handling**. No changes needed.

**Verification:** Test that pressing Escape closes:
- ACMRecordDialog
- ConfirmDialog
- SiteConfigPanel (if it uses Sheet)
- CommandPalette

#### 4.2 Add Escape Handler to ACMCellViewer

**File:** `frontend/src/components/acm/ACMCellViewer.tsx`

The `ACMCellViewer` is likely a custom component (not using Radix Dialog/Sheet). If it's a Sheet-based component, Escape is already handled. If it's a custom overlay, add Escape support.

**Assumption:** ACMCellViewer uses Sheet component → Escape already works.

**Fallback Plan:** If ACMCellViewer is custom, add this effect:

```tsx
// Inside the component, after existing hooks
useEffect(() => {
  if (!selection) return // Only listen when viewer is open

  const handleEscape = (e: KeyboardEvent) => {
    if (e.key === 'Escape') {
      onClose()
    }
  }

  document.addEventListener('keydown', handleEscape)
  return () => document.removeEventListener('keydown', handleEscape)
}, [selection, onClose])
```

**Testing Required:** Verify that Escape closes the cell viewer during implementation.

---

### 5. Navigation Shortcuts (Go-to Keys)

**File:** Create `frontend/src/components/common/NavigationShortcuts.tsx` (NEW FILE)

Implement "Go-to" shortcuts (e.g., G+D for Dashboard, G+S for Sources) as a global listener.

```tsx
'use client'

import { useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'

const navigationShortcuts: Record<string, string> = {
  'd': '/',           // G+D → Dashboard
  's': '/sources',    // G+S → Sources
  'a': '/acm',        // G+A → ACM Register
  'm': '/models',     // G+M → Models
  'h': '/search',     // G+H → Search (H for "help"/"hunt")
}

export function NavigationShortcuts() {
  const router = useRouter()
  const gKeyPressed = useRef(false)
  const timeoutRef = useRef<NodeJS.Timeout>()

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignore if user is typing in an input/textarea
      const target = e.target as HTMLElement
      if (
        target &&
        (target.isContentEditable ||
          ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName))
      ) {
        return
      }

      // Detect "G" key press (start of sequence)
      if (e.key === 'g' || e.key === 'G') {
        gKeyPressed.current = true

        // Reset after 1 second if no second key pressed
        if (timeoutRef.current) clearTimeout(timeoutRef.current)
        timeoutRef.current = setTimeout(() => {
          gKeyPressed.current = false
        }, 1000)

        return
      }

      // If G was pressed, check for navigation key
      if (gKeyPressed.current) {
        const destination = navigationShortcuts[e.key.toLowerCase()]
        if (destination) {
          e.preventDefault()
          router.push(destination)
          gKeyPressed.current = false
          if (timeoutRef.current) clearTimeout(timeoutRef.current)
        }
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      if (timeoutRef.current) clearTimeout(timeoutRef.current)
    }
  }, [router])

  return null // This component only provides behavior, no UI
}
```

**Location:** Create new file at `frontend/src/components/common/NavigationShortcuts.tsx`

**Register in Layout:**

```tsx
// In frontend/src/app/(dashboard)/layout.tsx
import { NavigationShortcuts } from '@/components/common/NavigationShortcuts'

// Add to layout
<div className="flex min-h-screen">
  {/* Existing content */}
  <NavigationShortcuts />
  <KeyboardShortcutSheet />
</div>
```

---

### 6. ACMTab Event Listener for Command Palette Actions

**File:** `frontend/src/components/acm/ACMTab.tsx`

Add an event listener that responds to command palette actions dispatched via custom events.

```tsx
// After existing useEffect hooks (after line 189)
// Listen for command palette actions
useEffect(() => {
  const handleCommand = (event: CustomEvent<{ action: string }>) => {
    const { action } = event.detail

    switch (action) {
      case 'extract':
        handleExtract()
        break
      case 'export-csv':
        handleExportCsv()
        break
      case 'export-excel':
        handleExportExcel()
        break
      case 'add-record':
        handleAddNew()
        break
      case 'upload':
        // Navigate to sources page with upload action
        window.location.href = '/sources?action=upload'
        break
      default:
        // Unknown action, ignore
        break
    }
  }

  // Type assertion for CustomEvent
  const listener = handleCommand as EventListener
  window.addEventListener('acm-command', listener)
  return () => window.removeEventListener('acm-command', listener)
}, [handleExtract, handleExportCsv, handleExportExcel, handleAddNew])
```

**Location:** Insert after line 189 (after the building selection reset effect)

**Note:** This pattern allows the command palette to trigger actions on the active page without tight coupling.

---

## File Changes

| File | Change Type | Description |
|------|-------------|-------------|
| `frontend/src/components/common/CommandPalette.tsx` | Modify | Add Actions and Go To command groups, add `handleAction` callback, update imports |
| `frontend/src/components/acm/ACMGrid.tsx` | Modify | Enhance `onCellKeyDown` with Space (expand/collapse), E (edit), Delete keys; add keyboard hint footer |
| `frontend/src/components/common/KeyboardShortcutSheet.tsx` | Create | New component showing all keyboard shortcuts in a modal, triggered by `?` key |
| `frontend/src/components/common/NavigationShortcuts.tsx` | Create | New component handling G+[key] navigation shortcuts |
| `frontend/src/app/(dashboard)/layout.tsx` | Modify | Register `KeyboardShortcutSheet` and `NavigationShortcuts` components |
| `frontend/src/components/acm/ACMTab.tsx` | Modify | Add event listener for command palette actions dispatched via custom events |
| `frontend/src/components/acm/ACMToolbar.tsx` | No Change | Already has Ctrl+F shortcut for search (lines 67-87) |

---

## Dependencies

**Prerequisites:**
- E14-S3 (Hide Brownfield Features) should be completed to ensure command palette has correct navigation items
- Existing Radix UI components (Dialog, Sheet) for Escape key handling

**External Libraries:**
- No new dependencies required
- Uses existing Radix UI primitives for dialog/sheet Escape handling
- Uses AG Grid's native keyboard navigation APIs

**Browser Compatibility:**
- CustomEvent API (supported in all modern browsers)
- KeyboardEvent.key (supported in all modern browsers)
- No polyfills required

---

## Testing

### Unit Testing

No new unit tests required. Keyboard event handlers are integration-level concerns best tested manually or with E2E tests.

**Future Enhancement:** Add Playwright E2E tests for keyboard navigation flows.

### Manual Testing

**Test 1: Command Palette Actions**
- [ ] Press Cmd+K → Command palette opens
- [ ] Type "upload" → "Upload Document" appears in Actions group
- [ ] Type "extract" → "Extract ACM Records" appears in Actions group
- [ ] Type "export" → Both CSV and Excel options appear
- [ ] Select "Extract ACM Records" → ACM extraction starts (on ACM page)
- [ ] Press Cmd+K, type "dashboard" → Dashboard option appears in "Go to" group
- [ ] Select Dashboard → Navigates to Dashboard page

**Test 2: AG Grid Keyboard Navigation**
- [ ] Navigate to `/acm` or open ACM tab in a source
- [ ] Click into grid → Focus ring appears on first cell
- [ ] Press arrow keys → Cell selection moves correctly
- [ ] Press Enter on data cell → Cell citation viewer opens
- [ ] Press Escape → Cell viewer closes
- [ ] Focus group header row → Press Space → Group expands/collapses
- [ ] Select a record → Press E → Edit dialog opens
- [ ] Select a record → Press Delete → Delete confirmation dialog opens
- [ ] Press Tab → Cycles through cells

**Test 3: Keyboard Shortcut Sheet**
- [ ] Press Shift+? → Shortcut sheet modal opens
- [ ] Sheet displays all shortcuts organized by category
- [ ] Press Escape → Sheet closes
- [ ] Open sheet while on grid → Press ? again → Sheet remains open (idempotent)

**Test 4: Go-to Navigation Shortcuts**
- [ ] Press G then D → Navigates to Dashboard
- [ ] Press G then S → Navigates to Sources
- [ ] Press G then A → Navigates to ACM Register
- [ ] Press G then M → Navigates to Models
- [ ] Press G then wait 2 seconds → Sequence resets (next G starts new sequence)
- [ ] Press G while typing in search box → No navigation (correctly ignored)

**Test 5: Escape Key Handling**
- [ ] Open ACMRecordDialog → Press Escape → Dialog closes
- [ ] Open ConfirmDialog → Press Escape → Dialog closes
- [ ] Open Cell Citation Viewer → Press Escape → Viewer closes
- [ ] Open Command Palette (Cmd+K) → Press Escape → Palette closes
- [ ] Open SiteConfigPanel → Press Escape → Panel closes

**Test 6: Focus Management**
- [ ] Press Ctrl+F in ACM grid → Search input receives focus
- [ ] Press Cmd+K → Command palette input receives focus
- [ ] Tab through toolbar buttons → Focus ring visible on each button
- [ ] Tab from search input → Focus moves to risk filter dropdown

**Test 7: Keyboard Hints**
- [ ] Grid footer shows: "Arrow keys to navigate, Enter to view, E to edit, Space to expand/collapse, ? for all shortcuts"
- [ ] Search input placeholder shows: "Search all columns... (Ctrl+F)"
- [ ] Command palette placeholder shows: "Type a command or search..."

### Build Verification

```bash
cd frontend
npm run build
```

**Expected:**
- ✅ Build passes with no errors
- ✅ No TypeScript errors about event types
- ✅ No unused imports warnings
- ✅ All new components properly exported

---

## Estimated Complexity

**Story Points:** 5

**Effort Breakdown:**
- Command palette expansion: 1 hour (add action/view groups, handler, imports)
- AG Grid keyboard enhancements: 1 hour (enhance onCellKeyDown, add hints)
- KeyboardShortcutSheet component: 2 hours (build modal, categorize shortcuts, styling)
- NavigationShortcuts component: 1 hour (sequence detection, routing)
- ACMTab event listener: 30 minutes (add custom event listener)
- Layout registration: 30 minutes (add components to layout)
- Testing: 2 hours (manual testing of all shortcuts across pages)

**Risk Level:** Low-Medium
- **Low risk:** Most shortcuts use existing browser/library behavior (arrow keys, Escape, Tab)
- **Medium risk:** Custom event-based command dispatch requires coordination between components
- **Mitigation:** Use defensive checks (ignore shortcuts when typing in inputs, verify element exists before dispatching events)

---

## Implementation Notes

### Why Custom Events for Command Palette Actions?

The command palette is a global component rendered in the layout, but actions like "Extract ACM" are context-specific (only meaningful on ACM pages). Using custom events (`window.dispatchEvent`) allows:

1. **Decoupling:** Command palette doesn't need to know about ACM-specific hooks or state
2. **Opt-in listening:** Only pages that care about actions listen for events
3. **Flexibility:** New pages can add their own action handlers without modifying the command palette

**Alternative considered:** Zustand global store for actions → Rejected because it adds state management overhead for ephemeral actions.

### Accessibility Considerations

**WCAG 2.4.7 - Focus Visible:** All keyboard interactions maintain visible focus rings using the existing Tailwind focus ring styles (`focus:ring-2 focus:ring-ring focus:ring-offset-2`).

**WCAG 2.1.1 - Keyboard Accessible:** All functionality is accessible via keyboard:
- Command palette (Cmd+K)
- Grid navigation (arrows, Tab, Enter, Space, E, Delete)
- Dialog dismissal (Escape)
- Navigation (G+[key])

**Screen Reader Compatibility:**
- Keyboard shortcuts are visual affordances and don't affect screen reader navigation
- All interactive elements already have proper ARIA labels (inherited from Radix UI)
- Consider adding `aria-live` region to announce shortcut actions (future enhancement)

### AG Grid suppressKeyboardEvent

AG Grid provides a `suppressKeyboardEvent` callback that can prevent default keyboard behavior. We **do not use it** in this implementation because:
1. We want Tab to cycle cells (default AG Grid behavior)
2. We want arrow keys to navigate (default AG Grid behavior)
3. Our custom keys (E, Delete, Space) are handled in `onCellKeyDown` without suppression

If future requirements need to suppress default behavior:

```tsx
suppressKeyboardEvent: (params) => {
  const key = params.event.key
  // Suppress Tab if we want custom Tab handling
  if (key === 'Tab') {
    return true // Suppress AG Grid's default Tab behavior
  }
  return false // Allow default behavior
}
```

### Future Enhancements (Not in Scope for E14-S9)

1. **Customizable shortcuts:** Allow users to rebind shortcuts via Settings page
2. **Shortcut cheat sheet in sidebar footer:** Persistent ? icon in sidebar
3. **Vim-style navigation:** H/J/K/L keys for grid navigation (power user mode)
4. **Bulk selection shortcuts:** Shift+Arrow to select multiple rows
5. **Undo/Redo shortcuts:** Cmd+Z / Cmd+Shift+Z for record edits
6. **Copy cell data:** Cmd+C to copy cell value to clipboard

---

## Verification Checklist

Before marking this story complete:

- [ ] `npm run build` passes with no errors
- [ ] Command palette shows Actions and Go To groups
- [ ] All 6 manual test scenarios pass
- [ ] Escape key closes all dialogs, panels, and modals
- [ ] ? key opens keyboard shortcut sheet
- [ ] G+[key] navigation shortcuts work for all pages
- [ ] AG Grid keyboard shortcuts (Enter, Space, E, Delete) work
- [ ] Ctrl+F focuses search in ACM toolbar
- [ ] No console errors about event listeners or key handling
- [ ] Focus rings visible on all keyboard navigation
- [ ] Screenshot of keyboard shortcut sheet saved to `docs/sprint-artifacts/e14-s9-keyboard-shortcuts.png`
- [ ] Screen recording of keyboard navigation workflow saved to `docs/sprint-artifacts/e14-s9-demo.mp4` (optional)

---

## References

- **UX Audit Finding:** `docs/ux-audit.md` Section 5 (A11Y-06), Section 9 (ENT-07)
- **Current Command Palette:** `/mnt/d/ailocal/acm-ai-frontend/frontend/src/components/common/CommandPalette.tsx`
- **Current ACM Grid:** `/mnt/d/ailocal/acm-ai-frontend/frontend/src/components/acm/ACMGrid.tsx`
- **AG Grid Keyboard Events:** https://www.ag-grid.com/react-data-grid/keyboard-navigation/
- **Radix UI Dialog (Escape handling):** https://www.radix-ui.com/primitives/docs/components/dialog#keyboard-interactions
- **Story:** E14-S9 from Epic 14 (UX & Enterprise Readiness)
