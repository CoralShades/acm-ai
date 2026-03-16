# CopilotKit UI/UX Code Audit

**Date:** 2026-03-16
**Auditor:** Frontend Specialist
**Scope:** All CopilotKit chat components — renderers, panels, providers

---

## Summary

- **Components audited:** 15
- **Issues found:** 31 (6 critical, 13 important, 12 minor)

### Files Audited

| File | Status |
|------|--------|
| `renderers/HITLApprovalDialog.tsx` | Issues found |
| `renderers/WriteDiffView.tsx` | Issues found |
| `renderers/BuildingSummaryCard.tsx` | Issues found |
| `renderers/ItemDetailCard.tsx` | Issues found |
| `renderers/ExtractionProgress.tsx` | Issues found |
| `renderers/DefaultToolFallback.tsx` | Issues found |
| `renderers/ToolErrorCard.tsx` | PASS |
| `renderers/ACMTableResult.tsx` | Issues found |
| `renderers/ACMStatsResult.tsx` | Issues found |
| `renderers/AgentActivityIndicator.tsx` | Issues found |
| `chat/SmartChatPanel.tsx` | Issues found |
| `jobs/JobCrudChatPanel.tsx` | Issues found |
| `jobs/CrudToolRenderers.tsx` | Issues found |
| `chat/ToolResultRenderers.tsx` | Issues found |
| `providers/CopilotProvider.tsx` | PASS |

---

## Per-Component Findings

---

### HITLApprovalDialog.tsx

- [x] **/uncodixfy:** PASS — no gratuitous gradients or glass effects. Amber warning pattern is purposeful and appropriate for a destructive action gate.
- [x] **Dark mode:** PARTIAL FAIL — line 44: `<code className="bg-white dark:bg-gray-800 ...">` uses raw `gray-800` instead of `bg-muted` / `bg-muted-foreground` tokens. Line 71: input uses `bg-white dark:bg-gray-800` — same issue. Neither maps to the VAEA teal dark palette defined in `globals.css`.
- [x] **Responsive:** PASS — layout works in narrow containers. `flex-wrap` is present on value row.
- [x] **Accessibility:** FAIL

**Issues:**

1. **[CRITICAL A1] Missing `aria-label` on the pencil edit button (line 54–61).** The button has no text content — only an icon — and no `aria-label` or `title` accessible to screen readers. While `title` is present (line 57), `title` attributes are not reliably exposed to screen readers. Replace with `aria-label="Edit value before approving"`.

2. **[IMPORTANT A2] Approve/Reject buttons have no `focus-visible` ring in their inline Tailwind classes.** The global CSS at `globals.css:692` provides a universal `button:focus-visible` rule, so this is partially mitigated — but the green Approve button uses `bg-green-600` which is a hardcoded Tailwind color, not a CSS variable token. The design system has `--risk-low` and `--risk-high` tokens but no "confirm/success" action token. Recommend using `bg-primary` or adding a `--color-action-confirm` token, or at minimum keeping `bg-green-600` explicitly documented as intentional.

3. **[MINOR A3] `onApprove`/`onReject` do not disable the buttons during an in-progress state.** If the user double-clicks Approve, both calls fire. Add a `submitting` state and disable after first click.

4. **[MINOR A4] `editedValue` state initializes from `preview.new_value` at render time (line 28) but `new_value` is from a prop.** If the parent re-renders with a new `preview.new_value`, the edited value silently diverges. Add a `useEffect` to sync `editedValue` when `preview.new_value` changes.

5. **[MINOR A5] Hardcoded `bg-white` / `dark:bg-gray-800` (lines 44, 71).** Should use `bg-background` / `bg-muted` to respect the VAEA dark teal background (`--background: oklch(0.175 0.025 170)` in dark mode). `gray-800` resolves to `#1f2937`, which clashes with the dark teal theme.

---

### WriteDiffView.tsx

- [x] **/uncodixfy:** PASS — minimal, functional diff presentation.
- [x] **Dark mode:** PASS — both red and green variants include `dark:` prefixes.
- [x] **Responsive:** PASS — `flex-wrap` on value row handles overflow.
- [x] **Accessibility:** FAIL

