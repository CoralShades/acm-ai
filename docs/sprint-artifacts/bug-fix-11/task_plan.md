# Bug Fix 11 Phase 2: Extraction Quality — 16→31 Records

**Created**: 2026-03-11
**Source**: Clutch_Broadmeadows.pdf (source:rw12h46pyx00urdp545v)
**Baseline**: 16/31 records (52% recall) after Phase 1 fixes
**Target**: 31/31 records (100% recall) with >80% field accuracy
**Ground Truth**: `benchmarks/ground_truth/broadmeadows.json`

## Dependencies

| Issue | Priority | Blocks |
|-------|----------|--------|
| `bug-page-range-table-loss` | P0 | Record count (estimated +10-15 records) |
| `bug-per-row-schema-missing-fields` | P0 | Field accuracy + benchmark matching |
| `bug-row-segmenter-subheaders` | P1 | `internal_external` field accuracy |
| `bug-building-record-not-persisted` | P1 | Frontend building view |
| `bug-correction-stage-format-json` (existing) | P1 | Ollama correction quality |
| `bug-extraction-progress-stuck-running` (existing) | P1 | Benchmark automation reliability |

## Execution Plan

### Phase 1: Record Recovery (P0 — fixes record count) [estimated +15 records]

#### Task 1.1: Fix `_merge_provider_tables` multi-table-per-page overwrite
- **File**: `commands/source_commands.py:276-317`
- **Change**: `docling_by_page[t.page] = t` → `docling_by_page[t.page].append(t)` (defaultdict(list))
- **Update**: All downstream consumers of `docling_by_page` to handle lists
- **Test**: Fixture with 2 tables on same page → both preserved
- **Status**: [ ] Not started

#### Task 1.2: Fix building `page_end` for single-building documents
- **File**: `open_notebook/extractors/building_inventory.py`
- **Change**: When only 1 building in inventory, set `page_end = total_pages` (no cross-building risk)
- **Also**: Use `site_name` from metadata as building name instead of "Main Building"
- **Test**: Single-building doc → page_end equals total_pages
- **Status**: [ ] Not started

#### Task 1.3: Fix page filter silent fallback + page_number=0 handling
- **File**: `open_notebook/extractors/row_segmenter.py:486-494`
- **Change**: Log warning on fallback; include `page_number=0` tables in all buildings
- **Test**: Tables with page_number=0 included in extraction
- **Status**: [ ] Not started

#### Task 1.4: Add page range exclusion warning in orchestrator
- **File**: `open_notebook/extractors/orchestrator.py:51-57`
- **Change**: Log count of excluded tables when page filter removes any
- **Test**: Warning logged when tables outside building range exist
- **Status**: [ ] Not started

### Phase 2: Field Completeness (P0 — fixes field accuracy) [estimated +5 fields per record]

#### Task 2.1: Add `sample_number`, `sample_result`, `acm_product` to ACMItemRow
- **File**: `open_notebook/domain/acm_row_schemas.py`
- **Change**: Add 3-4 new Optional fields to ACMItemRow model
- **Test**: Pydantic validation accepts new fields
- **Status**: [ ] Not started

#### Task 2.2: Update row extraction prompt for new fields
- **File**: `prompts/acm/row_extraction.jinja`
- **Change**: Add extraction instructions for sample_number, sample_result, product
- **Constraint**: Keep within num_ctx=2048 budget (9→12-13 fields)
- **Test**: Prompt renders correctly with new field instructions
- **Status**: [ ] Not started

#### Task 2.3: Update mapper to use new fields
- **File**: `open_notebook/domain/acm_row_mappers.py`
- **Change**: Map `sample_result` → `result`, `sample_number` → `sample_number`, `acm_product` → `acm_product`
- **Remove**: `result="Unknown"` hardcode
- **Test**: Mapped record has correct field values
- **Status**: [ ] Not started

#### Task 2.4: Add `internal_external` to ACMItemRow + segmenter
- **File**: `open_notebook/domain/acm_row_schemas.py`, `row_segmenter.py`
- **Change**: Add `INTERNAL` to `_LEVEL_REGEX`, track `internal_external` context, add field to schema
- **Test**: "Internal" sub-header sets context for subsequent rows
- **Status**: [ ] Not started

### Phase 3: Building Persistence (P1 — fixes frontend) [enables building view]

#### Task 3.1: Persist buildings to `building_record` table
- **File**: `open_notebook/graphs/acm_extraction.py`
- **Change**: After inventory compilation, UPSERT each BuildingMeta to `building_record`
- **Verify**: Migration exists for `building_record` table
- **Test**: After extraction, `building_record` table has entries
- **Status**: [ ] Not started

#### Task 3.2: Use site_name for generic fallback building names
- **File**: `open_notebook/extractors/building_inventory.py`
- **Change**: When generic fallback creates buildings, use `document_metadata.site_name` as name
- **Test**: Building name = "Broadmeadows Police Station" not "Main Building"
- **Status**: [ ] Not started

### Phase 4: Correction + Progress Fixes (P1 — existing issues)

#### Task 4.1: Apply `format="json"` to correction stage
- **File**: `open_notebook/graphs/acm_extraction.py` (~line 2600)
- **Change**: `correction_model = _apply_ollama_extraction_settings(correction_model)`
- **Test**: Ollama correction returns valid JSON
- **Status**: [ ] Not started
- **Ref**: `docs/issues/bug-correction-stage-format-json.md`

#### Task 4.2: Add terminal status write for extraction progress
- **File**: `commands/acm_commands.py`
- **Change**: Explicit status="completed" write after graph END node
- **Test**: extraction_progress shows "completed" after extraction finishes
- **Status**: [ ] Not started
- **Ref**: `docs/issues/bug-extraction-progress-stuck-running.md`

### Phase 5: Verification

#### Task 5.1: Run benchmark harness against ground truth
- **Command**: `uv run python scripts/research/e29_benchmark_harness.py`
- **Target**: Broadmeadows ≥28/31 records (90% recall), ≥70% field accuracy
- **Status**: [ ] Not started

#### Task 5.2: Live extraction with agent-browser screenshots
- **Steps**: Upload Broadmeadows PDF → extract → verify records in UI → screenshots
- **Target**: All 31 records visible, building name correct, fields populated
- **Status**: [ ] Not started

## Subagent Routing

| Task | Agent Type | Model |
|------|-----------|-------|
| 1.1-1.4 | `backend-specialist` | sonnet |
| 2.1-2.4 | `backend-specialist` | sonnet |
| 3.1-3.2 | `backend-specialist` | sonnet |
| 4.1-4.2 | `backend-specialist` | sonnet |
| 5.1 | `qa-specialist` | sonnet |
| 5.2 | `acm-e2e-tester` | sonnet |

## Success Criteria

- [ ] Broadmeadows: ≥28/31 records (90% recall)
- [ ] Broadmeadows: ≥70% field accuracy (sample_no, sample_result, product, room_name)
- [ ] `building_record` table populated with correct building name
- [ ] Source register view shows building(s) with record counts
- [ ] Extraction progress reaches "completed" status
- [ ] All existing tests pass (2119+)
- [ ] Ruff lint clean
