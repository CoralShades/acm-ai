# Sprint Change Proposal — Salesforce Reconciliation

**Date:** 2026-04-11
**Author:** bmad-architect (AI-assisted, executed in main session)
**Branch:** `feat/sf-reconciliation-20260411`
**Status:** Draft — awaiting user review before merge
**Supersedes:** partial elements of SCP-20260207 (RAG Strategy Alignment) and implicit assumptions in PRD v3.0 about SF schema shape

## 1. Executive Summary

ACM-AI's Salesforce export path was audited against the live
`vaea-demidev` sandbox on 2026-04-11. The audit found three classes of
gap between the code and the actual SF schema, and one external
blocker that cannot be fixed from this repository.

### Gap summary

| Area | Gap | Status after this SCP |
|---|---|---|
| `sf_export.py` field mappings | ~21 fabricated SF field names that don't exist in demidev (Item__c had the worst contamination) | ✅ **Fixed** — rewrote both mapping tables against live describe |
| Extraction rule discipline | LLM inference over 4 SF-bound fields via corrective RAG Layer 2 | ✅ **Fixed** — 1-line surgical removal at `acm_extraction.py:1811` |
| External_ID__c strategy | Sequence-based IDs produced duplicates on re-extraction | ✅ **Fixed** — switched to deterministic hash |
| Item__c upsert capability | `Item__c.External_ID__c` is misconfigured in SF (textarea, externalId=false) | 🚨 **Blocked** on external VAEA SF admin change |
| Domain model / API / guardrails carry 127 refs to fields that don't exist in SF | | ⏭ **Deferred** to follow-up E38 story |
| Test suite was unaware of any of the above because no integration test runs against real SF | | ⏭ **Deferred** to Phase 3 (scorched-earth rebuild) |

### What this SCP proposes
1. **Accept** the Phase 2a + 2b changes on `feat/sf-reconciliation-20260411` (4 commits, +265 -56 lines net).
2. **Schedule** a new epic **E38 — SF Reconciliation Follow-Up** with 5 stories covering the deferred work.
3. **Escalate** the Item__c.External_ID__c blocker to the VAEA SF admin team as a prerequisite for the one-way-push export architecture documented in PRD FR-1406/1407.
4. **Update** PRD v3.0 and Architecture v3.0 to reflect the real field counts, real field names, and real Item__c upsert limitation.

## 2. Context

### 2.1 The premise
User direction from the 2026-04-11 interview:
> The main purpose of this app is extracting PDF documents and sending them to Salesforce (with AI querying, grid edits, citations in between). All other fields I might have missed mentioning are irrelevant. By querying the sandbox (read-only), you can get all required values, picklists, validations, etc.

This reframed the project from "document intelligence with SF as one destination" to "SF-aligned extraction pipeline". Everything not in the SF Building__c + Item__c schema was declared out of scope.

### 2.2 Interview-derived ruleset
Full list in `docs/cleanup/assumptions-and-decisions.md`. Load-bearing decisions:

- DEC-005: literal-only extraction + deterministic mapping. No LLM inference over SF-bound fields.
- DEC-007: deterministic External_ID via sha256(source_id + building_name).
- DEC-010: Item__c upsert blocker remediated by VAEA SF admin, not ACM-AI.
- DEC-018: checkpoint at each phase; defer aggressive work to fresh sessions.

### 2.3 What had been previously assumed
PRD v3.0 §14 and Architecture v3.0 §14.1 both describe:
- 29+ Building__c fields and 35+ Item__c fields (undercounted the real universe by ~3x).
- Working Data Loader upsert for both objects.
- `ITEM_SF_MAPPING` built during E33-S8 without cross-checking against a live SF describe.

The audit invalidated all three assumptions.

## 3. Changes in this SCP

### 3.1 Accepted into `feat/sf-reconciliation-20260411`

Commits:
```
444a66f9  fix(sf-export): rewrite field mappings + hash-based External_ID
7ad8a871  chore(audit): add picklists.json extract to Phase 1 artifacts
5dc3ef30  feat(sf): Phase 2a — schema snapshot + BAR→SF mapping + RAG fix
ebfabef0  chore: snapshot before SF reconciliation (Phase 1 audit)
```

#### 3.1.1 New config files

**`config/sf-schema-snapshot.json`** — 141 lines. Extractable-field-only
projection of the live `vaea-demidev` describe dumps. Documents:
- 25 extractable Building__c fields with types, restrictions, picklist values
- 21 extractable Item__c fields with the same metadata
- Dependent picklist chains:
  - `Friability_of_Material__c → ACM_Classification__c → ACM_Sub_Classification__c`
  - `Building_Type__c → Building_Category__c`
- Required-field list for each object
- `Item__c` upsert blocker documented inline with remediation options

