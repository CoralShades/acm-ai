# Findings: ACM Pipeline Audit — Tables, Data Flow, Graph Nodes, Frontend Mapping

Date: 2026-03-14
Branch: ACMV3
Migrations: 49 (1.surrealql through 49.surrealql)

---

## 1. SurrealDB Table Catalog

### 1.1 Summary

| Category | Tables | Status |
|----------|--------|--------|
| ACM Core | 5 | Active — written by pipeline |
| ACM Support | 7 | Active — written by pipeline/API |
| ACM Config (singletons) | 4 | Partially active — some never written |
| ACM Knowledge Graph | 4 tables + 4 relations | **Orphaned** — defined but never populated |
| Non-ACM (notebook/chat/podcast) | 11 tables + 3 relations | Active for non-ACM features |
| External (surreal-commands) | 2 | Active — managed externally |
| Removed | 2 | Dropped in M46 |
| **Total** | **42** (40 active + 2 removed) | |

### 1.2 ACM Core Tables (5)

These tables form the primary data path for ACM extraction.

#### `source` — Uploaded PDF documents (root entity)

| Field | Type | Migration | Notes |
|-------|------|-----------|-------|
| id | record (auto) | M1 | |
| asset | option\<object\> FLEXIBLE | M1 | File path/URL metadata |
| title | option\<string\> | M1 | |
| topics | option\<array\<string\>\> | M1 | |
| full_text | option\<string\> | M1 | Populated by source_graph before ACM pipeline |
| created | datetime | M1 | Immutable |
| updated | datetime | M1 | Auto-update |
| command | option\<record\<command\>\> | M8 | FK to job queue |
| archived_at | option\<datetime\> | M28 | |
| deleted_at | option\<datetime\> | M28 | |
| status | option\<string\> | M28 | DEFAULT 'active' |
| review_status | option\<string\> | M32 | DEFAULT 'pending_review' |

Indexes: `idx_source_title` (BM25), `idx_source_full_text` (BM25), `source_status_idx`, `idx_source_review_status`
Cascade events (M49): Deletes cascade to `source_embedding`, `source_insight`, `building_record`, `acm_table_section`, `site_config`, `source_intelligence`, `raw_extraction`, `extraction_progress`

#### `raw_extraction` — Per-provider raw table outputs (Docling/MinerU)

| Field | Type | Migration | Notes |
|-------|------|-----------|-------|
| source_id | record\<source\> | M42 | FK |
| provider_id | string | M42 | e.g. "docling", "mineru" |
| extraction_backend | string | M42 | |
| page_number | int | M42 | |
| raw_html | option\<string\> | M42 | |
| raw_markdown | option\<string\> | M42 | |
| structured_json | option\<string\> | M42 | |
| bbox | option\<object\> | M42 | Bounding box {x,y,w,h,page} |
| confidence | option\<float\> | M42 | |
| officer_edits | array | M42 | DEFAULT [] |
| created_at | option\<datetime\> | M42 | |

Indexes: `idx_raw_extraction_source_id`, `idx_raw_extraction_source_provider`

#### `acm_table_section` — Table sections linking raw tables to buildings/pages

| Field | Type | Migration | Notes |
|-------|------|-----------|-------|
| source_id | record\<source\> | M18 | FK |
| page_start | int | M18 | |
| page_end | int | M18 | |
| raw_html | option\<string\> | M18 | |
| raw_text | option\<string\> | M18 | |
| building_name | option\<string\> | M18 | |
| table_type | option\<string\> | M18 | "docling_direct_api" or "register" |
| created | datetime | M18 | |
| updated | option\<datetime\> | M18 | |
| structured_json | option\<string\> | M37 | DataFrame CSV |
| consensus_tier | option\<string\> | M42 | |
| consensus_scores | option\<object\> | M42 | |
| docling_document_json | option\<object\> | M48 | Full DoclingDocument JSON |

Indexes: `section_source` (source_id), `section_pages` (page_start, page_end)

#### `building_record` — Building__c entities (per-building metadata)

