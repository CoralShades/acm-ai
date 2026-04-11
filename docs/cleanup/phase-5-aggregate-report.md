# Phase 5 Aggregate Report — 9-Agent Post-Code Audit

**Date:** 2026-04-12
**Branch:** `feat/sf-reconciliation-20260411` (12 commits ahead of main)
**Audit duration:** ~2 hours wall clock (22:30 → 00:30 approx)
**Tmux session:** `phase5-audit` (9 parallel windows, all complete)
**Status:** ALL 9 SPECIALISTS COMPLETE

---

## 1. Verdict at a glance

| Area | Verdict | Evidence |
|---|---|---|
| Phase 2a surgical RAG fix | ✅ **CLEAN** | No span/event regression (observability), Layer 1 still runs (extraction-post), `_llm_correct_records` dead with 0 callers on main (extraction-core) |
| Phase 2b sf_export rewrite | ⚠️ **PARTIAL** | CSV exports produce zero fabricated field names ✅, but 3 classes of leakage survive — see §2.1 |
| Dead field cleanup scope (E38-S2) | 🚨 **EXPAND 25 → 46, mind 3 data-loss risks** | db-state + schema-expert converged; 3 fields have real data and need pre-drop migration |
| RAG strategy | ✅ **NO FURTHER SIMPLIFICATION NEEDED** | rag-strategist strategic verdict |
| Observability wiring | ✅ **INTACT** | All 5 smoke tests pass, zero new callback-placement violations |
| Runtime schema source of truth | 🚨 **CRITICAL CONFLICT** | `config/sf-schema-snapshot.json` is INERT; `load_sf_field_schema()` still reads `V3/output/*.md`. Blocks E38-S2 (§2.2) |
| Live E2E extraction | ✅ **PARTIAL PASS** | Broadmeadows PDF extracted 35 records (expected 31, +4 pre-existing over-extraction); Building.csv + Item.csv exports clean (§2.3) |
| Frontend UI | ⚠️ **6 stale SF names in AG Grid tooltips** | frontend-e2e |
| Log history | ✅ **0 fabricated-field hits in logs** | log-sentinel — they only fire at export time, and no real export has run |

---

## 2. Critical findings (convergent — multiple agents flagged the same thing)

### 2.1 `_merge_site_config()` latent fabricated-field bug
**Severity:** HIGH | **Confirmed by 4 agents**: extraction-pre, extraction-post F4, extraction-core F5, frontend-e2e

File: `open_notebook/extractors/exporters/sf_export.py:203-223`

```python
def _merge_site_config(row: dict[str, str], site_config: object) -> None:
    ...
    department = getattr(site_config, "department", None)
    if department:
        row["Department__c"] = str(department)      # ❌ FABRICATED — not in SF schema
    agency = getattr(site_config, "agency", None)
    if agency:
        row["Agency__c"] = str(agency)               # ❌ FABRICATED — not in SF schema
```

**Real field:** `Responsible_Agency_Department__c` (verified in `phase-5-audit-db-state.md` — "One Building__c field missing"). 

**Why Phase 2b missed it:** my rewrite only touched `BUILDING_SF_MAPPING` and `ITEM_SF_MAPPING` — I didn't search for direct `row[...]` assignments in helper functions.

**Why it's latent not live:** frontend-e2e confirmed — the bug only fires when `SiteConfig.agency` or `SiteConfig.department` is populated. Test run had neither, so Item__c.csv and Building__c.csv came out clean. But any production ARA run with site config will inject fabricated columns → Data Loader rejection.

### 2.2 `config/sf-schema-snapshot.json` is INERT at runtime — E38-S0 BLOCKER
**Severity:** CRITICAL | **Confirmed by 3 agents**: schema-expert §2.4, db-state §critical runtime conflict, extraction-post F5

File: `open_notebook/extractors/parsers/config_loader.py:402` — `load_sf_field_schema()` still reads from stale `V3/output/*.md` files (building_fields_summary.md + item_fields_summary.md, 132+ fields). The snapshot I created in Phase 2a is a dead file at runtime.

**Blast radius if E38-S2 drops fields without fixing this:**
- `SalesforcePicklistValidator` references deleted fields → every extraction throws `KeyError`
- `normalize_record_to_sf()` writes to fields that don't exist in the model
- `validate_records_strict()` emits validation errors against deleted fields

**This is a prerequisite story (E38-S0).** Must land before E38-S2 field drops.

### 2.3 Data-loss risk in E38-S2 — 3 fields have production data
**Severity:** HIGH | **Surfaced by**: db-state exclusive finding (only agent that queried live data)

Of the 46 fields flagged for E38-S2 deletion, **3 have non-null production data**:

