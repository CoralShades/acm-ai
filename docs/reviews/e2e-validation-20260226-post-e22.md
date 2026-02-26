# E2E Extraction Validation - 2026-02-26 (Post-E22 Schema Fixes)

## Test Conditions
- All E22 fixes applied: schema resilience, dashboard, job detail, building tabs, streaming
- E22-S1 risk_status "Moderate" -> "Medium" normalization confirmed in code
- Phase 3B `data_issues` null-coercion confirmed in code
- Worker restarted with latest code (`uv run run_worker.py --import-modules commands`)
- Sources validated in this rerun:
  - `source:z2a59rp36ur25znpaavr` (`Clutch_Broadmeadows (22).pdf`)
  - `source:ubbsh2i0b6ypy64vs1hh` (`Clucth_Alexander_District_Hospital.pdf`)
- Model path observed in logs: Anthropic via OpenRouter preferences; schema-error fallback to direct JSON parsing executed and succeeded
- Latest commit at validation time: `3355a24`

## PDF A: Broadmeadows (baseline: 31 rows in CSV)

| Metric | Previous (2026-02-25) | Current |
|--------|----------------------|---------|
| Total records | 16 | 17 |
| Core samples (16 NATA) | 16/16 (100%) | 16/16 |
| Overall accuracy | 16/31 (52%) | 17/31 (54.84%) |
| Sample 34511-039-014 | missing | found |
| Duplicate records | 0 (post-dedup) | 0 |

### Building Breakdown

| Building | Records |
|----------|---------|
| Broadmeadows Police Station | 17 |

### Previous Findings and Remaining Gaps (still present)

| Gap Category | Baseline Rows | Extracted Rows | Status |
|--------------|---------------|----------------|--------|
| "As Per" reference rows | 9 | 0 | missing |
| "Not Sampled" assumed-positive rows | 6 | 0 | missing |

Notes:
- Extra extracted sample not present in CSV baseline: `34511-039-005`
- Net count delta remains 14 (`31` baseline vs `17` extracted), but baseline row matching gap is effectively 15 due one extra non-baseline row.

## PDF B: Alexander District Hospital (baseline: 54+ rows, 6 buildings)

| Metric | Previous (E1-S22) | Current |
|--------|-------------------|---------|
| Total records | 54 (pre-fix) / 16 (post-data_issues regression) | 54 |
| Buildings with records | 1/6 (regression phase) | 6/6 |
| Main Hospital Building | 0 records (killed by risk_status rejection) | 38 records |
| risk_status values | "Moderate" caused rejection | "Moderate" = 0, "Medium" = 1 |
| data_issues nulls | expected none after fix | 41 stored as `NONE`, 13 non-empty arrays |

### Building Breakdown

| Building | Records |
|----------|---------|
| Main Hospital Building | 38 |
| Mortuary Buildings | 7 |
| Myrtle Street Clinic | 2 |
| Nurses Accommodation | 2 |
| Pathology Department | 1 |
| VMO Accommodations | 4 |

### Key Validation: risk_status Distribution (Alexander)

| risk_status | Count |
|-------------|-------|
| Low | 27 |
| Medium | 1 |
| null | 26 |
| Moderate | 0 |

## Schema Fix Validation
- [x] risk_status: No "Moderate" values persisted in DB (Alexander `Moderate=0`, `Medium=1`)
- [x] No entire-building rejections from field_validator errors (Main Hospital recovered to 38 records)
- [x] disturbance_potential "Moderate" values present where valid (`1` row)
- [ ] data_issues persisted as empty lists for non-issue rows (current persistence uses `NONE` for many rows)

## Conclusion
- Integrated fix stack works together in E2E execution: worker atomic claim, schema resilience, and large-document multi-building extraction all succeeded.
- Alexander re-validation is strong: `54` records across `6/6` buildings with Main Hospital recovered.
- Broadmeadows extraction completeness remains below closure target at `17/31` (54.84%), with prior prompt coverage gaps unchanged ("As Per" + "Not Sampled").
- E20-S5 closure criteria (`>=28/31` Broadmeadows) are still not met; previous gap story (`E20-S6`) remains required.
