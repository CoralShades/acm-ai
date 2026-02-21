# Story E16-S3: Empty States & Onboarding Hints

**Epic:** E16 — UX Enhancement Sprint
**Priority:** P1
**Status:** done
**Change Proposal:** SCP-20260220 (2026-02-20)

---

## User Story

**As a** new user opening ACM-AI for the first time,
**I want to** see helpful guidance when there are no documents or records,
**So that** I know what to do next and the app doesn't feel broken.

---

## Background

Currently blank/empty views show empty grids with no guidance. E14-S4 added skeleton loading screens but these only appear while loading — not for genuinely empty states. This story adds proper empty states for all key views plus one-time dismissable onboarding hints.

---

## Acceptance Criteria

### Empty States

#### Documents Page (no sources uploaded)
- [ ] When source list is empty: show centered empty state card
- [ ] Content: Simple icon (document/upload SVG) + "No SAMP documents yet" heading + "Upload your first SAMP to get started" body + "Upload SAMP" primary button → opens upload wizard

#### ACM Register (no records extracted)
- [ ] When `acm_record` count is 0: show centered empty state
- [ ] Content: Table/data icon + "No ACM records yet" + "Upload and extract a SAMP document to populate the register" body + "Go to Documents" link

#### Chat (no sources with ACM context)
- [ ] When entering chat with no ACM-enabled source: show inline hint card
- [ ] Content: "Add ACM context to get started — open a SAMP document and enable ACM mode" with link to Documents

#### Extraction Monitor (no extractions)
- [ ] When history list is empty: "No extraction history found" + "Upload a SAMP document to start"
- [ ] When active list is empty: "No extractions currently running"

### Design Consistency
- [ ] All empty states use the same card style: `bg-muted/30 rounded-xl border border-dashed border-muted-foreground/20 p-8 text-center`
- [ ] Icons are simple inline SVG (no external image files)
- [ ] Text uses muted foreground colour for body text
- [ ] CTA buttons use existing button components from design system

### Onboarding Hints (dismissable)

#### Documents Page — first visit only
- [ ] Callout banner above document list: "Drag and drop a PDF or use the Upload button to add a SAMP document"
- [ ] Close (×) button dismisses permanently via `localStorage.setItem('acm-hint-documents', 'dismissed')`
- [ ] Only shown if `localStorage.getItem('acm-hint-documents')` is null

#### ACM Register — first visit only
- [ ] Callout banner above grid: "Use the column visibility button to show/hide fields. Click any row for full record details."
- [ ] Dismissed via `localStorage.setItem('acm-hint-acm-register', 'dismissed')`

#### General hint rules
- [ ] Hints never re-appear after dismissal (localStorage key set)
- [ ] Hints do NOT appear when empty state is showing (only when content exists)
- [ ] Accessible: dismiss button has `aria-label="Dismiss hint"`

---

## Technical Notes

### Empty State Detection
- Documents: check `sources.length === 0` after loading completes (not during skeleton state)
- ACM Register: check `acmRecords.length === 0` after loading
- Guards: only show empty state when `isLoading === false` and data is confirmed empty

### Reusable Component
Create a shared `EmptyState` component:
```tsx
<EmptyState
  icon={<UploadIcon />}
  heading="No SAMP documents yet"
  body="Upload your first SAMP to get started"
  action={{ label: "Upload SAMP", onClick: openWizard }}
/>
```

### Onboarding Hint Component
Create a shared `OnboardingHint` component:
```tsx
<OnboardingHint id="documents" message="Drag and drop a PDF..." />
```
Reads/writes `localStorage.getItem('acm-hint-{id}')` internally.

---

## Key Files to Create/Modify

| File | Change |
|------|--------|
| `frontend/src/components/common/EmptyState.tsx` | New shared empty state component |
| `frontend/src/components/common/OnboardingHint.tsx` | New dismissable hint component |
| `frontend/src/components/documents/DocumentList.tsx` | Add empty state |
| `frontend/src/components/acm/ACMSpreadsheet.tsx` | Add empty state + hint |
| `frontend/src/components/chat/ChatView.tsx` | Add empty state |
| `frontend/src/components/extraction/ExtractionMonitorPage.tsx` | Add empty states (both tabs) |

---

## Dependencies

- **Requires:** E9-S1 (done ✓), E2-S2 (done ✓), E4-S1 (done ✓)
- **Blocks:** nothing

---

## Estimated Effort

S (Small) — Mostly new UI components with no backend work. Straightforward implementation.

## Dev Agent Record
- **Completed:** 2026-02-22
- **Commit:** 29cb783
- **Build Status:** PASS
- **Implementation:** Ralph sprint batch implementation
