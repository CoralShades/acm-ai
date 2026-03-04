# Sprint Change Proposal: Salesforce Schema Alignment (SCP-20260301-SF)

> **Date:** 2026-03-01
> **Proposer:** Architect + PM (Party Mode Session)
> **Type:** Course Correction — PRD + Architecture + New Epic(s)
> **BMAD Workflow:** /correct-course
> **Status:** PROPOSED
> **Depends On:** E29 completion (Pipeline Unification)

---

## 1. Executive Summary

The current ACM-AI data model uses a **Victorian BAR schema** (~50 fields on a flat acm_record table) reverse-engineered from the BAR Excel template. Review of VAEA's **actual Salesforce instance** reveals two distinct objects — Building__c (143 fields) and Item__c (154 fields) — with master-detail relationships, dependent picklists, and business rules the current system does not model.

This course correction aligns the internal data model to Salesforce Building__c + Item__c, replaces the flat acm_record with separate building_record + acm_record tables, loads SF picklist values and dependency chains, updates extraction prompts, validation, and export for Salesforce Data Loader compatibility.

**Timing:** Execute AFTER E29 (Pipeline Unification) completes.

---

## 2. Impact Analysis

### 2.1 What Changes

| Area | Current State | Target State | Impact |
|------|--------------|--------------|--------|
| Data Model | Flat acm_record ~50 BAR fields | Separate building_record (SF Building__c) + acm_record (SF Item__c) | HIGH |
| Field Schema | register_row.schema.json (BAR template) | salesforce_building_schema.json + salesforce_item_schema.json | HIGH |
| Dependent Picklists | Flat enums (no dependencies) | 2 chains: BuildingType→Category→SubCat, Friability→Group→Type→ItemName | HIGH |
| Extraction Prompts | Single prompt per record | Two-phase: Building fields then ACM Items per building | MEDIUM |
| Site Config | 8 fields | Expanded for non-extractable Building__c fields | MEDIUM |
| AG Grid | Single grid ~47 columns | Two views: Building grid + ACM grid per building | MEDIUM |
| Export | Single BAR Excel sheet | Two sheets: Building__c + Item__c with SF API field names | MEDIUM |
| AI Provider | OpenRouter multi-model | Anthropic Claude Sonnet direct API | MEDIUM |

### 2.2 What Stays

PDF Processing, Structure Analysis, LangGraph orchestration, Next.js shell, AG Grid infra, SurrealDB infra, SSE/Observability, Chat interface.

### 2.3 Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| E29 agents need reconfiguring | HIGH | MEDIUM | E30 stories map to E29 agents |
| Data migration breaks records | MEDIUM | HIGH | Additive migration, toggle-flag |
| 294 Item Name values overwhelm AI | MEDIUM | MEDIUM | Subset by Product Group |
| Dependent picklist rejects valid data | MEDIUM | MEDIUM | Warn don't reject; officer reviews |

---

## 3. PRD Updates (FR-1400 Series)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-1401 | Store Building data in building_record mapped to SF Building__c | P0 |
| FR-1402 | Store ACM data in acm_record mapped to SF Item__c | P0 |
| FR-1403 | Enforce Friability → ACM_Classification → ACM_Sub_Classification | P0 |
| FR-1404 | Enforce Building_Type → Building_Category → Building_Sub_Category | P0 |
| FR-1405 | Validate picklist values against exact SF values (case-sensitive) | P0 |
| FR-1406 | Export Building__c Data Loader CSV | P0 |
| FR-1407 | Export Item__c Data Loader CSV | P0 |
| FR-1408 | Load SF schema from JSON config (describe metadata) | P0 |
| FR-1409 | Use Anthropic Claude Sonnet as sole AI provider | P1 |
| FR-1410 | Extract Building and ACM fields in separate AI calls | P0 |
| FR-1411 | Provide context-relevant Item_Name subsets by Product Group | P1 |
| FR-1412 | Business rule: Negative → Condition = N/A (negative) | P0 |

---

## 4. Architecture Updates

| Section | Change |
|---------|--------|
| Data Model | Replace ER diagram: Building__c → Item__c, add building_record table |
| Extraction | Two-phase: Building fields then ACM Items per building |
| Validation | Dependent picklist validation layer |
| AI Provider | Replace OpenRouter with Anthropic Claude Sonnet direct API |

---

## 5. Epic 30 — Salesforce Schema Alignment

> Depends On: E29 complete | Priority: P0 | Total: 10 stories, ~28 SP

### E30-S1: Salesforce Schema Config Loader (3 SP)
As a system, I want SF schemas loaded from JSON config so picklist values and dependencies are available at runtime.
- Parse building_list.txt and item_list.txt into JSON configs
- SalesforceSchemaConfig Pydantic model
- Dependency chains: BuildingType→Category→SubCat, Friability→Group→Type
- Load into field_schema table (version = salesforce-v1)

### E30-S2: Building Record Table + Domain Model (3 SP)
As a developer, I want a separate building_record table mapped to SF Building__c.
- Migration: building_record with 29 extractable fields
- BuildingRecord Pydantic model
- Master-detail: acm_record.building_id → building_record.id
- API endpoints: CRUD

