# V3 Sprint Plan — ACM-AI

> **Generated:** 2026-03-03
> **Scrum Master:** Bob (BMAD SM agent)
> **Source:** Party Mode plan (2026-03-02), Implementation Readiness (Step 08/08b), Epics & Stories v3.0
> **Total:** 5 epics, 33 stories, 97 SP, 7 sprints (~32-42 days)

---

## Executive Summary

V3 transforms ACM-AI from a single-provider BAR-schema system into a multi-provider, Salesforce-aligned extraction platform with a two-view UI. The plan sequences 33 stories across 7 sprints with a critical **Schema Freeze Gate** after Sprint 2 that unlocks all downstream work.

**Key metrics:**
- Sprint velocity target: ~15-17 SP per sprint (conservative for V3 complexity)
- Critical path: E30 → E31 → E32 → E33-S3+ → E34 (~28-35 days)
- Parallel lane: E33-S1/S2 alongside E31, E32-S6 alongside E31/E32
- 4 gate milestones: Schema Freeze, Extraction Complete, AI Complete, UI Complete

---

## Gate Milestones

| Gate | After | Criteria | Unlocks |
|------|-------|----------|---------|
| **G1: SCHEMA FREEZE** | E30-S6 | All SF schema, models, validator, and vocabulary in place. Benchmarks pass. | E31, E32, E33, E34 |
| **G2: EXTRACTION COMPLETE** | E31-S6 | Dual-provider extraction produces consensus results. Broadmeadows 31/31. | E32-S1 (AI extraction) |
| **G3: AI COMPLETE** | E32-S5 | Full pipeline: extract → consensus → AI → validate → save. E2E test green. | E33-S3+ (advanced UI) |
| **G4: UI COMPLETE** | E33-S8 | All UI components functional. Upload → Extract → Review → Export flow works. | E34 (streaming, polish) |

---

## Critical Path

```
E30-S1 → E30-S2,S3 → E30-S4,S5,S6 → [SCHEMA FREEZE]
  → E31-S1 → E31-S2 → E31-S3,S4 → E31-S5 → E31-S6 → [EXTRACTION COMPLETE]
    → E32-S1 → E32-S2 → E32-S3 → E32-S5 → [AI COMPLETE]
      → E33-S3 → E33-S4 → E33-S8 → [UI COMPLETE]
        → E34-S1,S2,S3 → E34-S4

Critical path length: ~28-35 days (E30 8-10d + E31 6-8d + E32 6-8d + E33-S3+ 5-6d + E34 3-4d)
```

### Parallel Opportunities

```
CRITICAL PATH:   E30-S1..S6 ──── E31-S1..S6 ──── E32-S1..S5 ──── E33-S3..S8 ─── E34
                      │               │                │                │
PARALLEL LANE A:      │          E30-S7,S8        E32-S6 (spike)       │
                      │               │                                │
PARALLEL LANE B:      │          E33-S1,S2 ────────────────────────────┘
                      │          (after schema freeze,
                      │           API contracts defined)
```

**Parallel work items:**
1. **E30-S7 + E30-S8** can proceed alongside E31 (post schema freeze, not on critical path)
2. **E33-S1, E33-S2** can start after schema freeze (need API contracts, not AI data)
3. **E32-S6** (Ollama spike) only needs E30-S8, independent of E31/E32 critical path
4. **E34-S4** (artifact update) can start anytime after E30 as running documentation

---

## Sprint-by-Sprint Plan

### Sprint V3-1: Foundation Core (16 SP, ~5-6 days)

**Goal:** Load SF schema, create building model, align ACM record to SF Item__c fields.

| Story | SP | Epic | Description | Blocked By |
|-------|----|------|-------------|------------|
| E30-S1 | 5 | E30 | SF Schema Config Loader | None — **FIRST V3 STORY** |
| E30-S2 | 5 | E30 | Building Record Table + Domain Model | S1 |
| E30-S3 | 3 | E30 | ACM Record SF Item__c Alignment | S1 |
| E30-S4 | 5 | E30 | Dependent Picklist Validator | S1 |

> **Notes:**
> - S2, S3, S4 can all start once S1 is done (parallel within sprint)
> - S1 is the most foundational story — generates all SF field configs
> - Sprint produces: field_schema table, BuildingRecord model, SF aliases, validator

**Demonstrable progress:** API returns SF field schema; building_record table exists; picklist validation runs

---

### Sprint V3-2: Foundation Completion + Schema Freeze (8 SP, ~3-4 days)

**Goal:** Complete data migration, vocabulary transition, and hit the Schema Freeze Gate.

| Story | SP | Epic | Description | Blocked By |
|-------|----|------|-------------|------------|
| E30-S5 | 3 | E30 | Data Migration Script | S2, S3 |
| E30-S6 | 2 | E30 | BAR→SF Vocabulary Transition | S3 |
| E30-S8 | 3 | E30 | Anthropic Direct API + OpenRouter Fallback | S1 |

