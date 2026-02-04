# Tech Spec: E10-S1 - Simplify Navigation for ACM-AI Focus

> **Story:** E10-S1
> **Epic:** ACM-AI UI Simplification
> **Status:** Drafted
> **Created:** 2025-12-19

---

## Overview

Simplify the Open Notebook UI to focus on ACM document management workflows by hiding irrelevant navigation items. This creates a cleaner, more focused experience for ACM compliance users while keeping hidden features easily re-enableable via configuration.

---

## User Story

**As a** user
**I want** a simplified UI focused on ACM document management
**So that** I'm not distracted by features irrelevant to my ACM compliance workflow

---

## Acceptance Criteria

- [ ] Hide "Notebooks" navigation item (not needed for ACM workflow)
- [ ] Hide "Podcasts" navigation item (not relevant to compliance)
- [ ] Hide "Transformations" navigation item (advanced feature, not POC scope)
- [ ] Hide "Advanced" navigation item (developer features)
- [ ] Keep "Sources" navigation (document management)
- [ ] Keep "ACM Register" navigation (core functionality)
- [ ] Keep "Ask and Search" navigation (semantic search for compliance questions)
- [ ] Keep "Models" navigation (AI model configuration for local inference)
- [ ] Keep "Settings" navigation (user preferences)
- [ ] Navigation items hidden via feature flag or environment config
- [ ] Hidden items easily re-enabled via configuration (no hard delete)
- [ ] UI feels cohesive with reduced navigation (no empty groups)

---

## Technical Design

### 1. Navigation Configuration

#### Current Navigation Structure (AppSidebar.tsx)

```tsx
// Current structure to modify
const navigation = [
  {
    title: "Collect",
    items: [
      { name: "Sources", href: "/sources", icon: FileText },      // KEEP
      { name: "ACM Register", href: "/acm", icon: FileWarning },  // KEEP
    ],
  },
  {
    title: "Process",
    items: [
      { name: "Notebooks", href: "/notebooks", icon: Book },      // HIDE
      { name: "Ask and Search", href: "/search", icon: Search },  // KEEP
    ],
  },
  {
    title: "Create",
    items: [
      { name: "Podcasts", href: "/podcasts", icon: Mic },         // HIDE
    ],
  },
  {
    title: "Manage",
    items: [
      { name: "Models", href: "/models", icon: Bot },             // KEEP
      { name: "Transformations", href: "/transformations" },      // HIDE
      { name: "Settings", href: "/settings", icon: Settings },    // KEEP
      { name: "Advanced", href: "/advanced", icon: Wrench },      // HIDE
    ],
  },
];
```

### 2. Feature Flag Implementation

#### Option A: Environment Variable (Recommended for POC)

```bash
# .env
NEXT_PUBLIC_ACM_MODE=true
```

#### Update: `frontend/src/components/layout/AppSidebar.tsx`

```tsx
import { FileText, FileWarning, Search, Bot, Settings, Book, Mic, Wrench, FolderOpen } from "lucide-react";

// Feature flag for ACM-focused mode
const ACM_MODE = process.env.NEXT_PUBLIC_ACM_MODE === "true";

// Items hidden in ACM mode
const HIDDEN_IN_ACM_MODE = new Set([
  "/notebooks",
  "/podcasts",
  "/transformations",
  "/advanced",
]);

// Full navigation configuration
const fullNavigation = [
  {
    title: "Documents",
    items: [
      { name: "Library", href: "/documents", icon: FolderOpen, acmOnly: true },
      { name: "Sources", href: "/sources", icon: FileText },
      { name: "ACM Register", href: "/acm", icon: FileWarning },
    ],
  },
  {
    title: "Process",
    items: [
      { name: "Notebooks", href: "/notebooks", icon: Book },
      { name: "Ask and Search", href: "/search", icon: Search },
    ],
  },
  {
    title: "Create",
    items: [
      { name: "Podcasts", href: "/podcasts", icon: Mic },
    ],
  },
  {
    title: "Manage",
    items: [
      { name: "Models", href: "/models", icon: Bot },
      { name: "Transformations", href: "/transformations", icon: Wrench },
      { name: "Settings", href: "/settings", icon: Settings },
      { name: "Advanced", href: "/advanced", icon: Wrench },
    ],
  },
];

// Filter navigation based on mode
function getNavigation() {
  if (!ACM_MODE) {
    return fullNavigation;
  }

  return fullNavigation
    .map((group) => ({
      ...group,
      items: group.items.filter(
        (item) => !HIDDEN_IN_ACM_MODE.has(item.href) || item.acmOnly
      ),
    }))
    .filter((group) => group.items.length > 0); // Remove empty groups
}

export function AppSidebar() {
  const navigation = getNavigation();

  return (
    <aside className="w-64 border-r bg-background">
      <div className="flex flex-col h-full">
        {/* Logo */}
        <div className="p-4 border-b">
          <Logo />
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-6">
          {navigation.map((group) => (
            <div key={group.title}>
              <h3 className="px-3 mb-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                {group.title}
              </h3>
              <ul className="space-y-1">
                {group.items.map((item) => (
                  <NavItem key={item.href} item={item} />
                ))}
              </ul>
            </div>
          ))}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t">
          <UserMenu />
        </div>
      </div>
    </aside>
  );
}
```

### 3. Reorganized Navigation Groups (ACM Mode)

When `ACM_MODE=true`, the navigation simplifies to:

