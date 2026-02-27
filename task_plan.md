# Task Plan — E26-S7: Alexander Ground Truth + Epic 26 Closeout

## PART 1: Install Alexander Ground Truth CSV

- [x] 1.1 Copy `Alexandra Distric.csv` to `docs/samplePDF/Clutch_Alexandra.csv`
- [x] 1.2 Fix trailing whitespace on column 27 (`ACM GROUP NAME EXCEL ` → `ACM GROUP NAME EXCEL`)
- [x] 1.3 Verify: 43 records, 47 columns, 5 buildings, all key fields populated
- [x] 1.4 Compare columns with Broadmeadows — documented 4 extra Greencap columns
- [x] 1.5 Create `docs/samplePDF/README.md` with ground truth documentation

## PART 2: E26 Closeout

- [x] 2.1 Verify `.env.example` has `DOCLING_DIRECT_TABLE_EXTRACTION=true` (already done)
- [x] 2.2 Update ADR-001 D5 decision status to PROMOTED in `adr-tableformer-integration.md`
- [x] 2.3 Add E26-S6 and E26-S7 stories to `05-epics-and-stories.md`
- [x] 2.4 Update E26 header: 7 stories, 12 SP, status Done (PROMOTE — 31/31)
- [x] 2.5 Close GitHub Issue #80 with summary comment

## PART 3: Commit & Push

- [x] 3.1 Commit 1: `bc17561a` — Alexander ground truth CSV + README
- [x] 3.2 Commit 2: `e1a840fa` — E26 closeout (ADR + epic tracking)
- [x] 3.3 Push to remote — all pushed to ACMV3
