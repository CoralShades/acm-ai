# E2E Test Master Plan - 2026-02-11

## Objective
Re-test ACM extraction pipeline with 5-agent team to validate improvements since Issue #14 (5.5/10 FAIL).

## Team
- health-checker: Service monitoring (haiku)
- log-monitor: Log capture and analysis (haiku)
- browser-pilot: Playwright UI automation (haiku)
- data-validator: Ground truth comparison (sonnet)
- reporter: Scorecard and GitHub update (sonnet)

## Tasks
- T1: Service health monitoring (health-checker)
- T2: Log monitoring (log-monitor)
- T3: Upload PDF and trigger extraction (browser-pilot)
- T4: Validate extracted data against CSV (data-validator) - blocked by T3
- T5: UI/UX verification on ACM Register page (browser-pilot) - blocked by T3
- T6: Generate final report and scorecard (reporter) - blocked by T4, T5
- T7: Update GitHub Issue #14 (reporter) - blocked by T6

## Input
- PDF: docs/samplePDF/Clutch_Broadmeadows.pdf
- CSV Ground Truth: docs/samplePDF/Clutch_Broadmeadows.csv (31 records, 42 columns)

## Baseline (Issue #14)
- Overall: 5.5/10 FAIL
- Records: 8/31 (26%)
- Compliance: 0%
- Core ID: 89.8%
