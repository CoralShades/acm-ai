# MCS8: Ghost Save Fix — Progress

## Phase 1: Root Cause Analysis
- [x] Read base.py:save() — understood early-return guard at line 154
- [x] Read repository.py:repo_create() — understood GHOST-SAVE diagnostics
- [x] Read acm_extraction.py — found 5 workarounds (query-back, null FKs, disabled checkpointer)
- [x] Read parse_record_ids() — converts RecordID→string recursively
- [x] Read migration schemas — confirmed record<> types for source_id, building_record_id, parent_table_id
- [x] Root cause: repo_create returns error strings without raising; base.py swallows via early return

## Phase 2: Fix repo_create
- [ ] Make repo_create raise on non-dict results
- [ ] Add type assertion after parse_record_ids()
- [ ] Remove GHOST-SAVE diagnostic logging

## Phase 3: Fix base.py:save()
- [ ] Remove early-return guard at line 154
- [ ] Let failures propagate

## Phase 4: Fix record-link fields in acm_extraction.py
- [ ] Remove building_record_id = None workaround (line 2761)
- [ ] Remove parent_table_id = None workaround (line 2762)
- [ ] Remove query-back for building ID (lines 740-757)
- [ ] Remove query-back for section ID (lines 2679-2690)

## Phase 5: Fix LangGraph checkpointer serialization
- [ ] Replace Source object in state with source_id string
- [ ] Replace PipelineLogger in state with reconstructable reference
- [ ] Re-enable MemorySaver checkpointer

## Phase 6: Verification
- [ ] Tests pass
- [ ] Build passes