| Field | Type | Migration | Notes |
|-------|------|-----------|-------|
| internal_id | string | M40 | Server-generated BLD#XXX_NNN |
| source_id | record\<source\> | M40 | FK |
| building_code | option\<string\> | M40 | |
| building_name | option\<string\> | M40 | |
| building_year, building_construction, building_address, suburb, postcode | option\<string\> | M40 | |
| building_type, building_category, building_address_lga, building_address_region | option\<string\> | M40 | |
| roof_type | option\<string\> | M40 | |
| number_of_levels | option\<int\> | M40 | |
| est_building_size_m2 | option\<float\> | M40 | |
| frequency_of_use, daily_duration, level_of_activity, public_access | option\<string\> | M40 | |
| mobile_plant, owned_or_leased | option\<string\> | M40 | |
| asbestos_register_available, audit_report_available, date_of_audit_report | option\<string\> | M40 | |
| no_identified_acms | option\<int\> | M40 | |
| no_identified_acms_note | option\<string\> | M40 | |
| site_name, school_uid, building_unique_id, external_id | option\<string\> | M40 | |
| building_out_of_scope | option\<bool\> | M40 | |
| building_out_of_scope_comments | option\<string\> | M40 | |
| demolished_status, demolition_date, demolition_type, demolition_comments | option\<string\> | M40 | |
| additional_comments, within_your_portfolio | option\<string\> | M40 | |
| psb_district_region, state, country, gps_coordinates | option\<string\> | M40 | |
| capital_works_project_details, possible_capital_works_project | option\<string\> | M40 | |
| embedding | option\<array\<float\>\> | M40 | |
| embedding_text, embedding_model | option\<string\> | M40 | |
| embedded_at | option\<datetime\> | M40 | |
| enriched_text | option\<string\> | M40 | |
| created, updated | option\<datetime\> | M40 | |
| building_sub_category | option\<string\> | M47 | |
| building_risk_rating | option\<string\> | M47 | |

Indexes: `idx_building_source_id`, `idx_building_internal_id` (UNIQUE)

#### `acm_record` — Item__c entities (individual ACM samples)

| Field | Type | Migration | Notes |
|-------|------|-----------|-------|
| source_id | record\<source\> | M10 | FK |
| building_id | string | M10 | Legacy text ID |
| building_record_id | option\<record\<building_record\>\> | M40 | FK to building_record |
| school_name, school_code | string / option\<string\> | M10 | |
| building_name, building_year, building_construction | option fields | M10 | |
| room_id, room_name, room_area | option fields | M10 | |
| area_type | option\<string\> | M10 | |
| product | string | M10 | |
| material_description | string | M10 | |
| extent, location, friable, material_condition | option\<string\> | M10 | |
| risk_status, result | string / option\<string\> | M10 | |
| page_number | option\<int\> | M10 | |
| disturbance_potential, sample_no, sample_result | option\<string\> | M11 | |
| identifying_company, quantity | option\<string\> | M11 | |
| acm_labelled | option\<bool\> | M11 | |
| acm_label_details, hygienist_recommendations | option\<string\> | M11 | |
| psb_supplied_acm_id, removal_status, date_of_removal | option\<string\> | M11 | |
| extraction_confidence | option\<string\> | M11 | Was float, changed to string enum |
| data_issues | option\<array\<string\>\> | M11 | |
| embedding | option\<array\<float\>\> | M12 | 1024-dim MTREE COSINE |
| embedding_text, embedding_model | option\<string\> | M12 | |
| embedded_at | option\<datetime\> | M12 | |
| acm_product_group, acm_product_type | option\<string\> | M14 | |
| classification_confidence | option\<float\> | M14 | |
| classification_override | option\<bool\> | M14 | |
| classification_method | option\<string\> | M14 | |
| normalized_action | option\<string\> | M15 | |
| enriched_text | option\<string\> | M16 | |
| parent_table_id | option\<record\<acm_table_section\>\> | M18 | FK |
| no_access | option\<bool\> | M32 | DEFAULT false |
| smf_present | option\<string\> | M32 | |
| floor_level, date_of_inspection | option\<string\> | M35 | |
| building_address, suburb, postcode, building_type | option\<string\> | M36 | |
| quantity_removed, removal_notification_no, epa_certificate_no | option\<string\> | M36 | |
| additional_comments | option\<string\> | M36 | |
| labelled_sf, assea_risk_level, date_identified | option\<string\> | M39 | |

