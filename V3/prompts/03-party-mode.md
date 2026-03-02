# 03: Party Mode — V3 Multi-Agent Planning Session

> **BMAD Command:** `/bmad-party-mode`
> **Agent:** All Agents (Winston, Mary, John, Bob, Quinn, Amelia, Sally)
> **Depends On:** 01-correct-course (E29/E30 archived) + 02-tech-research (provider evaluation)
> **Output:** `V3/output/v3-party-mode-plan.md`
> **Run in:** Fresh context window
> **NOTE:** This is the critical planning session. Bring all V3 documents.

---

## Pre-Read Documents (Agent should read ALL before starting)

### Approved V3 Requirements
- `V3/SCP-20260301-SF-salesforce-alignment.md` — SF alignment (approved)
- `V3/output/e30-multi-agent-audit-unified.md` — Multi-agent audit findings
- `V3/output/item_fields_summary.md` — SF Item__c fields (154 fields, 23 picklists)
- `V3/output/building_fields_summary.md` — SF Building__c fields (143 fields, 18 picklists)

### Technical Research (from Step 02)
- `V3/output/tech-research-extraction-providers.md` — Provider evaluation + consensus layer design

### Architecture Context (from P0)
- `V3/output/solution-architecture-v3.md` — Client solution architecture (extracted markdown)
- `V3/output/heuristic-rules-reference.md` — Extraction rules (if assessed as relevant in P0)
- `V3/output/bmad-architecture-audit.md` — Architecture audit (if assessed as relevant in P0)

### Current System State
- `_bmad-output/project-planning-artifacts/acm-ai/03-prd.md` — Current PRD
- `_bmad-output/project-planning-artifacts/acm-ai/04-architecture.md` — Current architecture
- `docs/architecture/e29-architecture-delta.md` — E29 architecture changes
- `V3/output/SCP-V3-scope-expansion.md` — Course correction document (from Step 01)

---

## Prompt