Raw describe dumps are preserved under
`docs/sprint-artifacts/full-audit-2026-04-11/sf-describe/`.

**`config/bar_to_sf_mapping.yaml`** — 118 lines. Deterministic vocabulary
mapping table. Confirmed translations from live picklist data:

```yaml
Item__c:
  Condition__c:
    "Good": "Stable"
  Disturbance_Potential_of_Material__c:
    "Medium": "Moderate"
  Labelled__c:
    "YES": "Yes"
    "NO": "No"
Building__c:
  Public_Access__c:
    "YES": "Yes"
    "NO": "No"
  # + Asbestos_Register_Available__c, Audit_Report_Available__c, Within_Your_Portfolio__c
```

Identity mappings omitted (normalizer treats unmapped values as identity). `null` on the right side means "drop this value, do not write to SF".

#### 3.1.2 Extraction pipeline change — `open_notebook/graphs/acm_extraction.py`

Lines 1806-1822 (15 lines) replaced with lines 1806-1813 (6 lines):

```python
    # Layer 2 LLM correction disabled 2026-04-11 (SF reconciliation).
    # Why: literal-only extraction rule forbids LLM inference over SF-bound fields
    # (sample_result, material_condition, friable, disturbance_potential).
    # Remaining invalid values are now marked failed; operator must fix via grid.
    if records_needing_llm:
        for _idx in records_needing_llm:
            correction_stats["failed"] = correction_stats.get("failed", 0) + 1
```

Layer 1 (deterministic synonym substitution) at lines 1776-1804 is preserved — it is compliant with the literal-only rule.

`_llm_correct_records()` function definition at line 1853 is now dead code. Left in place to avoid touching test references in the same commit; scheduled for deletion in E38-S2.

#### 3.1.3 Export mapping rewrite — `open_notebook/extractors/exporters/sf_export.py`

Before: 27 Building__c mappings + 22 Item__c mappings with ~21 fabricated SF field names.
After: 25 Building__c mappings + 21 Item__c mappings, all verified against the live describe.

Key replacements in `ITEM_SF_MAPPING`:

| Old (fabricated) | New (real SF) |
|---|---|
| `Room_ID__c` | (deleted — no equivalent) |
| `Room_Name__c` | `Room_or_Area__c` |
| `Floor_Level__c` | `Level__c` |
| `ACM_Name__c` | `Item_Name__c` (+ `If_Other_Item_Name__c` fallback) |
| `ACM_Description__c` | (deleted — no equivalent) |
| `Extent__c` | `Units_of_Measure__c` (via `ACMRecord.extent`) |
| `Location__c` | `Location_in_Room__c` |
| `Risk_Status__c` | (deleted — formula field, not writable) |
| `Result__c` | (deleted — duplicate of Sample_Analysis_Result_Material_Status__c) |
| `Sample_No__c` | `NATA_Endorsed_Sample_no__c` |
| `Sample_Result__c` | `Sample_Analysis_Result_Material_Status__c` |
| `ACM_Labelled__c` | `Labelled__c` |
| `Disturbance_Potential__c` | `Disturbance_Potential_of_Material__c` |
| `Identifying_Company__c` | `Identifying_Hygiene_Consulting_Company__c` |
| `Hygienist_Recommendations__c` | (deleted — not a SF field) |

Key replacements in `BUILDING_SF_MAPPING`:

| Old (fabricated) | New (real SF) |
|---|---|
| `Building_Code__c` | (deleted — exists on Item__c as lookup to Building, not on Building__c itself) |
| `Est_Building_Size_m2__c` | (deleted — no SF field for building size) |
| `Daily_Duration__c` | (deleted — only a formula score field exists) |
| `Level_of_Activity__c` | (deleted — only a formula score field) |
| `Mobile_Plant__c` | (deleted — only a formula score field) |

Plus additions for real fields that were missing:
`School_UID__c`, `Within_Your_Portfolio__c`, `GPS_Coordinates_provided_by_metro__c`.

#### 3.1.4 External_ID generator rewrite

```python
def generate_external_id(building: object, source_id: str) -> str:
    """Generate a stable External_ID__c for a building.

    Resolution order (2026-04-11 — deterministic hash-based):
      1. building.external_id (if already set) — honour stored value
      2. building.building_unique_id (if set) — consultant-provided ID
      3. Deterministic hash: "ACM_" + sha256(source_id + building_name)[:16]
    """
```

Previous behaviour: sequence-based fallback `{source_part}_{code}` produced different IDs on re-extraction. New behaviour: same PDF → same building → same ID → SF upsert updates in place.

Smoke-test sample: `generate_external_id` on `(building_name="Broadmeadows Police Station", source_id="source:abc123xyz")` produces `ACM_9c631b45bb3cf1b1`.

