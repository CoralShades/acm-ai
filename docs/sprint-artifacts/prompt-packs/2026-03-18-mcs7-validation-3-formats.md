# Multi-Consultant Story 7: Validation with 3+ Consultant Formats
# Generated via /generate-prompt --save --with-plan --tmux

**SP: 5 | Wave: 5 (final) | Dependencies: Stories 1-5 complete**
**Design doc: `docs/architecture/multi-consultant-format-design.md` Section 7 Story 7, Section 8 (Regression)**

## Skills to Load

/planning-with-files — persistent markdown plan
/dogfood — E2E exploration with real extraction runs
/systematic-debugging — diagnose extraction failures on new formats
/e2e-test — self-healing E2E test workflows
/prompt-engineering — adjust prompts if new format accuracy is low
/acm-observability — Langfuse trace analysis for extraction quality
/verification-before-completion — verify before claiming done

---

## Prerequisites

- Branch: `git checkout ACMV3`
- Stories 1-5 complete (all infrastructure in place)
- Story 6 (HITL UI) recommended but not blocking
- All services running (SurrealDB, API, Worker, Frontend)
- **3 test PDFs available:**
  1. Broadmeadows Police Station (Standard DET format) — `docs/samplePDF/` (check for exact filename)
  2. Alexander District Hospital (ARA/Prensa format) — `docs/samplePDF/` (check for exact filename)
  3. At least 1 PDF with a different table structure (e.g., pipe-table format, or any unknown layout)
- Langfuse running (optional but recommended for trace analysis)

---

## Glossary

| Term | Definition |
|------|-----------|
| Ground truth | Known-correct extraction results for benchmark PDFs |
| Broadmeadows benchmark | 31 records from Standard DET format (100% achieved in E26) |
| Alexander benchmark | 43 records from ARA/Prensa format (36/43 achieved in E28) |
| Schema inference | Story 2 auto-detection — should handle new format without code changes |
| Format profile | Story 3 cache — should auto-save on first run, cache-hit on second |
| Accuracy metrics | Record count, field-level accuracy, recall vs ground truth |

---

## Key Files

**Read:**
- `docs/architecture/multi-consultant-format-design.md` — Section 8 (Regression Safety)
- `tests/e2e/fixtures/ara-documents/broadmeadows-expected-results.json` — Broadmeadows ground truth
- `docs/reviews/e28-validation-results.md` — Alexander ground truth reference
- `scripts/benchmark_ollama.py` — existing benchmark runner pattern
- `open_notebook/extractors/schema_inference.py` — verify inference runs on new format

**Create:**
- `docs/reviews/multi-consultant-validation-results.md` — validation report
- `tests/e2e/fixtures/ara-documents/<new-format>-expected-results.json` — new format ground truth (if available)

---

## Plan

Create `docs/sprint-artifacts/mcs7-validation/task_plan.md`:

### Phase 1: Existing Benchmark Regression
- [ ] Run extraction on Broadmeadows PDF → verify 31/31 records (Standard DET)
- [ ] Run extraction on Alexander PDF → verify ≥36/43 records (ARA/Prensa)
- [ ] Compare field-level accuracy with pre-Story baselines
- [ ] If regression: diagnose via Langfuse traces, fix before proceeding

### Phase 2: New Format Validation
- [ ] Upload new consultant format PDF (unknown to the pipeline)
- [ ] Verify schema inference node triggers (no cached profile exists)
- [ ] If confidence < 0.8: verify HITL dialog appears (Story 6)
- [ ] If confidence ≥ 0.8: verify auto-mapping applied
- [ ] Count extracted records vs manual count
- [ ] Assess field-level accuracy (spot-check 10 records)
- [ ] Verify format profile auto-saved in SurrealDB

### Phase 3: Cache Hit Verification
- [ ] Re-upload same new format PDF (or another PDF from same consultant)
- [ ] Verify schema inference cache hit (LLM not called)
- [ ] Verify `sample_count` incremented
- [ ] Verify extraction results identical to first run

### Phase 4: Report
- [ ] Document results in `docs/reviews/multi-consultant-validation-results.md`
- [ ] Record: format name, record count, field accuracy, schema inference confidence, cache behavior
- [ ] Document any format-specific issues or limitations
- [ ] Update design doc Section 8 benchmarks table with new results

---

## Agent Strategy: TMUX

```
Pane 0 (left-top):    Extraction runner — upload PDFs, trigger extractions
Pane 1 (left-bottom): API/Worker logs — monitor extraction progress
Pane 2 (right-top):   Langfuse — trace analysis (if available)
Pane 3 (right-bottom): Validation — compare results to ground truth, write report
```

---

## Context7 Directives

No library documentation needed for this validation session.

---

## Verification Checklist

### Regression (must pass)
- [ ] Broadmeadows: ≥31/31 records extracted (Standard DET format)
- [ ] Alexander: ≥36/43 records extracted (ARA/Prensa format)
- [ ] No field-level accuracy regression vs pre-Story baselines

### New Format (target)
- [ ] New format PDF: schema inference triggers successfully
- [ ] Column mapping produced with confidence score
- [ ] Records extracted (target: ≥70% of manual count for unknown format)
- [ ] Format profile auto-saved to SurrealDB

### Cache (must pass)
- [ ] Second run on same format: cache hit (no LLM call)
- [ ] Results identical to first run
- [ ] `sample_count` = 2 in format profile

### Report
- [ ] `docs/reviews/multi-consultant-validation-results.md` created
- [ ] All 3 formats documented with metrics

---

## Commit Template

```
test(extraction): validate multi-consultant format support with 3+ PDF formats

- Regression: Broadmeadows 31/31 (Standard DET), Alexander ≥36/43 (ARA/Prensa)
- New format: [FORMAT_NAME] — [N] records extracted, [CONFIDENCE]% inference confidence
- Cache verification: second run cache hit, identical results, sample_count incremented
- Validation report: docs/reviews/multi-consultant-validation-results.md
- Multi-Consultant Story 7 of 7

Co-Authored-By: Claude <noreply@anthropic.com>
```
