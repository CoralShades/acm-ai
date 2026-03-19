# Dogfood Report: VAEA | ACM AI

| Field | Value |
|-------|-------|
| **Date** | 2026-03-16 |
| **App URL** | https://demo.vaea.coralshades.ai |
| **Session** | acm-demo |
| **Scope** | Full app walkthrough: navigation, pages, upload, chat, settings, console errors |

## Summary

| Severity | Count |
|----------|-------|
| Critical | 1 |
| High | 2 |
| Medium | 3 |
| Low | 2 |
| **Total** | **8** |

## Issues

### ISSUE-001: Settings > General returns 404

| Field | Value |
|-------|-------|
| **Severity** | high |
| **Category** | functional |
| **URL** | https://demo.vaea.coralshades.ai/settings/general |
| **Repro Video** | N/A |

**Description**

The Settings dropdown menu lists "General" as a navigation option, but clicking it navigates to `/settings/general` which returns a Next.js 404 error. The page does not exist in the deployed build. Either the page needs to be created or the menu item should be removed.

**Repro Steps**

1. Navigate to any page and click "Settings" in the sidebar footer to open the dropdown menu.
   ![Step 1](screenshots/04-settings.png)

2. Click "General" from the dropdown.

3. **Observe:** The page shows a Next.js 404 error: "This page could not be found."
   ![Result](screenshots/11-general.png)

---

### ISSUE-002: Sign Out locks users out when auth is disabled

| Field | Value |
|-------|-------|
| **Severity** | critical |
| **Category** | functional |
| **URL** | https://demo.vaea.coralshades.ai/login |
| **Repro Video** | N/A |

**Description**

The backend reports `auth_enabled: false` via `/api/auth/status`, meaning no password is required. However, clicking "Sign Out" in the Settings dropdown clears the frontend auth state and redirects to `/login`, which displays a password form. Users must guess that any password will work to regain access. On a publicly-accessible demo, this is a critical UX trap -- a user who clicks Sign Out will believe they are locked out.

The frontend should either: (a) hide the Sign Out button when auth is disabled, or (b) check `auth_enabled` on the login page and auto-redirect back if auth is not required.

**Repro Steps**

1. Navigate to any page and click "Settings" in the sidebar footer.
   ![Step 1](screenshots/04-settings.png)

2. Click "Sign Out" at the bottom of the dropdown.

3. **Observe:** The app redirects to `/login` showing a password prompt even though authentication is disabled on the backend.
   ![Result](screenshots/16-sign-out.png)

4. Entering any password (e.g., "test") and clicking "Sign In" successfully logs back in, confirming auth is not actually enforced.

---

### ISSUE-003: React Error #185 (maximum update depth) on multiple pages

| Field | Value |
|-------|-------|
| **Severity** | high |
| **Category** | console |
| **URL** | https://demo.vaea.coralshades.ai/jobs, https://demo.vaea.coralshades.ai/jobs/source:* (Content tab) |
| **Repro Video** | N/A |

**Description**

React error #185 ("Maximum update depth exceeded") appears in the browser console on the Jobs page and the job detail Content tab. This error fires 3 times per page load and indicates an infinite re-render loop in a React component -- likely a `useEffect` that updates state it depends on, or a state setter called unconditionally during render.

While the pages still render, this error degrades performance and could cause intermittent crashes or freezing on lower-powered devices.

**Repro Steps**

1. Navigate to `/jobs` when at least one job exists.
   ![Step 1](screenshots/32-jobs-with-data.png)

2. Open browser console (or use `agent-browser errors`).

3. **Observe:** Three instances of `Minified React error #185` are logged to the console.

4. Navigate to a job detail page and click the "Content" tab to see the same error.
   ![Result](screenshots/31-content-tab.png)

---

### ISSUE-004: Processing Settings page has slow initial load with spinner

| Field | Value |
|-------|-------|
| **Severity** | medium |
| **Category** | performance |
| **URL** | https://demo.vaea.coralshades.ai/settings/processing |
| **Repro Video** | N/A |

**Description**

The Processing Settings page (`/settings/processing`) shows only a loading spinner for 3-5 seconds before the content renders. Other settings pages (Extraction, AI Models, Field Schema) render almost immediately. This suggests the Processing page is making a blocking API call or has a heavy client-side computation during initial load.

**Repro Steps**

1. Navigate to Settings > Processing (or directly to `/settings/processing`).

2. **Observe:** A loading spinner is displayed for several seconds before the page content appears.
   ![Step 1](screenshots/10-processing.png)

3. After the wait, the page eventually loads with Presets and Processing Parameters.
   ![Step 2](screenshots/10b-processing-after-wait.png)

---

### ISSUE-005: Command Palette "Sources" label is misleading

| Field | Value |
|-------|-------|
| **Severity** | low |
| **Category** | ux |
| **URL** | https://demo.vaea.coralshades.ai (Ctrl+K command palette) |
| **Repro Video** | N/A |

**Description**

The Command Palette (Ctrl+K) lists "Sources" as the first navigation option. Clicking it navigates to `/jobs`. In the current ACM-focused product, the concept of "Sources" has been replaced by "Jobs" in the UI. The Command Palette should use the label "Jobs" instead of "Sources" to match the sidebar navigation and page headings.

Additionally, the Command Palette shows duplicate "Upload Document" entries (one under Navigation, one under Actions).

**Repro Steps**

1. Press Ctrl+K to open the Command Palette on any page.
   ![Step 1](screenshots/14-command-palette.png)

