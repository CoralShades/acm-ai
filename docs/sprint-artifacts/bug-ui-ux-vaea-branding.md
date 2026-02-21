# Bug Fix: UI/UX Polish + VAEA Branding

Status: done

## Story

As a **VAEA stakeholder**,
I want **the application branded as "VAEA | ACM AI" with minor UI polish fixes**,
so that **the product reflects the VAEA brand identity and has improved usability**.

## Acceptance Criteria

1. Application name displays as "VAEA | ACM AI" in header, manifest, and title
2. Command palette dropdown height increased for better discoverability
3. Source detail TabsList is scrollable on narrow screens (overflow-x-auto)
4. Web manifest updated with VAEA branding
5. No regressions in existing UI

## Tasks / Subtasks

- [x] Task 1: Update branding config (AC: #1)
  - [x] 1.1 `branding.ts:16` — `name: 'ACM-AI'` → `name: 'VAEA | ACM AI'`
- [x] Task 2: Update web manifest (AC: #4)
  - [x] 2.1 `manifest.json` — Update `name` and `short_name`
- [x] Task 3: Increase command palette height (AC: #2)
  - [x] 3.1 `command.tsx:93` — `max-h-[300px]` → `max-h-[min(400px,60vh)]`
- [x] Task 4: Fix TabsList overflow (AC: #3)
  - [x] 4.1 `sources/[id]/page.tsx:343` — Add `overflow-x-auto` to BentoCardHeader
- [x] Task 5: Build verification (AC: #5)
  - [x] 5.1 Frontend build passes

## Dev Notes

### Favicon Conversion — DEFERRED

The plan included converting `docs/vaea-assets/VAEA_Ripple2_FavIcon_0.png` to multiple icon formats (logo.png, icon.png, icon.svg, favicon.ico). This was deferred because image processing tools were not available in the CLI environment. Should be done manually or with a design tool.

### Files Changed

| File | Action | Purpose |
|------|--------|---------|
| `frontend/src/config/branding.ts` | MODIFY | App name → "VAEA | ACM AI" |
| `frontend/public/manifest.json` | MODIFY | PWA manifest branding |
| `frontend/src/components/ui/command.tsx` | MODIFY | Command palette height |
| `frontend/src/app/(dashboard)/sources/[id]/page.tsx` | MODIFY | TabsList overflow scroll |

## Dev Agent Record

### Agent Model Used
Claude Opus 4.6

### Completion Notes List
- Part of Bug Triage Plan Phase 1 (Quick Wins)
- Favicon conversion deferred (needs image processing tools)
- Maps to original bug #11 from triage

### File List
- frontend/src/config/branding.ts (line 16)
- frontend/public/manifest.json (name, short_name)
- frontend/src/components/ui/command.tsx (line 93)
- frontend/src/app/(dashboard)/sources/[id]/page.tsx (line 343)
