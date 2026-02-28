# Task Plan — E27-S2: SSE/AG-UI Pipeline Visibility + Frontend Step Display

## Phase 1: Backend — New Pipeline Stages
- [ ] A1. Add DOCLING_EXTRACTION and NO_ACCESS_RECOVERY StageId enums + metadata
- [ ] A2. Instrument `_extract_tables_with_docling()` in source_commands.py
- [ ] A3. Instrument `recover_no_access_node()` in acm_extraction.py
- [ ] A4. AGUIEventEmitter — emit step events for new stages

## Phase 2: A2A Agent Card
- [ ] B1. Update agent.json with docling/recovery capabilities

## Phase 3: Frontend — Pipeline Display
- [ ] C1. Update pipeline.ts types (StageId, STAGE_ORDER, STAGE_LABELS, STAGE_CONFIG)
- [ ] C2. Update StageProgressPill labels
- [ ] C3. Update ExtractionProgressPanel STAGE_CONFIG

## Phase 4: Tests
- [ ] D1. Backend unit tests for new StageId enums

## Phase 5: Validation
- [ ] E1. Ruff lint
- [ ] E2. Pytest (all tests)
- [ ] E3. Frontend build + lint

## Phase 6: Sprint Status + Commit
- [ ] F1. Update sprint-status.yaml