| Field | Record count | Disposition |
|---|---|---|
| `result` | **212 records (ALL rows)** | **Highest risk**. String type, not optional, always populated. `sample_result` IS the SF-bound field but has only 142 records populated (70 missing). Pre-drop migration required: `UPDATE acm_record SET sample_result = result WHERE sample_result = NONE`. Without this, 70 rows will lose their sample result value. |
| `room_id` | 74 records | Low-risk data, not mapped to any SF field. Safe to drop. |
| `risk_status` | 12 records | Formula field in SF anyway; drop with confidence. |

**db-state also CORRECTED the schema-expert agent:** `floor_level` (104 records) and `sample_result` (142 records) are **NOT dead** — both are active in `sf_export.py ITEM_SF_MAPPING`. schema-expert's dead list over-reports by 2 fields.

**Revised dead-field count:** ~44 safe to drop + 2 needing data migration (`result`, `risk_status`) + 1 orphan (`room_id`) = **47 cleanup targets**, but `floor_level` + `sample_result` must stay.

### 2.4 MERGE RISK — `fix-a-no-access-markers` worktree will reintroduce LLM correction
**Severity:** HIGH | **Exclusive finding**: extraction-core F1

The worktree at `.claude/worktrees/fix-a-no-access-markers/` is based on commit `c560e2b0` (predates the Phase 2a surgical fix at `5dc3ef30`). Its `acm_extraction.py:1717` still has:

```python
await _llm_correct_records(records, records_needing_llm, correction_stats, model_id, ...)
```

**If that worktree is merged or rebased onto the current branch**, it will reintroduce the LLM correction call, violating DEC-005 (literal-only) and DEC-006 (Option C). Latest commit there is `c560e2b0 wip: safety checkpoint — Extraction Quality — Fuse Cartridge & No-Access Records` — apparently unfinished work.

**Action:** When that worktree is resumed, rebase onto `feat/sf-reconciliation-20260411` and resolve the conflict at `acm_extraction.py:1811` in favor of the Phase 2a fix.

### 2.5 `Labelled__c` export is broken — bool extracted but string never set
**Severity:** HIGH | **Exclusive finding**: extraction-core F3

`ACMRecord.acm_labelled` is a `bool` populated by extraction. `ACMRecord.labelled_sf` is the `str` ("Yes"/"No") that `sf_export.py ITEM_SF_MAPPING` reads. **No code translates `acm_labelled` → `labelled_sf`.** Result: `Labelled__c` column in every Item CSV will be empty.

Per `bar_to_sf_mapping.yaml`, the mapping `YES/NO → Yes/No` exists, but the normalizer runs on `labelled_sf` which is never populated in the first place.

### 2.6 Date format risk — SF date field vs free-form string
**Severity:** HIGH | **Confirmed by**: extraction-pre

`DocumentMeta.report_date` is a free-form string (e.g. "15 March 2023" or "2023-03-15" depending on the consultant). `Date_of_Audit_Report__c` is SF `type=date`. No ISO 8601 normalization exists between extraction and CSV export. **Data Loader will reject non-conforming dates** on every production run.

### 2.7 Phase 2b over-corrected: 2 real fields were deleted
**Severity:** MEDIUM | **Confirmed by**: schema-expert

- `Est_Building_Size_m2__c` — exists on Building__c, was dropped from `BUILDING_SF_MAPPING`
- `Hygienist_Recommendations__c` — exists on Item__c, was dropped from `ITEM_SF_MAPPING`

Both should be re-added. My session log incorrectly labeled them fabricated.

### 2.8 `schema_inference.py` contains 5 fabricated SF field names
**Severity:** HIGH | **Exclusive finding**: extraction-core F2

The `SF_FIELD_CATALOG`, `SF_TO_CANONICAL`, and `SF_TO_ITEM_ROW_FIELD` dicts in `open_notebook/extractors/schema_inference.py` reference 5 SF API names that don't exist per `config/sf-schema-snapshot.json`. Must be enumerated and corrected — schema_inference drives per-run column alias resolution, so these names leak into the pipeline's parsing logic even though the Phase 2b rewrite cleaned the export layer.

---

## 3. Non-blocking findings (noted, can defer)

