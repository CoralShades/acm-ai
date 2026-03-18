# Session: Design and implement multi-consultant PDF format adaptability — dynamic schema inference without templates

## Skills to Load

/planning-with-files — persistent markdown plan for session continuity
/langgraph-fundamentals — LangGraph graph/node/state patterns
/prompt-engineering — design adaptive extraction prompts
/systematic-debugging — structured diagnosis of format detection failures
/langgraph-human-in-the-loop — HITL for manual schema mapping fallback
/verification-before-completion — verify work before claiming done

---

## Prerequisites

Before starting this session, verify:

- Branch: `git checkout ACMV3`
- Read audit findings: `docs/sprint-artifacts/pipeline-audit-2026-03-18/findings.md` (F3: Consultant Format Lock-in)
- Have 3+ different consultant PDF samples available for testing (different table layouts, column orders, header styles)
- Existing Broadmeadows (SAMP format) and Alexander (ARA format) PDFs for regression testing
- Consider installing: `npx skills add aj-geddes/useful-ai-prompts@gap-analysis -g -y`

---

## Project Glossary

| Term | Definition |
|------|-----------|
| SAMP | School Asbestos Management Plan — primary PDF format the pipeline currently handles. Specific table layouts and header patterns |
| ARA | Asbestos Register Assessment — secondary format. Handled via `_recover_not_sampled_records_ara()` regex |
| COLUMN_ALIASES | Hardcoded dict in `row_segmenter.py` mapping raw column names to canonical field names. Currently SAMP-specific |
| DoclingDocument | Docling's structured document object containing tables, text blocks, metadata. Primary extraction input |
| Building inventory | Pre-extraction stage that identifies buildings from PDF. Currently assumes specific header patterns |
| SF field mapping | Process of mapping extracted raw values to Salesforce API field names (Building__c, Item__c) |
| Schema inference | (NEW CONCEPT) Auto-detecting table structure, column meanings, and field mappings from an unknown PDF |
| Consultant format registry | (NEW CONCEPT) Registry of known PDF formats with their column mappings and extraction patterns |
| ExtractionProvider | Protocol class for extraction adapters: `extract_tables()`, `extract_text()`, `is_available()` |
| Pre-extraction stages | STRUCTURE, PREFLIGHT, ORCHESTRATOR — gather metadata, validate source, plan strategy |
| Skill | Markdown instruction set for Claude Code activated via `/skill-name` |
| Plan mode | Session reads/writes `task_plan.md` to prevent scope creep |

---

## Current State

- Pipeline handles 2 PDF types: SAMP (Broadmeadows) and ARA (Alexander)
- 5 hardcoded consultant-specific patterns identified:
  1. `COLUMN_ALIASES` in `row_segmenter.py` — hardcoded column name mapping
  2. `_LEVEL_REGEX` — SAMP-specific room/area header detection
  3. `_recover_not_sampled_records_ara()` — ARA-specific regex
  4. Building inventory prompt — references "SAMP" terminology
  5. Pre-extraction intelligence — assumes specific header patterns
- No mechanism for: auto-detecting table schema, dynamic column mapping, consultant profiles, LLM-driven schema inference
- Docling tables provide structured column headers → can be used for schema inference

---

## Key Files

**Read (reference — understand current hardcoding):**
- `open_notebook/extractors/row_segmenter.py` — `COLUMN_ALIASES`, `_LEVEL_REGEX`, segment logic
- `open_notebook/extractors/row_extractor.py` — per-row extraction, `build_kv_prompt()`
- `open_notebook/graphs/acm_extraction.py` — extraction graph, building inventory node, orchestrator
- `open_notebook/extractors/orchestrator.py` — table injection, page range logic
- `open_notebook/extractors/providers/docling_adapter.py` — Docling table structure
- `open_notebook/domain/acm_row_schemas.py` — `ACMItemRow` (9 fields)
- `open_notebook/domain/acm.py` — `ACMExtractionRecord`, SF field alignment
- `prompts/acm/building_inventory.jinja` — building inventory prompt
- `prompts/acm/building_extraction.jinja` — building extraction prompt
- `prompts/acm/row_extraction.jinja` — per-row KV prompt
- `V3/output/item_fields_summary.md` — SF Item__c field definitions
- `V3/output/building_fields_summary.md` — SF Building__c field definitions

**Create (design phase — this session is research + design):**
- `docs/architecture/multi-consultant-format-design.md` — architecture design document
- `open_notebook/extractors/schema_inference.py` — (stub) schema inference module
- `open_notebook/extractors/consultant_registry.py` — (stub) format registry

---

## Plan

### Phase 1: Gap Analysis (this session)