2. Click "Sources" (the first option).

3. **Observe:** The app navigates to `/jobs` -- the label says "Sources" but the destination is the Jobs page.
   ![Result](screenshots/23-sources.png)

---

### ISSUE-006: Notebooks page accessible but not discoverable

| Field | Value |
|-------|-------|
| **Severity** | medium |
| **Category** | ux |
| **URL** | https://demo.vaea.coralshades.ai/notebooks |
| **Repro Video** | N/A |

**Description**

The `/notebooks` page still exists and renders a full Notebooks UI with "New Notebook" and "Search notebooks..." functionality. However, it is not linked from the sidebar, dashboard, or any visible navigation. This is legacy functionality from the Open Notebook base that was not removed during the ACM pivot.

On first visit (before any cookies are set), the root URL briefly showed the Notebooks page before subsequent visits showed the Dashboard. This suggests a race condition in the root page routing.

The presence of an orphaned page with create/search functionality could confuse users who discover it via URL guessing or browser history.

**Repro Steps**

1. Navigate directly to `/notebooks`.
   ![Step 1](screenshots/27-notebooks.png)

2. **Observe:** A full Notebooks page renders with "New Notebook" button and search -- but there is no sidebar link to reach this page.

---

### ISSUE-007: Content tab shows "No uploaded PDF available" for uploaded document

| Field | Value |
|-------|-------|
| **Severity** | medium |
| **Category** | functional |
| **URL** | https://demo.vaea.coralshades.ai/jobs/source:dco6ld86nscbktalnnbv (Content tab) |
| **Repro Video** | N/A |

**Description**

On the job detail page for "Boradmeadows.pdf", the Content tab shows "No uploaded PDF available" even though the document was successfully uploaded (it appears in the Dashboard documents table and has an active extraction job). This suggests the PDF file was either not persisted to storage, or the Content tab is looking for the file in the wrong location.

The expected behavior is to show the PDF content (or at least the extracted text/markdown) for the uploaded document.

**Repro Steps**

1. Navigate to the job detail page for Boradmeadows.pdf.
   ![Step 1](screenshots/29-source-detail.png)

2. Click the "Content" tab.

3. **Observe:** The tab shows "No uploaded PDF available" and "No extracted content available yet."
   ![Result](screenshots/31-content-tab.png)

---

### ISSUE-008: Dark theme Upload Document sidebar button loses visibility

| Field | Value |
|-------|-------|
| **Severity** | low |
| **Category** | visual |
| **URL** | https://demo.vaea.coralshades.ai (dark theme) |
| **Repro Video** | N/A |

**Description**

When switching to dark theme via the Command Palette or Settings > Theme, the "Upload Document" button in the sidebar changes from a solid teal/green background (light theme) to a transparent/outline style. While still functional, the button loses its visual prominence as the primary call-to-action. The border-only styling makes it blend into the sidebar background.

**Repro Steps**

1. Open the Command Palette (Ctrl+K) and select "Dark Theme".

2. **Observe:** The sidebar "Upload Document" button changes from a solid fill to an outline style, reducing its visual weight.
   ![Result](screenshots/24-dark-theme.png)

---

## Pages Tested

| Page | Route | Status | Console Errors |
|------|-------|--------|---------------|
| Dashboard (Home) | `/` | OK | None |
| Jobs | `/jobs` | OK | React #185 (x3) |
| Job Detail (Overview) | `/jobs/source:*` | OK | None |
| Job Detail (Buildings) | `/jobs/source:*` (tab) | OK | None |
| Job Detail (ACM Records) | `/jobs/source:*` (tab) | OK | None |
| Job Detail (Content) | `/jobs/source:*` (tab) | Partial | React #185 (x3) |
| Source Detail | `/source/[id]` | OK | None |
| Source Raw Tables | `/source/[id]/raw` | OK | None |
| Upload Dialog (Quick) | Dialog overlay | OK | None |
| Upload Wizard (Full) | `/upload` | OK | None |
| Extraction Monitor | `/settings/extraction-monitor` | OK | None |
| Extraction Settings | `/settings/extraction` | OK | None |
| AI Models | `/settings/models` | OK | None |
| Parsers | `/settings/parsers` | OK (placeholder) | None |
| Field Schema | `/settings/field-schema` | OK | None |
| Processing | `/settings/processing` | Slow load | None |
| General | `/settings/general` | **404** | N/A |
| Ask and Search | `/ask` | OK | None |
| Settings (Legacy) | `/settings` | OK | None |
| Login | `/login` | OK | None |
| Notebooks (Legacy) | `/notebooks` | OK (orphaned) | None |
| Command Palette | Ctrl+K overlay | OK | None |
| CRUD Chat Panel | Side panel | OK | None |
| Dark Theme | All pages | OK | None |

## Positive Findings

- **No CORS errors detected** across any page -- the Vercel same-origin proxy is working correctly.
- **No API timeouts** observed during the session.
- **Empty states are well-designed** -- Dashboard, Jobs, Buildings, ACM Records all show helpful empty state messages with appropriate CTAs.
- **Upload flows are polished** -- both Quick Upload dialog and Full Wizard render correctly with clear instructions.
- **CRUD Chat panel works** -- CopilotKit integration renders properly with model selector, message input, and action buttons.
- **Command Palette (Ctrl+K)** is functional with comprehensive navigation and action options.
- **Theme switching** works correctly via Command Palette.
- **Job progress tracking** shows real-time extraction status with stage indicators.
- **Breadcrumb navigation** on job detail pages is clear and functional.
