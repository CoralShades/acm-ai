# Tech Spec: E14-S10 - Add Breadcrumb Navigation for Deep Pages

> **Story:** E14-S10
> **Epic:** Epic 14 - UX & Enterprise Readiness
> **Status:** Ready for Dev
> **Created:** 2026-02-08

---

## Overview

Implement breadcrumb navigation for detail pages to improve wayfinding and provide clear hierarchical context. Breadcrumbs will help users understand their current location and enable easy navigation back to parent pages.

This feature addresses the UI/UX specification requirement for breadcrumb navigation on deep pages (Section 4.3 of ui-ux-spec.md).

---

## User Story

**As a** user viewing a source detail page
**I want** breadcrumb navigation showing my location
**So that** I can easily navigate back to the parent page

---

## Acceptance Criteria

- [ ] Breadcrumb component created following VAEA design tokens
- [ ] Breadcrumbs shown on: Source detail, ACM Register (within source), Notebook detail
- [ ] Links are functional (clicking "Documents" goes to documents list)
- [ ] Responsive: truncated with ellipsis on mobile

---

## Technical Design

### 1. Breadcrumb Component

Create a reusable `Breadcrumbs` component in `frontend/src/components/common/Breadcrumbs.tsx` that uses semantic HTML and follows the VAEA design system.

**Component Props:**
```typescript
interface BreadcrumbItem {
  label: string
  href?: string  // Optional - last item has no href
}

interface BreadcrumbsProps {
  items: BreadcrumbItem[]
  className?: string
}
```

**Implementation Requirements:**

1. **Semantic HTML Structure:**
   - Use `<nav aria-label="Breadcrumb">` for accessibility
   - Use `<ol>` for ordered list of breadcrumb items
   - Use `<li>` for each breadcrumb item
   - Current page (last item) should be `aria-current="page"`

2. **Visual Design:**
   - Items separated by chevron-right separator (`/` or `>`)
   - Links use `text-muted-foreground` with `hover:text-foreground` transition
   - Current page (last item) uses `text-foreground font-medium`
   - Separator uses `text-muted-foreground/50`
   - Text size: `text-sm`

3. **Responsive Behavior:**
   - **Desktop (>= 1024px):** Show all breadcrumb items
   - **Tablet (768px - 1023px):** Show first, ellipsis middle items (if > 3), last
   - **Mobile (< 768px):** Show only last 2 items with ellipsis if more exist

**Code Pattern:**
```tsx
import Link from 'next/link'
import { ChevronRight } from 'lucide-react'
import { cn } from '@/lib/utils'

interface BreadcrumbItem {
  label: string
  href?: string
}

interface BreadcrumbsProps {
  items: BreadcrumbItem[]
  className?: string
}

export function Breadcrumbs({ items, className }: BreadcrumbsProps) {
  return (
    <nav aria-label="Breadcrumb" className={cn("flex", className)}>
      <ol className="flex items-center gap-2 text-sm">
        {items.map((item, index) => {
          const isLast = index === items.length - 1

          return (
            <li key={index} className="flex items-center gap-2">
              {item.href && !isLast ? (
                <Link
                  href={item.href}
                  className="text-muted-foreground hover:text-foreground transition-colors"
                >
                  {item.label}
                </Link>
              ) : (
                <span
                  className={cn(
                    isLast ? "text-foreground font-medium" : "text-muted-foreground"
                  )}
                  aria-current={isLast ? "page" : undefined}
                >
                  {item.label}
                </span>
              )}

              {!isLast && (
                <ChevronRight className="h-4 w-4 text-muted-foreground/50" />
              )}
            </li>
          )
        })}
      </ol>
    </nav>
  )
}
```

### 2. Page Integration

#### 2.1 Source Detail Page

**File:** `frontend/src/app/(dashboard)/sources/[id]/page.tsx`

**Breadcrumb Structure:**
```
Home > Sources > [Source Name]
```

**Integration Location:**
Add breadcrumbs after the back button, before the main bento grid:

```tsx
// After line 221 (after back button)
<div className="px-6 pb-2 flex-shrink-0">
  <Breadcrumbs
    items={[
      { label: 'Home', href: '/' },
      { label: 'Sources', href: '/sources' },
      { label: source.title || 'Untitled Source' }
    ]}
  />
</div>
```

