# Tech Spec: E8-S8 - Update Navigation & Sidebar

> **Story:** E8-S8
> **Epic:** UI Refresh (Bento Grid Design)
> **Status:** Draft
> **Created:** 2025-12-08

---

## Overview

Update the navigation sidebar to match the new design system with improved visual hierarchy and modern styling.

---

## User Story

**As a** user
**I want** modern navigation that matches the new design
**So that** the app feels cohesive

---

## Acceptance Criteria

- [ ] Updated sidebar with new color scheme
- [ ] Improved iconography
- [ ] Active state indicators
- [ ] Collapsible sections
- [ ] Quick access shortcuts

---

## Technical Design

### 1. Updated Sidebar Component

Update `frontend/src/components/layout/AppSidebar.tsx`:

```tsx
'use client';

import * as React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Logo } from '@/components/brand/Logo';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import {
  LayoutDashboard,
  FileText,
  FolderOpen,
  TableProperties,
  Settings,
  ChevronDown,
  Upload,
  Search,
  Keyboard,
} from 'lucide-react';

interface NavItem {
  title: string;
  href: string;
  icon: React.ElementType;
  badge?: string;
  children?: { title: string; href: string }[];
}

const navItems: NavItem[] = [
  {
    title: 'Dashboard',
    href: '/',
    icon: LayoutDashboard,
  },
  {
    title: 'Sources',
    href: '/sources',
    icon: FileText,
    children: [
      { title: 'All Sources', href: '/sources' },
      { title: 'Upload New', href: '/sources/new' },
    ],
  },
  {
    title: 'Notebooks',
    href: '/notebooks',
    icon: FolderOpen,
  },
  {
    title: 'ACM Register',
    href: '/acm',
    icon: TableProperties,
  },
];

const quickActions = [
  { title: 'Upload', href: '/sources/new', icon: Upload, shortcut: '⌘U' },
  { title: 'Search', href: '/search', icon: Search, shortcut: '⌘K' },
];

export function AppSidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = React.useState(false);

  return (
    <TooltipProvider delayDuration={0}>
      <aside
        className={cn(
          'flex flex-col h-screen border-r bg-card transition-all duration-300',
          collapsed ? 'w-16' : 'w-64'
        )}
      >
        {/* Header */}
        <div className="flex items-center h-14 px-4 border-b">
          {collapsed ? (
            <Logo variant="icon" className="w-8 h-8 mx-auto" />
          ) : (
            <Logo variant="full" />
          )}
        </div>

        {/* Quick Actions */}
        <div className={cn('p-3 border-b', collapsed && 'px-2')}>
          {collapsed ? (
            <div className="space-y-2">
              {quickActions.map((action) => (
                <Tooltip key={action.href}>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      asChild
                      className="w-full"
                    >
                      <Link href={action.href}>
                        <action.icon className="w-5 h-5" />
                      </Link>
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent side="right">
                    {action.title}
                    <kbd className="ml-2 text-xs opacity-50">{action.shortcut}</kbd>
                  </TooltipContent>
                </Tooltip>
              ))}
            </div>
          ) : (
            <div className="flex gap-2">
              {quickActions.map((action) => (
                <Button
                  key={action.href}
                  variant="outline"
                  size="sm"
                  asChild
                  className="flex-1"
                >
                  <Link href={action.href}>
                    <action.icon className="w-4 h-4 mr-2" />
                    {action.title}
                  </Link>
                </Button>
              ))}
            </div>
          )}
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto py-4">
          <ul className="space-y-1 px-2">
            {navItems.map((item) => (
              <NavItemComponent
                key={item.href}
                item={item}
                pathname={pathname}
                collapsed={collapsed}
              />
            ))}
          </ul>
        </nav>

        {/* Footer */}
        <div className="p-3 border-t">
          {collapsed ? (
            <Tooltip>
              <TooltipTrigger asChild>
                <Button variant="ghost" size="icon" asChild className="w-full">
                  <Link href="/settings">
                    <Settings className="w-5 h-5" />
                  </Link>
                </Button>
              </TooltipTrigger>
              <TooltipContent side="right">Settings</TooltipContent>
            </Tooltip>
          ) : (
            <Button variant="ghost" asChild className="w-full justify-start">
              <Link href="/settings">
                <Settings className="w-5 h-5 mr-2" />
                Settings
              </Link>
            </Button>
          )}
        </div>

        {/* Collapse Toggle */}
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setCollapsed(!collapsed)}
          className="absolute bottom-20 -right-3 w-6 h-6 rounded-full border bg-background p-0"
        >
          <ChevronDown
            className={cn(
              'w-4 h-4 transition-transform',
              collapsed ? '-rotate-90' : 'rotate-90'
            )}
          />
        </Button>
      </aside>
    </TooltipProvider>
  );
}

function NavItemComponent({
  item,
  pathname,
  collapsed,
}: {
  item: NavItem;
  pathname: string;
  collapsed: boolean;
}) {
  const isActive = pathname === item.href || pathname.startsWith(item.href + '/');
  const [open, setOpen] = React.useState(isActive);

  if (item.children && !collapsed) {
    return (
      <li>
        <Collapsible open={open} onOpenChange={setOpen}>
          <CollapsibleTrigger asChild>
            <Button
              variant={isActive ? 'secondary' : 'ghost'}
              className="w-full justify-between"
            >
              <span className="flex items-center">
                <item.icon className="w-5 h-5 mr-3" />
                {item.title}
              </span>
              <ChevronDown
                className={cn(
                  'w-4 h-4 transition-transform',
                  open && 'rotate-180'
                )}
              />
            </Button>
          </CollapsibleTrigger>
          <CollapsibleContent className="pl-8 pt-1 space-y-1">
            {item.children.map((child) => (
              <Button
                key={child.href}
                variant={pathname === child.href ? 'secondary' : 'ghost'}
                size="sm"
                asChild
                className="w-full justify-start"
              >
                <Link href={child.href}>{child.title}</Link>
              </Button>
            ))}
          </CollapsibleContent>
        </Collapsible>
      </li>
    );
  }

  if (collapsed) {
    return (
      <li>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant={isActive ? 'secondary' : 'ghost'}
              size="icon"
              asChild
              className="w-full"
            >
              <Link href={item.href}>
                <item.icon className="w-5 h-5" />
              </Link>
            </Button>
          </TooltipTrigger>
          <TooltipContent side="right">{item.title}</TooltipContent>
        </Tooltip>
      </li>
    );
  }

  return (
    <li>
      <Button
        variant={isActive ? 'secondary' : 'ghost'}
        asChild
        className="w-full justify-start"
      >
        <Link href={item.href}>
          <item.icon className="w-5 h-5 mr-3" />
          {item.title}
          {item.badge && (
            <span className="ml-auto text-xs bg-primary text-primary-foreground px-2 py-0.5 rounded-full">
              {item.badge}
            </span>
          )}
        </Link>
      </Button>
    </li>
  );
}
```

---

## File Changes

| File | Change |
|------|--------|
| `frontend/src/components/layout/AppSidebar.tsx` | Redesign |
| `frontend/src/components/brand/Logo.tsx` | Update if needed |

---

## Dependencies

- E6-S2: Logo component
- E8-S2: Design tokens

---

## Testing

1. Navigate between pages - verify active states
2. Collapse/expand sidebar
3. Test tooltips in collapsed mode
4. Verify quick actions work
5. Test collapsible sub-navigation
6. Test keyboard shortcuts display
7. Verify responsive behavior

---

## Estimated Complexity

**Medium** - Interactive sidebar with multiple states

---