**Issues:**

6. **[IMPORTANT B1] No semantic role or ARIA labeling on the diff container.** When rendered inside a chat message, screen readers receive no context that this represents a field change. The container `div` (line 11) should carry `role="region"` and `aria-label="Field change: {field}"`.

7. **[MINOR B2] The arrow `→` at line 22 is a raw Unicode character with no `aria-hidden`.** Screen readers will announce "right arrow" mid-sentence. Wrap with `<span aria-hidden="true">→</span>`.

8. **[MINOR B3] The "Field Change" label (line 12) uses `text-xs font-medium text-muted-foreground` — visually de-emphasized but semantically ambiguous.** Promote to a semantic `<dt>` or at minimum ensure it's a structural heading for the diff group.

---

### BuildingSummaryCard.tsx

- [x] **/uncodixfy:** PASS — clean, icon usage is purposeful (Building2, AlertTriangle, FileText each map to a specific datum).
- [x] **Dark mode:** PASS — relies on semantic tokens (`text-primary`, `text-muted-foreground`, `text-amber-600 dark:text-amber-400`).
- [x] **Responsive:** PASS — `min-w-0` + `truncate` on building name prevents overflow. `shrink-0` on icon is correct.
- [x] **Accessibility:** FAIL

**Issues:**

9. **[IMPORTANT C1] The entire card is display-only with no interactive affordance, but it contains data that users may want to act on.** No `role` or `aria-label` is defined. If these cards are standalone messages in a chat thread, add `role="article"` and `aria-label="Building: {building_name}"` so screen readers can navigate between them.

10. **[MINOR C2] `high_risk_count` is only shown when `> 0` but `record_count` shows as `0 records` when zero.** Inconsistent nil-handling logic. Either both show zero or neither does. Currently misleads: a building card with 0 records and no risk badge looks identical to a card that simply never received data.

---

### ItemDetailCard.tsx

- [x] **/uncodixfy:** PASS — the expand/collapse pattern for extra fields is a genuine UX economy, not decoration.
- [x] **Dark mode:** PASS — `RISK_COLORS` map includes `dark:` variants for all three levels. Fallback at line 35 uses `dark:bg-gray-800 dark:text-gray-400` — same gray token problem as HITLApprovalDialog (should be `dark:bg-muted dark:text-muted-foreground`).
- [x] **Responsive:** PASS — `grid-cols-2` works in narrow chat panels. `min-w-0 flex-1 truncate` correctly prevents overflow on product name.
- [x] **Accessibility:** FAIL

**Issues:**

11. **[CRITICAL D1] Expand/collapse button (line 90–97) has no `aria-expanded` attribute.** A screen reader user cannot determine whether additional fields are visible. Add `aria-expanded={expanded}` and `aria-controls` pointing to the expanded panel's `id`.

12. **[IMPORTANT D2] The `extraFields` list at line 100–107 renders raw field key names as labels (e.g., `material_description`, `sample_result`).** These are snake_case database field names, not human-readable labels. In a chat context especially, users should see "Material Description" not `material_description`. Add a `humanizeKey()` utility or a `FIELD_LABELS` map.

13. **[MINOR D3] `String(val)` at line 104 will render `[object Object]` for nested objects.** If an unexpected object lands in `extraFields` via the `[key: string]: unknown` index signature, the output is unreadable. Use `typeof val === 'object' ? JSON.stringify(val) : String(val)`.

---

### ExtractionProgress.tsx

- [x] **/uncodixfy:** FAIL — line 26: `text-blue-600` on the spinner icon and line 43: `bg-blue-600` on the progress bar are hardcoded blue values from the generic AI stereotype palette. The project's primary/accent is VAEA teal (`--primary`). These should be `text-primary` and `bg-primary`.
- [x] **Dark mode:** PARTIAL FAIL — `text-blue-600` has no dark variant. The progress bar fill `bg-blue-600` has no dark variant. The track uses `dark:bg-gray-700` (correct token-missing issue, should be `dark:bg-muted`). `text-green-600` for the check icon has no dark variant.
- [x] **Responsive:** PASS — single-column layout works at any width.
- [x] **Accessibility:** FAIL