Indexes: 12 indexes including BM25 full-text search on product/material/location/recommendations
Modified in: M10, M11, M12, M14, M15, M16, M18, M27, M32, M35, M36, M39, M40

### 1.3 ACM Support Tables (7)

| Table | Purpose | Written By | Read By |
|-------|---------|------------|---------|
| `source_intelligence` (M41, M43) | Pre-extraction intelligence (metadata, structure, inventory, page tags) | `save_intelligence_node` (graph) | `GET /api/acm/source-intelligence/{id}` → `SourceIntelligencePanel` |
| `extraction_progress` (M19, M22) | Pipeline run state for SSE streaming | `PipelineLogger._persist_state()` (background, throughout pipeline) | `GET /api/acm/extraction-progress/{id}/stream` → `ExtractionProgressPanel` |
| `site_config` (M13, M32) | Victorian BAR site-level configuration | `save_records` → `auto_populate_site_config()`, `POST /api/acm/config` | `GET /api/acm/config`, SF export endpoints |
| `raw_extraction` (M42) | Per-provider raw table outputs | `_store_raw_extractions()` (pre-graph) | `GET /api/acm/raw-extractions/{id}` → `RawTableGrid`, `GET /api/acm/provenance/{id}` → `ProvenanceViewer` |
| `agui_events` (M21) | AG-UI protocol events (RunStarted, StepStarted, etc.) | AG-UI event emitter in pipeline | `GET /api/agui/extraction/{id}/stream` → `useAguiStream` |
| `field_schema` (M17, M38) | BAR field schema config (47 fields, enums, rules) | `PUT /api/acm/field-config`, `POST /api/acm/field-config/reset` | `GET /api/acm/field-config` |
| `crud_audit` (M33) | Audit trail for CRUD operations | API CRUD handlers | (no frontend consumer found) |

### 1.4 ACM Config Singletons (4)

| Table | Purpose | Status |
|-------|---------|--------|
| `extraction_settings` (M24) | Pipeline feature flags (enable TOC, page tagging, corrective RAG, etc.) | **Likely orphaned** — no API endpoint or graph node found that writes to it |
| `extraction_stage_models` (M29) | Per-stage model overrides (structure, inventory, extraction, etc.) | **Likely orphaned** — no write path found |
| `processing_config` (M30) | Chunk size, confidence threshold, batch size, timeouts | **Likely orphaned** — no write path found |
| `open_notebook:default_models` (M1, M45) | Global default model IDs | Written by `PUT /api/models/defaults`, read by extraction graph |

### 1.5 Knowledge Graph Tables (8) — **ORPHANED**

These were defined in M25 for a planned knowledge graph feature that was never completed.

| Table | Type | Purpose | Written By | Read By |
|-------|------|---------|------------|---------|
| `school` | SCHEMAFULL | School entity (code, name, address, region) | **Nothing** | **Nothing** |
| `building` | SCHEMAFULL | Building entity (school_code, building_code, name, year) | **Nothing** | **Nothing** |
| `room` | SCHEMAFULL | Room entity (school_code, building_code, room_code) | **Nothing** | **Nothing** |
| `school_has_building` | RELATION | school → building | **Nothing** | **Nothing** |
| `building_has_room` | RELATION | building → room | **Nothing** | **Nothing** |
| `room_has_acm` | RELATION | room → acm_record | **Nothing** | **Nothing** |
| `extracted_from` | RELATION | acm_record → source | **Nothing** | **Nothing** |
| `a2a_tasks` | SCHEMALESS | Agent-to-Agent task tracking | **Nothing found** | **Nothing found** |

**Note:** The `KnowledgeGraph.tsx` frontend component exists but uses `GET /api/graph/source/{id}` which queries `acm_record` directly with GROUP BY — it does NOT use these graph tables.

### 1.6 Non-ACM Tables (14)

These support the original Open Notebook features (notebooks, notes, chat, podcasts).

