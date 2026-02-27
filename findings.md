# Findings — E26-S7: Alexander Ground Truth + Closeout

## Pre-Read Complete

### CSV Source Files
- `docs/samplePDF/Alexandra Distric.csv` — 43 data rows + 1 header, 47 columns
- `docs/samplePDF/Alexandra_District_Health - Sheet1.csv` — identical content (same source)
- Both files have trailing space on column 27: `"ACM GROUP NAME EXCEL "` → needs strip

### Current State
- `.env.example` already has `DOCLING_DIRECT_TABLE_EXTRACTION=true` (promoted in prior session)
- ADR D5 title: "YES" — needs updating to "PROMOTED" with results
- Epic tracking: "Done (INVESTIGATE — 28/31, flag remains false)" — stale, needs "Done (PROMOTE — 31/31)"
- E26 shows 5 stories, 9 SP — needs S6 (3 SP) + S7 (1 SP) = 7 stories, 12 SP

### Column Differences (Expected)
- Alexander col 3: `Site Name (if applicable)` vs Broadmeadows: `Site Name`
- Alexander col 34: `Quantity` vs Broadmeadows: `Extent`
- These are valid BAR column names from different consultants (Greencap vs Prensa)