**Issues:**

14. **[CRITICAL E1] `text-blue-600` (lines 26, 43) conflicts with the VAEA brand palette.** Every other component in the renderer suite uses `text-primary` for the active/loading state color. This is the only exception and visually inconsistent.

15. **[IMPORTANT E2] `text-green-600` on `CheckCircle2` (line 24) has no `dark:` variant.** In dark mode the green-600 on a dark teal background has low contrast. Should be `text-green-600 dark:text-green-400` to match the pattern used in `ItemDetailCard` and `AgentActivityIndicator`.

16. **[IMPORTANT E3] Progress bar uses an inline style (`style={{ width: ... }}`) at line 43.** This is the one inline style in the entire codebase outside of dynamic values. The clamping logic `Math.min(100, Math.max(0, progress))` is correct, but this is the only pattern divergence — everything else uses Tailwind. Since dynamic width genuinely requires inline style, add a comment: `// dynamic width — cannot use Tailwind class`.

17. **[MINOR E4] `dark:bg-gray-700` at line 40 (progress track).** Should be `dark:bg-muted` to respect the dark teal design tokens. `gray-700` is `#374151`, which clashes with the dark background `oklch(0.175 0.025 170)`.

18. **[MINOR E5] No `prefers-reduced-motion` consideration for the progress bar transition.** The global CSS at `globals.css:775` disables transitions under `prefers-reduced-motion`, but the `transition-all duration-300` on the progress bar element means it will still apply before the media query fires. This is handled globally, but it is worth noting.

---

### DefaultToolFallback.tsx

- [x] **/uncodixfy:** PASS — minimal, purposeful. Using `Wrench` inline within the span text (line 30–31) is slightly unusual but not egregious.
- [x] **Dark mode:** PARTIAL FAIL — `text-blue-600` on Loader2 (line 23) and `text-green-600` on CheckCircle2 (line 25) have no `dark:` variants. Matches the ExtractionProgress issue.
- [x] **Responsive:** PASS — `max-h-32 overflow-auto` on the result pre-block prevents layout breaking.
- [x] **Accessibility:** FAIL

**Issues:**

19. **[IMPORTANT F1] Icon inside `<span>` at lines 29–31:** `<span className="font-medium text-xs"><Wrench className="h-3 w-3 inline mr-1" />{name}</span>`. This creates an icon that renders before visually-structured text, making the DOM read as: status-icon + wrench-icon + tool-name. The double icon pattern is visual noise. The status icon (Loader2/CheckCircle2/AlertCircle) already communicates state. The Wrench should be removed or moved to a consistent heading slot.

20. **[IMPORTANT F2] `text-blue-600` / `text-green-600` without dark variants** — same as E1/E2. Use `text-primary` for loading and `text-green-600 dark:text-green-400` for complete.

21. **[MINOR F3] `bg-muted/20` on the container.** Other tool result containers use `bg-muted/30` or `bg-muted/50`. This creates a subtle but inconsistent feel across the tool result palette. Standardize to `bg-muted/30`.

---

### ToolErrorCard.tsx

- [x] **/uncodixfy:** PASS
- [x] **Dark mode:** PASS — uses `text-destructive` and `bg-destructive/10` which are CSS variable-backed.
- [x] **Responsive:** PASS
- [x] **Accessibility:** PASS

No issues. This is the best-written component in the suite — concise, uses semantic tokens, and the copy ("Try rephrasing your request.") is genuinely helpful.

---

### ACMTableResult.tsx

- [x] **/uncodixfy:** PASS — functional table, appropriate density for a chat context.
- [x] **Dark mode:** PASS — uses semantic tokens throughout. Risk color classes use `bg-risk-*` CSS variable tokens.
- [x] **Responsive:** FAIL — see G1.
- [x] **Accessibility:** FAIL — see G2, G3.