```
Documents
├── Library (new - E9-S1)
├── Sources
└── ACM Register

Search
└── Ask and Search

Settings
├── Models
└── Settings
```

### 4. Type-Safe Navigation Config

#### Location: `frontend/src/config/navigation.ts`

```tsx
import { LucideIcon, FileText, FileWarning, Search, Bot, Settings, Book, Mic, Wrench, FolderOpen } from "lucide-react";

export interface NavItem {
  name: string;
  href: string;
  icon: LucideIcon;
  acmOnly?: boolean;  // Only show in ACM mode
  hideInAcm?: boolean; // Hide in ACM mode
}

export interface NavGroup {
  title: string;
  items: NavItem[];
}

export const navigationConfig: NavGroup[] = [
  {
    title: "Documents",
    items: [
      { name: "Library", href: "/documents", icon: FolderOpen, acmOnly: true },
      { name: "Sources", href: "/sources", icon: FileText },
      { name: "ACM Register", href: "/acm", icon: FileWarning },
    ],
  },
  {
    title: "Process",
    items: [
      { name: "Notebooks", href: "/notebooks", icon: Book, hideInAcm: true },
      { name: "Ask and Search", href: "/search", icon: Search },
    ],
  },
  {
    title: "Create",
    items: [
      { name: "Podcasts", href: "/podcasts", icon: Mic, hideInAcm: true },
    ],
  },
  {
    title: "Manage",
    items: [
      { name: "Models", href: "/models", icon: Bot },
      { name: "Transformations", href: "/transformations", icon: Wrench, hideInAcm: true },
      { name: "Settings", href: "/settings", icon: Settings },
      { name: "Advanced", href: "/advanced", icon: Wrench, hideInAcm: true },
    ],
  },
];

export function getFilteredNavigation(isAcmMode: boolean): NavGroup[] {
  return navigationConfig
    .map((group) => ({
      ...group,
      items: group.items.filter((item) => {
        if (isAcmMode) {
          return !item.hideInAcm;
        }
        return !item.acmOnly;
      }),
    }))
    .filter((group) => group.items.length > 0);
}
```

### 5. Settings Toggle (Optional Enhancement)

If runtime toggle is desired instead of env variable:

#### Update: `frontend/src/stores/settingsStore.ts`

```tsx
import { create } from "zustand";
import { persist } from "zustand/middleware";

interface SettingsState {
  acmMode: boolean;
  setAcmMode: (enabled: boolean) => void;
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      acmMode: process.env.NEXT_PUBLIC_ACM_MODE === "true",
      setAcmMode: (enabled) => set({ acmMode: enabled }),
    }),
    {
      name: "acm-settings",
    }
  )
);
```

#### Add to Settings Page:

```tsx
import { useSettingsStore } from "@/stores/settingsStore";

function SettingsPage() {
  const { acmMode, setAcmMode } = useSettingsStore();

  return (
    <Card>
      <CardHeader>
        <CardTitle>Interface Mode</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-between">
          <div>
            <Label>ACM-Focused Mode</Label>
            <p className="text-sm text-muted-foreground">
              Simplify navigation for ACM compliance workflows
            </p>
          </div>
          <Switch
            checked={acmMode}
            onCheckedChange={setAcmMode}
          />
        </div>
      </CardContent>
    </Card>
  );
}
```

### 6. Environment Variables

#### Update: `.env.example`

```bash
# ACM-AI Mode
# Set to "true" to enable ACM-focused UI (hides irrelevant features)
NEXT_PUBLIC_ACM_MODE=true
```

#### Update: `frontend/next.config.js`

```js
module.exports = {
  env: {
    NEXT_PUBLIC_ACM_MODE: process.env.NEXT_PUBLIC_ACM_MODE || "false",
  },
};
```

---

## Visual Comparison

### Before (Open Notebook Full UI)
```
Collect
├── Sources
└── ACM Register

Process
├── Notebooks
└── Ask and Search

Create
└── Podcasts

Manage
├── Models
├── Transformations
├── Settings
└── Advanced
```

### After (ACM-AI Simplified)
```
Documents
├── Library ← NEW
├── Sources
└── ACM Register

Search
└── Ask and Search

Settings
├── Models
└── Settings
```

---

## File Changes

| File | Change |
|------|--------|
| `frontend/src/components/layout/AppSidebar.tsx` | Filter navigation by mode |
| `frontend/src/config/navigation.ts` | New config file with typed navigation |
| `frontend/src/stores/settingsStore.ts` | Add acmMode setting (optional) |
| `frontend/.env.example` | Add ACM_MODE variable |
| `frontend/next.config.js` | Expose environment variable |

---

## Dependencies

- None (can be done independently)
- Recommended early in development to set UI focus

---

## Testing

1. Set `NEXT_PUBLIC_ACM_MODE=true` and restart frontend
2. Verify hidden items no longer appear:
   - Notebooks (hidden)
   - Podcasts (hidden)
   - Transformations (hidden)
   - Advanced (hidden)
3. Verify visible items work:
   - Sources (visible)
   - ACM Register (visible)
   - Ask and Search (visible)
   - Models (visible)
   - Settings (visible)
4. Verify no empty navigation groups appear
5. Set `NEXT_PUBLIC_ACM_MODE=false` and verify full UI returns
6. (Optional) Test settings toggle if implemented

---

## Rollback

To restore full Open Notebook UI:
```bash
NEXT_PUBLIC_ACM_MODE=false
```

Or remove the environment variable entirely.

---

## Estimated Complexity

**Low** - Simple conditional rendering based on feature flag

---
