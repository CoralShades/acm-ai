# E2E Test Run #2 - Master Findings
**Date:** 2026-02-11 | **Duration:** ~25 min | **Result:** 5.0/10 FAIL

## Scorecard

| Phase | Score | Previous | Delta |
|-------|-------|----------|-------|
| Service Health | 10.0/10 | 10/10 | 0 |
| PDF Upload | 8.0/10 | 9/10 | -1.0 |
| Extraction | 2.6/10 | 4/10 | -1.4 |
| Data Accuracy | 4.0/10 | 3/10 | +1.0 |
| UI/UX | 5.5/10 | 7/10 | -1.5 |
| **Overall** | **5.0/10** | **5.5/10** | **-0.5** |

## Team Performance
- 5 agents spawned (health-checker, log-monitor, browser-pilot, data-validator, reporter)
- All agents produced required artifacts (task_plan.md, findings.md, progress.md)
- 14 screenshots captured by browser-pilot
- 31-record comparison table produced by data-validator
- GitHub Issue #14 updated by reporter

## Critical Issues
1. **Negative records not extracted** (20/31 = 65% of records skipped)
2. **Race condition**: acm_extract fires before process_source completes
3. **Model configuration**: OpenRouter model 404, required manual fix to direct Anthropic
4. **Compliance fields missing from API** (structural gap in ACMRecordResponse)

## What Improved
- Previous critical routing bugs (BUG-001-004 from Issue #14) are FIXED
- Grid now loads and is testable with populated data
- Assessment accuracy strong at 87.5%
- Document type correctly identified as DIVISION_5

## Detailed Reports
- Browser: `browser-pilot/findings.md` (8 bugs, 10 passes, 14 screenshots)
- Validation: `data-validator/findings.md` + `data-validator/comparison.md`
- Logs: `log-monitor/findings.md` (3 extraction attempts, pipeline timing)
- Health: `health-checker/findings.md` (all services 100% uptime)
- Report: `reporter/scorecard.md` + `reporter/findings.md`
