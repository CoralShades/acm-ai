# VAEA UI Design Review Checklist

Run this checklist before marking ANY UI story as complete. This integrates with
the Story Verification Protocol in CLAUDE.md.

**BLOCKING**: If any Critical item fails, the story is INCOMPLETE. Fix before marking done.

---

## How to Use

1. Complete all implementation work
2. Run the build verification from CLAUDE.md (`cd frontend && npm run build`)
3. Run this checklist item by item
4. Record results in the story's Dev Agent Record
5. Only mark the story complete if ALL Critical items pass

---

## Critical Items (Must Pass)

### C1. Design Tokens Only
- [ ] No raw hex values in className or style props (grep for `#[0-9a-fA-F]`)
- [ ] No raw pixel values in className (grep for `\[.*px\]`)
- [ ] All colors use semantic tokens (`bg-primary`, `text-muted-foreground`) or VAEA tokens (`bg-vaea-teal-300`)
- [ ] All spacing uses the token scale (`p-4`, `gap-space-4`) not arbitrary values

**Verify**: `grep -rn '#[0-9a-fA-F]\{3,8\}' frontend/src/components/ --include='*.tsx'`
Any matches in NEW or MODIFIED files = FAIL.

### C2. Responsive Behavior
- [ ] Tested at mobile (< 640px): layout doesn't break, content is accessible
- [ ] Tested at tablet (768px): functional, touch-friendly
- [ ] Tested at desktop (1280px+): full feature set visible
- [ ] AG Grid components: card view fallback exists below md breakpoint

**Verify**: Use chrome-devtools MCP `emulate` at 375px, 768px, and 1440px widths.
Take screenshots at each breakpoint.

### C3. Dark Mode
- [ ] Component renders correctly in light mode
- [ ] Component renders correctly in dark mode
- [ ] No hardcoded white/black backgrounds (use `bg-background`, `bg-card`)
- [ ] Dark mode backgrounds maintain teal tint (hue ~170-175 in oklch)

**Verify**: Toggle theme via command palette (Ctrl+K > "Dark"/"Light"). Visual check.

### C4. ARIA and Accessibility
- [ ] All buttons with icon-only content have `aria-label`
- [ ] All search/filter inputs have `aria-label`
- [ ] Data regions wrapped in `role="region"` with `aria-label`
- [ ] Loading states use `role="status"` + `aria-busy="true"` + `sr-only` text
- [ ] Progress indicators use `role="progressbar"` with min/max/now values
- [ ] Focus is visible on all interactive elements (`focus-visible:ring-2`)

**Verify**: Tab through all new interactive elements. Every element must show a visible
focus ring and be operable via keyboard.

### C5. Risk Indicators (if applicable)
- [ ] Risk level badges use BOTH icon AND color (dual encoding)
- [ ] Icons match: Low=CheckCircle, Medium=AlertTriangle, High=XCircle, Presumed=HelpCircle
- [ ] Risk tokens from globals.css used (not custom colors)

**Verify**: Visual check — can you distinguish risk levels in greyscale?

### C6. AG Grid Theme (if applicable)
- [ ] Grid uses `ag-theme-custom` class (via DataGrid wrapper)
- [ ] NO inline `<style jsx global>` blocks defining AG Grid styles
- [ ] Column state persisted to localStorage if user-configurable

**Verify**: `grep -rn 'style jsx global' frontend/src/components/ --include='*.tsx'`
Any AG Grid style blocks in modified files = FAIL.

### C7. Typography
- [ ] Headings use `<Text variant="h1|h2|h3|h4|h5">` component
- [ ] Body text uses `<Text variant="body|body-sm">`
- [ ] Data displays use `<Text variant="data">` (JetBrains Mono + tabular-nums)
- [ ] No raw `<h1>`, `<h2>`, `<p>` tags with manual Tailwind classes for text styling

**Verify**: `grep -rn '<h[1-6]\s' frontend/src/components/ --include='*.tsx'`
Raw heading tags in new component files = FAIL.

---

## Important Items (Should Pass)

### I1. Loading States
- [ ] Skeleton components match the final layout structure (not generic spinners)
- [ ] `role="status"` and `aria-busy="true"` on loading containers
- [ ] `sr-only` text announces what is loading
- [ ] Shimmer variant used for content areas, pulse for smaller elements

### I2. Error States
- [ ] ErrorBoundary wraps the page or major section
- [ ] Error fallback is meaningful (not blank white screen)
- [ ] Error fallback includes retry action
- [ ] Dev-only stack trace hidden in production

### I3. Empty States
- [ ] Empty data views show helpful message (not blank)
- [ ] Empty state suggests next action ("Upload a document to get started")
- [ ] Empty state uses appropriate icon at h-12 w-12

### I4. Coral Usage
- [ ] Primary CTAs use coral (`bg-vaea-coral`) for visual emphasis
- [ ] Notification dots/badges use coral for attention
- [ ] Secondary actions use teal (default Button variant)
- [ ] Coral is not overused (max 1-2 coral elements per viewport)

### I5. Icon Consistency
- [ ] All icons from lucide-react (no other icon libraries)
- [ ] Sizing convention followed: h-3/h-4/h-5/h-12 per context
- [ ] Decorative icons have `aria-hidden="true"`
- [ ] Interactive icons have accessible labels

### I6. Shadows and Elevation
- [ ] Shadow tokens used (`shadow-sm` through `shadow-xl`)
- [ ] No raw `box-shadow` values in component code
- [ ] Cards use `shadow-sm` or `shadow-md` (not `shadow-lg` unless modal/popover)

---

## Advisory Items (Nice to Have)

### A1. Motion and Animation
- [ ] Transitions use the token system (fast=150ms, normal=250ms, slow=350ms)
- [ ] No bounce/elastic easing (use ease-out or spring physics)
- [ ] Loading shimmer uses `animate-shimmer` keyframe
- [ ] Page transitions smooth (if framer-motion is installed)

### A2. Government Patterns
- [ ] Important information cards use left-border accent (`border-l-4 border-l-vaea-teal-300`)
- [ ] Aboriginal acknowledgment footer present (via branding.ts)
- [ ] Border radius uses `rounded-lg` for cards (12px base)

### A3. Performance
- [ ] No unnecessary re-renders (React DevTools check)
- [ ] React Query has appropriate staleTime (30s for records, 15s for progress)
- [ ] Large lists use virtualization (AG Grid handles this natively)
- [ ] Images use next/image with appropriate sizing

### A4. AI Slop Check
- [ ] No card-in-card nesting
- [ ] No uniform card grids without visual hierarchy
- [ ] No gradient text
- [ ] No glassmorphism effects
- [ ] No sparklines as decoration
- [ ] Design feels like Salesforce/Xero, not "AI made this"

---

## Recording Results

Add to the story's Dev Agent Record:

```markdown
### Design Review Checklist
- **Critical**: X/7 passed (list any failures)
- **Important**: X/6 passed
- **Advisory**: X/4 passed
- **Screenshots**: [paths to evidence at each breakpoint]
- **Dark mode verified**: Yes/No
- **Mobile card fallback**: Yes/No/N/A
```

If critical items fail, the story CANNOT be marked as complete.
Fix the failures, re-run the checklist, and update the record.