| Table | Type | Purpose | Feature |
|-------|------|---------|---------|
| `notebook` | SCHEMAFULL | Notebook containers | Notebooks |
| `note` | SCHEMAFULL | Individual notes | Notes |
| `source_embedding` | SCHEMAFULL | Vector embeddings for source chunks | Semantic search |
| `source_insight` | SCHEMAFULL | Source insights (summaries, topics) | Source analysis |
| `reference` | RELATION | source → notebook | Notebooks |
| `artifact` | RELATION | note → notebook | Notebooks |
| `chat_session` | SCHEMALESS | Chat conversations | Chat |
| `refers_to` | RELATION | chat_session → notebook\|source | Chat |
| `transformation` | SCHEMAFULL | Prompt templates for transformations | Source processing |
| `episode_profile` | SCHEMAFULL | Podcast episode configuration | Podcasts |
| `speaker_profile` | SCHEMAFULL | Podcast speaker/voice configuration | Podcasts |
| `episode` | SCHEMAFULL | Generated podcast episodes | Podcasts |
| `podcast_config` | SCHEMALESS | Podcast settings | Podcasts |
| `model` | External | AI model registry | Global |
| `command` | External | Job queue entries | Global |

### 1.7 Removed Tables (2)

| Table | Defined | Removed | Reason |
|-------|---------|---------|--------|
| `bar_template` | M23 | M46 | Replaced by field_schema approach |
| `field_mapping` | M26 | M46 | Replaced by SF field config loader |

---

## 2. Domain Model → Table Mapping

| Pydantic Model | SurrealDB Table | Base Class | File |
|---------------|-----------------|------------|------|
| `ObjectModel` | (abstract base) | BaseModel | `domain/base.py` |
| `RecordModel` | (singleton records) | BaseModel | `domain/base.py` |
| `Notebook` | `notebook` | ObjectModel | `domain/notebook.py` |
| `Source` | `source` | ObjectModel | `domain/notebook.py` |
| `SourceEmbedding` | `source_embedding` | ObjectModel | `domain/notebook.py` |
| `SourceInsight` | `source_insight` | ObjectModel | `domain/notebook.py` |
| `Note` | `note` | ObjectModel | `domain/notebook.py` |
| `ChatSession` | `chat_session` | ObjectModel | `domain/notebook.py` |
| `Asset` | (embedded object) | BaseModel | `domain/notebook.py` |
| `Model` | `model` | ObjectModel | `domain/models.py` |
| `DefaultModels` | `open_notebook:default_models` | RecordModel | `domain/models.py` |
| `ACMRecord` | `acm_record` | ObjectModel | `domain/acm.py` |
| `BuildingRecord` | `building_record` | ObjectModel | `domain/acm.py` |
| `ACMItemRow` | (not persisted — LLM extraction schema) | BaseModel | `domain/acm_row_schemas.py` |

### Tables with NO dedicated Pydantic model (accessed via `repo_query` / `repo_upsert`):

| Table | How Accessed |
|-------|-------------|
| `site_config` | Direct SurQL queries in API routers and `metadata_extractor.py` |
| `source_intelligence` | Direct SurQL queries in `save_intelligence_node` |
| `raw_extraction` | Direct SurQL queries in `source_commands.py` and API routers |
| `acm_table_section` | Direct SurQL queries in `source_commands.py`, orchestrator, graph |
| `extraction_progress` | Direct SurQL queries in `PipelineLogger` |
| `agui_events` | Direct SurQL queries in AG-UI event emitter |
| `field_schema` | Direct SurQL queries in API routers |
| `crud_audit` | Direct SurQL queries in API CRUD handlers |
| `extraction_settings` | Direct SurQL queries (if any — likely orphaned) |
| `extraction_stage_models` | Direct SurQL queries (if any — likely orphaned) |
| `processing_config` | Direct SurQL queries (if any — likely orphaned) |

---

## 3. LangGraph Node Data Flow

### 3.1 Graph Structure

```
START
  │
  ▼
metadata_and_structure_node
  │  (1 LLM call: combined metadata + document structure)
  ▼
compile_inventory
  │  (1 LLM call: building inventory; synthesizes page_tags)
  ▼
save_intelligence_node
  │  (no LLM; writes to source_intelligence table)
  ▼
extract_building_node
  │  (1 LLM call per building, concurrent, semaphore-bounded)
  │  (writes to building_record table)
  ▼
extract_items_node
  │  (per-row mode: segment → extract_single_row per row)
  │  (bulk mode: one LLM call per building/chunk)
  ▼
normalize_to_sf_node
  │  (deterministic, no I/O)
  ▼
validate_records_strict
  │
  ├── [no issues OR max attempts] ──► deduplicate_records
  └── [issues found] ──► correct_records ──► validate_records_strict

deduplicate_records
  ▼
recover_no_access_node
  │  (skipped if per_row_actually_ran=True)
  ▼
save_records
  │  (writes acm_table_section type=register, acm_record, site_config)
  ▼
END
```

