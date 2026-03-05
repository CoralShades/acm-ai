# 04: Edit PRD — Update with V3 Requirements

> **BMAD Command:** `/bmad-bmm-edit-prd`
> **Agent:** John — 📋 Product Manager
> **Depends On:** 03-party-mode (V3 plan + PRD delta)
> **Output:** Updated `_bmad-output/project-planning-artifacts/acm-ai/03-prd.md`
> **Run in:** Fresh context window

---

## Pre-Read Documents

- `_bmad-output/project-planning-artifacts/acm-ai/03-prd.md` — Current PRD (to be edited)
- `V3/output/v3-party-mode-plan.md` — Party Mode output (source of new requirements)
- `V3/SCP-20260301-SF-salesforce-alignment.md` — Approved SF alignment FRs (FR-1401–FR-1412)
- `V3/output/e30-multi-agent-audit-unified.md` — Audit findings (Mary's PRD gap analysis M1-M14)
- `V3/output/building_fields_summary.md` — SF Building__c field reference
- `V3/output/item_fields_summary.md` — SF Item__c field reference

---

## Prompt

```text
/bmad-bmm-edit-prd

## PRD Update: V3 Scope Expansion

### Context
The ACM-AI PRD at `_bmad-output/project-planning-artifacts/acm-ai/03-prd.md` needs updating to reflect the V3 scope expansion. The original PRD covers Epics 1-17. We need to add V3 requirements while preserving the existing approved content.

### Sources for New Requirements

1. **Salesforce Alignment (APPROVED)** — Add FR-1401 through FR-1412 from `V3/SCP-20260301-SF-salesforce-alignment.md`
2. **Party Mode Findings** — Add new FRs from `V3/output/v3-party-mode-plan.md` section "PRD Delta"
3. **Multi-Agent Audit Gaps** — Address findings M1-M14 from the audit

### New Functional Requirement Areas to Add

#### FR-1500 Series: Multi-Provider Extraction
- FR-1501: Support parallel extraction from multiple providers (Docling, Google Doc AI, PaddleOCR)
- FR-1502: Provider adapter interface for normalized output
- FR-1503: Consensus layer with confidence scoring (HIGH/MEDIUM/LOW)
- FR-1504: User selection of extraction provider(s) during upload
- FR-1505: Provider-specific configuration and feature flags

#### FR-1600 Series: Raw Data + Provenance
- FR-1601: Store raw extracted table data before AI processing
- FR-1602: Editable raw data table view in UI
- FR-1603: Auto-generate building IDs (BLD#001 pattern) during extraction
- FR-1604: Full extraction provenance (page, bounding box, provider, model, confidence)
- FR-1605: Provenance click-through to source PDF location
- FR-1606: Edit history tracking for all record modifications

#### FR-1700 Series: AI Processing + Batching
- FR-1701: Smart AI batching based on token limits and model capabilities
- FR-1702: Multi-provider AI routing (Ollama/OpenRouter/Google/Anthropic)
- FR-1703: AI-filled records table mapped to raw building records
- FR-1704: Batch processing configuration (per-building, per-page-range, per-table)

#### FR-1800 Series: UI Flows
- FR-1801: Upload wizard with provider selection step
- FR-1802: Raw table editor with inline editing
- FR-1803: Building list view with drill-down to ACM items
- FR-1804: Record editing wizard with dependent picklist cascading
- FR-1805: Bulk operations (multi-select, bulk edit, bulk export)
- FR-1806: Provenance viewer panel (per-record extraction source)

#### FR-1900 Series: SSE + Real-Time
- FR-1901: SSE streaming for all long-running operations
- FR-1902: AG-UI micro-transaction events for real-time frontend updates
- FR-1903: Record-by-record streaming during extraction
- FR-1904: Progress tracking for multi-provider parallel extraction

### Instructions
1. Read the current PRD thoroughly
2. Add V3 sections WITHOUT removing existing approved content
3. Add all FR-1400 series (from E30 SCP) and new FR-1500–1900 series
4. Update the "Non-Functional Requirements" section if Party Mode identified new NFRs
5. Update the "User Personas" section if new user workflows require it
6. Add a "V3 Scope" section that clearly delineates V3 additions from the original PRD
7. Use specific, testable acceptance criteria for each FR
8. Cross-reference Party Mode decisions for AI model strategy, consensus layer design, etc.

### Constraints
- Do NOT remove or modify existing approved FRs (FR-001 through FR-1300)
- FR-1401–FR-1412 from E30 SCP are APPROVED — add them verbatim
- New FRs (1500+) should reference Party Mode output for detailed specifications
- Maintain the existing PRD structure and formatting conventions
```

---

## Verification Checklist

After running:
- [ ] `03-prd.md` updated with V3 section
- [ ] FR-1401–FR-1412 present (SF alignment)
- [ ] FR-1500 series present (multi-provider extraction)
- [ ] FR-1600 series present (raw data + provenance)
- [ ] FR-1700 series present (AI batching)
- [ ] FR-1800 series present (UI flows)
- [ ] FR-1900 series present (SSE streaming)
- [ ] Existing FRs untouched
- [ ] Each new FR has testable acceptance criteria
