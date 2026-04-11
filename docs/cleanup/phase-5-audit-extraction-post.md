# Phase 5 Audit — Extraction-Post Domain

**Agent:** EXTRACTION-POST
**Date:** 2026-04-11
**Branch:** `feat/sf-reconciliation-20260411`
**Scope:** Consensus engine, corrective validation, provenance, export formatting.

---

## Scope

Files inspected:

| File | Purpose |
|------|---------|
| `open_notebook/graphs/acm_extraction.py` (1705–2101) | `correct_records`, `validate_records_strict`, `should_correct`, `_apply_field_correction`, `_llm_correct_records` |
| `open_notebook/extractors/validators/acm_validator.py` | `validate_acm_record`, `validate_enum_fields`, `sf_valid_fields`, `validate_sf_chains` |
| `open_notebook/extractors/validators/sf_picklist_validator.py` | `SalesforcePicklistValidator`, `normalize_record_to_sf`, `SF_FLAT_ENUM_FIELD_MAP` |
| `open_notebook/extractors/consensus/engine.py` | `ConsensusEngine._merge_group`, `_vote_field`, `_assign_tier` |
| `open_notebook/extractors/consensus/resolver.py` | `ConflictResolver._escalate`, L1–L4 chain |
| `open_notebook/extractors/exporters/sf_export.py` | `BUILDING_SF_MAPPING`, `ITEM_SF_MAPPING`, `item_to_sf_row`, `building_to_sf_row` |
| `open_notebook/extractors/parsers/config_loader.py` | `load_field_schema` (BAR enums), `load_sf_field_schema` (V3/output markdown) |
| `prompts/acm/correction.jinja` | LLM correction prompt template |
| `config/sf-schema-snapshot.json` | Phase 2a SF schema reference |
| `config/bar_to_sf_mapping.yaml` | Phase 2a BAR→SF vocabulary mapping |

---

## Findings

### F1 — Layer 1 (deterministic synonym substitution) still runs correctly

**Status:** PASS with minor counter issue.

`correct_records` at lines 1770–1801 iterates all validation issues and calls
`normalize_enum_value()` for each `enum_mismatch` or `invalid_sf_enum` issue before
reaching the dead LLM block. `_apply_field_correction` (line 1796) is still invoked
for every successful Layer 1 synonym hit. The surgical removal at 1806–1813 only
affects records in `records_needing_llm` (those Layer 1 could not fix).

**Counter double-increment issue (LOW):** `enable_corrective_loop: True` +
`max_correction_attempts: 2` (lines 3215–3216) means the graph runs `correct_records`
up to twice. A record that Layer 1 cannot fix is added to `records_needing_llm` on
both passes. Each pass increments `correction_stats["failed"]` once per record, so
a permanently-unfixable record increments `failed` twice. The `agui.emit_step_finished`
call at line 1826 also reports `llm_corrected=0` on every pass. No functional
consequence — records still proceed to deduplication — but the `failed` counter in
the pipeline log is inflated by a factor of up to `max_correction_attempts`.

**Recommendation:** After line 1813, set `enable_corrective_loop: False` in the
returned state dict if Layer 1 found nothing to correct on this pass, or add a
deduplication guard so the `failed` counter is not incremented more than once per
record. Alternatively lower `max_correction_attempts` to 1.

---

### F2 — `_llm_correct_records` and `prompts/acm/correction.jinja` are dead code

**Status:** CONFIRMED dead. No other callers exist.

`prompts/acm/correction.jinja` is rendered only at `acm_extraction.py:1916`, inside
`_llm_correct_records()`. That function (defined at line 1853) has zero callers: the
only call site was the `await _llm_correct_records(...)` at lines 1806–1813, which
was replaced by the no-op counter block in commit `5dc3ef30`.

`grep -rn "correction.jinja\|_llm_correct_records"` across all Python files confirms
no other callers. The function definition at line 1853 and the `correction.jinja`
template are orphaned and can be deleted in a follow-up cleanup pass.

**Downstream note:** `_apply_field_correction` at line 1839 is still live — it is
called by Layer 1 (line 1796) and was also referenced by `_llm_correct_records`
(line 2018). It can stay; only `_llm_correct_records` itself is dead.

---

