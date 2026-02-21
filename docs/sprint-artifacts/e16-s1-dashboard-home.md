# Story E16-S1: Dashboard Home Page with ACM Stats

**Epic:** E16 — UX Enhancement Sprint
**Priority:** P1
**Status:** done
**Change Proposal:** SCP-20260220 (2026-02-20)

---

## User Story

**As a** user opening ACM-AI,
**I want to** see a dashboard overview with system metrics and quick actions,
**So that** I understand the system state at a glance without navigating to multiple pages.

---

## Background

Currently the home route (`/`) renders the Documents (Sources) list directly. There is no system overview. E6-S4 updated the landing page for logged-out users, but there is no authenticated dashboard. E8-S5 (Redesign Dashboard Home Page) was archived when E8 was archived.

This story creates an authenticated dashboard home that leverages the full ACM data model.

---

## Acceptance Criteria

### Summary Cards (row of 4)
- [ ] **Total ACM Records** — count of all `acm_record` entries
- [ ] **Buildings Managed** — count of distinct site_name values
- [ ] **Documents Processed** — count of sources (with extraction complete)
- [ ] **Risk Breakdown** — inline mini-bar: % High / Medium / Low / Unknown
- [ ] All cards show skeleton loading while fetching
- [ ] Cards are clickable: Total Records → `/acm`, Buildings → `/acm?group=building`, Documents → `/sources`

### Charts (2-column grid)
- [ ] **Risk Status Distribution** (donut chart) — High / Medium / Low / Unknown / Not Assessed with record counts
- [ ] **Top 10 Buildings by Record Count** (horizontal bar chart)
- [ ] Charts use Recharts (already in use for any existing charts, or install if not present)
- [ ] Charts show skeleton while loading
- [ ] Charts degrade gracefully if no data: empty state message

### Recent Activity
- [ ] Last 5 extractions with: document name, timestamp (relative: "2 hours ago"), status badge, record count
- [ ] "View all" link → `/extraction-monitor`

### Quick Actions Row
- [ ] "Upload SAMP" button → opens upload wizard
- [ ] "View ACM Register" button → `/acm`
- [ ] "Extraction Monitor" button → `/extraction-monitor`

### General
- [ ] Route: `/` (replace current landing) or `/dashboard`
- [ ] Page title: "Dashboard"
- [ ] Responsive: works on 1280px+ desktop (tablet degrades gracefully)
- [ ] All data from new `GET /api/acm/stats` endpoint

---

## Technical Notes

### New Backend Endpoint

```
GET /api/acm/stats
```

Returns:
```json
{
  "total_records": 127,
  "buildings_count": 8,
  "documents_processed": 12,
  "risk_breakdown": {
    "High": 23,
    "Medium": 45,
    "Low": 52,
    "Unknown": 7
  },
  "recent_extractions": [
    {
      "source_id": "source:abc",
      "source_name": "Broadmeadows SAMP",
      "started_at": "2026-02-19T10:30:00Z",
      "status": "completed",
      "record_count": 31
    }
  ]
}
```

Implement as read-only aggregation in `api/routers/acm.py` or new `api/routers/stats.py`.

### SurrealDB Query
```surql
SELECT
  count() AS total_records,
  count(DISTINCT site_name) AS buildings_count,
  risk_status, count() GROUP BY risk_status
FROM acm_record;
```

---

## Key Files to Create/Modify

| File | Change |
|------|--------|
| `frontend/src/app/(dashboard)/page.tsx` | New dashboard page |
| `frontend/src/components/dashboard/DashboardPage.tsx` | New component |
| `frontend/src/components/dashboard/StatsCard.tsx` | Summary card component |
| `frontend/src/components/dashboard/RiskDonutChart.tsx` | Recharts donut |
| `frontend/src/components/dashboard/BuildingsBarChart.tsx` | Recharts bar |
| `frontend/src/components/dashboard/RecentActivity.tsx` | Activity list |
| `api/routers/stats.py` | New stats endpoint (or add to `acm.py`) |
| `frontend/src/lib/api/statsApi.ts` | API client |

---

## Dependencies

- **Requires:** E1-S1 (done ✓ — schema), E2-S1 (done ✓ — ACM data available)
- **Blocks:** nothing

---

## Estimated Effort

L (Large) — New page, new backend endpoint, multiple chart components. Charts have a non-trivial implementation surface.

## Dev Agent Record
- **Completed:** 2026-02-22
- **Commit:** Ralph sprint batch implementation
- **Build Status:** PASS
- **Implementation:** Dashboard home page with ACM stats, quick actions, and recent activity
