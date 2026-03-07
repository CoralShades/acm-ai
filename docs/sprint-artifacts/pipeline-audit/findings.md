# Research Findings: Prompt Pack Revision

## 1. Undefined Terms in Current Prompt Pack

| Term | Used In | What It Actually Means |
|------|---------|----------------------|
| "Phase 1" | S5, S3 | Building__c metadata extraction via `_v3_extract_building_meta()` in `orchestrator.py:726` |
| "Phase 2" | S5, S3 | Item__c record extraction via `_v3_extract_items()` in `orchestrator.py:800` |
| "S2 fixed the message structure" | S4, S5, S6 | Commit `c5aa555b` moved document content from SystemMessage to HumanMessage across all 7 LLM call sites |
| "S3 cached Phase 1 results" | S5 | Added `building_meta_cache` field to ExtractionState; `extract_building_node` populates it, `extract_items_node` reads it |
| "S2 pattern" | S4 | Pattern: SystemMessage = instructions only, HumanMessage = document content |
| "observations 16-20 in the trace audit" | S7 | Langfuse GENERATION observations showing 5 LLM correction calls for trivial string mappings |
| "`_trim_to_register()`" | S4 | Function that slices document content to just the register section using `register_start_page` from DocumentStructure |
| "ACM_V3_PROMPTS feature flag" | S8 | Environment variable that switches between legacy and V3 extraction paths |
| "SAMP and ARA format documents" | S4 | SAMP = School Asbestos Management Plan, ARA = Asbestos Risk Assessment — two document formats the pipeline handles |

## 2. Skill Availability

| Skill Name | Location | Available via `/skill` | Notes |
|-----------|----------|----------------------|-------|
| `langgraph-fundamentals` | `.agents/skills/` | Yes | LangGraph StateGraph, nodes, edges, Command patterns |
| `langchain-fundamentals` | `.agents/skills/` | Yes | LangChain agents, tools, middleware |
| `pydantic-models-py` | `.claude/skills/` | Yes | Multi-model pattern (Base/Create/Update/Response/InDB) |
| `acm-observability` | `.claude/skills/` | Yes | 6-tool observability stack, Langfuse queries |
| `systematic-debugging` | `.claude/skills/` | Yes | Root-cause-first debugging methodology |
| `dispatching-parallel-agents` | `.claude/skills/` | Yes | Parallel subagent dispatch for independent tasks |
| `subagent-driven-development` | `.claude/skills/` | Yes | Fresh subagent per task + two-stage review |
| `planning-with-files` | `.claude/skills/` | Yes | task_plan.md + findings.md + progress.md |
| `verification-before-completion` | `.claude/skills/` | Yes | Pre-completion verification checklist |

## 3. Current Graph Topology (acm_extraction.py:3547-3571)

```
START → extract_metadata → structure → inventory → tag_pages
  → save_intelligence → extract_building → extract_items
  → [conditional: should_run_orchestrate] → {orchestrate | validate}
  → [conditional: should_correct] → {correct → validate (loop) | deduplicate}
  → recover_no_access → save → END
```

**Legacy nodes** (registered but unreachable): `prepare`, `extract`

## 4. ExtractionState Key Fields (acm_extraction.py:431-474)

- `source`, `content`, `chunks`, `records`, `error`, `model_id`
- `document_structure: Optional[DocumentStructure]`
- `building_inventory: Optional[BuildingInventory]`
- `page_tags: Optional[PageTaggingResult]`
- `document_metadata: Optional[DocumentMeta]`
- `building_records: List[str]` — persisted BuildingRecord IDs
- `building_meta_cache: Dict[str, Any]` — Phase 1 cache (building_code → BuildingExtractionResult)
- `correction_attempt`, `max_correction_attempts`, `enable_corrective_loop`

## 5. Key Functions and Files

| Function | File | Line | Purpose |
|----------|------|------|---------|
| `_v3_extract_building_meta()` | `orchestrator.py` | 726 | Phase 1: Extract Building__c metadata |
| `_v3_extract_items()` | `orchestrator.py` | 800 | Phase 2: Extract Item__c records |
| `_get_docling_tables()` | `orchestrator.py` | 69 | Fetch Docling HTML tables for a page range |
| `_inject_docling_tables()` | `orchestrator.py` | 105 | Append Docling tables to content string |
| `normalize_enum_value()` | `normalizers/enums.py` | 84 | Map raw field values to canonical SF picklist values |
| `SalesforcePicklistValidator` | `validators/sf_picklist_validator.py` | — | Chain validation for dependent picklists |
| `load_sf_field_schema()` | `parsers/config_loader.py` | — | Parse SF field summary files into config |
| `provision_langchain_model()` | `graphs/utils.py` | — | Create LangChain model with token budget |
| `parse_json_response()` | `graphs/utils.py` | — | Parse JSON from LLM response text |
