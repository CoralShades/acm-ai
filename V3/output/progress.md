# V3 Planning — Progress Journal

## Session: 2026-03-02 — Party Mode V3 Planning

### Status: COMPLETE

### Completed
- All 12 pre-read documents loaded and analyzed
- 5 debate topics resolved with full multi-agent participation
- v3-party-mode-plan.md synthesized (31 stories, 88 SP, 5 epics)
- Planning files maintained throughout

### Key Decisions
1. Docling + MinerU 2.x now, Google Doc AI later
2. Consensus layer BEFORE LLM interpretation
3. Anthropic Claude Sonnet for extraction (FR-1409 revised)
4. SSE for all operations (not WebSockets)
5. Two-view UI: building sidebar + item grid
6. Schema freeze gate after E30 before downstream work
7. 31 stories across 5 epics, ~31-40 days

### Follow-Up Update (same session)
- All 6 open questions (Q1-Q6) resolved by Demi
- Q1: Building_Sub_Category__c confirmed absent — chain simplified to BuildingType→Category
- Q2: WARN during editing, REJECT on export
- Q3: MinerU torch test in E31-S1, subprocess bridge contingency
- Q4: Google Doc AI deferred (not V3)
- Q5: Cell-level bbox accepted (~250KB negligible)
- Q6: E29 R1/R2 reviewed during E32 story writing
- AI provider strategy updated: Anthropic default + OpenRouter fallback (MUST NOT break)
- Ollama model evaluation spike added as E32-S6 (2 SP)
- Capability registry routing table added (6 task types × providers)
- Totals updated: 32 stories, 90 SP, ~32-42 days

### MinerU Audit Corrections (same session)
- CRITICAL: Torch constraint was WRONG (`<2.7`). Actual: `>2.6.0,<3` — our torch 2.10.0 is COMPATIBLE
- Risk R1 ELIMINATED (no torch conflict)
- MinerU has 3 backends since v2.7.0: pipeline, VLM, hybrid. Selected: hybrid (default)
- E31-S1 simplified from 3→2 SP (no subprocess bridge needed)
- E31-S6 Alexander benchmark separated: completionState fix first (E27 bug), then MinerU delta
- Consensus normalizer must handle VLM image-based output (not just HTML tables)
- CUDA 12.6 compat added as low-risk R11
- Totals revised: 32 stories, 89 SP, ~32-42 days

### Next Steps
1. BMAD: PRD v3.0 (/bmad:mmm:edit-prd)
2. BMAD: Architecture v3.0 (/bmad:mmm:create-architecture)
3. BMAD: Epics & Stories (/bmad:mmm:create-epics-and-stories)
4. BMAD: Sprint Planning (/bmad:mmm:sprint-planning)

---

## Session: 2026-03-02 — PRD v3.0 Edit (BMAD /edit-prd workflow)

### Status: COMPLETE

### Completed
- PRD v3.0 edit via BMAD edit-prd workflow (step-e-01 discovery → step-e-02 review → execution)
- All V3 FR series added with testable acceptance criteria
- All existing FRs preserved (additive only)

### Changes Made to 03-prd.md
1. **Header:** v3.0, dated 2026-03-02, updated change log
2. **Section 1.3:** Scope updated to reference V3 expansion
3. **Section 2.12:** FR-1400 Series — SF Schema Alignment (12 FRs, verbatim from SCP)
4. **Section 2.13:** FR-1500 Series — Multi-Provider Extraction (6 FRs)
5. **Section 2.14:** FR-1600 Series — UI/UX Flows (10 FRs)
6. **Section 2.15:** FR-1700 Series — Streaming & Observability (4 FRs)
7. **Section 2.16:** FR-1800 Series — AI Strategy (4 FRs)
8. **FR-1409:** Amended — Anthropic default + OpenRouter fallback (Party Mode consensus)
9. **Section 3.5:** NFR-500 Series — V3 Performance Targets (5 NFRs)
10. **Section 3.6:** NFR-600 Series — Data Sovereignty & Compliance (4 NFRs)
11. **Section 4.4:** V3 UI Structure — page flow + 10 new components
12. **Section 5.1.5:** Building Record Table schema (SF Building__c)
13. **Section 5.1.6:** Raw Extraction Table schema (per-provider provenance)
14. **Section 5.1.7:** V3 Schema Additions to existing tables (acm_record, acm_table_section, site_config, field_schema)
15. **Section 5.2:** 15 new V3 API endpoints added
16. **Section 5.3.1:** Salesforce Export Format spec
17. **Section 5.4.1:** V3 Target Pipeline (5-phase flow)
18. **Section 5.5:** SF Vocabulary Alignment mapping table (8 BAR→SF mappings)
19. **Section 7.2:** 20 V3 test scenarios (T-V3-001 through T-V3-020)
20. **Section 8:** V3 Rollout Phases 5-9 (E30-E34)
21. **Section 10A:** 11 new glossary terms
22. **Section 10B:** 3 new references (MinerU, Anthropic API, SF Data Loader)
23. **Section 10C:** v3.0 change log entry
24. **Section 11:** V3 Scope Expansion (overview, epic summary, dependency graph, data model, AI routing, FR traceability)

