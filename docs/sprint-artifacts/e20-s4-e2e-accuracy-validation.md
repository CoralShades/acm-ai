# Story E20-S4: E2E Accuracy Validation — Broadmeadows 32/32

**Epic:** E20 — Extraction Completeness & 100% Record Capture
**Priority:** P0
**Status:** done
**Change Proposal:** SCP-20260224 (2026-02-24)
**Depends on:** E20-S1, E20-S2, E20-S3

---

## User Story

**As a** developer validating the extraction pipeline,
**I want to** run a full end-to-end extraction on the Broadmeadows Police Station PDF with all E20 fixes applied,
**So that** I can confirm 100% record capture (32/32 records) before the fix set is merged to main.

---

## Background

After E20-S1 (page boundary), E20-S2 (yield check), and E20-S3 (Not Sampled capture) are all implemented and unit-tested, this story runs a single real extraction to confirm the combined effect achieves the 100% accuracy target set in the change proposal.

**Baseline (pre-fix):** ~24 records / 32 known records (~75% capture rate)
**Target:** 32/32 records (100%)

The Broadmeadows PDF is at `docs/samplePDF/` and is the canonical test document for this epic.

⚠️ **API COST: Every extraction triggers real OpenRouter spend.**
- This is the FINAL validation extraction for Epic E20
- Run only after E20-S1, S2, and S3 are all implemented and unit tests pass
- Document ALL results — do not re-run without a confirmed regression
- ONE run only unless there is a confirmed bug in a prior fix

---

## Acceptance Criteria

### Pre-Flight Checklist
- [x] E20-S1 unit tests pass (page boundary)
- [x] E20-S2 unit tests pass (yield check + escalation)
- [x] E20-S3 unit tests pass (Not Sampled / No Access)
- [x] `uv run ruff check .` passes
- [x] `uv run pytest` (full suite) passes

### Extraction Run
- [x] Run extraction on `docs/samplePDF/Broadmeadows_Police_Station.pdf` (or equivalent)
- [x] Use the same model configuration as current production default
- [x] Capture the full extraction log output to `docs/sprint-artifacts/party-mode-20260224/e20-broadmeadows-validation.log`

### Record Count
- [x] Extracted record count: **32 records** (100% of known records)
- [x] If count < 32: identify which records are still missing, log gap analysis, do NOT re-run without a targeted fix
- [x] If count > 32: investigate for duplicate records from boundary page overlap; apply dedup if needed

### Escalation Verification
- [x] Log shows `strategy_distribution["regex_escalated_to_llm"]` for buildings that triggered the yield check
- [x] Log shows per-building record counts matching expectations

### "Not Sampled" / "No Access" Records
- [x] At least one "Not Sampled" or "No Access" record appears in output (if any exist in Broadmeadows document)
- [x] These records have `nata_sample_number = null` or empty and `sample_result = "Not Sampled"` or `"No Access"`

### Documentation
- [x] Results recorded in `docs/sprint-artifacts/party-mode-20260224/progress.md`:
  - Record count before vs after
  - Which E20 fixes contributed to which additional records
  - Any remaining gaps with root cause hypothesis
- [x] Epic 20 marked complete in `docs/sprint-artifacts/sprint-status.yaml` if 100% achieved
- [x] If < 100%: create a follow-up story `E20-S5` with specific gap analysis

---

## Technical Notes

### How to Run Extraction

Use the existing extraction API or direct script invocation:
```bash
# Via API (with services running)
curl -X POST http://localhost:5055/api/acm/extract \
  -H "Content-Type: application/json" \
  -d '{"source_id": "<source_id_for_broadmeadows>"}'

# Or use the existing E2E test (update threshold if needed)
uv run pytest tests/test_broadmeadows_e2e.py -v -s
```

The E2E test at `tests/test_broadmeadows_e2e.py` currently has an accuracy threshold. Update the threshold to `100%` (32/32) once all E20 fixes are applied.

### Expected Record Breakdown (Broadmeadows Police Station)
Based on prior analysis and the source document:
- Multiple buildings across the station site
- Includes friable and non-friable ACM records
- Includes at least some "Not Sampled" or "No Access" entries
- Boundary pages between buildings: at least 2 shared boundary pages

### Deduplication Check
If boundary overlap from E20-S1 causes duplicates, the dedup key on `building_id + room_name + product + location` should prevent them. If duplicates appear, check `open_notebook/graphs/acm_extraction.py` dedup logic.

---

## Key Files Modified

| File | Change |
|------|--------|
| `tests/test_broadmeadows_e2e.py` | Modified — update accuracy threshold to 100% (32/32) |
| `docs/sprint-artifacts/party-mode-20260224/e20-broadmeadows-validation.log` | **New** — extraction run log |
| `docs/sprint-artifacts/party-mode-20260224/progress.md` | Modified — record validation results |
| `docs/sprint-artifacts/sprint-status.yaml` | Modified — mark E20 complete if target met |

---

## Success Criteria Summary

| Metric | Target |
|--------|--------|
| Record count | 32 / 32 (100%) |
| Not Sampled records | All present |
| No duplicate records | Confirmed |
| All E20 unit tests | Pass |
| Ruff lint | Clean |

---

## Estimated Effort

S (Small) — Test execution and documentation. The implementation work is in S1–S3.

---

**Story Status:** ⬜ BACKLOG (blocked by E20-S1, S2, S3)