```text
/bmad-party-mode

## V3 Multi-Agent Planning Session: ACM-AI Scope Expansion

### Session Goal
Produce a unified V3 plan covering ALL new requirements. Each agent debates their domain, identifies gaps, proposes solutions, and the session synthesizes into a coherent plan with epic boundaries.

### Background
ACM-AI has completed Epics 1-28 and E29 S1-S4 (JSON parser, benchmark harness, unified orchestrator, capability registry). The remaining E29 stories and E30 (Salesforce alignment) have been archived in favor of a comprehensive V3 scope expansion.

The V3 vision encompasses:
1. Multi-provider parallel extraction with consensus layer
2. Salesforce Building__c + Item__c schema alignment
3. Completely new UI flows
4. Smart AI batching across providers
5. SSE streaming for all operations
6. Full extraction provenance tracking

### DEBATE TOPIC 1: Multi-Provider Extraction Architecture + Consensus Layer

**For discussion by: Winston (Architect), Amelia (Dev), Quinn (QA)**

Refer to: `V3/output/tech-research-extraction-providers.md` for provider evaluation.

Questions to resolve:
- What is the provider adapter interface? How do we normalize output from Docling, Google Doc AI, and PaddleOCR into a common format?
- How does the consensus layer work? Voting algorithm? Confidence thresholds?
- Where does consensus happen in the pipeline? Before or after LLM interpretation?
- How do we handle the user's choice of "extract from one or all providers" in the upload flow?
- What's the storage model for multi-provider results? Separate `acm_table_section` rows per provider? Or a unified table with provider metadata?
- How does this interact with the existing orchestrator from E29 S3-S4?
- PaddlePaddle venv isolation: subprocess bridge (like MinerU pattern) or Docker container?

### DEBATE TOPIC 2: New UI Flows (Wizard, Raw Tables, Provenance)

**For discussion by: Sally (UX), John (PM), Amelia (Dev)**

The V3 UI must support:
- **Upload wizard**: User uploads PDF → selects extraction provider(s) → sees progress → lands on results
- **Raw extracted table view**: Shows the raw extracted data BEFORE AI processing. Editable. Saved to database.
- **Building ID generation**: Auto-assign BLD#001, BLD#002, etc. to keep buildings unified across the app
- **AI-filled records view**: Separate table showing AI-enriched records mapped to raw building records
- **Provenance viewer**: Click a button on any record row to see WHERE it was extracted from (page, table coordinates, provider, AI model, confidence, edit history)
- **Record wizard**: Edit records with dependent picklist cascading (SF validation)
- **Bulk operations**: Multi-select, bulk edit, bulk export
- **Two-view layout**: Building grid + ACM items per building (from E30 audit)

Questions to resolve:
- What is the page flow? Upload → Raw Table → AI Processing → Building View → Item View?
- How does the raw table relate to the AI-filled table? 1:1 mapping? Or AI creates additional records?
- Where does the building ID assignment happen? During extraction or during AI processing?
- How does the provenance click-through work technically? PDF.js viewer with bounding box overlay?
- What AG Grid configuration is needed for dependent picklist cascading?
- How does the wizard handle records that fail SF validation?

### DEBATE TOPIC 3: AI Batching Strategy + Model Routing

**For discussion by: Winston (Architect), Mary (BA), Amelia (Dev)**

Current state: Esperanto multi-provider abstraction with OpenRouter fallback chain.
E30 SCP proposed: Anthropic Claude only for extraction.
V3 requirement: Smart routing across Ollama (local), OpenRouter (multi-model), Google (cloud).

Questions to resolve:
- Should extraction be locked to one provider (Anthropic) or dynamically routed?
- How to handle token limits? Batch by building? By page range? By table count?
- What's the Pydantic schema for LLM requests? How do different providers handle structured output?
- OpenRouter vs direct API for Claude — cost, reliability, feature parity?
- Local Ollama — for what tasks? Classification? Enrichment? Or just as fallback?
- How does the capability registry (E29 S4) fit? Extend it for multi-provider routing?
- What happens when a provider fails mid-batch? Retry? Fallback? Partial results?

### DEBATE TOPIC 4: SSE Streaming + AG-UI Integration

**For discussion by: Winston (Architect), Amelia (Dev), Sally (UX)**

Current state: SSE endpoints exist for extraction progress. AG-UI event emitter exists but limited.

V3 requirement: Full SSE for ALL endpoints, real-time progress for every operation, AG-UI micro-transactions.

Questions to resolve:
- Which endpoints need SSE? Extraction (existing), export, AI processing, validation, bulk operations?
- AG-UI protocol: what events does the frontend need? Progress bars? Record-by-record streaming? Error notifications?
- How to handle long-running operations (multi-building extraction, 50+ page PDFs)?
- Should we use Server-Sent Events, WebSockets, or a combination?
- How does SSE interact with the worker/command pattern? Commands emit events, frontend subscribes?
- What's the frontend state management pattern? Zustand store for streaming state?

### DEBATE TOPIC 5: AI Model Strategy (UNDECIDED — needs recommendation)

**For discussion by: All agents**

The current system uses Esperanto for multi-provider abstraction. E30 proposed Anthropic-only for extraction.
V3 adds Google and local Ollama as options.

Each agent should weigh in:
- Winston: Architecture implications of multi-provider vs single-provider
- Mary: Business analysis — cost, vendor lock-in, compliance
- John: Product perspective — what do users/officers need?
- Amelia: Implementation complexity — what's actually buildable?
- Quinn: Testing implications — how to test across providers?

### Expected Output

Produce `V3/output/v3-party-mode-plan.md` containing:

1. **Consensus Decisions** — Resolved answers for each debate topic
2. **Architecture Outline** — High-level V3 architecture (data model, pipeline flow, UI structure)
3. **Epic Boundary Recommendations** — How to split V3 into epics (suggested: Foundation/Schema, Extraction/Providers, AI/Processing, UI/Frontend, Integration/E2E)
4. **Story Count Estimates** — Rough SP and story counts per epic
5. **Risk Register** — Top risks with mitigation
6. **Open Questions** — Anything that needs more research or user decision
7. **PRD Delta** — New FRs beyond FR-1401-1412 that need adding
8. **Dependency Graph** — Epic and cross-epic dependencies

### Constraints
- SF alignment requirements (FR-1401-1412) are APPROVED — do not re-debate them
- E29 S1-S4 completed work is retained — build on it, don't redo it
- Design for 3 extraction providers, implement 2 now (per Demi's decision)
- Full extraction lineage is required (page, bbox, provider, model, confidence, edit history)
- Must support 2000+ production documents from various consulting firms
```

---

## Verification Checklist

After running:
- [ ] `V3/output/v3-party-mode-plan.md` exists
- [ ] All 5 debate topics have consensus decisions
- [ ] Epic boundary recommendations are clear (3-5 epics suggested)
- [ ] Story count estimates are provided per epic
- [ ] PRD delta lists new FRs beyond the E30 set
- [ ] AI model strategy has a clear recommendation
- [ ] Provenance data model is outlined
- [ ] Consensus layer design is specified