### Key Decisions
- All 36 new FRs have testable acceptance criteria in pipe-delimited table format
- FR-1409 amended per Party Mode consensus (Anthropic default, NOT exclusive; OpenRouter MUST remain)
- BAR→SF vocabulary mapping documented explicitly (e.g., "Good"→"Stable")
- FR numbering: 1400 (SF alignment), 1500 (extraction), 1600 (UI), 1700 (streaming), 1800 (AI)
- NFR numbering: 500 (V3 perf), 600 (data sovereignty)

### Reboot Check
1. Last milestone: PRD v3.0 complete — all V3 sections added, verification passed
2. Current task: None (PRD edit complete)
3. Blockers: None
4. Last files modified: _bmad-output/project-planning-artifacts/acm-ai/03-prd.md, V3/output/task_plan.md, V3/output/progress.md
5. Next action: BMAD Architecture v3.0 (/bmad:mmm:create-architecture)

---

## Session: 2026-03-02 — Architecture v3.0 (BMAD /create-architecture workflow)

### Status: COMPLETE

### Completed
- Architecture v3.0 created as Section 14 of 04-architecture.md (appended to existing v1.3 content)
- All 10 required architecture sections written with full technical detail
- 3 parallel research agents used to analyze: V3 technical docs, SF field summaries + codebase, current architecture structure
- V3 architecture section standalone copy saved to V3/output/v3-architecture-section.md

### Changes Made to 04-architecture.md
1. **Header:** Updated to v3.0, dated 2026-03-02, added v3.0 change log entry
2. **Section 14.0:** V3 Architecture Overview — key changes, supersession map
3. **Section 14.1:** Data Model — Mermaid ER with SF API field names, BuildingRecord + ACMRecord Pydantic models, type change migration table, embedding preservation
4. **Section 14.2:** Extraction Pipeline — 5-phase flow diagram, ExtractionProvider protocol, NormalizedExtractionResult, consensus layer (3-stage matching, 4-level conflict resolution), feature flags
5. **Section 14.3:** AI Processing — two-phase extraction (Building__c then Item__c), ModelCapability enum, ModelPolicy, direct ChatAnthropic + OpenRouter fallback, structured output via tool_use, batching strategy
6. **Section 14.4:** Dependent Picklist Validation — SalesforcePicklistValidator class, ACM chain (36 combos), Building chain (114→13), WARN/REJECT policy, Negative→N/A business rule
7. **Section 14.5:** Provenance — 6-layer provenance chain, EditHistoryEntry model, click-to-source UI flow
8. **Section 14.6:** SSE — 15 event types across 3 categories, PipelineEventBus, V3StreamingState Zustand store, SSE→React Query refetch pattern
9. **Section 14.7:** Frontend — page flow, 10 new components, AG Grid two-view config (building + item), DependentPicklistEditor cell editor
10. **Section 14.8:** Export — SF Data Loader format, External ID linkage, validation gate, BAR backward compatibility, SFExportService
11. **Section 14.9:** Migration — 6 additive migrations (38-43), data migration script, vocabulary mapping, rollback plan, schema freeze gate
12. **Section 14.10:** API Design — 15 new V3 endpoints (building CRUD, raw extraction, SF schema, export, admin, SSE), TypeScript response types
13. **Section 14.11:** Audit Finding Traceability — W1-W12 mapped to architecture sections
14. **Section 14.12:** V3 File Impact Summary — 28 files (NEW/CRITICAL/HIGH/MEDIUM/REWRITE)