### 3.2 Node → Table I/O Matrix

| Node | Reads State | Writes State | Reads DB | Writes DB |
|------|------------|-------------|----------|-----------|
| `metadata_and_structure_node` | source.full_text, model_id | document_metadata, document_structure | — | — |
| `compile_inventory` | source.full_text, model_id, document_structure, document_metadata | building_inventory, page_tags | — | — |
| `save_intelligence_node` | source.id, document_metadata, document_structure, building_inventory, page_tags | {} | — | `source_intelligence` (UPSERT) |
| `extract_building_node` | source.full_text, source.id, building_inventory, schema_bundle, model_id | building_records, building_meta_cache | `building_record` (count) | `building_record` (CREATE) |
| `extract_items_node` | source.full_text, source.id, building_inventory, schema_bundle, model_id, building_meta_cache | records, items_extracted, per_row_actually_ran | `building_record` (SELECT), `acm_table_section` (SELECT docling tables) | — |
| `normalize_to_sf_node` | records | records (mutated) | — | — |
| `validate_records_strict` | records, context, correction_attempt | records, records_rejected, correction_stats | — | — |
| `correct_records` | records, correction_attempt, correction_stats, model_id | records, correction_attempt, correction_stats | `model` (Qwen detection) | — |
| `deduplicate_records` | records, context | records (deduplicated) | — | — |
| `recover_no_access_node` | per_row_actually_ran, records, source.full_text | records (appended) | — | — |
| `save_records` | records, source, context, building_inventory, document_metadata, correction_stats | extraction_result, error | — | `acm_table_section` (register), `acm_record`, `site_config` |

### 3.3 Side Channels

| Channel | Written By | Writes To |
|---------|-----------|-----------|
| `PipelineLogger` | Any node with `pipeline_logger` in state | `extraction_progress` (UPSERT, background async) |
| `AGUIEventEmitter` | Any node with `agui_emitter` in state | `agui_events` (append, background async) |
| `PipelineEventBus` | `validate_records_strict`, `extract_items_node` (per-row) | In-memory only (SSE via `/api/v3/stream/`) |

---

## 4. Pre-Graph Steps (source_commands.py)

The following sequence executes in `process_source_command()` BEFORE the ACM graph is invoked:

| Step | Action | Tables |
|------|--------|--------|
| 1 | Load transformations | READ `transformation` |
| 2 | Load source record | READ `source` |
| 3 | Update source with command reference | WRITE `source` (set command FK) |
| 4 | Invoke `source_graph` (content extraction) | READ/WRITE `source` (populates full_text) |
| 5a | Run DoclingAdapter.extract() | No DB (returns NormalizedExtractionResult) |
| 5b | Store raw extractions | WRITE `raw_extraction` (CREATE per table per provider) |
| 5c | Optionally run MinerUAdapter.extract() | No DB (returns NormalizedExtractionResult) |
| 5d | Store MinerU raw extractions | WRITE `raw_extraction` (CREATE per table) |
| 5e | Store merged Docling tables | WRITE `acm_table_section` (type="docling_direct_api") |
| 6 | Create PipelineLogger | WRITE `extraction_progress` (initial state) |
| 7 | Invoke ACM extraction graph | (see Section 3 above) |

---

## 5. API Endpoint → Table Mapping

### 5.1 ACM Core CRUD

| Method | Path | Tables | Description |
|--------|------|--------|-------------|
| GET | /api/acm/records | `acm_record` | List with pagination/filtering |
| GET | /api/acm/records/{id} | `acm_record` | Single record |
| POST | /api/acm/records | `acm_record` | Create |
| PUT | /api/acm/records/{id} | `acm_record` | Update |
| DELETE | /api/acm/records/{id} | `acm_record` | Delete |
| GET | /api/acm/buildings | `building_record`, `acm_record` | List with item counts |
| GET | /api/acm/buildings/{id} | `building_record` | Single building |
| POST | /api/acm/buildings | `building_record` | Create |
| PUT | /api/acm/buildings/{id} | `building_record` | Update |
| DELETE | /api/acm/buildings/{id} | `building_record` | Delete |

