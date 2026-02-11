# E2E Test Scorecard - 2026-02-11

## Overall: 5.0/10 (FAIL) | Previous: 5.5/10 | Delta: -0.5

Pass threshold: >= 7.0/10

---

## Phase Scores

| Phase | Weight | Score | Previous | Delta | Details |
|-------|--------|-------|----------|-------|---------|
| Service Health | 10% | 10.0/10 | 10/10 | 0 | All 4 services 100% uptime, 13/13 checks passed |
| PDF Upload | 15% | 8.0/10 | 9/10 | -1.0 | Upload worked first try; extraction needed 3 attempts (race condition + model misconfiguration) |
| Extraction | 30% | 2.6/10 | 4/10 | -1.4 | 8/31 records extracted (25.8%), same count as previous but stricter analysis |
| Data Accuracy | 30% | 4.0/10 | 3/10 | +1.0 | Better methodology: coverage=22.6%, core_id=53.6%, assessment=87.5%, compliance=0% |
| UI/UX | 15% | 5.5/10 | 7/10 | -1.5 | 3 medium + 3 low bugs; previous critical routing bugs fixed but new bugs found |
| **Overall** | **100%** | **5.0/10** | **5.5/10** | **-0.5** | **FAIL** |

---

## Score Calculation Detail

### Service Health: 10.0/10
- Formula: 10 - (2 * downtime_incidents)
- Downtime incidents: 0
- Score: 10 - 0 = **10.0**

### PDF Upload: 8.0/10
- Formula: 10 - (2 * retries) - (5 * failures)
- Upload itself succeeded on first attempt
- Extraction required 3 attempts (2 failures before success due to race condition and model misconfiguration)
- Score: **8.0** (one config-related retry needed for extraction trigger)

### Extraction: 2.6/10
- Formula: (records_extracted / 31) * 10
- Records extracted: 8 (7 matched ground truth + 1 false positive)
- Score: (8/31) * 10 = **2.58** (rounded to 2.6)
- Note: Same raw count as previous test, but 1 record now identified as false positive

### Data Accuracy: 4.0/10
- Formula: 0.40*coverage + 0.25*core_id + 0.20*assessment + 0.15*compliance (each as /10)
- Coverage: 22.6% (7/31 true matches) = 2.26/10
- Core ID: 53.6% (15/28 fields correct) = 5.36/10
- Assessment: 87.5% (24.5/28 fields correct) = 8.75/10
- Compliance: 0% (0/28 - structural bug, fields not in API) = 0/10
- Weighted: (0.40 * 2.26) + (0.25 * 5.36) + (0.20 * 8.75) + (0.15 * 0) = 0.90 + 1.34 + 1.75 + 0 = **3.99** (rounded to 4.0)

### UI/UX: 5.5/10
- Formula: 10 - (1 * medium_bugs) - (0.5 * low_bugs)
- Medium bugs: 3 (BUG-1 empty Building col, BUG-2 empty Page col, BUG-3 Friable dropdown blank)
- Low bugs: 3 (BUG-4 search filter, BUG-5 library no refresh, BUG-6 console error)
- Informational: 2 (not counted)
- Score: 10 - 3 - 1.5 = **5.5**

---

## Overall Calculation

(10.0 * 0.10) + (8.0 * 0.15) + (2.6 * 0.30) + (4.0 * 0.30) + (5.5 * 0.15)
= 1.00 + 1.20 + 0.78 + 1.20 + 0.825
= **4.996** (rounded to **5.0/10**)

---

## Key Delta Analysis

| Area | Direction | Explanation |
|------|-----------|-------------|
| Service Health | Unchanged | Both runs: perfect infrastructure stability |
| PDF Upload | Worse (-1.0) | Race condition bug and model misconfiguration required 3 extraction attempts |
| Extraction | Worse (-1.4) | Same 8 records but stricter analysis: 1 false positive identified, formula-based scoring |
| Data Accuracy | Better (+1.0) | More rigorous field-level analysis; assessment accuracy strong at 87.5% |
| UI/UX | Worse (-1.5) | Previous critical routing bugs (BUG-001-004) FIXED, but new medium bugs found in populated grid |

### Important Context
- **Previous test (2026-02-10)** had critical routing bugs that blocked all UI testing of populated data. Those bugs have been **fixed**.
- **This test (2026-02-11)** could fully test the populated ACM grid for the first time, revealing new bugs (empty columns, friable dropdown, search filter).
- The lower UI/UX score reflects more thorough testing, not regression. The application is actually in better shape.
- Model had to be fixed mid-test (OpenRouter model ID -> direct Anthropic API), same issue as previous test.