| Finding | Severity | Source | Notes |
|---|---|---|---|
| `_llm_correct_records` function definition still in source (dead) | LOW | extraction-core F1, rag-strategist | ~250 lines. Remove in E38-S2. |
| `prompts/acm/correction.jinja` dead template | LOW | extraction-post F2 | Remove in E38-S2. |
| Stale docstring at `acm_schemas.py:455` mentioning `_llm_correct_records` | LOW | rag-strategist | Clean up with E38-S2. |
| 3 stale imports in `acm_extraction.py` (`tag_pages`, `extract_document_metadata`, `extract_document_structure`) | LOW | extraction-pre | Not called after metadata_and_structure merge. |
| 9 LLM-extracted `DocumentMeta` fields never mapped to SF (`building_size`, `building_age`, `inspection_dates`, `inspector_names`, `document_scope`, `methodology`, `revision_date`, `regional_classification`, `organization`) | LOW | extraction-pre | Dead output — drop from prompt or wire to SF. |
| AG Grid tooltips on 6 columns reference fabricated SF names (`Disturbance_Potential__c`, `Room_Name__c`, `Floor_Level__c`, `Sample_Result__c`, `Item_Location__c`, `Assessor__c`) | LOW | frontend-e2e | Frontend-only cosmetic. Defer to E38-S4 UI work. |
| `correct_records` `failed` counter double-increments when `max_correction_attempts=2` | LOW | extraction-post F1 | Inflates logs, no functional impact. Lower to 1 or add dedup guard. |
| `Survey_Date__c` mapping points to wrong Python field | LOW | extraction-post F6 | Single-line fix. |
| 3 zombie `command` records stuck since 2026-03-21 for a source that no longer exists | LOW | db-state | Monitoring pollution. `DELETE command WHERE id IN ...` |
| 16 orphan `extraction_progress` records with null metadata | LOW | db-state | Pollute live-stats endpoint. `DELETE extraction_progress WHERE metadata IS NONE` |
| Ollama container false-unhealthy (image lacks `curl` in healthcheck) | LOW | log-sentinel | Swap healthcheck to `wget`. Cosmetic. |
| `field_schema:sf_v1` record has null `table_name` | LOW | db-state | Underseeded; fix with the E38-S0 wiring story. |
| ConsensusEngine votes without SF picklist awareness | MEDIUM (by design) | extraction-post F3 | Layer 1 picks up the slack. Document as intentional. |
| 6 row extraction failures from Broadmeadows test (non-item rows in table, `item_name=None`) | LOW | frontend-e2e | Pre-existing segmentation behavior, not introduced by this sprint. |
| SF schema has 7 Item__c fields absent from DB (`If_Other_Item_Name__c`, `Frequency_of_Use__c`, `Public_Access__c`, plus 4 more) + `Responsible_Agency_Department__c` on Building__c | MEDIUM | db-state | Means extraction populates the CSV but the DB can't round-trip. Schema migration needed. |
| 7 screenshots captured at `docs/cleanup/phase-5-screenshots/` | INFO | frontend-e2e | Evidence of E2E run. |
| Full extraction run: 35 records (expected 31) in 285s / 407s total | INFO | frontend-e2e | Over-extraction is pre-existing. Worker needed manual start (2:04 init). |

---

## 4. E38 epic expansion — proposed stories

Existing E38 had 5 stories (S1..S5). After Phase 5 findings, the epic needs **8 more stories** to cover the newly surfaced work. Total: 13 stories, estimated ~45 SP.

### Prerequisite (blocks S2)

- **E38-S0 — Wire `config/sf-schema-snapshot.json` into `load_sf_field_schema()`** (3 SP)
  - Replace `V3/output/*.md` read with snapshot JSON parser
  - Verify `SalesforcePicklistValidator` picks up the new source
  - Update `field_schema:sf_v1` record `table_name` population
  - Acceptance: `uv run python -c "from open_notebook.extractors.parsers.config_loader import load_sf_field_schema; load_sf_field_schema()"` matches snapshot field count

### Existing (from SCP)

- **E38-S1** — VAEA SF admin fix to `Item__c.External_ID__c` (external, blocked)
- **E38-S2** — Delete dead fields — **scope revised from 25 → 47**, with the 3-field data-loss caveat
- **E38-S3** — Incremental test rebuild (still deferred)
- **E38-S4** — BAR→SF mapping frontend UI (extended to include tooltip cleanup)
- **E38-S5** — (retrospective) superseded by this Phase 5 aggregate

### New stories from Phase 5 findings

- **E38-S6 — Fix `_merge_site_config()` fabricated fields** (1 SP)
  - Replace `Department__c`/`Agency__c` writes with `Responsible_Agency_Department__c`
  - Add test to `tests/test_sf_export_contract.py` that invokes `building_to_sf_row` with a populated `site_config` and asserts no fabricated columns
- **E38-S7 — Fix `Labelled__c` export (bool → str translation)** (1 SP)
  - Add translator: `labelled_sf = "Yes" if acm_labelled else "No"` in the row builder
  - Add test that extracts a labelled row and asserts `Item__c.csv` column "Labelled__c" = "Yes"
