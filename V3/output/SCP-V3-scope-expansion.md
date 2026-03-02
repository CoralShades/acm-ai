# Sprint Change Proposal: V3 Scope Expansion

> **SCP ID**: SCP-V3-scope-expansion
> **Date**: 2026-03-02
> **Author**: Demi (Project Owner) + Claude Opus 4.6 (Correct-Course Workflow)
> **Status**: APPROVED
> **Type**: Strategic Pivot — Scope Expansion + Epic Archival
> **BMAD Workflow**: /correct-course

---

## 1. Decision Rationale

### Trigger

After completing E29 S1-S4 (JSON parser, benchmark harness, unified orchestrator, capability registry) and reviewing the E30 Salesforce alignment proposal via multi-agent audit, the scope of required changes has expanded significantly beyond what E29 or E30 individually cover.

### Key Findings

1. **E29 Gate 2 FAIL** — The recovery stories (R1, R2) address benchmark fidelity and match-gap issues, but the underlying problems (single-provider extraction, BAR-only schema, monolithic prompt design) require a fundamentally different approach than agent decomposition within the current pipeline.

2. **E30 Salesforce Alignment** — The audit confirmed that Salesforce Building__c (143 fields) + Item__c (154 fields) alignment requires data model, extraction, validation, and export changes that are too broad for a single epic bolted onto E29.

3. **Multi-Agent Audit** (V3/output/e30-multi-agent-audit-unified.md) — Three independent audits (Claude, Codex, unified) converged on the need for:
   - Multi-provider extraction with consensus layer
   - Separate Building and Item extraction phases
   - Full provenance/lineage tracking
   - New UI surfaces (upload wizard, raw table editor, record wizard)

4. **Scope exceeds incremental correction** — The combination of SF alignment, multi-provider extraction, new UI, and pipeline restructuring constitutes a V3 reboot, not a course correction on E29/E30.

### Decision

**Archive E29 remaining stories and E30 SCP. Plan V3 from scratch through Party Mode + full BMAD planning cycle.**

This is NOT a pivot away from the existing system. E29 S1-S4 completed work (JSON parser, benchmark harness, unified orchestrator, capability registry) remains the foundation. V3 builds on top of it.

---

## 2. What's Archived

### E29 Stories (S5-S8)

| Story | Status Before | Status After | Rationale |
|-------|--------------|--------------|-----------|
| E29-S5: Agent Decomposition I (Table Parser + BAR Mapper) | drafted (blocked) | **archived** | V3 replaces BAR-only agent decomposition with multi-provider extraction + SF schema alignment |
| E29-S6: Agent Decomposition II (Enricher/Classifier/Validator) | drafted (blocked) | **archived** | V3 designs enrichment/classification around SF picklist chains, not BAR-only taxonomy |
| E29-S7: Validation Gate + Legacy Cleanup | drafted (blocked) | **archived** | Legacy cleanup will be addressed organically in V3 extraction epics |
| E29-S8: Export Hardening + Integration + Doc Alignment | drafted (blocked) | **archived** | V3 export design targets SF Data Loader format, not BAR Excel |

### E29 Recovery Stories (R1, R2)

| Story | Status Before | Status After | Rationale |
|-------|--------------|--------------|-----------|
| E29-R1: Benchmark Fidelity | review | **archived** | Benchmark fidelity improvements (Docling table seeding, normalization) carry forward as V3 requirements |
| E29-R2: Match-Gap Remediation | review | **archived** | Match-gap fixes (RoomMeta typing, room/location normalization) carry forward as V3 extraction requirements |

### E30 SCP (Salesforce Schema Alignment)

| Artifact | Action |
|----------|--------|
| V3/SCP-20260301-SF-salesforce-alignment.md | **Preserved as-is** — V3 input document |
| E30-S1 through E30-S10 (backlog entries) | **Never added to sprint-status** — superseded by V3 epic planning |
| FR-1401 through FR-1412 (PRD requirements) | **Carried forward** — approved decisions, will be incorporated into V3 PRD |

---

## 3. What Carries Forward (V3 Inputs)

### Completed Work (E29 S1-S4) — RETAINED

| Story | Deliverable | V3 Relevance |
|-------|-------------|--------------|
| E29-S1 | JSON parser resilience (markdown fence handling) | Foundation — all V3 extraction stages benefit |
| E29-S2 | Benchmark harness + baseline capture | Foundation — V3 uses same harness with expanded benchmarks |
| E29-S3 | Unified orchestrator path (no legacy fork) | Foundation — V3 builds on single-path architecture |
| E29-S4 | Capability registry + fallback contract | Foundation — V3 extends registry for multi-provider strategies |

### Approved Requirements (E30 FR-1400 Series) — CARRIED FORWARD