**Issues:**

22. **[CRITICAL G1] No horizontal scroll container for narrow chat panels.** Line 62: `<div className="overflow-x-auto">` wraps the table, which is correct in principle. However, the table has 5 fixed columns (Building, Room, Product, Risk, Result) with a `max-w-[150px] truncate` only on the Product column (line 90). In a 300-350px chat panel, Building + Room + Risk + Result columns will each be ~50–60px, causing the Product truncation to be irrelevant while the other columns squeeze to unreadable widths. Either: (a) reduce to 3 columns for chat context (Building, Product, Risk) with a "show more" affordance, or (b) set `min-width` on the table itself (e.g., `min-w-[480px]`) so horizontal scroll actually activates.

23. **[IMPORTANT G2] Clickable rows (lines 75–105) have no keyboard navigation.** Each `<tr>` has an `onClick` but no `tabIndex`, `onKeyDown`, or `role="button"`. Keyboard users cannot activate row clicks. Add `tabIndex={0}` and `onKeyDown={(e) => e.key === 'Enter' && openModal(...)}`.

24. **[IMPORTANT G3] No `<caption>` element on the table.** Screen readers announce tables without captions with no context. Add `<caption className="sr-only">ACM records — {queryType} query, {records.length} of {total} results</caption>`.

25. **[MINOR G4] `getRiskBadgeVariant` function (lines 12–23) is defined but not meaningfully used** — it always gets overridden by `className={getRiskColorClass(...)}` (line 96). The `variant` prop on Badge sets base styles that `className` then overrides. The function adds code weight with no visual output. Remove it and use only `getRiskColorClass`.

---

### ACMStatsResult.tsx

- [x] **/uncodixfy:** FAIL — see H1.
- [x] **Dark mode:** PASS — uses `bg-risk-*` semantic tokens.
- [x] **Responsive:** FAIL — see H2.
- [x] **Accessibility:** FAIL — see H3.

**Issues:**

26. **[IMPORTANT H1] Dual-mode component (stats view vs. building list) in a single component.** Lines 18–39 check `data.buildings` and render an entirely different layout if truthy. This is the same component serving two unrelated data shapes, which violates single-responsibility. The buildings list path (lines 20–38) should be a separate `BuildingListResult` component. The current design is an `/uncodixfy` warning: a generic "if it has this key, render differently" pattern is fragile and difficult to debug.

27. **[IMPORTANT H2] Stats grid `grid-cols-3` (line 47) at `text-[10px]` sub-captions.** `text-[10px]` (10px rendered) is below the WCAG recommended minimum of 12px for body text. In a narrow chat panel this is potentially unreadable. Replace `text-[10px]` with `text-xs` (12px).

28. **[MINOR H3] Stat numbers use `text-lg font-bold` (line 49, 53, 59) but those spans also contain icons inside the number display (lines 53–55, 59–61).** The icon inside the metric number creates an odd layout: "Building2-icon + number" side by side in a `flex items-center justify-center` container. The icon appears to be part of the number value visually. Icons should be placed below or above the number as a label, not inline with it.

---

### AgentActivityIndicator.tsx

- [x] **/uncodixfy:** PASS — appropriately minimal inline activity indicator.
- [x] **Dark mode:** PARTIAL FAIL — `text-green-500` (line 33) on the CheckCircle2 has no dark variant. Should be `text-green-500 dark:text-green-400`.
- [x] **Responsive:** PASS
- [x] **Accessibility:** FAIL

**Issues:**

29. **[IMPORTANT I1] The "done" label transform at line 35** (`label.replace('...', ' - done')`) is fragile. If any TOOL_LABELS value does not end with `...`, the replacement silently produces the original string appended with nothing. Example: if a future entry is `'Running bulk extraction'` (no trailing `...`), the complete state reads identically to the in-progress state. Use explicit done labels or a secondary map.

30. **[MINOR I2] No `role="status"` or `aria-live` on this indicator.** When the agent starts a tool call, this element appears in the DOM. For screen readers, dynamic content insertions are not announced unless the container has `aria-live="polite"`. Add `role="status" aria-live="polite"` to the wrapper div.

