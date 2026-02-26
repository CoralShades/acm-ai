# E2E Extraction Validation — 2026-02-26

**Epic:** E20 — Extraction Completeness & 100% Record Capture  
**Story:** E20-S5 — Extraction Accuracy Gap Analysis  
**Phase:** 3B — Schema Fix + Re-Validation  
**Date:** 2026-02-26  

---

## Blocker Resolved

| Field | Detail |
|-------|--------|
| **Issue** | `data_issues: null` → Pydantic `List[str]` validation failure |
| **Symptom** | 0/31 records persisted despite successful LLM processing (95s extraction) |
| **Root cause** | `default_factory=list` does not coerce an *explicit* `null` value; Pydantic v2 validates `None` against `List[str]` and raises `ValidationError` |
| **Fix** | Added `@field_validator("data_issues", mode="before")` in `ACMExtractionRecord` to coerce `None → []` |
| **Commit** | see git log |
| **Impact** | Was causing 100% record loss (0/31); now 17/31 persisted |

### Files Changed

| File | Change |
|------|--------|
| `open_notebook/extractors/acm_schemas.py` | Added `coerce_data_issues` field_validator (null → []) |
| `open_notebook/extractors/orchestrator.py` | Added `elif di is None: record["data_issues"] = []` in `_normalize_extraction_json` (belt-and-suspenders for orchestrator fallback path) |
| `open_notebook/graphs/acm_extraction.py` | Null-safe `_merge_records`: `existing.data_issues or []` guard |
| `tests/test_acm_schemas.py` | New file — 18 tests covering null coercion, model_validate path, normalize helper, and merge null-safety |

---

## Test Conditions

| Condition | Value |
|-----------|-------|
| Worker restarted | Yes — PIDs 99020 & 61372 killed; fresh process 68996 started |
| Latest commit | `81470fa` + Phase 3B changes (uncommitted at validation time) |
| Model used | Anthropic (via OpenRouter) — all 17 records high confidence |
| Stale commands cleaned | Yes — `command:m42peq0yktih36vpgvpq` marked `superseded` |
| Previous failed records deleted | N/A — 0 records existed from failed Phase 3 run |
| Source | `source:nlmw7at56043qsjlikvq` — Clutch_Broadmeadows (21).pdf |
| Command | `command:595aux2j5xrfie0ryrwd` |
| Execution time | 95.75s |

---

## Results

| Metric | Value |
|--------|-------|
| CSV baseline rows | 31 |
| Extracted records | **17** |
| Records failed validation | 0 (down from 13 in Phase 3) |
| Records embedded | 17 |
| Confidence distribution | 17 high, 0 medium, 0 low |
| Accuracy | **17/31 = 55%** |
| NATA sample coverage | 16/16 unique samples + 1 extra (sample-005 in PDF, not in CSV) |

---

## Gap Analysis: Missing 14 Records

The extraction pipeline captured all uniquely-sampled records. The 14 missing records
fall into two pre-existing extraction coverage categories:

### Category A — "As Per" Reference Rows (9 rows)

Items identified in the register that reuse a previously collected sample for testing.
These appear in the CSV as separate rows but share a sample number with another record.

| Room | Sample Reference | Item |
|------|-----------------|------|
| Corridor Adjacent Cells and Custody Counter | As Per 34511-039-001 | Floor covering |
| Lift Foyer | As Per 34511-039-001 | Floor covering |
| Throughout | As Per 34511-039-003 | Skirting |
| Kitchen | As Per 34511-039-009 | Floor covering |
| Kitchen | As Per 34511-039-003 | Skirting |
| Fan Room 2.24 | As Per 34511-039-007 | Flange joints |
| Fan Room | As Per 34511-039-007 | Flange joints |
| East Roof Fan Room | As Per 34511-039-016 | Ceiling |
| Exterior | As Per 34511-039-014 | Expansion joint |

### Category B — "Not Sampled" / Assumed Positive Rows (6 rows)

Items identified as likely ACM but not formally sampled. Assumed Positive by default.

| Room | Item | Result |
|------|------|--------|
| Front Desk Area | Filing Cabinet | Assumed Positive |
| Switch Room | Fuse cartridge | Assumed Positive |
| Switch Room | Fuse cartridge | Assumed Positive |
| Boiler Room | Fuse cartridge | Assumed Positive |
| Lift Foyer | Internal lining | Assumed Positive |
| Main Foyer | Unknown | Assumed Positive |

### Extra Record Not in CSV (1 record)

| Sample | Room | Significance |
|--------|------|-------------|
| 34511-039-005 | Ceiling space | Present in PDF source, absent from CSV baseline. CSV may be incomplete. |

---

## Conclusion

**Schema blocker resolved.** The `data_issues` null coercion fix eliminates the
`ValidationError` that was causing 100% record loss. Records now persist correctly
(17 created, 0 failed, all high confidence).

**E20-S5 closure assessment: PARTIALLY BLOCKED**

- ✅ Schema validation error: FIXED
- ✅ Records now persist: YES (17 records, 0 failures)
- ❌ Accuracy target ≥28/31 (90%): NOT MET — 17/31 (55%)
- ❌ Gap reason: Extraction pipeline does NOT capture "As Per" reference rows or "Not Sampled" assumed positive rows (pre-existing coverage gap, not caused by schema bug)

**Recommendation:** E20-S5 requires a follow-up story to improve extraction coverage for:
1. "As Per" reference records (items reusing prior sample results)
2. "Not Sampled" / Assumed Positive records (items identified but not formally tested)

These are extraction prompt/logic gaps, not schema issues.