#### 2.2 ACM Register Page (Standalone)

**File:** `frontend/src/app/(dashboard)/acm/page.tsx`

**Breadcrumb Structure (when source selected):**
```
Home > ACM Register
```

**Integration Location:**
Add breadcrumbs after the page header, before source selector card:

```tsx
// After line 137 (after header description)
<div className="mb-4">
  <Breadcrumbs
    items={[
      { label: 'Home', href: '/' },
      { label: 'ACM Register' }
    ]}
  />
</div>
```

**Note:** ACM Register is a top-level page, so breadcrumbs are minimal. If we implement a future source-specific ACM route (e.g., `/sources/[id]/acm`), breadcrumbs would be:
```
Home > Sources > [Source Name] > ACM Register
```

#### 2.3 Notebook Detail Page

**File:** `frontend/src/app/(dashboard)/notebooks/[id]/page.tsx`

**Breadcrumb Structure:**
```
Home > Notebooks > [Notebook Name]
```

**Integration Location:**
Add breadcrumbs in the header section, before the NotebookHeader component:

```tsx
// After line 118 (inside flex-shrink-0 div)
<div className="flex-shrink-0 p-6 pb-0 space-y-2">
  <Breadcrumbs
    items={[
      { label: 'Home', href: '/' },
      { label: 'Notebooks', href: '/notebooks' },
      { label: notebook.name || 'Untitled Notebook' }
    ]}
  />
  <NotebookHeader notebook={notebook} />
</div>
```

### 3. Responsive Behavior

#### Mobile Truncation (< 768px)

When breadcrumb items exceed 2, show only the last 2 items with an ellipsis:

```tsx
// Responsive logic inside Breadcrumbs component
const isMobile = items.length > 2 // Simplified - use media query hook in real implementation

const displayItems = isMobile && items.length > 2
  ? [
      { label: '...', href: undefined },
      items[items.length - 2],
      items[items.length - 1]
    ]
  : items
```

**Better Approach:** Use CSS-based truncation for middle items:

```tsx
<li
  className={cn(
    "flex items-center gap-2",
    index > 0 && index < items.length - 1 && "hidden md:flex"
  )}
>
  {/* breadcrumb item */}
</li>

{/* Show ellipsis on mobile when items are hidden */}
{items.length > 2 && index === 0 && (
  <li className="flex md:hidden items-center gap-2">
    <span className="text-muted-foreground">...</span>
    <ChevronRight className="h-4 w-4 text-muted-foreground/50" />
  </li>
)}
```

#### Tablet (768px - 1023px)

Show all items but with reduced padding/spacing if needed.

#### Desktop (>= 1024px)

Show all items with full spacing.

---

## File Changes

| File | Type | Description |
|------|------|-------------|
| `frontend/src/components/common/Breadcrumbs.tsx` | CREATE | Reusable breadcrumb component with responsive behavior |
| `frontend/src/app/(dashboard)/sources/[id]/page.tsx` | MODIFY | Add breadcrumbs showing: Home > Sources > [Source Name] |
| `frontend/src/app/(dashboard)/acm/page.tsx` | MODIFY | Add breadcrumbs showing: Home > ACM Register |
| `frontend/src/app/(dashboard)/notebooks/[id]/page.tsx` | MODIFY | Add breadcrumbs showing: Home > Notebooks > [Notebook Name] |

---

## Dependencies

### Required Before This Story

- None - all parent pages and routes already exist

### Component Dependencies

- **Lucide Icons:** `ChevronRight` icon (already installed)
- **Next.js Link:** For navigation (already available)
- **Tailwind CSS:** For styling (already configured)
- **cn utility:** For className merging (already in `@/lib/utils`)

### Routes Referenced

- `/` - Home/Dashboard (exists)
- `/sources` - Sources list page (exists)
- `/acm` - ACM Register page (exists)
- `/notebooks` - Notebooks list page (exists)

---

## Testing Strategy

### Unit Tests

**Test File:** `frontend/src/components/common/__tests__/Breadcrumbs.test.tsx`