> **Notes:**
> - S5 and S6 are on the critical path (must complete for Schema Freeze)
> - S8 is NOT on the critical path but completes cleanly here
> - **SCHEMA FREEZE GATE** reached when S1-S6 are all Done
> - S7 (extraction prompts) deliberately held for Sprint V3-3 to benefit from E31 adapter work

**Demonstrable progress:** Existing data migrated to new schema; all tests pass with SF vocabulary; Anthropic direct extraction works

**MILESTONE: G1 — SCHEMA FREEZE** (after S5 + S6 done)

---

### Sprint V3-3: Multi-Provider Extraction (17 SP, ~6-7 days)

**Goal:** Add MinerU as second extraction provider, build consensus layer, wire pipeline.

| Story | SP | Epic | Description | Blocked By |
|-------|----|------|-------------|------------|
| E31-S1 | 2 | E31 | MinerU 2.x Integration + Validation | Schema Freeze |
| E31-S2 | 3 | E31 | Provider Adapter Framework | S1 |
| E31-S3 | 3 | E31 | Consensus Layer Core | S2 |
| E31-S4 | 2 | E31 | Raw Extraction Table + Storage | S2 |
| E30-S7 | 3 | E30 | Two-Phase Extraction Prompts | Schema Freeze, post-S2 ideal |
| E32-S6 | 2 | E32 | Ollama Model Evaluation Spike | E30-S8 only |
| E33-S2 | 5 | E33 | Building Grid + Item Grid (Two-View) | Schema Freeze, E30-S2 |

> **Notes:**
> - **Parallel lane:** E33-S2 and E32-S6 can run concurrently with E31 core work
> - S3 and S4 can proceed in parallel once S2 is done
> - E30-S7 fits here because it benefits from seeing adapter output shapes
> - E32-S6 (Ollama spike) is fully independent — only needs capability registry from E30-S8

**Demonstrable progress:** MinerU extracts tables; two providers produce raw output; building grid UI renders

---

### Sprint V3-4: Pipeline + SSE + Core UI (14 SP, ~5-6 days)

**Goal:** Complete dual-provider pipeline with consensus, add SSE infrastructure, launch core UI.

| Story | SP | Epic | Description | Blocked By |
|-------|----|------|-------------|------------|
| E31-S5 | 3 | E31 | Pipeline Integration | E31-S3, S4 |
| E31-S6 | 2 | E31 | Dual-Provider Benchmark | S5 |
| E31-S7 | 3 | E31 | PipelineEventBus + SSE Infrastructure | S5 |
| E33-S1 | 3 | E33 | Upload Wizard + Extraction Progress | Schema Freeze, E31-S7 |
| E32-S4 | 2 | E32 | Classifier Update (SF Taxonomy) | E30-S6 |

> **Notes:**
> - E31-S6 and E31-S7 can proceed in parallel after S5
> - E33-S1 needs SSE (E31-S7) — sequence matters within sprint
> - E32-S4 (classifier regex update) is independent of E31 — fills parallel slot

**Demonstrable progress:** Dual-provider extraction runs end-to-end; SSE streams events; upload wizard works

**MILESTONE: G2 — EXTRACTION COMPLETE** (after E31-S6)

---

### Sprint V3-5: AI Extraction + Validation (13 SP, ~5-6 days)

**Goal:** Two-phase AI extraction (Building + Item), SF validation with correction loop, E2E test.

| Story | SP | Epic | Description | Blocked By |
|-------|----|------|-------------|------------|
| E32-S1 | 3 | E32 | Building__c AI Extraction Node | E31-S5, E30-S7 |
| E32-S2 | 3 | E32 | Item__c AI Extraction Node | S1 |
| E32-S3 | 3 | E32 | SF Validation + Correction Loop | S2, E30-S4 |
| E32-S5 | 3 | E32 | Extraction Pipeline E2E Test | S1-S4 |

> **Notes:**
> - Strictly sequential: S1 → S2 → S3 → S5 (two-phase extraction pattern)
> - S5 validates the entire pipeline end-to-end (Broadmeadows 31/31, Alexander ≥42/43)
> - E32-S4 (classifier) was done in Sprint V3-4 to unblock S3's dependency on SF taxonomy

**Demonstrable progress:** Full pipeline: PDF → dual extract → consensus → AI Building + Item → validate → save. E2E test green.

**MILESTONE: G3 — AI COMPLETE** (after E32-S5)

---

### Sprint V3-6: Advanced UI (17 SP, ~6-7 days)

**Goal:** Dependent picklist editors, validation badges, raw table review, provenance, building detail, export.