### 5.2 Extraction & Processing

| Method | Path | Tables | Description |
|--------|------|--------|-------------|
| POST | /api/acm/extract | `command` (job queue) | Trigger async extraction |
| GET | /api/acm/source-intelligence/{id} | `source_intelligence` | Pre-extraction intelligence |
| GET | /api/acm/raw-extractions/{id} | `raw_extraction` | Per-provider raw outputs |
| PATCH | /api/acm/raw-extractions/{id}/{eid} | `raw_extraction` | Append officer edits |
| GET | /api/acm/provenance/{id} | `acm_record`, `acm_table_section`, `raw_extraction`, `source` | Record provenance |
| GET | /api/acm/validation-summary | `acm_record` | Per-building validation errors |

### 5.3 Bulk Operations

| Method | Path | Tables | Description |
|--------|------|--------|-------------|
| POST | /api/acm/bulk-edit | `acm_record` | Set field across selected records |
| POST | /api/acm/bulk-validate | `acm_record` | Re-run SF validation |
| POST | /api/acm/bulk-fix | `acm_record` | Auto-correct fixable issues |
| POST | /api/acm/backfill-parents | `acm_record`, `acm_table_section` | Link parent_table_id FK |
| POST | /api/acm/backfill-buildings | `acm_record`, `building_record` | Create BuildingRecords from existing |
| POST | /api/acm/classify/batch | `acm_record` | Classify all records |
| POST | /api/acm/re-embed | `acm_record` | Re-embed with contextual enrichment |

### 5.4 Export

| Method | Path | Tables | Description |
|--------|------|--------|-------------|
| GET | /api/acm/export | `acm_record`, `source` | BAR CSV download |
| GET | /api/acm/export/excel | `acm_record`, `source` | Formatted Excel |
| GET | /api/acm/export/sf-csv | `acm_record`, `building_record`, `site_config`, `source` | Salesforce ZIP |
| GET | /api/acm/export/sf-excel | `acm_record`, `building_record`, `site_config`, `source` | Salesforce XLSX |

### 5.5 Config & Schema

| Method | Path | Tables | Description |
|--------|------|--------|-------------|
| GET | /api/acm/config | `site_config` | Get site config |
| POST | /api/acm/config | `site_config` | Upsert site config |
| GET | /api/acm/field-config | `field_schema` | Get BAR field schema |
| PUT | /api/acm/field-config | `field_schema` | Update field schema |
| POST | /api/acm/field-config/reset | `field_schema` | Reset to defaults |
| GET | /api/acm/field-schema | (SF markdown files) | V3 Salesforce field schema |

### 5.6 Streaming & Events

| Method | Path | Source | Description |
|--------|------|--------|-------------|
| GET | /api/acm/extraction-progress/{id}/stream | `extraction_progress` (polling) | Pipeline SSE |
| GET | /api/acm/extraction-progress/{id} | `extraction_progress` | Polling fallback |
| GET | /api/agui/extraction/{id}/stream | `agui_events` (polling) | AG-UI SSE |
| GET | /api/v3/stream/extraction/{id} | In-memory PipelineEventBus | V3 extraction SSE |
| GET | /api/v3/stream/ai/{id} | In-memory PipelineEventBus | V3 AI events SSE |
| GET | /api/v3/stream/bulk/{id} | In-memory PipelineEventBus | V3 bulk ops SSE |

### 5.7 Graph & Stats

| Method | Path | Tables | Description |
|--------|------|--------|-------------|
| GET | /api/graph/source/{id} | `acm_record` | React Flow graph nodes/edges |
| GET | /api/graph/stats/{id} | `acm_record` | Graph statistics |
| GET | /api/acm/stats | `acm_record` | Risk status counts |
| GET | /api/acm/search | `acm_record`, `acm_table_section` | Semantic/BM25 search |

---

## 6. Frontend Screen → API → Table Flow

### 6.1 Primary View: `/source/[id]` (SourceACMPage)

