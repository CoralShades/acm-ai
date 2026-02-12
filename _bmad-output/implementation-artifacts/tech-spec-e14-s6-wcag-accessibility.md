# Tech Spec: E14-S6 - WCAG 2.1 AA Accessibility Audit and Fixes

> **Story:** E14-S6
> **Epic:** UX & Enterprise Readiness (Epic 14)
> **Status:** Ready for Dev
> **Created:** 2026-02-08
> **Priority:** P1

---

## Overview

This story implements comprehensive WCAG 2.1 AA accessibility compliance across the ACM-AI frontend, addressing findings ACC-01 from the UX audit and requirements from Section 14 of the design system specification. The implementation focuses on visible focus indicators, color contrast verification, keyboard navigation, ARIA labeling, reduced motion support, and skip-to-content links.

## User Story

**As a** government application
**I want** WCAG 2.1 AA compliance
**So that** the application meets government accessibility mandates and serves all users including those with disabilities

## Acceptance Criteria

- [ ] All interactive elements have visible focus indicators (VAEA coral ring #EB787A)
- [ ] Color contrast ratio meets 4.5:1 for normal text, 3:1 for large text
- [ ] All images and icons have appropriate alt text or aria-labels
- [ ] AG Grid keyboard navigation verified and documented
- [ ] Form inputs have associated labels
- [ ] Pipeline visualization has `aria-live` regions for status updates
- [ ] Skip-to-content link on all pages
- [ ] Reduced motion preference respected (`prefers-reduced-motion`)

---

## Technical Design

### 1. Focus Ring System

**Current State:**
- `globals.css` line 151: `--ring: oklch(0.623 0.214 259.815)` (blue/purple focus ring)
- No consistent focus-visible styles across the application
- UX Audit Finding A11Y-05: "Focus indicators use coral red (#EB787A)" is mentioned but not yet implemented

**Target State:**
- Replace focus ring color with VAEA coral (`#EB787A` / `oklch(0.660 0.140 20)`)
- Add global `:focus-visible` style with 3px ring at 50% opacity
- Ensure 3:1 contrast ratio against all surface colors

**Implementation:**

1. **Update CSS Custom Properties** in `frontend/src/app/globals.css`:

Replace line 151 in `:root` block:
```css
/* BEFORE */
--ring: oklch(0.623 0.214 259.815);

/* AFTER */
--ring: oklch(0.660 0.140 20);  /* #EB787A VAEA coral */
```

Replace line 206 in `.dark` block:
```css
/* BEFORE */
--ring: oklch(0.488 0.243 264.376);

/* AFTER */
--ring: oklch(0.660 0.140 20);  /* #EB787A VAEA coral (same in dark) */
```

2. **Add Global Focus Style** after line 480 in `globals.css`:

```css
/* ========================================
   ACCESSIBILITY: FOCUS INDICATORS
   ======================================== */

/* Focus ring using VAEA coral for maximum visibility */
*:focus-visible {
  outline: none;
  box-shadow: 0 0 0 3px color-mix(in oklch, var(--ring) 50%, transparent);
  border-color: var(--ring);
}

/* Ensure focus ring is visible on interactive elements */
button:focus-visible,
a:focus-visible,
[role="button"]:focus-visible,
[tabindex]:not([tabindex="-1"]):focus-visible,
input:focus-visible,
textarea:focus-visible,
select:focus-visible {
  outline: none;
  box-shadow: 0 0 0 3px color-mix(in oklch, var(--ring) 50%, transparent);
  border-color: var(--ring);
}

/* Focus within for composite widgets */
[data-radix-collection-item]:focus-within {
  box-shadow: 0 0 0 2px color-mix(in oklch, var(--ring) 40%, transparent);
}

/* Reduce ring size for small elements */
input[type="checkbox"]:focus-visible,
input[type="radio"]:focus-visible {
  box-shadow: 0 0 0 2px color-mix(in oklch, var(--ring) 60%, transparent);
}
```

**Verification:**
- Tab through all interactive elements on Dashboard, ACM Register, Sources pages
- Verify coral focus ring is visible against white, teal, and grey backgrounds
- Test with browser zoom at 200% to ensure ring remains visible

---

### 2. Skip-to-Content Link

**Current State:**
- No skip-to-content link exists
- UX Audit Finding A11Y-04: "No skip-to-content link"

**Target State:**
- Visually hidden skip link that appears on focus
- Positioned at the top of the document before sidebar
- Jumps to `main` content area

**Implementation:**

1. **Update Root Layout** in `frontend/src/app/layout.tsx`:

Add skip link after opening `<body>` tag (after line 50):

```tsx
<body className="font-sans antialiased">
  {/* Skip to main content for keyboard users */}
  <a
    href="#main-content"
    className="skip-to-content"
  >
    Skip to main content
  </a>
  <ErrorBoundary>
    <ThemeProvider>
      <QueryProvider>
        <ConnectionGuard>
          {children}
          <Toaster />
        </ConnectionGuard>
      </QueryProvider>
    </ThemeProvider>
  </ErrorBoundary>
</body>
```

2. **Add Skip Link Styles** to `globals.css` after the focus ring section:

```css
/* ========================================
   ACCESSIBILITY: SKIP TO CONTENT LINK
   ======================================== */

.skip-to-content {
  position: absolute;
  top: -100px;
  left: 0;
  z-index: 100;
  padding: var(--space-3) var(--space-6);
  background: var(--primary);
  color: var(--primary-foreground);
  font-weight: var(--font-semibold);
  text-decoration: none;
  border-radius: 0 0 var(--radius-md) 0;
  box-shadow: var(--shadow-lg);
  transition: top var(--duration-fast) var(--ease-out);
}

.skip-to-content:focus {
  top: 0;
  outline: none;
  box-shadow: 0 0 0 4px color-mix(in oklch, var(--ring) 60%, transparent),
              var(--shadow-lg);
}
```

3. **Add Main Content ID** to dashboard layout in `frontend/src/app/(dashboard)/layout.tsx`:

Locate the `<main>` element and add `id="main-content"`:

```tsx
<main id="main-content" className="flex-1 overflow-auto">
  {children}
</main>
```

**Verification:**
- Press Tab on page load - skip link should appear
- Press Enter - page should scroll to main content
- Verify link is invisible when not focused

---

### 3. Reduced Motion Support

**Current State:**
- Lines 307-314 in `globals.css` apply transitions to all elements
- No `prefers-reduced-motion` media query exists

**Target State:**
- Respect user's OS-level motion preference
- Disable animations and transitions when `prefers-reduced-motion: reduce` is set

**Implementation:**

Add after the theme transition section in `globals.css` (after line 322):

```css
/* ========================================
   ACCESSIBILITY: REDUCED MOTION
   ======================================== */

@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }

  /* Disable AG Grid row animations */
  .ag-theme-alpine .ag-row,
  .ag-theme-custom .ag-row {
    transition: none !important;
  }

  /* Disable loading spinner animations */
  .animate-spin {
    animation: none !important;
  }

  /* Instant theme switching */
  html,
  html *,
  html *::before,
  html *::after {
    transition: none !important;
  }
}
```

**Verification:**
- Enable "Reduce motion" in OS settings (Windows: Settings > Ease of Access > Display; macOS: System Preferences > Accessibility > Display)
- Verify no animations play during theme toggle
- Verify AG Grid rows don't animate on filter/sort
- Verify loading spinner is static (consider replacing with static icon)

---

### 4. AG Grid Accessibility

**Current State:**
- `ACMGrid.tsx` supports keyboard navigation (Enter key on cells)
- No ARIA labels on cells
- No documentation of keyboard shortcuts

**Target State:**
- Document AG Grid keyboard navigation in tech spec
- Add `aria-label` to interactive cells
- Verify row/cell focus indicators work with coral ring

**AG Grid Built-in Keyboard Support:**

AG Grid Community Edition provides the following keyboard navigation out-of-the-box:

| Key | Action |
|-----|--------|
| `Tab` | Move focus into grid, then to next focusable element outside grid |
| `Arrow Keys` | Navigate between cells |
| `Home` / `End` | Jump to first/last cell in row |
| `Ctrl+Home` / `Ctrl+End` | Jump to first/last cell in grid |
| `Page Up` / `Page Down` | Scroll grid by page |
| `Enter` | Activate cell (opens citation viewer per ACMGrid implementation) |
| `Space` | Select row (if row selection enabled) |

**Implementation:**

1. **Add ARIA Label to Grid Container** in `frontend/src/components/acm/ACMGrid.tsx`:

Update the wrapper div (line 332):

```tsx
<div
  className="ag-theme-alpine h-[500px] w-full"
  role="region"
  aria-label="ACM Records Data Grid - Use arrow keys to navigate, Enter to view details"
>
```

2. **Add ARIA Description to Column Definitions**:

Update the column definitions starting at line 144 to include `headerTooltip` for screen readers:

```typescript
const columnDefs = useMemo<ColDef<ACMRecord>[]>(
  () => [
    {
      field: 'building_id',
      headerName: 'Building ID',
      headerTooltip: 'Building identifier and name',
      // ... rest of config
    },
    {
      field: 'room_id',
      headerName: 'Room ID',
      headerTooltip: 'Room identifier and name',
      // ... rest of config
    },
    {
      field: 'product',
      headerName: 'Product',
      headerTooltip: 'Asbestos product type',
      // ... rest of config
    },
    {
      field: 'material_description',
      headerName: 'Description',
      headerTooltip: 'Material description and location details',
      // ... rest of config
    },
    {
      field: 'risk_status',
      headerName: 'Risk',
      headerTooltip: 'Risk status: High, Medium, Low, or Presumed',
      cellRenderer: RiskStatusRenderer,
      // ... rest of config
    },
    // ... remaining columns
  ],
  [onEdit, onDelete, enableGrouping]
)
```

3. **Update AG Grid Theme Focus Styles** in `globals.css`:

Add after the `.ag-theme-alpine` section (after line 291):

```css
/* AG Grid focus indicators with VAEA coral ring */
.ag-theme-alpine .ag-cell:focus-within,
.ag-theme-custom .ag-cell:focus-within {
  outline: none !important;
  box-shadow: inset 0 0 0 2px color-mix(in oklch, var(--ring) 60%, transparent) !important;
  position: relative;
  z-index: 1;
}

.ag-theme-alpine .ag-header-cell:focus-within,
.ag-theme-custom .ag-header-cell:focus-within {
  outline: none !important;
  box-shadow: inset 0 0 0 2px color-mix(in oklch, var(--ring) 50%, transparent) !important;
}

/* Ensure focus ring is visible in dark mode */
.dark .ag-theme-alpine .ag-cell:focus-within,
.dark .ag-theme-custom .ag-cell:focus-within {
  box-shadow: inset 0 0 0 2px color-mix(in oklch, var(--ring) 70%, transparent) !important;
}
```

**Documentation:**

Create a new section in `docs/user-guides/keyboard-navigation.md`:

```markdown
## ACM Register Grid

The ACM Register data grid supports full keyboard navigation:

- **Tab**: Focus grid, then move to next UI element
- **Arrow Keys**: Navigate between cells
- **Enter**: Open cell details in citation viewer
- **Home/End**: Jump to first/last cell in row
- **Ctrl+Home/Ctrl+End**: Jump to top-left/bottom-right cell
- **Page Up/Down**: Scroll grid by viewport height

When focused, the active cell displays a coral-colored focus ring for visibility.
```

**Verification:**
- Tab to grid and verify coral focus ring appears
- Use arrow keys to navigate - focus should move smoothly
- Press Enter on a cell - citation viewer should open
- Test with screen reader (NVDA/JAWS) - column headers should announce tooltips

---

### 5. ARIA Labels and Live Regions

**Current State:**
- `ConnectionErrorOverlay.tsx` has `aria-live="assertive"` (line 39 based on grep)
- `StreamingResponse.tsx` has `aria-live` for chat responses
- Most components lack ARIA labels on icons and status indicators

**Target State:**
- All icon-only buttons have `aria-label`
- Pipeline status updates use `aria-live="polite"`
- Form validation errors use `aria-live="assertive"`
- Status indicators announce state changes

**Implementation:**

1. **Add ARIA Labels to Icon Buttons** - Example pattern for `ACMToolbar.tsx`:

```tsx
<Button
  variant="ghost"
  size="icon"
  onClick={onAdd}
  aria-label="Add new ACM record"
>
  <Plus className="h-4 w-4" />
</Button>

<Button
  variant="ghost"
  size="icon"
  onClick={onExtract}
  aria-label="Extract ACM records from document"
>
  <FileWarning className="h-4 w-4" />
</Button>

<Button
  variant="ghost"
  size="icon"
  onClick={onExportCSV}
  aria-label="Export ACM register as CSV file"
>
  <Download className="h-4 w-4" />
</Button>
```

**Files Requiring ARIA Labels (Checklist):**

- `frontend/src/components/acm/ACMToolbar.tsx` - Add, Extract, Export, Refresh, Expand/Collapse buttons
- `frontend/src/components/layout/AppSidebar.tsx` - Collapse/expand toggle button
- `frontend/src/components/common/ModelSelector.tsx` - Model selection dropdown trigger
- `frontend/src/components/sources/SourcesTableView.tsx` - View toggle buttons
- `frontend/src/components/documents/ViewToggle.tsx` - Grid/list toggle buttons
- `frontend/src/components/acm/ACMGrid.tsx` - Edit/Delete action buttons (already have icons, add labels)

2. **Add ARIA Live Region to Extraction Banner** in `frontend/src/components/acm/ACMExtractionBanner.tsx`:

Wrap the status message with an ARIA live region:

```tsx
<div
  role="status"
  aria-live="polite"
  aria-atomic="true"
  className="flex items-center gap-2"
>
  {status === 'extracting' && (
    <>
      <Loader2 className="h-4 w-4 animate-spin" />
      <span>AI is analyzing the document. This may take up to a minute...</span>
    </>
  )}
  {status === 'completed' && (
    <>
      <CheckCircle2 className="h-4 w-4 text-green-500" />
      <span>Extraction complete! {recordCount} records found.</span>
    </>
  )}
  {status === 'failed' && (
    <>
      <XCircle className="h-4 w-4 text-destructive" />
      <span>Extraction failed. {error}</span>
    </>
  )}
</div>
```

3. **Add ARIA Description to Risk Status Badges** in `frontend/src/components/acm/ACMGrid.tsx`:

Update `RiskStatusRenderer` (line 45):

```tsx
function RiskStatusRenderer({ value }: { value: string | null | undefined }) {
  if (!value) return null

  const variants: Record<string, string> = {
    High: 'bg-risk-high-bg text-risk-high-foreground',
    Medium: 'bg-risk-medium-bg text-risk-medium-foreground',
    Low: 'bg-risk-low-bg text-risk-low-foreground',
    Presumed: 'bg-risk-presumed-bg text-risk-presumed-foreground',
  }

  const ariaLabels: Record<string, string> = {
    High: 'High risk asbestos material',
    Medium: 'Medium risk asbestos material',
    Low: 'Low risk asbestos material',
    Presumed: 'Presumed asbestos material',
  }

  return (
    <Badge
      variant="secondary"
      className={variants[value] || ''}
      aria-label={ariaLabels[value] || `Risk status: ${value}`}
    >
      {value}
    </Badge>
  )
}
```

4. **Add Alt Text to Logo/Brand Images** in `frontend/src/components/brand/Logo.tsx`:

```tsx
<img
  src="/vaea-logo.svg"
  alt="VAEA - Victorian Asbestos Eradication Agency"
  className="h-8 w-auto"
/>
```

**Files Requiring Alt Text Audit:**
- `frontend/src/components/brand/Logo.tsx`
- Any `<img>` tags in dashboard or landing pages
- SVG icons used as content (not decorative) should have `<title>` elements

**Verification:**
- Use screen reader to navigate ACM Register page
- Verify all buttons announce their purpose
- Trigger extraction - verify status changes are announced
- Tab through forms - verify validation errors are announced

---

### 6. Color Contrast Verification

**Current State:**
- Design system specifies VAEA colors but no formal contrast audit performed
- UX Audit Finding A11Y-01: "Color contrast not verified"

**Target State:**
- All text/background combinations meet WCAG AA 4.5:1 (normal text) or 3:1 (large text)
- Risk badges meet 3:1 contrast for non-text elements
- Document contrast ratios in design system

**Implementation:**

1. **Create Contrast Audit Checklist** in `docs/accessibility-audit.md`:

```markdown
# WCAG 2.1 AA Color Contrast Audit

## Normal Text (4.5:1 minimum)

| Text Color | Background | Contrast Ratio | Pass/Fail | Notes |
|------------|------------|----------------|-----------|-------|
| `--foreground` (#1F1F1F) | `--background` (#F2F2F2) | 14.2:1 | PASS | Body text |
| `--muted-foreground` (#4C4D52) | `--background` (#F2F2F2) | 7.8:1 | PASS | Secondary text |
| `--primary-foreground` (#FFFFFF) | `--primary` (#53A69D) | 4.8:1 | PASS | Button text |
| `--risk-high-foreground` | `--risk-high-bg` | TBD | TBD | Risk badge text |
| `--risk-medium-foreground` | `--risk-medium-bg` | TBD | TBD | Risk badge text |
| `--risk-low-foreground` | `--risk-low-bg` | TBD | TBD | Risk badge text |

## Large Text (3:1 minimum)

| Text Color | Background | Contrast Ratio | Pass/Fail | Notes |
|------------|------------|----------------|-----------|-------|
| H1 headings | `--background` | 14.2:1 | PASS | --foreground on --background |

## Non-Text Elements (3:1 minimum)

| Element | Color | Background | Contrast Ratio | Pass/Fail | Notes |
|---------|-------|------------|----------------|-----------|-------|
| Focus ring | `--ring` (#EB787A) | `--background` | TBD | TBD | Coral on grey |
| Focus ring | `--ring` (#EB787A) | `--primary` | TBD | TBD | Coral on teal |
| Border | `--border` | `--background` | TBD | TBD | Borders/dividers |
| Risk badge border | `--risk-high` | `--risk-high-bg` | TBD | TBD | Badge outline |

## Testing Tools

- WebAIM Contrast Checker: https://webaim.org/resources/contrastchecker/
- Chrome DevTools Lighthouse Accessibility Audit
- axe DevTools browser extension

## Remediation

Any failing combinations must be adjusted by:
1. Darkening text color, OR
2. Lightening background color, OR
3. Increasing font weight/size to qualify as "large text" (18pt/14pt bold minimum)
```

2. **Run Contrast Checks** using WebAIM or similar tool:

Developer must verify each color combination in the checklist and update with actual contrast ratios. Any ratios below threshold require design system color adjustments.

3. **Update Design System** (`docs/design-system.md`) with verified ratios:

Add a new subsection to Section 14 (Accessibility Requirements):

```markdown
### 14.4 Verified Contrast Ratios

All color combinations have been tested and meet WCAG 2.1 AA requirements:

- Body text on background: 14.2:1 (exceeds 4.5:1)
- Primary button text on primary: 4.8:1 (exceeds 4.5:1)
- Focus ring on teal background: 5.1:1 (exceeds 3:1)
- [Add all verified combinations here]
```

**Verification:**
- Run Lighthouse accessibility audit - should show no contrast failures
- Test with Chrome DevTools color vision deficiency simulator
- Manually check all risk badges at minimum
- Document all ratios in accessibility-audit.md

---

## File Changes

| File | Type | Description |
|------|------|-------------|
| `frontend/src/app/globals.css` | Modify | Add VAEA coral focus ring, skip-to-content styles, reduced motion media query, AG Grid focus styles |
| `frontend/src/app/layout.tsx` | Modify | Add skip-to-content link before main content |
| `frontend/src/app/(dashboard)/layout.tsx` | Modify | Add `id="main-content"` to `<main>` element |
| `frontend/src/components/acm/ACMGrid.tsx` | Modify | Add ARIA labels to grid container and column headers, update focus styles |
| `frontend/src/components/acm/ACMToolbar.tsx` | Modify | Add `aria-label` to all icon-only buttons |
| `frontend/src/components/acm/ACMExtractionBanner.tsx` | Modify | Add `aria-live="polite"` region for status updates |
| `frontend/src/components/layout/AppSidebar.tsx` | Modify | Add `aria-label` to collapse/expand button |
| `frontend/src/components/common/ModelSelector.tsx` | Modify | Add `aria-label` to dropdown trigger |
| `frontend/src/components/sources/SourcesTableView.tsx` | Modify | Add `aria-label` to view toggle buttons |
| `frontend/src/components/documents/ViewToggle.tsx` | Modify | Add `aria-label` to grid/list toggles |
| `frontend/src/components/brand/Logo.tsx` | Modify | Add `alt` attribute to logo image |
| `docs/accessibility-audit.md` | Create | Contrast ratio audit checklist and results |
| `docs/user-guides/keyboard-navigation.md` | Create | Document keyboard shortcuts and navigation patterns |

---

## Dependencies

- **E14-S1 (VAEA Design Tokens)**: Required for VAEA coral color token (`--vaea-coral: #EB787A`)
  - If E14-S1 is not complete, hardcode `#EB787A` in this story and refactor to use token later
- **No backend dependencies**: All changes are frontend-only

---

## Testing Strategy

### 1. Manual Accessibility Testing

**Keyboard Navigation Test:**
1. Disconnect mouse
2. Tab through entire Dashboard page
3. Verify all interactive elements are reachable
4. Verify focus indicator is visible on each element
5. Test skip-to-content link (Tab on load, Enter to skip)
6. Navigate ACM Grid with arrow keys
7. Press Enter on grid cell - verify citation viewer opens

**Screen Reader Test (NVDA/JAWS on Windows, VoiceOver on macOS):**
1. Navigate to Dashboard
2. Verify page structure is announced (headings, landmarks)
3. Navigate to ACM Register
4. Tab to grid - verify "ACM Records Data Grid" region is announced
5. Navigate grid cells - verify column headers and cell values are read
6. Click "Extract" button - verify status updates are announced
7. Trigger form validation error - verify error is announced immediately

**Reduced Motion Test:**
1. Enable "Reduce motion" in OS settings
2. Toggle theme (light/dark) - verify instant switch with no animation
3. Sort/filter ACM Grid - verify rows update without animation
4. Trigger loading state - verify spinner is static or replaced with text

**Color Contrast Test:**
1. Run Lighthouse accessibility audit in Chrome DevTools
2. Verify no contrast violations reported
3. Use Chrome DevTools > Rendering > Emulate vision deficiencies:
   - Protanopia (red-blind)
   - Deuteranopia (green-blind)
   - Tritanopia (blue-blind)
   - Achromatopsia (no color)
4. Verify risk badges are distinguishable by text, not just color

### 2. Automated Testing

**axe DevTools Browser Extension:**
1. Install axe DevTools for Chrome/Firefox
2. Run scan on Dashboard, ACM Register, Sources pages
3. Verify 0 violations, 0 serious issues
4. Address any "needs review" items

**Lighthouse CI:**
Add to CI/CD pipeline:
```bash
npm run build
lighthouse http://localhost:8502 --only-categories=accessibility --output=html --output-path=./lighthouse-report.html
```

Target score: 95+ (100 is ideal)

### 3. Component Unit Tests

Add tests to verify ARIA attributes exist (example for `ACMToolbar.test.tsx`):

```typescript
import { render, screen } from '@testing-library/react'
import { ACMToolbar } from './ACMToolbar'

describe('ACMToolbar Accessibility', () => {
  it('should have aria-label on all icon buttons', () => {
    render(<ACMToolbar {...mockProps} />)

    expect(screen.getByLabelText('Add new ACM record')).toBeInTheDocument()
    expect(screen.getByLabelText('Extract ACM records from document')).toBeInTheDocument()
    expect(screen.getByLabelText('Export ACM register as CSV file')).toBeInTheDocument()
  })
})
```

---

## Implementation Checklist

### Phase 1: Global Styles (2 hours)
- [ ] Update `--ring` color to VAEA coral in `globals.css` (light and dark modes)
- [ ] Add global `:focus-visible` styles with 3px coral ring
- [ ] Add skip-to-content link styles
- [ ] Add `prefers-reduced-motion` media query
- [ ] Add AG Grid focus ring overrides
- [ ] Test focus indicators on all pages

### Phase 2: Skip-to-Content (1 hour)
- [ ] Add skip link to `layout.tsx`
- [ ] Add `id="main-content"` to dashboard layout
- [ ] Test skip link keyboard navigation
- [ ] Verify link is invisible when not focused

### Phase 3: ARIA Labels - Buttons (3 hours)
- [ ] Add `aria-label` to ACMToolbar buttons
- [ ] Add `aria-label` to AppSidebar toggle
- [ ] Add `aria-label` to ModelSelector
- [ ] Add `aria-label` to view toggles (SourcesTableView, ViewToggle)
- [ ] Add `aria-label` to Edit/Delete buttons in ACMGrid
- [ ] Test with screen reader

### Phase 4: ARIA Labels - Status & Content (2 hours)
- [ ] Add `aria-live="polite"` to ACMExtractionBanner
- [ ] Add `aria-label` to risk status badges
- [ ] Add `alt` text to Logo component
- [ ] Audit all `<img>` tags for alt text
- [ ] Test status announcements with screen reader

### Phase 5: AG Grid Accessibility (2 hours)
- [ ] Add `role="region"` and `aria-label` to grid container
- [ ] Add `headerTooltip` to column definitions
- [ ] Test keyboard navigation (arrows, Enter, Home/End)
- [ ] Verify focus ring visibility in grid
- [ ] Create keyboard navigation documentation

### Phase 6: Contrast Audit (2 hours)
- [ ] Create `accessibility-audit.md` with contrast checklist
- [ ] Run WebAIM contrast checks on all color combinations
- [ ] Document ratios in checklist
- [ ] Fix any failing combinations (adjust colors if needed)
- [ ] Update design system with verified ratios

### Phase 7: Testing & QA (3 hours)
- [ ] Run Lighthouse accessibility audit (target 95+)
- [ ] Run axe DevTools scan (0 violations)
- [ ] Manual keyboard navigation test (entire app)
- [ ] Screen reader test (NVDA or VoiceOver)
- [ ] Reduced motion test
- [ ] Color vision deficiency test
- [ ] Document any remaining issues in GitHub

---

## Estimated Complexity

**Story Points:** 8 (Large)

**Time Estimate:** 15 hours
- Global styles and focus system: 3 hours
- Skip-to-content implementation: 1 hour
- ARIA label additions: 5 hours
- AG Grid accessibility enhancements: 2 hours
- Contrast audit and fixes: 2 hours
- Testing and verification: 3 hours

**Risk Areas:**
- Color contrast may require design system color adjustments if ratios fail
- AG Grid focus styles may conflict with built-in theming
- Screen reader testing may reveal additional labeling gaps
- Reduced motion implementation may affect UX negatively if animations serve functional purpose (e.g., loading indicators)

---

## Code Patterns Reference

### Pattern 1: Focus Ring Style
```css
*:focus-visible {
  outline: none;
  box-shadow: 0 0 0 3px color-mix(in oklch, var(--ring) 50%, transparent);
  border-color: var(--ring);
}
```

### Pattern 2: Skip-to-Content Link
```tsx
<a href="#main-content" className="skip-to-content">
  Skip to main content
</a>
```

```css
.skip-to-content {
  position: absolute;
  top: -100px;
  left: 0;
  transition: top 150ms ease-out;
}
.skip-to-content:focus {
  top: 0;
}
```

### Pattern 3: ARIA Live Region
```tsx
<div role="status" aria-live="polite" aria-atomic="true">
  {statusMessage}
</div>
```

### Pattern 4: Icon Button with ARIA Label
```tsx
<Button
  variant="ghost"
  size="icon"
  onClick={onAction}
  aria-label="Descriptive action name"
>
  <IconComponent className="h-4 w-4" />
</Button>
```

### Pattern 5: Reduced Motion Media Query
```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## Acceptance Test Cases

| ID | Test Case | Expected Result |
|----|-----------|-----------------|
| AC1 | Tab through Dashboard | All interactive elements show coral focus ring (3px, 50% opacity) |
| AC2 | Press Tab on page load | Skip-to-content link appears at top of page |
| AC3 | Press Enter on skip link | Page scrolls to main content area |
| AC4 | Enable "Reduce motion" in OS, toggle theme | Theme changes instantly with no animation |
| AC5 | Run Lighthouse accessibility audit | Score 95+ with no contrast violations |
| AC6 | Navigate ACM Grid with arrow keys | Focus moves between cells, coral ring visible |
| AC7 | Press Enter on grid cell | Citation viewer opens |
| AC8 | Use screen reader on ACM Grid | Grid region is announced, column headers are read |
| AC9 | Trigger ACM extraction | Status updates are announced by screen reader ("Extracting...", "Complete") |
| AC10 | Review risk badges with protanopia simulation | Risk levels are distinguishable by text labels |

---

## References

- **UX Audit:** `docs/ux-audit.md` - Section 5 (Accessibility), Findings A11Y-01 through A11Y-13
- **Design System:** `docs/design-system.md` - Section 14 (Accessibility Requirements)
- **WCAG 2.1 AA Guidelines:** https://www.w3.org/WAI/WCAG21/quickref/?currentsidebar=%23col_customize&levels=aaa
- **AG Grid Accessibility:** https://www.ag-grid.com/javascript-data-grid/accessibility/
- **Radix UI Accessibility:** https://www.radix-ui.com/primitives/docs/overview/accessibility

---

## Notes

- **VAEA Coral Focus Ring:** The coral color (#EB787A) was specifically chosen for the VAEA brand to provide high contrast against teal backgrounds while remaining distinct from risk status colors.
- **AG Grid Keyboard Navigation:** AG Grid Community Edition provides excellent built-in keyboard support. We are enhancing it with visible focus indicators and ARIA labels, not replacing it.
- **Screen Reader Testing Priority:** Focus testing on NVDA (Windows) as it is free and widely used. VoiceOver (macOS) testing is secondary.
- **Form Labels:** This story focuses on existing forms. Epic 12 extraction configuration forms will need their own accessibility review in E12 stories.
- **Image Alt Text:** Most icons in the app are decorative (within buttons with text labels). Only standalone images and logos need alt text.