---

### SmartChatPanel.tsx

- [x] **/uncodixfy:** PASS — no decorative excess. The panel is a clean integration wrapper.
- [x] **Dark mode:** PASS — uses `bg-primary/10 text-primary` (token-backed).
- [x] **Responsive:** PASS
- [x] **Accessibility:** FAIL

**Issues:**

31. **[IMPORTANT J1] Duplicate ACM toggle UI.** The panel renders two separate ACM toggle affordances: a banner (lines 79–84) showing "ACM Register data included in context" AND a Badge toggle (lines 118–129) labeled "ACM Data ON/OFF". Both are visible simultaneously when `hasAcmData && includeAcmContext`. This is redundant — the banner is read-only status, the badge is interactive. The banner should either be removed (the badge already communicates status through its `variant`) or the badge should be removed in favor of a more prominent toggle. As-is, users see two related but different controls and may not understand the relationship.

32. **[IMPORTANT J2] The `Badge` component (lines 120–128) is used as an interactive control with `onClick` and `cursor-pointer`.** `Badge` is a display component in shadcn/ui, not an interactive element. It renders as a `<div>` or `<span>` depending on implementation — not a `<button>`. This means: no keyboard activation (Enter/Space), no focus ring from the design system's button rule, and `role="button"` is absent. Replace with an actual `<button>` styled to look like a badge, or use a `Toggle` / `ToggleButton` component.

33. **[MINOR J3] The `useCoAgentStateRender` render callback (lines 55–68) embeds a hardcoded `bg-blue-500` color on the pulse indicator dot (line 62).** Again, blue is out-of-theme. Replace with `bg-primary`.

---

### JobCrudChatPanel.tsx