### 3.2 Audit artifacts (already committed)

All under `docs/sprint-artifacts/full-audit-2026-04-11/`:

- `PHASE-1-FINDINGS.md` (~11 KB) — full gap matrix vs PRD, required fields, extractable subsets
- `sf-describe/Building__c.json` (14,463 lines) — raw SF describe
- `sf-describe/Item__c.json` (16,203 lines) — raw SF describe
- `sf-describe/picklists.json` — extracted picklist values for target fields
- `rag-disposition-research.md` — Sonnet subagent's Option C recommendation with code locations

### 3.3 Session artifacts (this SCP bundle)

All under `docs/cleanup/`:
- `README.md` — directory overview
- `session-log-2026-04-11.md` — chronological narrative
- `assumptions-and-decisions.md` — interview-derived ruleset
- `phase-4-doc-cleanup-manifest.md` — deletion manifest from Phase 4 subagent (awaiting review)

## 4. Deferred Work — Proposed Epic E38

E38 — SF Reconciliation Follow-Up. 5 stories, estimated 18-24 story points.

### E38-S1 — VAEA SF Admin External_ID fix (external dependency)
- **Owner**: VAEA SF admin team (not ACM-AI dev)
- **Ask**: Change `Item__c.External_ID__c` from `Text Area(32768)` to `Text(255)` with `externalId=true, unique=false`
- **Blocks**: All Item__c upsert functionality
- **Acceptance**: `sf sobject describe --sobject Item__c` reports `External_ID__c.type == 'string'` and `.externalId == true`
- **ACM-AI cost**: zero (external)

### E38-S2 — Delete 127 non-SF field references
- **Scope**: Remove the following fields from all Python files:
  - `est_building_size_m2`, `daily_duration`, `level_of_activity`, `mobile_plant`
  - `building_risk_rating`, `building_sub_category`
  - `psb_district_region`, `demolished_status`, `demolition_date`, `demolition_type`, `demolition_comments`
  - `building_out_of_scope`, `building_out_of_scope_comments`
  - `no_identified_acms`, `no_identified_acms_note`
  - `room_id`, `risk_status`, `result`, `hygienist_recommendations`, `psb_supplied_acm_id`
  - `removal_status`, `date_of_removal`, `quantity_removed`, `removal_notification_no`, `epa_certificate_no`
- **Affected files** (approx.):
  - `open_notebook/domain/acm.py` (28 refs)
  - `api/models.py` (43 refs)
  - `api/routers/acm.py` (4 refs)
  - `open_notebook/graphs/guardrails.py` (6 refs)
  - `open_notebook/graphs/acm_extraction.py` (1 ref)
  - `open_notebook/extractors/acm_schemas_v3.py` (1 ref)
  - `open_notebook/domain/site_config.py` (2 refs)
  - Plus any frontend TypeScript that renders them
- **Also**: delete `_llm_correct_records()` function definition (dead code after 5dc3ef30)
- **Acceptance**: `uv run pytest` green (after Phase 3 rebuild), `grep -r 'est_building_size_m2' open_notebook/ api/` returns zero hits
- **Estimate**: 5 SP

### E38-S3 — Tests scorched earth + agent-team rebuild
- **Scope**: Delete `tests/`, `frontend/tests/`, `*.spec.ts`; rebuild via Sonnet agent team with access to skill registry + context7 + MCP tools
- **Rationale**: Existing tests never caught the fabricated SF field mappings; coverage was theatre
- **Rebuild priorities**:
  1. Contract tests that assert every field in `sf_export.py:ITEM_SF_MAPPING` + `:BUILDING_SF_MAPPING` exists in the SF describe dump
  2. BAR→SF mapping round-trip tests (feed known BAR values through the normalizer, verify SF-valid output)
  3. External_ID determinism test (same input produces same hash across runs)
  4. Extraction pipeline integration test against `docs/samplePDF/Clutch_Broadmeadows.pdf`
  5. Re-establish existing domain/migration/repository test coverage
- **Acceptance**: `uv run pytest` green, coverage report shows sf_export.py + acm_extraction.py extraction path covered
- **Estimate**: 8 SP

### E38-S4 — BAR→SF mapping management UI (frontend)
- **Scope**: Build the frontend UI to create and manage `config/bar_to_sf_mapping.yaml` entries. User flagged that "we already have some parts made but not functioning" — find existing skeleton via grep before scaffolding new components
- **Affected files**: `frontend/src/app/**/sf-mapping/*`, new Zustand store slice, new API endpoints in `api/routers/acm.py`
- **Acceptance**: admin user can view current mappings, add/edit/delete entries, save changes to the YAML file (via API), see validation against current `sf-schema-snapshot.json`
- **Estimate**: 5 SP