### E30-S3: Update ACM Record Schema to SF Item__c (2 SP)
As a developer, I want acm_record fields aligned to SF Item__c API names.
- Additive migration (new SF-named fields alongside old)
- Field mapping: product→Item_Name__c, friable→Friability_of_Material__c, etc.
- ACMRecord Pydantic aliases
- 294-value Item_Name picklist from config

### E30-S4: Dependent Picklist Validator (3 SP)
As a developer, I want validation enforcing SF dependent picklist chains.
- SalesforcePicklistValidator class
- Friability→ProductGroup, ProductGroup→ProductType
- BuildingType→Category→SubCategory
- Integrates with E29-S6 validator
- Unit tests for all 18 ACM_Classification values × both friability values

### E30-S5: Extraction Prompt — Building Fields (2 SP)
As a pipeline developer, I want a dedicated Building__c extraction prompt.
- New Jinja: prompts/acm/building_extraction.jinja
- Extracts: Name, Address, Suburb, Postcode, Construction, Year, Levels, Inspection Date, Roof, Size
- SF picklist values for constrained fields in prompt

### E30-S6: Extraction Prompt — ACM Item Fields (3 SP)
As a pipeline developer, I want ACM prompt using SF Item__c field names + picklist values.
- Updated Jinja template
- SF field names, picklist values from config (not hardcoded)
- Item_Name subset by Product Group
- Business rule: Negative → N/A condition

### E30-S7: Anthropic Claude Direct API Migration (2 SP)
As a pipeline developer, I want all LLM calls via Anthropic direct API.
- Replace OpenRouter with ChatAnthropic
- Remove _unwrap_completion_state() from all stages
- Update env vars (ANTHROPIC_API_KEY)
- Benchmarks pass

### E30-S8: Salesforce-Ready Export (2 SP)
As a compliance officer, I want export with exact SF API field names.
- Building__c.csv + Item__c.csv
- Excel with two sheets
- Building external ID in Item sheet for Data Loader matching

### E30-S9: AG Grid Column Update — Two-View Layout (2 SP)
As a compliance officer, I want separate Building and ACM grid views.
- Building grid: Building__c extractable fields
- ACM grid: Item__c fields filtered by building
- Columns from SalesforceSchemaConfig
- Dependent picklist cascading in dropdowns

### E30-S10: E2E Salesforce Alignment Test (3 SP)
As a developer, I want E2E tests validating SF-valid output.
- Upload→extract→validate→export→verify CSV
- All picklist values valid SF values
- Dependency chains valid
- Broadmeadows + Alexander benchmarks pass
- PRD, Architecture, Epics docs updated

---

## 6. Dependency Graph

```
E29 COMPLETE
  |
  v
E30-S1 (Schema Config) ─────────────────┐
  |                                       |
  ├──> E30-S2 (Building Table) ──┐       |
  |                               |       |
  ├──> E30-S3 (ACM Schema)  ──┐ |       |
  |                            |  |       |
  ├──> E30-S4 (Validator)  <──┘──┘───────┘
  |
  ├──> E30-S5 (Building Prompt) — needs S2
  ├──> E30-S6 (ACM Prompt) — needs S3
  ├──> E30-S7 (Anthropic API) — independent
  |
  ├──> E30-S8 (Export) — needs S2+S3
  ├──> E30-S9 (AG Grid) — needs S1+S2
  |
  └──> E30-S10 (E2E Test) — needs all
```

Parallel: S2||S3, S5||S6, S7 anytime

---

## 7. Sprint Status YAML

```yaml
  # Epic 30: Salesforce Schema Alignment (P0) - NEW 2026-03-01
  epic-30: backlog
  e30-s1-salesforce-schema-config-loader: backlog
  e30-s2-building-record-table-domain-model: backlog
  e30-s3-update-acm-record-salesforce-item: backlog
  e30-s4-dependent-picklist-validator: backlog
  e30-s5-extraction-prompt-building-fields: backlog
  e30-s6-extraction-prompt-acm-item-fields: backlog
  e30-s7-anthropic-claude-direct-api: backlog
  e30-s8-salesforce-ready-export: backlog
  e30-s9-ag-grid-column-update-two-view: backlog
  e30-s10-e2e-salesforce-alignment-test: backlog
```

---

## 8. Workflow Status Addition

```yaml
  correct-course-salesforce-alignment: "_bmad-output/sprint-change-proposal-20260301-salesforce.md"
```

---

## 9. Timeline

| Phase | Stories | SP | Duration |
|-------|---------|-----|----------|
| Foundation | S1, S7 | 5 | 2-3 days |
| Schema | S2, S3, S4 | 8 | 3-4 days |
| Extraction | S5, S6 | 5 | 2-3 days |
| Output | S8, S9 | 4 | 2 days |
| Validation | S10 | 3 | 1-2 days |
| **Total** | **10 stories** | **28** | **~10-12 days** |

---

## 10. Approval

| Role | Agent | Decision |
|------|-------|----------|
| PM | John | PENDING |
| Architect | Winston | PENDING |
| SM | Bob | PENDING |
| QA | Quinn | PENDING |
