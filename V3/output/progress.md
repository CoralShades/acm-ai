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