### E38-S5 — 6-agent post-code audit
- **Scope**: Run the 6-agent audit team (acm-extraction-core, acm-extraction-pre, acm-extraction-post, acm-schema-expert, acm-observability-debugger, acm-rag-strategist) on `feat/sf-reconciliation-20260411` after E38-S2 and E38-S3 land. Each agent reviews its domain for remaining non-SF drift.
- **Model policy**: Sonnet only, per CLAUDE.md agent-teams rule
- **Acceptance**: 6 reports aggregated into a single findings doc; any critical findings become new stories
- **Estimate**: 3 SP

## 5. Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| VAEA SF admin refuses to fix `Item__c.External_ID__c` | Medium | High — forces INSERT-only fallback | SCP documents 3 alternative paths (new field, INSERT-only + dedupe warning, live-API query-then-update). INSERT-only is the fallback. |
| Phase 3 test rebuild misses edge cases existing tests covered | High | Medium | Preserve the old tests in a `tests-legacy-20260411/` snapshot commit before deleting. Rebuild can consult the snapshot. |
| BAR→SF mapping YAML grows into a complex DSL | Medium | Medium | Keep it shallow. If it needs logic, promote to Python code with tests. YAML stays declarative. |
| Frontend BAR→SF mapping UI conflicts with existing unfinished code | Medium | Low | E38-S4 starts with discovery grep before scaffolding |
| `_llm_correct_records()` dead-code removal breaks something we missed | Low | Low | Deferred to E38-S2. Single caller already removed in 5dc3ef30. |
| Deleting 127 field refs breaks frontend TypeScript builds | Medium | Medium | E38-S2 runs `cd frontend && npm run build` before PR merge |
| `docs/interview/` (untracked in main) is accidentally committed | Low | High (privacy) | Explicitly excluded from all staged commits in this session |

## 6. Rollback Plan

If Phase 2a + 2b need to be reverted:

```bash
# Full rollback
git checkout main
git branch -D feat/sf-reconciliation-20260411

# Partial rollback — keep audit artifacts, drop code changes
git checkout main
git cherry-pick ebfabef0 7ad8a871   # keep snapshot + picklists
# skip 5dc3ef30 and 444a66f9
```

Config files at `config/sf-schema-snapshot.json` and `config/bar_to_sf_mapping.yaml` are inert — nothing reads them yet. Safe to leave or remove independently.

The surgical RAG fix at `acm_extraction.py:1811` is the only load-bearing runtime change. Reverting that single chunk restores pre-SCP behaviour.

## 7. Acceptance Checklist

- [ ] User reviews all 4 commits on `feat/sf-reconciliation-20260411`
- [ ] User runs `uv run ruff check .` and `cd frontend && npm run lint` locally — both green
- [ ] User contacts VAEA SF admin with the E38-S1 ask
- [ ] User updates `sprint-status.yaml` to mark E38 as drafted (done as part of this session)
- [ ] User decides whether to merge as-is or wait for E38-S1 external fix
- [ ] User rotates the `vaea-demidev` access token (`sf org logout` + `sf org login web`) — leaked in session
- [ ] (Optional) User reviews and executes the Phase 4 doc-cleanup manifest at `docs/cleanup/phase-4-doc-cleanup-manifest.md`

## 8. Open Questions

1. **Should `docs/interview/` be added to `.gitignore`?** It contains unrelated job-interview materials that keep appearing as untracked noise.
2. **What is the SLA from VAEA SF admin?** If >2 weeks, E38-S3 (tests) should build a mock SF describe fixture so tests can run without the fix landing.
3. **Does `Est_Building_Size_m2__c` matter to downstream consumers?** The audit deleted it from export, but if any SF formula or report depends on it, we need to know before E38-S2.
4. **Should `_llm_correct_records()` be deleted in this SCP or deferred to E38-S2?** Current answer: deferred (avoids cross-file coupling in the Phase 2b commit). Easy to revisit.

## 9. Traceability

- PRD FR-1401..FR-1411: scope still valid but field counts need update
- PRD FR-1405: confirmed (Good → Stable mapping)
- PRD FR-1406/1407: blocked on E38-S1 for Item__c
- PRD FR-1408: `config/sf-schema-snapshot.json` is the new canonical source; legacy `V3/output/building_fields_summary.md` + `item_fields_summary.md` are now stale and should be deleted by Phase 4
- PRD FR-1410 two-phase extraction: partially implemented; Building__c extraction phase is still missing (deferred)
- Architecture v3.0 §14.1: Mermaid ER diagram needs update to match `config/sf-schema-snapshot.json`
- `docs/sprint-artifacts/sprint-status.yaml`: E38 epic added in this session
