# MCS8-Gap1: Fix Ghost Save in base.py + SurrealDB Record Link Handling
# Generated from MCS7 validation audit — 2026-03-19

**SP: 5 | Priority: P0 | Dependencies: MCS7 validation complete (fa1ff9a4)**
**Audit ref: Pipeline Persistence Timing Audit (2026-03-19)**
**Related commits: fa1ff9a4, 5d560d06, 167f0c43**

## Skills to Load

/systematic-debugging — root cause the repo_create return type issue
/langgraph-persistence — understand LangGraph checkpoint vs DB persistence
/planning-with-files — persistent markdown plan
/verification-before-completion — verify saves persist end-to-end
/e2e-test — browser verification after fix
/acm-observability — trace save operations via Langfuse/Logfire
/test-driven-development — write failing test before fix

---

## Problem Statement

During MCS7 validation, `base.py:save()` at line 137 calls `repo_create()` which calls `connection.insert()`. The SurrealDB Python client returns a **string** instead of a dict for certain tables (`building_record`, `acm_table_section`). The current guard at line 154 catches this and returns early — but `self.id` is never populated, causing downstream FK failures.

### Evidence from MCS7

```
[GHOST-SAVE] acm_record insert returned string: 'Found source:b6eswuntqoxyozgvv995
for field `source_id`, with record `acm_record:2ae51xi16rzea2re6ynk`,
but expected a string'
```

**Root cause**: The SurrealDB Python client auto-converts strings matching `table:id` format to `RecordID` objects. When a field type is `TYPE string` but the value is auto-parsed as a RecordID, SurrealDB rejects it. When the field type is `TYPE record<table>`, it works.

### Workarounds applied during MCS7 (need proper fix)

1. `base.py:153-159` — guard that returns early on non-dict response
2. `acm_extraction.py:740-757` — query-back building ID after save
3. `acm_extraction.py:2679-2690` — query-back section ID after save
4. `acm_extraction.py:2761-2762` — null out `building_record_id` and `parent_table_id` before save
5. `acm_extraction.py:2884` — disabled LangGraph checkpointer entirely
6. Schema reverted: `source_id` back to `TYPE record<source>` (the "fix" of changing to string WAS the bug)

---

## Key Files

**Read (understand the bug):**
- `open_notebook/domain/base.py` — lines 112-175, the `save()` method
- `open_notebook/database/repository.py` — lines 85-116, `repo_create()` + GHOST-SAVE diagnostics
- `open_notebook/graphs/acm_extraction.py` — lines 2625-2770, `save_records` node
- `open_notebook/graphs/acm_extraction.py` — lines 700-760, building save + query-back
- `docs/reviews/multi-consultant-validation-results.md` — Bug #1-#5 documentation

**Modify:**
- `open_notebook/domain/base.py` — proper handling of non-dict repo results
- `open_notebook/database/repository.py` — ensure `parse_record_ids` always returns list of dicts
- `open_notebook/graphs/acm_extraction.py` — remove workarounds once root cause fixed

**Test:**
- `tests/test_base_save.py` (create) — unit tests for save with various repo_create return types
- `tests/test_acm_record_persistence.py` (create) — integration test: save ACMRecord + verify in DB

---

## Plan

### Phase 1: Root Cause (Debugging)
- [ ] Write test that reproduces the string return from `connection.insert()` for `building_record`
- [ ] Identify which fields trigger RecordID auto-parsing in the SurrealDB Python client
- [ ] Determine: is `parse_record_ids()` the culprit, or is it `connection.insert()` itself?
- [ ] Document the exact SurrealDB Python client version and behavior

### Phase 2: Fix repo_create
- [ ] Ensure `repo_create` ALWAYS returns `List[Dict[str, Any]]` — never a string
- [ ] If `connection.insert()` returns a string error, raise an exception (don't swallow)
- [ ] Add type assertion after `parse_record_ids()` call
- [ ] Remove GHOST-SAVE diagnostic logging (replace with proper error handling)

### Phase 3: Fix base.py:save()
- [ ] Remove the early-return guard at line 154 — it masks real failures
- [ ] If repo_create raises, let it propagate (callers handle it)
- [ ] Ensure `self.id` is always populated after successful save
- [ ] Remove query-back workarounds from `acm_extraction.py` (lines 740-757, 2679-2690)

### Phase 4: Fix record-link fields
- [ ] Remove `building_record_id = None` workaround at line 2761
- [ ] Verify `building_record_id` and `parent_table_id` save correctly with `record<>` types
- [ ] Re-enable LangGraph checkpointer (remove comment at line 2884) — requires Phase 5

### Phase 5: Fix LangGraph Checkpointer Serialization
- [ ] Audit graph state for non-serializable objects (`Source`, `PipelineLogger`)
- [ ] Replace `Source` object in state with `source_id: str` + load on demand
- [ ] Replace `PipelineLogger` in state with logger name string + reconstruct
- [ ] Re-enable `MemorySaver()` checkpointer
- [ ] Verify HITL interrupt/resume still works (MCS6 dependency)

### Phase 6: Verification
- [ ] Run Broadmeadows extraction — verify 31+ records persist with NO workarounds
- [ ] Run Alexander extraction — verify 36+ records persist
- [ ] Verify `building_record_id` FK is populated (not NULL)
- [ ] Verify `parent_table_id` FK is populated
- [ ] Browser verification: buildings appear in frontend during extraction
- [ ] Run /e2e-test for extraction workflow
- [ ] Run /acm-observability to verify traces

---

## Agent Strategy: Agent Team (Opus)

Create team `mcs8-ghost-save` with 3+ agents:

| Agent | Role | Model | Tasks |
|-------|------|-------|-------|
| `debugger` | Root cause analysis + fix base.py/repository.py | opus | Phase 1-3 |
| `graph-fixer` | Fix LangGraph state serialization + re-enable checkpointer | opus | Phase 4-5 |
| `validator` | Write tests + run verification + browser check | opus | Phase 6 |

```
Spawn with: TeamCreate → Agent(team_name="mcs8-ghost-save", model="opus")
```

---

## Context7 Directives

Fetch latest docs for:
- `surrealdb` Python SDK — `connection.insert()` return types
- `langgraph` — MemorySaver checkpointer serialization requirements

---

## Verification Checklist

- [ ] `base.py:save()` — no early-return guard, proper error propagation
- [ ] `repo_create()` — always returns `List[Dict]`, raises on failure
- [ ] All 5 MCS7 workarounds removed from `acm_extraction.py`
- [ ] LangGraph checkpointer re-enabled with serializable state
- [ ] Broadmeadows: 31+ records with `building_record_id` populated
- [ ] Alexander: 36+ records with `building_record_id` populated
- [ ] Frontend shows buildings during extraction (browser test)
- [ ] `/e2e-test` passes for extraction workflow
- [ ] `/acm-observability` traces show clean save operations

---

## Commit Template

```
fix(persistence): resolve ghost save bug in base.py and re-enable LangGraph checkpointer

- Root cause: SurrealDB Python client auto-parses record-link strings as RecordIDs
- Fix repo_create to always return List[Dict], raise on string returns
- Remove 5 MCS7 workarounds (query-back, null FKs, disabled checkpointer)
- Make LangGraph state fully serializable (Source → source_id, PipelineLogger → name)
- Re-enable MemorySaver checkpointer for HITL support
- Integration tests: verify building_record_id FK populated end-to-end

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>
```
