# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Fixed
- Extraction: `_get_db_extraction_model()` checks provider field, rejects non-Ollama models — prevents 0-record extraction from wrong model 404s
- Extraction: `validate_records_strict()` auto-fills `material_description` from `product` instead of hard-rejecting records
- Extraction: `ACMItemRecord.quantity` changed from `Optional[float]` to `Optional[str]` — prevents Pydantic rejection of measurement strings discarding all records for a building
- UI: `JobOverviewTab.tsx` optional chaining on `buildingInventory.buildings?.length` — prevents crash when buildings is null
- Sources: Delete endpoint now cascade-cleans uploaded PDF file, reference edges, command records, agui_events, and chat edges
- Sources: New `POST /api/sources/cleanup-orphaned-files` endpoint to batch-delete uploaded PDFs with no matching source record

## [1.2.3] - 2026-02-22

### Features
- Epic 17: Live Extraction Intelligence (AG-UI streaming, A2A agents)
- Epic 16: Dashboard & Landing Pages
- Epic 15: Extraction Monitor UX
- Epic 13: Knowledge Graph Visualization
- Epic 12: Settings & Configuration UI
- Epic 10: Navigation Simplification
- Epic 9: Document Actions & Bulk Operations

### Project Milestone
- Feature-complete: 112/122 stories done (92%), 16 epics complete