- **E38-S8 — ISO 8601 date normalization** (2 SP)
  - Normalize `DocumentMeta.report_date` → ISO 8601 before writing to `BuildingRecord.date_of_audit_report`
  - Add test asserting round-trip on 3 common date formats
- **E38-S9 — Resolve `fix-a-no-access-markers` worktree merge conflict** (1 SP)
  - Rebase the worktree onto `feat/sf-reconciliation-20260411`
  - Resolve `acm_extraction.py:1811` conflict in favor of Phase 2a fix
- **E38-S10 — Re-add `Est_Building_Size_m2__c` + `Hygienist_Recommendations__c`** (1 SP)
  - Update `BUILDING_SF_MAPPING` and `ITEM_SF_MAPPING`
  - Update `config/sf-schema-snapshot.json` to include both
- **E38-S11 — Clean up `schema_inference.py` 5 fabricated SF field names** (2 SP)
  - Enumerate exact offenders from extraction-core F2
  - Replace with real SF field names
  - Add contract test at `tests/test_schema_inference_contract.py`
- **E38-S12 — Pre-drop data migration for 3 non-empty fields** (2 SP, blocks E38-S2)
  - Migration: `UPDATE acm_record SET sample_result = result WHERE sample_result = NONE` (preserves 70 rows)
  - Then drop `result`, `room_id`, `risk_status` columns
- **E38-S13 — DB housekeeping** (1 SP)
  - Delete 3 zombie commands from `command` table
  - Delete 16 orphan `extraction_progress` records
  - Fix Ollama healthcheck `curl` → `wget` in `docker-compose.yml`

**Total estimated SP for full E38:** ~45 SP. Critical path: S0 → S6+S7+S10+S11 → S12 → S2 → S3 → S13. S1 is external.

---

## 5. Recording & provenance

### Agents that completed

| # | Agent | Findings file | Log size | Final summary |
|---|---|---|---|---|
| 0 | extraction-core | `phase-5-audit-extraction-core.md` (14.6 KB) | 684 B | summary in findings, 7 findings F1-F7 |
| 1 | extraction-pre | `phase-5-audit-extraction-pre.md` (12.5 KB) | 2.0 KB | marker present, 7 findings |
| 2 | extraction-post | `phase-5-audit-extraction-post.md` (12.2 KB) | 837 B | summary in findings, 6 findings F1-F6 |
| 3 | schema-expert | `phase-5-audit-schema-expert.md` (18.7 KB) | 2.1 KB | marker present, dead-field enumeration |
| 4 | observability | `phase-5-audit-observability.md` (8.4 KB) | 1.8 KB | marker present, clean bill |
| 5 | rag-strategist | `phase-5-audit-rag-strategist.md` (9.7 KB) | 1.8 KB | marker present, strategic verdict |
| 6 | db-state | `phase-5-audit-db-state.md` (20.1 KB) | 2.8 KB | marker present, 3-field data-loss + drift |
| 7 | log-sentinel | `phase-5-audit-logs.md` (14.3 KB) | 1.8 KB | marker present, 0 fab hits + Ollama fix |
| 8 | frontend-e2e | `phase-5-audit-frontend-e2e.md` (10.9 KB) | 1.6 KB | marker present, PARTIAL PASS verdict |

### Why extraction-core + extraction-post had tiny logs
The `tee` pipe captured what stdout emitted before the agent's own `Write` tool started writing the findings markdown. These 2 agents were the longest-running (21+ min); they exited after their final Write with minimal additional stdout. Findings are fully present in the MD files.

### Screenshots
`docs/cleanup/phase-5-screenshots/` — 7 files from the Broadmeadows E2E run.

### Live extraction artifact
- `source:cairo1ewyyn5rzz1pyfj` — Broadmeadows upload, 35 records extracted, 6 segmentation failures
- Pipeline time 285s / total 407s
- CSV exports confirmed clean in `docs/cleanup/phase-5-audit-frontend-e2e.md`

---

## 6. Next steps

1. **Apply this aggregate to sprint-status.yaml** — mark phase-5 done, expand E38 with S0, S6-S13
2. **Commit the aggregate + sprint-status update**
3. **Stop here.** Do NOT begin E38-S0 in this session — context is pressured, and the findings need your review before execution
4. **Out-of-band actions for you:**
   - Rotate the 4 leaked API keys + SF token (see session log §Security notes)
   - Decide: execute E38-S0 first (unblocks everything) or open PR on the current branch for review
   - Review the 7 screenshots at `docs/cleanup/phase-5-screenshots/`
   - Decide whether to close the `fix-a-no-access-markers` worktree or resume it (affects E38-S9 timing)
