# Demo Validation Findings — 2026-02-22

## Executive Summary

| Phase | Name | Priority | Status | Pass/Fail |
|-------|------|----------|--------|-----------|
| 0 | Environment Setup | P0 | Pending | - |
| 1 | Dashboard & Navigation | P2 | Pending | - |
| 2 | Document Upload | P0 | Pending | - |
| 3 | Extraction Pipeline | P0 | Pending | - |
| 4 | AG Grid Spreadsheet | P0 | Pending | - |
| 5 | Cell Click → PDF Viewer | P1 | Pending | - |
| 6 | Knowledge Graph | P2 | Pending | - |
| 7 | Chat with ACM Context | P1 | Pending | - |
| 8 | Export CSV & Excel | P0 | Pending | - |
| 9 | Settings & Configuration | P3 | Pending | - |
| 10 | Extraction Monitor | P3 | Pending | - |

## Failure Summary

| Severity | Count |
|----------|-------|
| P0-Critical | 0 |
| P1-High | 0 |
| P2-Medium | 0 |
| P3-Low | 0 |
| **Total** | **0** |

---

## Phase Results

### Phase 3: Extraction Pipeline — Partial (E18-S5)

| Metric | Before | After |
|--------|--------|-------|
| Records matched | 26/31 (84%) | 27/31 (87%) |
| Fuse cartridge naming | 0/3 correct | 2/3 correct |
| No-access items | 0/2 extracted | 0/2 extracted |
| Structured output | Fails on OpenRouter | Fallback parser works |

**Fixes applied:**
- Prompt template: ACM item vs equipment distinction, No Access rules, vocabulary guide
- E2E matching: Three-tier strategy with room+location fuzzy fallback
- Fallback JSON parser for OpenRouter compatibility
- max_tokens increased 8192 → 16384

**4 remaining misses:**
| # | Room | Expected Item | Root Cause | Proposed Fix |
|---|------|--------------|------------|-------------|
| 1 | Switch Room / Auto Battery Charger | Fuse cartridge | PDF says "Fuses" not "Fuse cartridge" | Vocabulary mapping (Fix B) |
| 2 | Roof / East Ductwork | Flange joints | PDF says "Flange mastic" — likely matching issue | Test synonym mapping (Fix C) |
| 3 | Lift Foyer / Lift | Internal lining | No Access — no preprocessor marker | Inject NO ACCESS marker (Fix A) |
| 4 | Main Foyer / Disabled Toilet | Unknown | No Access — no preprocessor marker | Inject NO ACCESS marker (Fix A) |

**Full research**: See `extraction-quality-research.md` in this directory.