```
SourceACMPage
├── BuildingTabStrip
│   ├── useBuildings → GET /api/acm/buildings → building_record, acm_record
│   └── useValidationSummary → GET /api/acm/validation-summary → acm_record
├── useV3BuildingStream → GET /api/v3/stream/ai/{id} → PipelineEventBus
├── useACMItems → GET /api/acm/records → acm_record
├── useFieldSchema → GET /api/acm/field-schema → SF markdown files
├── ACMGrid (display only, data from props)
├── ACMRecordDialog → PUT /api/acm/records/{id} → acm_record
├── BulkOperationsBar
│   ├── useBulkEdit → POST /api/acm/bulk-edit → acm_record
│   └── useBulkValidate → POST /api/acm/bulk-validate → acm_record
├── useBulkFix → POST /api/acm/bulk-fix → acm_record
└── ExportDialog → GET /api/acm/export/* → acm_record, building_record, site_config
```

### 6.2 Item Grid (with Provenance)

```
ItemGrid
├── useACMItems → GET /api/acm/records → acm_record
├── useFieldSchema → GET /api/acm/field-schema → SF markdown
├── useUpdateACMRecord → PUT /api/acm/records/{id} → acm_record
└── ProvenanceViewer (slide-out)
    ├── useProvenance → GET /api/acm/provenance/{id} → acm_record, acm_table_section, raw_extraction, source
    └── PDFPageViewer → GET /api/sources/{id}/download → filesystem
```

### 6.3 Legacy ACM Tab

```
ACMTab
├── useACMRecords → GET /api/acm/records → acm_record
├── useACMStats → GET /api/acm/stats → acm_record
├── useExtractACM → POST /api/acm/extract → command
├── useExportACMCsv/Excel → GET /api/acm/export/* → acm_record, source
├── SiteConfigPanel → GET/POST /api/acm/config → site_config
├── ExtractionProgressPanel ← useExtractionProgress → extraction_progress
└── ACMRecordDetailPanel → useACMRecord + useUpdateACMRecord → acm_record
```

### 6.4 Raw Table Review

```
RawTableGrid
├── useRawExtractions → GET /api/acm/raw-extractions/{id} → raw_extraction
├── usePatchRawExtraction → PATCH /api/acm/raw-extractions → raw_extraction
└── useReprocessExtraction → POST /api/acm/extract → command

RawTableViewer
└── inline query → GET /api/acm/jobs/{id}/raw-tables → acm_table_section, source
```

### 6.5 Other Views

| Component | Route/Location | Hook | API | Tables |
|-----------|---------------|------|-----|--------|
| BuildingSidebar | sidebar panel | useBuildings, useValidationSummary | buildings, validation-summary | building_record, acm_record |
| BuildingDetailForm | /source/[id]/building/[bid] | useBuildingDetail, useUpdateBuilding | buildings/{id} | building_record |
| KnowledgeGraph | panel | inline useQuery | graph/source/{id}, graph/stats/{id} | acm_record |
| SourceIntelligencePanel | panel | useSourceIntelligence | source-intelligence/{id} | source_intelligence |
| ExtractionProgressPanel | panel (props only) | — (receives pipelineState) | — | — |

### 6.6 Zustand Stores

| Store | File | Purpose | Used By |
|-------|------|---------|---------|
| `buildingStore` | `lib/stores/buildingStore.ts` | Selected building, streaming status, multi-select | SourceACMPage, BuildingTabStrip, BuildingSidebar, useV3BuildingStream, ExportDialog |
| `streamingStore` | `lib/stores/streamingStore.ts` | Active SSE connections, retry state | useV3SSE, useV3BuildingStream |

---

## 7. Orphaned / Outdated Tables

### 7.1 Orphaned Tables (defined but never populated by current code)