### F3 — ConsensusEngine votes without SF picklist awareness (by design, with one misleading artefact)

**Status:** ARCHITECTURAL GAP documented; L3 metadata is misleading.

**Design (correct):** `ConsensusEngine._merge_group` normalises values to
`str().strip().lower()` for vote comparison but does not validate against SF picklist
values. This is correct by design: the consensus layer reconciles multi-provider
disagreement; SF validation is downstream in `validate_records_strict`. For a record
where both providers agree (e.g., both extract `"Good"` for `material_condition`),
the engine returns `"Good"` with HIGH tier, and Layer 1 in `correct_records` later
normalises it to `"Stable"`.

**Single-provider pass-through:** For single-provider records (`len(field_votes_for_field) == 1`,
line 271–278 in engine.py), the value is accepted with `score=1.0, contested=False`
without any SF check. SF validation catches this downstream. No gap for current
single-provider use (most jobs run one provider).

**L3 stub produces misleading consensus_metadata (LOW):** `ConflictResolver._l3_llm_stub`
(resolver.py:198) returns `score=0.5` with `resolver_used="llm_arbitration"`.
Because `score >= 0.4` (line 138 of resolver.py), L4 human queue is effectively
unreachable in practice — L3 always resolves. But every field resolved at L3 is
logged as `resolver_used="llm_arbitration"` in `consensus_metadata`, implying LLM
involvement that never occurred. Story E31-S5 (real LLM arbitration) was never
implemented. This creates audit trails that overstate LLM involvement in conflict
resolution.

**Recommendation:** Update `_l3_llm_stub` to set `resolver_used="l3_stub"` until
E31-S5 is implemented. Add a TODO comment noting L4 is unreachable.

---

### F4 — Provenance tracking is correct, but `_merge_site_config` injects unverified SF field names

**Status:** Provenance design PASS; `_merge_site_config` has a fabricated-field risk.

**Provenance design (correct):** `consensus_metadata` is stored on `ACMRecord` in
SurrealDB. The `/api/acm/provenance/{record_id}` endpoint (acm.py:2968) exposes it
for the ProvenanceViewer UI. `sf_export.py`'s `ITEM_SF_MAPPING` and `BUILDING_SF_MAPPING`
correctly exclude `consensus_metadata` from the CSV columns — it is internal-only.
No provenance-per-SF-field trail is produced in the export, which is the correct
design: Data Loader does not consume provenance data.

**`_merge_site_config` fabricated fields (MEDIUM):** `sf_export.py:229–233` injects
`Department__c` and `Agency__c` directly into the building export row. These names
do not appear in `BUILDING_SF_MAPPING` (which was verified against the live describe
dump). `config/sf-schema-snapshot.json` contains `Responsible_Agency_Department__c`
(a single combined field), not `Department__c` and `Agency__c` as separate fields.
If `SiteConfig.department` or `SiteConfig.agency` are populated, the exported CSV
will include columns that don't exist in demidev — the same class of bug that Phase
2b fixed. This code path is guarded by `if site_config is not None` so it only fires
when the caller passes a `SiteConfig`, but the risk is latent.

**Recommendation:** Either verify `Department__c` and `Agency__c` exist in
demidev via `sf sobject describe --sobject Building__c`, or replace with
`Responsible_Agency_Department__c` (the confirmed field name), or guard with
a comment explaining the divergence.

---

### F5 — `validate_records_strict` reads from `V3/output/*.md`, not `config/sf-schema-snapshot.json`

**Status:** SCHEMA SOURCE FRAGMENTATION — three separate sources, new snapshot consumed by nothing.

`acm_validator.py` uses two sources for valid enum values:

| Source | Function | Role | Path |
|--------|----------|------|------|
| `V3/output/building_fields_summary.md` + `item_fields_summary.md` | `load_sf_field_schema()` | Primary blocking SF authority | `open_notebook/extractors/parsers/config_loader.py:409` |
| `docs/samplePDF/instructions-sample/register_enums.json` | `load_field_schema()` | Legacy BAR enums — audit-only (non-blocking) | `config_loader.py:211` |

`config/sf-schema-snapshot.json` — the Phase 2a deliverable — is **not imported
by any Python file**. It is human-readable reference documentation only. The
validator's primary picklist source is the pre-existing `V3/output/*.md` markdown
tables, not the new snapshot.

