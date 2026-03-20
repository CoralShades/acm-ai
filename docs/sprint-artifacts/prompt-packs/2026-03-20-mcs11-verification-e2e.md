# MCS11-Verification: E2E Browser Sign-off (Phases 6.2-6.6)
# Date: 2026-03-20 | SP: 2 | Priority: P1
# Dependencies: ALL MCS8-MCS13 done ✅, MCS11 phases 1-5 done ✅
# Result: Mark mcs11-jobs-source-unification DONE after this passes

## Context

MCS11 unified /jobs/[id] as the canonical ACM workflow page. All implementation
is complete (commits: b06c5788, c254974f, 545d6c41, f2941789, 658d21bb, 5c4a0d88).

This pack is **verification only** — no new code unless a failure is found.

## Skills to Load

/e2e-test — browser-based end-to-end verification
/agent-browser — DOM snapshots, screenshots, eval
/acm-observability — verify SSE event flow in traces
/verification-before-completion — complete checklist before marking Done
/systematic-debugging — if anything fails, root-cause before moving on

---

## What Was Implemented (verify these work)

| Phase | Feature | Commit |
|-------|---------|--------|
| 1 | SSE streaming on /jobs/[id] | b06c5788 |
| 2 | Bulk operations bar | b06c5788 |
| 3.1 | Quick text search | b06c5788 |
| 3.2 | Group by Room toggle | b06c5788 |
| 3.3 | Per-building ACM data loading (useACMItems + buildingId) | 5c4a0d88 |
| 3.4 | BuildingTabStrip with record count + error badges | 5c4a0d88 |
| 4 | JobStatusPill SSE override (shows "Extracting" during stream) | c254974f |
| 5.1 | useValidationSummary wired to Overview | b06c5788 |
| 5.2 | Error row highlighting in ACMGrid (red/amber) | 5c4a0d88 |
| 5.3 | Validation summary card with Fix All + View Errors | 5c4a0d88 |
| Gap4 | building_record_id + parent_table_id in ACMRecordResponse | f2941789 |

---

## Verification Tasks

### 6.2 — SSE Streaming Verification

Start a fresh extraction on a known PDF and verify live progress on /jobs/[id]:

```bash
agent-browser open http://localhost:8502/jobs
agent-browser snapshot -i
# Click a job in extracting state (or trigger upload → extract)
agent-browser screenshot 6.2-jobs-list.png
# Navigate to /jobs/{id}
agent-browser wait --text "Extracting" --timeout 30000
agent-browser screenshot 6.2-extracting-banner.png
# Verify ExtractionStatusBanner visible
# Verify BuildingTabStrip updates as buildings complete
agent-browser wait --text "Extraction complete" --timeout 300000
agent-browser screenshot 6.2-extract-complete.png
```

**Pass criteria:**
- [ ] ExtractionStatusBanner shows "Extracting... X pages" during extraction
- [ ] BuildingTabStrip shows per-building stream status indicators
- [ ] Banner changes to "Extraction complete" on finish
- [ ] Building/Record counts update without manual refresh

### 6.3 — Bulk Operations Verification

```bash
agent-browser open http://localhost:8502/jobs/{sourceId}
# Click ACM Records tab
agent-browser snapshot -i
# Select 3 rows (checkbox column)
# Click Bulk Edit
agent-browser screenshot 6.3-bulk-select.png
# Change a field value, confirm
agent-browser screenshot 6.3-bulk-edit-dialog.png
# Verify rows updated in grid
```

**Pass criteria:**
- [ ] BulkOperationsBar appears when rows selected
- [ ] Bulk edit dialog opens and saves changes
- [ ] Grid refreshes with updated values
- [ ] Bulk Validate triggers re-validation

### 6.4 — Cross-Page Consistency (/source/[id] still works)

```bash
agent-browser open http://localhost:8502/source/{sourceId}
agent-browser snapshot -i
agent-browser screenshot 6.4-source-page.png
# Verify Buildings tab, ACM Records tab both load
```

**Pass criteria:**
- [ ] /source/[id] Buildings tab renders BuildingGrid
- [ ] /source/[id] ACM Records tab renders ACMGrid
- [ ] No console errors (check DevTools)
- [ ] Switching between /jobs/[id] and /source/[id] for same source shows consistent data

### 6.5 — Mobile Responsive Check

```bash
agent-browser resize 390 844  # iPhone 14 size
agent-browser open http://localhost:8502/jobs/{sourceId}
agent-browser screenshot 6.5-mobile-overview.png
# Check BuildingTabStrip scrolls horizontally
# Check chat panel collapses / is accessible
agent-browser resize 1280 800  # back to desktop
```

**Pass criteria:**
- [ ] BuildingTabStrip scrollable horizontally on mobile (no overflow clipping)
- [ ] Chat sidebar accessible on mobile (slides in/out or scrolls)
- [ ] No horizontal page overflow at 390px width

### 6.6 — Screenshot Evidence Collection

Capture final state screenshots at all key views:

```bash
agent-browser open http://localhost:8502/jobs/{sourceId}
# Overview tab
agent-browser screenshot evidence/6.6-overview-tab.png
# Buildings tab
agent-browser click @buildings-tab
agent-browser screenshot evidence/6.6-buildings-tab.png
# ACM Records tab — select building 1
agent-browser click @acm-records-tab
agent-browser screenshot evidence/6.6-acm-records-building1.png
# ACM Records tab — select building 2 (verify data changes)
agent-browser click @building-2-tab
agent-browser screenshot evidence/6.6-acm-records-building2.png
# Validation Summary card (if errors exist)
agent-browser screenshot evidence/6.6-validation-card.png
```

Save all screenshots to: `docs/sprint-artifacts/evidence/mcs11/`

---

## Build Verification

Before running browser tests:
```bash
cd frontend && npm run build   # must pass
cd frontend && npm run lint    # must pass
uv run pytest tests/ -x -q    # must pass
```

---

## Failure Protocol

If any verification step fails:
1. Screenshot the failure state
2. Use /systematic-debugging to root-cause
3. Apply minimal targeted fix (do NOT refactor unrelated code)
4. Re-run that specific verification step
5. Only proceed after it passes

---

## Completion Gate

After all 6.2-6.6 tasks pass, update sprint-status.yaml:
```yaml
mcs11-jobs-source-unification-2026-03-19: done  # Full implementation + E2E verified 2026-03-20
```

And update the SUMMARY section counts accordingly.

---

## Commit Template (if any fixes needed)

```
fix(jobs-page): MCS11 E2E verification fixes

- [describe what failed and what was fixed]
- All 6.2-6.6 verification tasks now pass

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>
```