- [x] **/uncodixfy:** PASS — thin wrapper, nothing to flag.
- [x] **Dark mode:** N/A (no visual elements — delegates to CopilotChat)
- [x] **Responsive:** PASS
- [x] **Accessibility:** PASS (delegates to CopilotKit's own accessibility)

**Issues:**

34. **[MINOR K1] The `makeSystemMessage` function (lines 28–35) contains multi-line string concatenation with a hardcoded instruction: "Present a preview_write JSON payload and wait for the user to confirm by replying with 'confirm \<operation_id\>'"**. This instruction describes a text-based confirmation flow that has been superseded by the HITL interrupt pattern in `CrudToolRenderers`. If the CRUD agent is wired to the interrupt-based flow, this prompt instruction is stale and may confuse the agent. Remove the `confirm <operation_id>` instruction or update it to reflect the interrupt-based approval mechanism.

---

### CrudToolRenderers.tsx

- [x] **/uncodixfy:** PASS — clean hook-based composition.
- [x] **Dark mode:** PASS — the write success message (lines 88–91) uses `text-green-700 dark:text-green-400 bg-green-50 dark:bg-green-900/20`. Correct pattern.
- [x] **Responsive:** PASS
- [x] **Accessibility:** PASS

**Issues:**

35. **[MINOR L1] `void sourceId` at line 95.** This is a lint suppression smell. The prop is declared in the interface and passed by the parent but never used in the component body. If `sourceId` is needed for future use, document that explicitly. If not, remove it from the props interface. `void expr` to silence an "unused variable" warning in a function component is non-idiomatic — use `_sourceId` naming convention instead, consistent with `_args` on line 15 of `DefaultToolFallback.tsx`.

---

### ToolResultRenderers.tsx

- [x] **/uncodixfy:** PASS — repetitive hook registration is unavoidable given CopilotKit's API design.
- [x] **Dark mode:** PASS — delegates to renderer components.
- [x] **Responsive:** PASS
- [x] **Accessibility:** N/A (registration-only component)

**Issues:**

36. **[IMPORTANT M1] `isErrorResult` function is duplicated verbatim in both `ToolResultRenderers.tsx` (lines 35–42) and `CrudToolRenderers.tsx` (lines 11–22).** The implementations are slightly different (`CrudToolRenderers` only tries JSON parse for strings, `ToolResultRenderers` also has the same logic). Extract to a shared utility at `src/lib/utils/tool-result.ts`.

37. **[IMPORTANT M2] The inline fallback renderer (lines 181–188) duplicates `DefaultToolFallback.tsx` logic.** The `useDefaultTool` render (lines 173–189) is essentially a partial reimplementation of `DefaultToolFallback` without its status-icon logic. Either use `DefaultToolFallback` here or remove the `DefaultToolFallback` component file entirely to avoid maintenance divergence.

---

### CopilotProvider.tsx

- [x] **/uncodixfy:** PASS
- [x] **Dark mode:** N/A
- [x] **Responsive:** N/A
- [x] **Accessibility:** PASS

No significant issues. The error boundary pattern is correct. One note:

38. **[MINOR N1] `showDevConsole={process.env.NODE_ENV !== "production"}` (line 48)** enables the CopilotKit dev console in development. The CSS override in `globals.css` (lines 737–743) hides this with `opacity: 0; pointer-events: none`. This is a functional workaround but architecturally it means the dev console is still initialized and consuming resources — it's just hidden by CSS. Consider `showDevConsole={false}` permanently now that the CSS hide rule exists, or remove the CSS rule and let the prop control it.

---

## Cross-Cutting Issues

### Consistency Issues

**CC1: Blue color values throughout renderers**
Five components (`ExtractionProgress`, `DefaultToolFallback`, `SmartChatPanel`, `AgentActivityIndicator`) use hardcoded Tailwind blue values (`text-blue-600`, `bg-blue-500`) for loading/active states. The project's design system is VAEA teal (`--primary`). This creates a split visual language: teal everywhere in the main UI, blue in the chat panel.

Affected locations:
- `ExtractionProgress.tsx` lines 26, 43: `text-blue-600`, `bg-blue-600`
- `DefaultToolFallback.tsx` line 23: `text-blue-600`
- `SmartChatPanel.tsx` line 62: `bg-blue-500`

Fix: global search-replace `text-blue-600` → `text-primary` and `bg-blue-500` → `bg-primary` in these files.

**CC2: `dark:bg-gray-*` usage bypasses design tokens**
Three components use `dark:bg-gray-800` or `dark:bg-gray-700` which map to neutral gray, not the dark teal palette. This creates visible color seams in dark mode.

Affected locations:
- `HITLApprovalDialog.tsx` lines 44, 71: `dark:bg-gray-800`
- `ItemDetailCard.tsx` line 35: `dark:bg-gray-800`
- `ExtractionProgress.tsx` line 40: `dark:bg-gray-700`

Fix: replace with `dark:bg-muted` across all four instances.

**CC3: Missing `dark:` on green success icons**
Four components use `text-green-600` or `text-green-500` for success/complete states without a dark variant. Pattern should be `text-green-600 dark:text-green-400`.

Affected locations:
- `ExtractionProgress.tsx` line 24: `text-green-600` (no dark)
- `DefaultToolFallback.tsx` line 25: `text-green-600` (no dark)
- `AgentActivityIndicator.tsx` line 33: `text-green-500` (no dark)

**CC4: Duplicate utility functions**
`isErrorResult()` is implemented twice with slight differences (`ToolResultRenderers.tsx:35` and `CrudToolRenderers.tsx:11`). Should live in `src/lib/utils/tool-result.ts`.

**CC5: Inconsistent `my-*` margin on renderer containers**
- `WriteDiffView`, `ItemDetailCard`, `ExtractionProgress`, `DefaultToolFallback`, `BuildingSummaryCard` all use `my-1`
- `HITLApprovalDialog` uses `my-2`
- `ACMTableResult`, `ACMStatsResult`, `SearchResult` use no vertical margin (rely on parent's `space-y`)

This creates inconsistent inter-card spacing depending on which tool fires. Standardize to `my-2` on all renderer root containers, or remove margins entirely and let the CopilotKit message list handle spacing.

### Missing Features

**MF1: No empty/loading skeleton states for ACMTableResult and ACMStatsResult**
Both components show results or a plain "No records found" message. There is no skeleton/shimmer state for the moment between `status === 'executing'` and result arrival. The `AgentActivityIndicator` covers this at the message level, but if a cached result is stale or the result is a large dataset, there is no progressive disclosure. The globals.css has a fully implemented `animate-shimmer` class available.

**MF2: No pagination or virtual scrolling in ACMTableResult**
The component renders all records in the response as table rows with no upper bound. If the agent returns 100+ records (realistic for a "show all high risk items" query), the chat panel will have a very long scrollable table. Add a cap (e.g., `records.slice(0, 20)`) with a "Show all X results" link or pagination.

**MF3: No copy-to-clipboard on WriteDiffView or HITLApprovalDialog**
For audit trail purposes, users may want to copy the operation details. A small copy icon on the operation badge would enable this.

**MF4: No ARIA live region on CrudToolRenderers inline status messages**
Lines 60–63 and 78–81 of `CrudToolRenderers.tsx` render "Preparing write preview..." and "Applying change..." as plain italic divs. These appear dynamically in the DOM but have no `aria-live="polite"` or `role="status"`, so screen readers will not announce them.

### Optimization Opportunities

**OPT1: `TOOL_LABELS` map duplication**
`AgentActivityIndicator.tsx` and `ToolErrorCard.tsx` each maintain their own `TOOL_LABELS` / `TOOL_LABELS` (similar but different) maps keyed by tool name. These should share a single source of truth in `src/lib/constants/tool-labels.ts`.

**OPT2: `getRiskBadgeVariant` in ACMTableResult is dead code**
See issue G4. Remove to reduce bundle weight.

**OPT3: `SmartChatInput` OS detection**
Lines 29–32 perform navigator UA sniffing for Mac detection on every render. Move to a `useMemo` or a module-level constant since the OS does not change between renders.

---

## Recommended Fixes

Prioritized by impact and effort.

### P1 — Critical (fix before shipping)

| # | File | Fix |
|---|------|-----|
| P1-1 | `ExtractionProgress.tsx` lines 26, 43 | Replace `text-blue-600` with `text-primary`, `bg-blue-600` with `bg-primary`, `dark:bg-gray-700` with `dark:bg-muted` |
| P1-2 | `HITLApprovalDialog.tsx` line 55 | Add `aria-label="Edit value before approving"` to the pencil button |
| P1-3 | `ItemDetailCard.tsx` line 92 | Add `aria-expanded={expanded}` and `aria-controls="item-extra-fields"` to expand button; add `id="item-extra-fields"` to the expanded div at line 100 |
| P1-4 | `SmartChatPanel.tsx` lines 120–128 | Replace `<Badge ... onClick>` with `<button>` styled as badge, add keyboard handler |
| P1-5 | `ACMTableResult.tsx` lines 75–105 | Add `tabIndex={0}` + `onKeyDown` for keyboard row activation; add `<caption className="sr-only">` |
| P1-6 | `ACMTableResult.tsx` line 62 | Add `min-w-[480px]` to the table to ensure `overflow-x-auto` activates in 300px panels |

### P2 — Important (fix in current sprint)

| # | File | Fix |
|---|------|-----|
| P2-1 | All: `DefaultToolFallback.tsx`, `AgentActivityIndicator.tsx` | Replace `text-blue-600` with `text-primary`; `text-green-600` → `text-green-600 dark:text-green-400` |
| P2-2 | `HITLApprovalDialog.tsx` lines 44, 71; `ItemDetailCard.tsx` line 35; `ExtractionProgress.tsx` line 40 | Replace `dark:bg-gray-800` / `dark:bg-gray-700` with `dark:bg-muted` |
| P2-3 | `SmartChatPanel.tsx` lines 79–84 | Remove the read-only banner or merge with the Badge toggle to eliminate duplicate ACM status affordance |
| P2-4 | `ACMStatsResult.tsx` | Extract buildings-list path into a `BuildingListResult` component; replace `text-[10px]` with `text-xs` |
| P2-5 | `ACMTableResult.tsx` + `CrudToolRenderers.tsx` | Extract `isErrorResult` to `src/lib/utils/tool-result.ts`; import in both files |
| P2-6 | `AgentActivityIndicator.tsx` line 35 | Replace fragile `label.replace('...', ' - done')` with explicit done labels; add `role="status" aria-live="polite"` |
| P2-7 | `DefaultToolFallback.tsx` lines 30–31 | Remove inline `<Wrench>` icon from inside the status text span; place it as a standalone header element |
| P2-8 | `ItemDetailCard.tsx` line 104 | Replace `String(val)` with `typeof val === 'object' ? JSON.stringify(val) : String(val)` |
| P2-9 | `ItemDetailCard.tsx` extraFields labels | Add `humanizeKey` transform to convert `snake_case` to "Title Case" |
| P2-10 | `ToolResultRenderers.tsx` lines 173–188 | Replace inline fallback render body with `<DefaultToolFallback name={name} status={status} result={result} args={{}} />` |
| P2-11 | `JobCrudChatPanel.tsx` lines 32–34 | Remove stale `confirm <operation_id>` instruction from system message |
| P2-12 | `CrudToolRenderers.tsx` lines 60, 79 | Add `role="status" aria-live="polite"` to the inline italic status divs |

### P3 — Minor (backlog)

| # | File | Fix |
|---|------|-----|
| P3-1 | `HITLApprovalDialog.tsx` | Add `submitting` state to disable buttons after first click |
| P3-2 | `HITLApprovalDialog.tsx` line 28 | Add `useEffect` to sync `editedValue` when `preview.new_value` changes |
| P3-3 | `WriteDiffView.tsx` line 22 | Add `aria-hidden="true"` to the arrow `→` character |
| P3-4 | `WriteDiffView.tsx` line 11 | Add `role="region"` and `aria-label` to diff container |
| P3-5 | `BuildingSummaryCard.tsx` | Add `role="article"` and `aria-label` to card container |
| P3-6 | `CrudToolRenderers.tsx` line 95 | Rename `sourceId` prop to `_sourceId` or document future use; remove `void sourceId` |
| P3-7 | `ACMStatsResult.tsx` lines 53–61 | Move icons out of the metric number display into label captions |
| P3-8 | `SmartChatPanel.tsx` line 62 | Replace `bg-blue-500` with `bg-primary` on the pulse dot |
| P3-9 | `CopilotProvider.tsx` line 48 | Evaluate removing `showDevConsole` prop or the CSS hide rule — not both |
| P3-10 | `AgentActivityIndicator.tsx` + `ToolErrorCard.tsx` | Consolidate `TOOL_LABELS` maps into `src/lib/constants/tool-labels.ts` |
| P3-11 | `ACMTableResult.tsx` | Remove `getRiskBadgeVariant` function (dead code — overridden by className) |
| P3-12 | `SmartChatInput.tsx` lines 29–32 | Move Mac detection to `useMemo` or module-level constant |
| P3-13 | All renderer containers | Standardize vertical margin to `my-2` on all renderer root `div` elements |
| P3-14 | `ACMTableResult.tsx` | Cap rendered rows at 20 with a "Show all X results" affordance |

---

## Verdict

The component suite is **structurally sound** — the architecture is clean, the TypeScript is well-typed, and the CopilotKit hook usage is correct. The primary defects are:

1. **Brand color consistency**: blue values slipped through in 5 components and must be replaced with `text-primary` / `bg-primary`.
2. **Keyboard and screen reader accessibility**: interactive elements (clickable rows, icon-only buttons, expand toggles, dynamic status messages) are missing ARIA attributes needed for keyboard navigation and screen reader announcements.
3. **Dark mode token hygiene**: `gray-*` Tailwind classes appear in 3 components instead of the project's `muted` semantic tokens, creating visible seams in dark mode.

None of these are structural regressions — all can be fixed with targeted, low-risk edits to the affected lines.