### Verification Results
- All 10 architecture sections present (13 sub-sections under §14)
- Mermaid ER diagram with SF API field names (196 __c references)
- ExtractionProvider protocol designed with NormalizedExtractionResult
- Consensus layer: 3-stage matching + 4-level conflict resolution + 4 confidence tiers
- Provenance: 6-layer chain (PDF → raw → consensus → AI → validation → edit)
- SSE: 15 event types across extraction/AI processing/bulk categories
- Migration: 6 additive migrations, vocabulary mapping, rollback plan
- All audit findings W1-W12 + Amelia's risks addressed in §14.11

### Reboot Check
1. Last milestone: Architecture v3.0 complete — all 10 sections, verification passed
2. Current task: None (Architecture complete)
3. Blockers: None
4. Last files modified: _bmad-output/project-planning-artifacts/acm-ai/04-architecture.md, V3/output/v3-architecture-section.md, V3/output/task_plan.md, V3/output/progress.md
5. Next action: BMAD Epics & Stories v3.0 (/bmad:mmm:create-epics-and-stories)

---

## Session: 2026-03-03 — Epics & Stories v3.0 (BMAD /create-epics-and-stories)

### Status: IN PROGRESS

### Context
- All pre-read documents loaded (Party Mode plan, audit, PRD v3.0, arch v3.0, UX design, SCP, tech research)
- Primary source: Party Mode plan Section 3 (Epic Boundary Recommendations) with 32 stories, 89 SP
- Secondary adjustments: Audit findings J11-J14 (missing stories), UX design detail, prompt constraints
- Epic numbering: E30-E34 (E1-28 done, E29 S1-S4 done, S5-S8+R1/R2 archived)

### Key Adjustments from Party Mode Baseline
- Added E33-S7 (Building Detail Page) per audit finding J14
- Split E33-S7 (SF Export) into E33-S8 to make room
- Adjusted some SP estimates down to respect max 5 SP constraint
- All stories have full AC, dependencies, files affected, risk levels
- FR traceability added to each story

### Completed
- All 33 stories written with full ACs, SP, dependencies, files affected, risk levels
- Epic header/overview table updated (E30-E34 added)
- V3 Dependency Graph (text diagram) added
- Schema Freeze Gate specification written
- FR Traceability Matrix covering all 36 V3 FRs
- Audit Finding Coverage matrix (J11-J14, W1-W12)
- Cross-Epic Dependencies table

### Key Decisions
1. **SP Distribution:** E30:29, E31:15, E32:16, E33:25, E34:12 = 97 SP total
2. **E33-S7 added** (Building Detail Page) per audit finding J14 — was missing from Party Mode plan
3. **E33-S8 split** from E33-S7 (SF Export UI as separate story)
4. **Some SP adjusted down** from Party Mode: E30-S3 (4→3), E30-S7 (4→3), E32-S1 (4→3), E32-S2 (4→3), E33-S1 (4→3) to stay within the max 5 SP constraint and reflect refined scope understanding
5. **SP total 97** (vs Party Mode's 89) — accounts for audit upward revisions and added stories (S7, S8 in E33)
6. **Schema Freeze Gate** explicitly documented between E30-S6 and all downstream epics
7. **E34-S1 can start early** (SSE infrastructure needed by E33-S1, parallel development with mock SSE)

### Reboot Check
1. Last milestone: Epics & Stories v3.0 COMPLETE — 33 stories across 5 epics, 97 SP
2. Current task: None (Epics & Stories complete)
3. Blockers: None
4. Last files modified: _bmad-output/project-planning-artifacts/acm-ai/05-epics-and-stories.md, V3/output/task_plan.md, V3/output/progress.md
5. Next action: BMAD Sprint Planning (/bmad:mmm:sprint-planning)
