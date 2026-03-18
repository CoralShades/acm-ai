# MCS7 Validation — Task Plan

**Story**: Multi-Consultant Story 7: Validation with 3+ Consultant Formats
**SP**: 5 | **Wave**: 5 (final) | **Branch**: ACMV3
**Date**: 2026-03-19

---

## Phase 1: Service Health & Prerequisite Check
- [ ] Verify SurrealDB, API, Worker, Frontend are running
- [ ] Verify Stories 1-5 infrastructure is in place (schema_inference.py, format profiles table, etc.)
- [ ] Identify available test PDFs

## Phase 2: Broadmeadows Regression (Standard DET)
- [ ] Run extraction on `docs/samplePDF/Boradmeadows.pdf`
- [ ] Verify 31/31 records extracted
- [ ] Compare field-level accuracy with ground truth (`broadmeadows-expected-results.json`)
- [ ] Check Langfuse traces for any anomalies

## Phase 3: Alexander Regression (ARA/Prensa)
- [ ] Run extraction on `docs/samplePDF/AlexanderHospital.pdf`
- [ ] Verify ≥36/43 records extracted (E28 baseline)
- [ ] Compare per-category breakdown (NATA-sampled, As Per, Not Sampled)
- [ ] Check Langfuse traces for any anomalies

## Phase 4: New Format Validation (Clutch/Greencap)
- [ ] Upload new consultant format PDF (e.g., `Clutch_Broadmeadows.pdf` or numbered PDFs)
- [ ] Verify schema inference node triggers (no cached profile)
- [ ] Check confidence score — if < 0.8, verify HITL dialog
- [ ] Count extracted records vs manual count
- [ ] Spot-check 10 records for field-level accuracy
- [ ] Verify format profile auto-saved in SurrealDB

## Phase 5: Cache Hit Verification
- [ ] Re-upload same format PDF (or another PDF from same consultant)
- [ ] Verify schema inference cache hit (no LLM call)
- [ ] Verify `sample_count` incremented to 2
- [ ] Verify extraction results identical to first run

## Phase 6: Report & Documentation
- [ ] Create `docs/reviews/multi-consultant-validation-results.md`
- [ ] Document all 3 formats with metrics
- [ ] Update design doc Section 8 benchmarks table
