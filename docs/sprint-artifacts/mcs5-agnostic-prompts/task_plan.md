# MCS5: Format-Agnostic Prompts — Task Plan

**Story:** Multi-Consultant Story 5 | **SP:** 5 | **Branch:** ACMV3
**Dependencies:** Story 2 complete (InferredSchema exists)

## Tasks

- [x] 1. Add `detected_format` field to `InferredSchema` dataclass
- [x] 2. Create format example YAML files (standard.yaml, ara.yaml, pipe_table.yaml)
- [x] 3. Make `building_inventory.jinja` format-conditional via `detected_format`
- [x] 4. Make `row_extraction.jinja` accept dynamic `extraction_fields` list
- [x] 5. Make `v3_building_extraction.jinja` example-conditional by `detected_format`
- [x] 6. Update `build_kv_prompt()` to accept and use dynamic field list
- [x] 7. Wire `detected_format` from InferredSchema → prompt template context in graph nodes
- [x] 8. Write tests: prompt rendering with different format contexts (30 tests, all pass)
- [x] 9. Verify backward compatibility: `detected_format=None` renders existing defaults
- [x] 10. Run full test suite + lint (clean)