| Story | SP | Epic | Description | Blocked By |
|-------|----|------|-------------|------------|
| E33-S3 | 3 | E33 | Dependent Picklist Cell Editors | E32, E30-S4 |
| E33-S4 | 3 | E33 | SF Validation Badges + Record Wizard | S2, S3, E30-S4 |
| E33-S5 | 3 | E33 | Raw Table Review (Opt-In) | E31-S4, S2 |
| E33-S6 | 3 | E33 | Provenance Viewer | E31-S4, S2 |
| E33-S7 | 3 | E33 | Building Detail Page | E30-S2, S2 |
| E33-S8 | 2 | E33 | Salesforce-Ready Export UI | E30-S2, E30-S3, S4 |

> **Notes:**
> - S5, S6, S7 can proceed in parallel (different files, different domains)
> - S3 → S4 is sequential (picklist editors needed for validation badges)
> - S8 depends on S4 (export blocked when validation errors exist)
> - This sprint delivers the complete officer workflow

**Demonstrable progress:** Full UI: upload → extract → building grid → edit with picklist cascading → validate → provenance → export

**MILESTONE: G4 — UI COMPLETE** (after E33-S8)

---

### Sprint V3-7: Integration, Streaming & Polish (9 SP, ~3-4 days)

**Goal:** Record streaming, bulk operations, performance targets, artifact cleanup.

| Story | SP | Epic | Description | Blocked By |
|-------|----|------|-------------|------------|
| E34-S1 | 2 | E34 | Record-by-Record Streaming | E31-S7, E33-S2 |
| E34-S2 | 2 | E34 | Bulk Operations | E33-S2, E33-S4, E31-S7 |
| E34-S3 | 2 | E34 | Performance Optimization | E31-S5, E32-S5 |
| E34-S4 | 3 | E34 | Canonical Artifact Update | All V3 epics |

> **Notes:**
> - S1, S2, S3 can proceed in parallel (different domains)
> - S4 (artifact update) runs last or alongside S1-S3 as documentation catch-up
> - Performance targets: Broadmeadows <120s, Alexander <300s

**Demonstrable progress:** Records stream into grid as extracted; bulk operations work; performance targets met; all docs updated

---

## Summary Table

| Sprint | Stories | SP | Duration | Milestone |
|--------|---------|---:|:--------:|-----------|
| V3-1: Foundation Core | E30-S1, S2, S3, S4 | 16 | 5-6 days | — |
| V3-2: Foundation Complete | E30-S5, S6, S8 | 8 | 3-4 days | **G1: SCHEMA FREEZE** |
| V3-3: Multi-Provider + Core UI | E31-S1..S4, E30-S7, E32-S6, E33-S2 | 17 | 6-7 days | — |
| V3-4: Pipeline + SSE | E31-S5..S7, E33-S1, E32-S4 | 14 | 5-6 days | **G2: EXTRACTION COMPLETE** |
| V3-5: AI Extraction | E32-S1..S3, S5 | 13 | 5-6 days | **G3: AI COMPLETE** |
| V3-6: Advanced UI | E33-S3..S8 | 17 | 6-7 days | **G4: UI COMPLETE** |
| V3-7: Integration & Polish | E34-S1..S4 | 9 | 3-4 days | V3 Done |
| **TOTAL** | **33** | **97** | **~33-40 days** | |

---

## First Story for Create Story (Step 10)

**E30-S1: SF Schema Config Loader** — 5 SP, HIGH risk, zero dependencies.

This is the single most foundational V3 story. It:
- Parses SF object metadata from `building_fields_summary.md` and `item_fields_summary.md`
- Creates `field_schema` table in SurrealDB with version, picklists, dependency chains
- Provides the `GET /api/acm/field-schema` endpoint consumed by every downstream story
- Unblocks E30-S2, S3, S4, S7, S8 (5 of 7 remaining E30 stories)

**Recommended next action:** Run `/bmad-agent-bmm-sm` → [CS] Create Story for E30-S1.

---

## Risk Notes (Carried from Party Mode)

| # | Risk | Mitigation |
|---|------|-----------|
| R2 | SF schema complexity causes prompt regression | Schema freeze gate. Broadmeadows benchmark at every story. |
| R3 | Consensus layer adds latency | Sequential GPU. Target <42s dual-provider. |
| R4 | 33+ test files need BAR→SF fixture updates | E30-S6 dedicated story. Automated find-and-replace. |
| R5 | AG Grid dependent picklist cascading complexity | AG Grid Enterprise getValues(). Prototype in E33-S3. |
| R10 | Sprint duration exceeds estimate | Parallelization (E33-S1,S2 alongside E31). Schema freeze gate. |
| R11 | CUDA 12.6 compat with MinerU VLM | Verify in E31-S1. Low risk. |

---

*Sprint plan generated 2026-03-03 by Bob (SM) via BMAD Sprint Planning workflow.*
*33 stories, 97 SP, 7 sprints, 4 gate milestones.*