| Table | Migration | Type | Reason |
|-------|-----------|------|--------|
| `school` | M25 | SCHEMAFULL | Knowledge graph entity — never implemented. No write path. |
| `building` | M25 | SCHEMAFULL | Knowledge graph entity — superseded by `building_record` (M40). No write path. |
| `room` | M25 | SCHEMAFULL | Knowledge graph entity — never implemented. No write path. |
| `school_has_building` | M25 | RELATION | Knowledge graph relation — never implemented. |
| `building_has_room` | M25 | RELATION | Knowledge graph relation — never implemented. |
| `room_has_acm` | M25 | RELATION | Knowledge graph relation — never implemented. |
| `extracted_from` | M25 | RELATION | Knowledge graph relation — never implemented. |
| `a2a_tasks` | M21 | SCHEMALESS | Agent-to-Agent task tracking — no write/read path found. |
| `extraction_settings` | M24 | SCHEMAFULL | Config singleton — no API endpoint or graph node writes to it. |
| `extraction_stage_models` | M29 | SCHEMAFULL | Config singleton — no write path found. |
| `processing_config` | M30 | SCHEMAFULL | Config singleton — no write path found. |

**Total orphaned: 11 tables** (4 entity + 4 relation + 3 config)

### 7.2 Removed Tables

| Table | Defined | Removed | Replacement |
|-------|---------|---------|-------------|
| `bar_template` | M23 | M46 | `field_schema` table |
| `field_mapping` | M26 | M46 | SF field config loader (`config_loader.py`) |

### 7.3 Tables with Questionable Usage

| Table | Issue |
|-------|-------|
| `crud_audit` (M33) | Written by API CRUD handlers, but no frontend reads or admin UI found |
| `podcast_config` (M1) | SCHEMALESS with no field definitions — may not be used in ACM context |

---

## 8. Orphaned Domain Models

| Model | File | Issue |
|-------|------|-------|
| `ACMItemRow` | `domain/acm_row_schemas.py` | Not orphaned — used as intermediate LLM extraction schema in per-row pipeline, then mapped to `ACMExtractionRecord` via `acm_row_mappers.py` |

**No truly orphaned domain models found.** All Pydantic models in `domain/` are referenced by at least one graph node, API router, or service layer.

---

## 9. Complete Data Flow Summary

### 9.1 Write Path (Pipeline → DB)

```
PDF Upload
  │
  ├─ source_graph ──────────────────► source (full_text)
  │
  ├─ DoclingAdapter.extract() ──────► raw_extraction (per table per provider)
  │                                 ► acm_table_section (type="docling_direct_api")
  │
  ├─ MinerUAdapter.extract() ──────► raw_extraction (per table per provider)
  │
  ├─ save_intelligence_node ────────► source_intelligence
  │
  ├─ extract_building_node ─────────► building_record
  │
  ├─ save_records ──────────────────► acm_table_section (type="register")
  │                                 ► acm_record
  │                                 ► site_config
  │
  └─ PipelineLogger ────────────────► extraction_progress (throughout)
     AGUIEventEmitter ──────────────► agui_events (throughout)
```

### 9.2 Read Path (Frontend → DB)

```
SourceACMPage ─► useBuildings ──────► building_record + acm_record (counts)
               ─► useACMItems ──────► acm_record
               ─► useProvenance ────► acm_record + acm_table_section + raw_extraction + source
               ─► useExtractionProgress ► extraction_progress
               ─► useV3SSE ────────► PipelineEventBus (in-memory)

RawTableGrid ──► useRawExtractions ► raw_extraction
               ─► RawTableViewer ──► acm_table_section + source

BuildingDetail ► useBuildingDetail ► building_record

KnowledgeGraph ► graph API ────────► acm_record (GROUP BY)

Intelligence ──► useSourceIntelligence ► source_intelligence

Export ─────────► SF export ────────► acm_record + building_record + site_config + source
```

---

## Decisions Made

1. **11 orphaned tables identified** — 8 from the M25 knowledge graph feature (never implemented, superseded by `building_record` + direct `acm_record` queries for graph visualization), plus 3 config singletons with no write path.
2. **2 tables already removed** (M46) — `bar_template` and `field_mapping`.
3. **All 5 core ACM tables** have complete write + read paths documented.
4. **No orphaned domain models** — all Pydantic models are actively used.
5. **Migration 21 duplication noted** — files 21.surrealql and 22.surrealql contain identical content (both define `agui_events` and `a2a_tasks`). Appears to be a copy artifact.
6. **`KnowledgeGraph.tsx` does NOT use knowledge graph tables** — it queries `acm_record` directly via `/api/graph/source/{id}`, making the M25 graph tables fully orphaned.
