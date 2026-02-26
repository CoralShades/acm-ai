You are implementing E22-S2: Dashboard Layout Regression Fix.
You are Amelia (Developer). This is a frontend-only fix.

## MANDATORY PRE-READ — Read ALL before writing ANY code

### Your story:
- docs/sprint-artifacts/e22-s2-dashboard-layout-fix.md

### Layout files (THE CODE YOU'RE INVESTIGATING):
- frontend/src/app/(dashboard)/layout.tsx — the dashboard layout wrapper
- frontend/src/app/(dashboard)/page.tsx — dashboard page component
- frontend/src/app/layout.tsx — root layout
- frontend/src/components/layout/AppSidebar.tsx — sidebar component

### Working pages for comparison (DO they have sidebar?):
- frontend/src/app/(dashboard)/jobs/page.tsx
- frontend/src/app/(dashboard)/acm/page.tsx

### Loading files that may have broken layout:
- Check if frontend/src/app/(dashboard)/loading.tsx exists
- Check if frontend/src/app/(dashboard)/jobs/loading.tsx exists

### Sidebar design spec:
- docs/sprint-artifacts/tech-spec-e14-s2-sidebar-navigation.md

## THE BUG

The dashboard at localhost:8502/ (or :8503/) shows stats cards and content
but NO sidebar, NO header/navigation bar, NO footer. This was broken BEFORE
Phase 6+7 — it's a pre-existing regression.

Other pages (Jobs, ACM Register, Settings) DO show the sidebar correctly.
This means the (dashboard) layout.tsx wrapper works for child routes but
something is wrong specifically for the root page.

## INVESTIGATION STEPS

1. Check if `(dashboard)/page.tsx` is inside the route group:
   - Is it at `frontend/src/app/(dashboard)/page.tsx`?
   - Or is it at `frontend/src/app/page.tsx` (OUTSIDE the group)?
   - If outside: the dashboard bypasses the (dashboard)/layout.tsx entirely

2. Check the (dashboard)/layout.tsx:
   - Does it render `<AppSidebar>` + `<main>{children}</main>`?
   - Is there a conditional that hides sidebar based on pathname?

3. Check middleware.ts:
   - Does it redirect `/` somewhere that bypasses the layout?

4. Check if any loading.tsx file at the dashboard level breaks the wrapper:
   - If `(dashboard)/loading.tsx` exists and doesn't include the layout chrome, 
     it would show a bare page during Suspense

5. Check for CSS issues:
   - Is the sidebar z-index or position causing it to be hidden?
   - Is overflow:hidden on a parent clipping the sidebar?

## FIX APPROACH

Based on investigation, apply the appropriate fix:

**If page.tsx is outside (dashboard) group:**
Move it inside, or create a redirect from root to the dashboard route.

**If layout.tsx has a conditional hiding sidebar on `/`:**
Remove the conditional — dashboard should always show sidebar.

**If loading.tsx breaks the layout:**
Ensure loading.tsx files only replace the `{children}` area, not the entire
page chrome. The layout wrapper (sidebar + header) should persist during loading.

**If it's a CSS issue:**
Fix the positioning/overflow so sidebar is visible on all routes.

## ALSO CHECK

After fixing the dashboard:
1. Navigate to every page in sidebar — does sidebar persist?
   - Dashboard, Jobs, ACM Register, Search, Settings pages
2. Check dark mode — does sidebar render in both themes?
3. Check that the "Upload Document" button in sidebar works
4. Check that the Standard/Admin toggle at bottom of sidebar works

## VERIFICATION

```bash
cd frontend
npm run build    # MUST pass
npm run lint     # MUST pass
```

Then manually verify:
- localhost:8502/ shows sidebar + stats + content
- Click every sidebar link — sidebar persists
- No console errors on dashboard page

## UPDATE BMAD ARTIFACTS

Update docs/sprint-artifacts/sprint-status.yaml:
```yaml
e22-s2-dashboard-layout-fix: done  # 2026-02-26: [describe what was wrong and how fixed]
```

## GIT COMMIT

```bash
git add frontend/ docs/
git commit -m "fix(e22-s2): dashboard layout — restore sidebar/header/footer

[describe the root cause and fix]"
```

## GUARD RAILS
- Do NOT modify Python files
- Do NOT modify the sidebar component's navigation structure
- Do NOT modify other pages that are working correctly
- Do NOT install new npm packages
- FOCUS: find why dashboard specifically doesn't have sidebar, fix it