All Salesforce alignment requirements are approved decisions:
- **FR-1401**: Building data in building_record mapped to SF Building__c
- **FR-1402**: ACM data in acm_record mapped to SF Item__c
- **FR-1403**: Friability → ACM_Classification → ACM_Sub_Classification enforcement
- **FR-1404**: Building_Type → Building_Category → Building_Sub_Category enforcement
- **FR-1405**: Picklist values against exact SF values (case-sensitive)
- **FR-1406**: Building__c Data Loader CSV export
- **FR-1407**: Item__c Data Loader CSV export
- **FR-1408**: SF schema from JSON config (describe metadata)
- **FR-1409**: Anthropic Claude Sonnet as sole AI provider
- **FR-1410**: Separate Building and ACM field extraction AI calls
- **FR-1411**: Context-relevant Item_Name subsets by Product Group
- **FR-1412**: Business rule: Negative → Condition = N/A (negative)

### Analysis Documents — PRESERVED AS V3 INPUTS

| Document | Location | Content |
|----------|----------|---------|
| Multi-agent audit (unified) | V3/output/e30-multi-agent-audit-unified.md | Validated architectural analysis from 3 independent audits |
| Building fields summary | V3/output/building_fields_summary.md | SF Building__c field analysis |
| Item fields summary | V3/output/item_fields_summary.md | SF Item__c field analysis |
| Solution architecture V3 | V3/output/solution-architecture-v3.md | Preliminary V3 architecture sketch |
| Heuristic rules reference | V3/output/heuristic-rules-reference.md | Extraction heuristic rules catalog |
| BMAD architecture audit | V3/output/bmad-architecture-audit.md | Architecture gap analysis |
| E29 reconciled plan | V3/epic-29-pipeline-unification.reconciled.yaml | Reconciliation decisions (historical) |
| E30 SCP | V3/SCP-20260301-SF-salesforce-alignment.md | Full Salesforce alignment proposal |
| E29 SCP | V3/sprint-change-proposal-20260301-unified-pipeline.md | Original pipeline unification proposal |

---

## 4. V3 Scope Summary

V3 represents a comprehensive evolution of the ACM-AI extraction and compliance system. The following areas will be planned through the full BMAD cycle:

### 4.1 Multi-Provider Extraction
- Docling + Google Document AI + PaddleOCR with consensus/voting layer
- Provider-specific strengths: Docling (tables), Google Doc AI (handwriting/forms), PaddleOCR (fallback)
- Unified result merging with confidence scoring

### 4.2 Salesforce Schema Alignment
- Separate Building__c and Item__c data models (from E30 FR-1401 through FR-1412)
- Dependent picklist validation chains
- SF Data Loader-compatible export
- Two-phase extraction: Building fields then ACM Items per building

### 4.3 New UI Surfaces
- Upload wizard with document type detection and provider selection
- Raw table editor for manual correction of extracted tables
- Provenance viewer linking extracted records to source PDF locations
- Record wizard for creating/editing records with SF picklist guidance

### 4.4 AI Provider Strategy
- Anthropic Claude Sonnet as primary extraction provider (FR-1409)
- Batching strategy across multiple AI providers for cost optimization
- Structured output with Pydantic validation at every stage

### 4.5 Streaming & Observability
- SSE streaming for all extraction endpoints
- AG-UI protocol integration for real-time extraction monitoring
- Full extraction lineage/provenance tracking (table → record → field)

### 4.6 Pipeline Architecture
- Build on E29 S1-S4 unified orchestrator foundation
- Multi-provider capability registry (extending E29-S4)
- Per-stage metrics and quality gates
- Deterministic fallback chains per provider

---

## 5. Next Steps

| Step | Action | Owner | Output |
|------|--------|-------|--------|
| 1 | **Party Mode** — Brainstorm V3 epic structure with PM/Architect | Demi + AI Agents | V3 epic outline |
| 2 | **PRD Update** — Incorporate FR-1400 series + new scope | PM Agent | Updated PRD v2.0 |
| 3 | **Architecture** — V3 architecture document | Architect Agent | V3 architecture doc |
| 4 | **Epic Planning** — Create V3 epics with stories | SM Agent | V3 epics and stories |
| 5 | **Sprint Planning** — Sequence V3 stories into sprints | SM Agent | Updated sprint-status.yaml |

### Planning Constraints
- Do NOT create V3 epic entries in sprint-status.yaml until after Party Mode + epic planning completes
- V3 epics should be numbered starting from E30 (E30 SCP was never committed to sprint-status)
- All V3 planning documents go in `_bmad-output/planning-artifacts/` per BMAD convention

---

## 6. Impact Summary

| Area | Impact | Notes |
|------|--------|-------|
| sprint-status.yaml | E29 S5-S8 + R1/R2 archived | S1-S4 unchanged (done) |
| E30 SCP | Preserved as V3 input | Not added to sprint-status |
| V3 planning | Fresh BMAD cycle starting | Party Mode → PRD → Architecture → Epics |
| Codebase | No code changes | This is a planning-only correction |
| V3/output/ | All documents preserved | Serve as V3 inputs |

---

*SCP generated 2026-03-02. Approved by: Demi (Project Owner).*