1. **Catalog all hardcoded patterns** — Search codebase for SAMP/ARA/consultant-specific logic
2. **Map the extraction flow** — Trace how column headers flow from Docling → segmenter → extractor → SF mapping
3. **Identify extension points** — Where can format-specific logic be injected without breaking existing paths?
4. **Design schema inference** — How can the LLM auto-detect table structure from Docling column headers?
5. **Design consultant registry** — How to store and reuse format profiles?
6. **Write architecture document** — Comprehensive design for multi-consultant support

### Phase 2: Architecture Design

**Dynamic Schema Inference Pipeline:**
```
PDF → Docling tables → Extract column headers → LLM schema inference →
  → Map columns to SF fields → Generate extraction config → Run extraction
```

**Key Design Decisions:**
1. **Schema inference node** — New LangGraph node between PREFLIGHT and ORCHESTRATOR
   - Input: Docling table column headers (first 3 rows as sample)
   - LLM task: "Map these columns to SF Item__c fields, identify building identifier column"
   - Output: `ColumnMapping` (raw_col → sf_field_name) + confidence score
   - If confidence < threshold → HITL: show user the mapping, ask for confirmation

2. **Consultant format registry** — SurrealDB table storing format profiles
   - Key: hash of column header signature
   - Value: validated column mapping + extraction config
   - On match: skip LLM inference, use cached mapping
   - On miss: run LLM inference, offer to save as new profile

3. **Adaptive row segmenter** — Replace `COLUMN_ALIASES` with dynamic mapping
   - Accept `ColumnMapping` as parameter instead of hardcoded aliases
   - `_LEVEL_REGEX` becomes configurable per format profile

4. **Format-agnostic prompts** — Remove SAMP/ARA references from prompts
   - Use dynamic field lists from the inferred schema
   - Include sample data from first 3 rows as few-shot examples

### Phase 3: Implementation (future sessions)
- Story 1: Schema inference node + LLM prompt
- Story 2: Consultant format registry (SurrealDB + API)
- Story 3: Adaptive row segmenter (dynamic COLUMN_ALIASES)
- Story 4: Format-agnostic prompts
- Story 5: HITL mapping confirmation UI
- Story 6: Validation with 3+ consultant PDF formats

### Task Plan Reference
- task_plan.md: `docs/sprint-artifacts/pipeline-audit-2026-03-18/task_plan.md`
- findings.md: `docs/sprint-artifacts/pipeline-audit-2026-03-18/findings.md`
- progress.md: `docs/sprint-artifacts/pipeline-audit-2026-03-18/progress.md`

---

## Agent Strategy

Strategy: SUBAGENT-DISPATCH
Use the Task tool to dispatch independent research tasks in parallel.

Subagents:
- codebase-scanner: Grep for all SAMP/ARA/consultant-specific patterns across the codebase. Return: list of files, line numbers, pattern descriptions
- docling-analyzer: Read Docling adapter + table structure to understand column header extraction capabilities. Return: how column headers flow through the system
- sf-schema-mapper: Read SF field summaries to understand target schema. Return: all required fields, picklist values, dependent relationships
- design-writer: (after all above complete) Write the architecture design document

Dispatch codebase-scanner, docling-analyzer, sf-schema-mapper in parallel. design-writer runs after.

---

## Context7 Directives

Run these at session start to load current library documentation:

1. resolve-library-id for "langgraph" → query-docs for "node conditional edges state typing human-in-the-loop interrupt"
2. resolve-library-id for "docling" → query-docs for "DoclingDocument TableItem table extraction column headers"

---

## Verification Checklist

- [ ] All hardcoded consultant patterns cataloged with file:line references
- [ ] Column header flow mapped: Docling → segmenter → extractor → SF
- [ ] Architecture design document created: `docs/architecture/multi-consultant-format-design.md`
- [ ] Design covers: schema inference, format registry, adaptive segmenter, format-agnostic prompts, HITL fallback
- [ ] Regression plan: existing Broadmeadows (31) and Alexander (43) benchmarks must not degrade
- [ ] Implementation stories defined with dependencies and SP estimates

---

## Files Summary

| Operation | Count | Files |
|-----------|-------|-------|
| READ | 12 | row_segmenter.py, row_extractor.py, acm_extraction.py, orchestrator.py, docling_adapter.py, acm_row_schemas.py, acm.py, 3 prompts, 2 SF field summaries |
| NEW | 1 | multi-consultant-format-design.md |

---

## Commit Template

```
docs(architecture): design multi-consultant PDF format adaptability

- Catalog 5 hardcoded consultant-specific patterns
- Design schema inference pipeline (LLM + HITL fallback)
- Design consultant format registry (SurrealDB cache)
- Define 6 implementation stories with dependencies

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>
```