Test cases:
1. Renders all breadcrumb items with correct labels
2. Last item has no link (aria-current="page")
3. All non-last items render as links with correct href
4. Chevron separators appear between items
5. Accessibility: nav has aria-label="Breadcrumb"
6. Responsive: middle items hidden on mobile (className check)

### Integration Tests

**Manual Testing Checklist:**

1. **Source Detail Page:**
   - [ ] Navigate to any source detail page
   - [ ] Verify breadcrumbs show: Home > Sources > [Source Title]
   - [ ] Click "Home" - navigates to `/`
   - [ ] Click "Sources" - navigates to `/sources`
   - [ ] Current page (source title) is not clickable
   - [ ] Mobile: breadcrumbs truncate appropriately

2. **ACM Register Page:**
   - [ ] Navigate to `/acm`
   - [ ] Verify breadcrumbs show: Home > ACM Register
   - [ ] Click "Home" - navigates to `/`
   - [ ] Current page (ACM Register) is not clickable

3. **Notebook Detail Page:**
   - [ ] Navigate to any notebook detail page
   - [ ] Verify breadcrumbs show: Home > Notebooks > [Notebook Name]
   - [ ] Click "Home" - navigates to `/`
   - [ ] Click "Notebooks" - navigates to `/notebooks`
   - [ ] Current page (notebook name) is not clickable
   - [ ] Mobile: breadcrumbs truncate appropriately

4. **Visual Regression:**
   - [ ] Breadcrumbs align correctly with page layout
   - [ ] Spacing matches design system (consistent padding/margins)
   - [ ] Hover states work on links
   - [ ] Colors match VAEA theme (muted-foreground, foreground)

### Browser Testing

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile Safari (iOS)
- Chrome Mobile (Android)

### Responsive Testing

- Desktop: 1920px, 1440px, 1280px
- Tablet: 1024px, 768px
- Mobile: 425px, 375px, 320px

---

## Implementation Notes

### Design System Compliance

- **Typography:** Use `text-sm` for breadcrumb text
- **Colors:**
  - Links: `text-muted-foreground` with `hover:text-foreground`
  - Current page: `text-foreground font-medium`
  - Separators: `text-muted-foreground/50`
- **Spacing:** Use `gap-2` between items and separators
- **Icons:** Use Lucide's `ChevronRight` at `h-4 w-4`

### Accessibility Compliance

- **ARIA Labels:** `<nav aria-label="Breadcrumb">`
- **Current Page:** `aria-current="page"` on last item
- **Semantic HTML:** Use `<ol>` and `<li>` for proper list structure
- **Keyboard Navigation:** Links are keyboard-accessible (native `<a>` behavior)
- **Screen Readers:** Will announce "Breadcrumb navigation" and read items in order

### Code Reusability

The `Breadcrumbs` component is designed to be reusable across any page:

```tsx
// Easy to add to new pages
<Breadcrumbs
  items={[
    { label: 'Home', href: '/' },
    { label: 'Parent', href: '/parent' },
    { label: 'Current Page' }
  ]}
/>
```

### Future Enhancements (Out of Scope)

1. **Dynamic Breadcrumbs:** Auto-generate from route structure
2. **Collapsible Middle Items:** Dropdown menu for hidden items on mobile
3. **Schema.org Markup:** Add structured data for SEO
4. **Route-based Generation:** Automatic breadcrumb generation from Next.js routing

---

## Estimated Complexity

**Story Points:** 2

**Breakdown:**
- Component creation: 1 hour
- Page integrations (3 pages): 1.5 hours
- Responsive styling: 0.5 hours
- Testing: 1 hour
- **Total:** ~4 hours

**Complexity Level:** Low-Medium

This is a straightforward UI component with clear requirements. The main complexity is ensuring consistent integration across multiple pages and proper responsive behavior.

---

## References

- **UI/UX Spec:** Section 4.3 - Breadcrumb Pattern (`docs/ui-ux-spec.md`)
- **Design System:** VAEA color tokens and typography
- **Accessibility:** WAI-ARIA breadcrumb pattern
- **Lucide Icons:** https://lucide.dev/icons/chevron-right

---

*End of Technical Specification*
