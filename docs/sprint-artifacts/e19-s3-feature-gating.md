# Story E19-S3: Feature Gating — Standard vs. Admin User

**Epic:** E19 — Standard User UX Redesign
**Priority:** P0
**Status:** backlog
**Change Proposal:** SCP-20260224 (2026-02-24)
**Depends on:** E19-S1 (can be developed in parallel with E19-S2)

---

## User Story

**As a** standard compliance officer,
**I want to** see only the features I need (Jobs, Register, Chat),
**So that** I'm not confused by technical configuration options that aren't relevant to my workflow.

---

## Background

The current navigation exposes all features to all users: Extraction Monitor, AI Models, Knowledge Graph, Extraction Settings, BAR Field Schema, Processing Options. These are essential for power users and administrators but create cognitive overload for compliance officers who just need to upload, review, and export.

This story adds a simple user mode toggle (Standard / Admin) that hides the CONFIGURE section from standard users.

---

## Acceptance Criteria

### Navigation Gating
- [x] Sidebar CONFIGURE section hidden entirely for standard user mode
  - Hidden items: Extraction Settings, AI Models, Extraction Monitor, Knowledge Graph, BAR Field Schema
- [x] Sidebar WORKSPACE section shows only: Jobs, ACM Register, Chat
- [x] Admin/Power user mode shows all current navigation items (no regression)

### Mode Toggle
- [x] Simple toggle in sidebar footer: `[Standard] | [Admin]` — persisted to `localStorage`
- [x] Default mode: Standard (first visit or after clearing localStorage)
- [x] Switching to Admin mode: no confirmation required
- [x] Switching to Standard mode: shows brief toast "Configure features hidden. Switch to Admin to access them."

### No Server-Side Auth Required
- [x] This is a client-side UX simplification only — not an access control system
- [x] All API endpoints remain accessible regardless of mode (no backend gating)
- [x] Feature gating is purely nav-level: the pages still exist, they're just not linked from the sidebar

---

## Technical Notes

### Mode Store (Zustand)
```typescript
// frontend/src/stores/user-mode.ts
interface UserModeStore {
  mode: 'standard' | 'admin';
  setMode: (mode: 'standard' | 'admin') => void;
}
// Persist to localStorage key: 'acm-user-mode'
```

### Sidebar Changes
In `AppSidebar.tsx`, conditionally render CONFIGURE section:
```tsx
{mode === 'admin' && (
  <SidebarGroup label="CONFIGURE">
    {/* Extraction Settings, AI Models, Monitor, etc. */}
  </SidebarGroup>
)}
```

### No Breaking Changes
All existing configure pages remain accessible via direct URL. This is purely a nav visibility change.

---

## Key Files Created/Modified

| File | Change |
|------|--------|
| `frontend/src/stores/user-mode.ts` | **New** — Zustand user mode store with localStorage persistence |
| `frontend/src/components/layout/AppSidebar.tsx` | Modified — conditional CONFIGURE section + mode toggle in footer |

---

## Dev Notes

No API cost risk — purely frontend.

---

## Estimated Effort

XS (Extra Small) — One Zustand store + one conditional render in sidebar.

---

**Story Status:** ⬜ BACKLOG

---

## Dev Agent Record

**Implemented:** 2026-02-24
**Files changed:**
- `frontend/src/lib/stores/user-mode-store.ts` (new — Zustand user mode store, persisted to localStorage 'acm-user-mode')
- `frontend/src/components/layout/AppSidebar.tsx` (mode toggle UI in footer, Configure section hidden in standard mode)

**Tests added:** None (frontend-only, verified via build)
**Verification:** ruff ✓ | lint ✓ | build ✓