`config/bar_to_sf_mapping.yaml` is **not imported at runtime** but IS consumed by
the test suite. `tests/conftest.py:44` provides a `bar_to_sf_mapping` fixture and
`tests/test_bar_to_sf_mapping.py` runs round-trip invariants against it. The
synonym mappings it documents (e.g., `Good → Stable`, `Medium → Moderate`) are
also hard-coded in `sf_picklist_validator.py:_VALUE_ALIASES` (lines 67–78). The
YAML is the test oracle; the `_VALUE_ALIASES` dict is the runtime implementation.
Any update to synonyms must be applied to both.

**Fragmentation risk:** `V3/output/*.md` and `config/sf-schema-snapshot.json` will
diverge independently since neither is auto-generated from the other. If the VAEA
admin changes a picklist value in demidev, the `V3/output/*.md` files (parse-based)
and `sf-schema-snapshot.json` (manual compact snapshot) must both be updated
separately. There is no `load_sf_snapshot()` function that reads the snapshot.

**Test oracle (important nuance):** `tests/test_sf_export_contract.py` imports
`sf-schema-snapshot.json` as a contract oracle and checks that every SF name in
`BUILDING_SF_MAPPING` and `ITEM_SF_MAPPING` exists in the snapshot. This means the
snapshot IS consumed — but only by the test suite, not at runtime. The contract tests
would catch a fabricated name added to the mapping tables. They would NOT catch
fabricated names injected by `_merge_site_config` (which bypasses the mapping tables;
see F4).

**Recommendation:** Either:
(a) Wire `config/sf-schema-snapshot.json` as a third (or replacement) source for
`SalesforcePicklistValidator`, giving it a single authoritative runtime file;
(b) Or document explicitly in `sf-schema-snapshot.json` that it is the test-oracle
and `V3/output/*.md` is the runtime picklist source. Add a note that `_merge_site_config`
bypasses the contract tests and must be maintained manually. Decide before the
snapshot and markdown tables diverge.

---

### F6 — Minor: `Survey_Date__c` mapping points to wrong Python field

**Status:** LOW — worth verifying before go-live.

`ITEM_SF_MAPPING` contains `("Survey_Date__c", "date_identified")` (sf_export.py:80).
`ACMRecord.date_identified` has `validation_alias=AliasChoices("date_identified",
"Date_Identified__c")` (acm.py:318–320). The Python field holds the item-level
identification date, and it aliases to `Date_Identified__c` in the domain model —
not `Survey_Date__c`. The building-level survey date is on `BuildingRecord.date_of_inspection`
(acm.py:148) which has alias `Survey_Date__c`. Whether the item-level `date_identified`
correctly maps to `Survey_Date__c` in SF should be validated against the demidev
schema before first export.

---

## Recommendations Summary

| ID | Severity | Action |
|----|----------|--------|
| R1 | LOW | Fix `failed` counter double-increment: lower `max_correction_attempts` to 1, or reset loop flag after Layer 1 no-op pass |
| R2 | LOW | Delete `_llm_correct_records()` function (lines 1853–~2040) and `prompts/acm/correction.jinja` in a follow-up pass |
| R3 | LOW | Fix L3 stub metadata: set `resolver_used="l3_stub"` until E31-S5 is implemented |
| R4 | MEDIUM | Verify or fix `_merge_site_config` SF field names (`Department__c`, `Agency__c`) against live demidev |
| R5 | MEDIUM | Resolve schema source fragmentation: decide whether `config/sf-schema-snapshot.json` should be wired to the validator or remain reference-only |
| R6 | LOW | Verify `Survey_Date__c → date_identified` mapping against demidev `Item__c` schema |

---

## References

- `docs/cleanup/assumptions-and-decisions.md` — DEC-005, DEC-006, DEC-009
- `docs/sprint-artifacts/full-audit-2026-04-11/rag-disposition-research.md`
- `docs/sprint-artifacts/change-proposals/sprint-change-proposal-20260411-sf-reconciliation.md`
- Commit `5dc3ef30` (Phase 2a: RAG surgical fix + schema snapshot)
- Commit `444a66f9` (Phase 2b: sf_export.py rewrite)
