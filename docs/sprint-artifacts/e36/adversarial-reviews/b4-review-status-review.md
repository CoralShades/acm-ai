# Adversarial Review: B4 — effectiveReviewStatus (Stale Extracting Status)

## Fix Summary
`frontend/src/app/(dashboard)/jobs/[id]/page.tsx` introduces `effectiveReviewStatus` —
a `useMemo`-derived value that overrides the raw `source.review_status` from the database
when the UI's own streaming/phase signals indicate a different state. Specifically: if the
DB says `'extracting'` but `panelPhase` is `'completed'`, `'failed'`, or `'idle'`, the
effective status is coerced to `'pending_review'` to prevent a stale Cancel button.

## Files Reviewed
- `frontend/src/app/(dashboard)/jobs/[id]/page.tsx` (lines 154–166, 319–347)

## Findings

### [CONCERN] `panelPhase === 'idle'` Incorrectly Overrides Mid-Extraction Cold Load
**What**: When a user opens a job page while extraction is actively running in the
background (a cold load — the SSE connection has not started yet), `panelPhase` starts
as `'idle'` and `isStreaming` is `false` until the SSE hook connects and begins emitting
events. During this brief window, the condition on line 159–162 matches:
`source.review_status === 'extracting'` AND `panelPhase === 'idle'` → `effectiveReviewStatus`
returns `'pending_review'`.
**Why it matters**: The Cancel button disappears and a "pending review" state is shown to
a user whose job is actively extracting. When the SSE connection establishes and
`panelPhase` transitions to `'extracting'`, the status corrects itself, but the flash
period can last several seconds on slow connections.
**Evidence**: `page.tsx` line 161: `panelPhase === 'idle'` is included in the override
condition alongside `'completed'` and `'failed'`.
**Recommendation**: Remove `'idle'` from the stale-status override set, or gate the
override on `isStreaming === false AND panelPhase has transitioned at least once`. The
`idle` → `extracting` transition is normal for cold loads and should not trigger the
override.

### [CONCERN] `ExtractionStatusBanner` Still Reads Raw `review_status`, Not Effective
**What**: The `ExtractionStatusBanner` on line 340–343 checks
`source?.review_status === 'processing' || source?.review_status === 'extracting'`
directly — it does not use `effectiveReviewStatus`. This means the banner and the header
can disagree: the header shows "pending review" (via `effectiveReviewStatus`) while the
banner continues to display extraction progress (because raw DB status is still
`'extracting'`).
**Why it matters**: Contradictory signals in the same view confuse the user about whether
extraction is ongoing or done.
**Evidence**: `page.tsx` lines 336–346. `effectiveReviewStatus` is passed to
`JobDetailHeader` and `JobOverviewTab` but not used in the `ExtractionStatusBanner`
`enabled` guard.
**Recommendation**: Include `effectiveReviewStatus === 'extracting'` as an OR condition
in the banner's `enabled` check, alongside or replacing the raw status checks.

### [NITPICK] `useMemo` Dependency Is Fine But Naming Is Implicit
**What**: `effectiveReviewStatus` returns `source?.review_status` as the fallback (line
165), which can be `undefined` when the source is still loading. Callers receive
`undefined` and must handle it — which they appear to do (both `JobDetailHeader` and
`JobOverviewTab` accept `string | undefined`). However, this is not explicit in the memo
or in adjacent comments.
**Why it matters**: A future caller could accidentally render `undefined` as the string
`"undefined"`.
**Recommendation**: Return a defined default (e.g., `'unknown'`) instead of forwarding
`undefined`, or annotate the return type explicitly.

## Verdict: PASS WITH CONCERNS

The fix correctly handles the primary case (stale `'extracting'` after completion). The
`'idle'` cold-load flash is the most actionable concern — it produces a visible incorrect
state for users who navigate to a job while extraction is running. The banner/header
disagreement is a secondary UX inconsistency.
