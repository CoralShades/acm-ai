# Product Brief - ACM-AI

> **Product Name:** ACM-AI (Asbestos Containing Material - Artificial Intelligence)
> **Version:** 4.0
> **Date:** 2026-03-31
> **Author:** Mary (Business Analyst)
> **Last Updated:** 2026-03-31

## 1. Executive Summary

**ACM-AI** is a fully operational intelligent compliance management system that transforms Asbestos Register Assessment (ARA) documents and related asbestos survey reports into structured, queryable data. Built on the Open Notebook platform, it enables facility managers, compliance officers, and contractors to upload ARA PDFs from multiple consultant formats (Victorian BAR, ARA, Prensa, Greencap, Clutch), automatically extract structured ACM Register data aligned to the Salesforce schema (Building__c + Item__c), and query the data through a unified AI-powered chat agent with full citation support.

The system supports both cloud AI providers (Anthropic, OpenRouter) and fully local extraction via Ollama models. The V3.5 per-row extraction pipeline processes individual table rows with 9-field extraction, achieving 100% accuracy on validated benchmark documents. An auto-notebook ("AI-Editor") is created on every upload, and a unified chat agent with 15+ tools provides human-in-the-loop record correction, entity extraction, and natural language querying.

## 2. Problem Statement

### Current Pain Points

| Stakeholder | Pain Point | Impact |
|-------------|------------|--------|
| Facility Managers | Manual data entry from PDFs to spreadsheets | Hours of tedious work, error-prone |
| Compliance Officers | No quick way to query ACM status across buildings | Delayed risk assessments |
| Contractors | Must manually search PDFs before any work | Time wasted, compliance risk |
| Regulators | Inconsistent data formats across schools | Difficult auditing |
| Government Data Teams | Manual Salesforce Data Loader imports from PDFs | Slow onboarding, format mismatches |

### Root Cause
Asbestos Register data is locked inside PDF documents with no programmatic access. Existing solutions require cloud processing or expensive commercial tools, and each consultant uses a different report format.

## 3. Vision Statement

> **ACM-AI brings intelligence to asbestos compliance** -- transforming static PDF reports into queryable, structured data with AI-powered insights, while keeping all processing local and private.

## 4. Goals and Success Metrics

### 4.1 Primary Goals

| Goal | Description | Target | Actual Result |
|------|-------------|--------|---------------|
| **G1: Automate Extraction** | Automatically parse ACM Register tables from PDFs | 90%+ extraction accuracy | **100% Broadmeadows (31/31 records), 84% Alexander (36/43 records)** |
| **G2: Enable Querying** | Allow natural language questions about ACM data | Users can ask "What materials need attention in Building A?" | **Unified chat agent with 15+ tools, entity extraction, HITL corrections** |
| **G3: Maintain Traceability** | Every data point links back to source PDF | 100% of cells have citation metadata | **ProvenanceViewer with PDF.js + bounding box overlay implemented** |
| **G4: Local-First** | All processing happens locally | Zero external API calls for document processing | **Ollama support enables 100% local extraction (llama3.1:8b default)** |

### 4.2 Secondary Goals

| Goal | Description | Actual Result |
|------|-------------|---------------|
| **G5: Export Capability** | Export filtered data to Excel/CSV | **CSV, Excel, BAR template, and Salesforce Data Loader format exports delivered** |
| **G6: Multi-Document** | Compare ACM data across multiple sites | **Multi-source support with per-building extraction and cross-site querying** |
| **G7: Rebrand** | Transition from "Open Notebook" to "ACM-AI" brand | **VAEA government branding complete with custom design system** |

## 5. Target Users

### 5.1 Primary Users

| Persona | Role | Key Need |
|---------|------|----------|
| **Sarah** | School Facility Manager | Quick lookup of ACM locations before maintenance |
| **Mike** | Government Compliance Officer | Generate reports, track risk status across schools, BAR export for Salesforce Data Loader import |
| **Lisa** | Asbestos Assessor | Review extraction results, verify register accuracy, correct records via HITL chat |

### 5.2 User Journey (Sarah - Facility Manager)

```
1. Sarah receives a work order to repair ceiling in Room B00A-R0003
2. Opens ACM-AI, navigates to /jobs — sees her uploaded documents
3. Clicks into the job detail — system has already extracted ACM Register into AG Grid
4. Switches to "ACM Records" tab, filters by Building "B00A" and Room "R0003"
5. Sees: "Ceiling Structures/Linings - Flat AC Sheeting - Non Friable - Good Condition - Low Risk"
6. Clicks the cell → ProvenanceViewer shows highlighted location in original PDF with bbox overlay
7. Sarah knows work can proceed with standard precautions
8. Opens the chat sidebar: "What precautions for work near non-friable AC sheeting?"
9. AI responds with guidance, citing the ARA policy sections
```

## 6. Implemented Solution

### 6.1 Features

| Feature | Description | Priority | Status |
|---------|-------------|----------|--------|
| **F1: PDF Upload & Processing** | Upload ARA PDFs, extract via Docling + MinerU with consensus | P0 (MVP) | **Done** |
| **F2: AG Grid Spreadsheet View** | Interactive table with filtering, sorting, grouping, column presets | P0 (MVP) | **Done** |
| **F3: Cell Citations** | Click cell → ProvenanceViewer with PDF.js + bbox overlay | P0 (MVP) | **Done** |
| **F4: Chat with ACM Context** | Unified chat agent with 15+ tools, HITL corrections, entity extraction | P0 (MVP) | **Done** |
| **F5: Export** | CSV, Excel, BAR template, Salesforce Data Loader format | P1 | **Done** |
| **F6: Multi-Consultant Support** | Victorian BAR, ARA, Prensa, Greencap, Clutch format detection | P1 | **Done** |
| **F7: SSE Real-Time Streaming** | PipelineEventBus with live extraction progress via SSE | P1 | **Done** |
| **F8: Auto-Notebook (AI-Editor)** | Auto-created notebook per upload with enriched metadata | P1 | **Done** |
| **F9: Salesforce Schema Alignment** | Building__c + Item__c field mapping, picklist validation | P1 | **Done** |
| **F10: Observability** | Langfuse (self-hosted) + LangSmith (dev) + Logfire (Pydantic traces) | P1 | **Done** |
| **F11: Risk Dashboard** | Visual summary of risk levels | P2 | Planned |
| **F12: Change Tracking** | Compare register versions over time | P2 | Planned |

### 6.2 Solution Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     ACM-AI Frontend (Next.js 15, port 8503)            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌───────────┐  │
│  │ Jobs List    │  │ AG Grid      │  │ Smart Chat   │  │ AI-Editor │  │
│  │ (/jobs)      │  │ (Buildings + │  │ (CopilotKit  │  │ (auto-    │  │
│  │              │  │  ACM Records)│  │  15+ tools)  │  │  created) │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  └───────────┘  │
│        Zustand state  │  AG-UI/SSE streaming  │  React Query           │
└───────────────────────┼───────────────────────┼───────────────────────┘
                        │                       │
              ┌─────────┴───────────────────────┴─────────┐
              │          FastAPI Backend (port 5055)        │
              │    LangGraph (acm_extraction, supervisor)   │
              │    PipelineEventBus (SSE streaming)         │
              └─────────┬───────────┬───────────┬─────────┘
                        │           │           │
              ┌─────────┴───┐ ┌────┴─────┐ ┌───┴──────────┐
              │ Docling +   │ │ Ollama / │ │ SurrealDB    │
              │ MinerU 2.x  │ │ Anthropic│ │ (port 8000)  │
              │ (PDF Parse) │ │ /OpenRtr │ │              │
              └─────────────┘ └──────────┘ └──────────────┘
```

## 7. Scope

### 7.1 In Scope -- Delivered

**MVP (all complete):**
- [x] Rebrand UI to ACM-AI (VAEA government branding)
- [x] Upload and process ARA PDFs
- [x] Extract ACM Register tables to structured data
- [x] Display in AG Grid with filtering/sorting/grouping
- [x] Cell-level citations linking to PDF page (ProvenanceViewer)
- [x] Chat queries with spreadsheet context
- [x] Basic export (CSV)

**Post-MVP (all complete):**
- [x] Salesforce schema alignment (Building__c + Item__c field mapping)
- [x] Multi-provider extraction (Docling + MinerU consensus engine)
- [x] Multi-consultant format support (Victorian BAR, ARA, Prensa, Greencap, Clutch)
- [x] Per-row extraction pipeline (V3.5) with 9-field per-row LLM calls
- [x] SSE real-time streaming (PipelineEventBus)
- [x] Unified chat agent with 15+ tools and HITL record correction
- [x] Auto-notebook / AI-Editor creation on upload
- [x] Observability stack (Langfuse self-hosted + LangSmith dev + Logfire Pydantic traces)
- [x] Excel, BAR template, and Salesforce Data Loader exports
- [x] Ollama-first local extraction (llama3.1:8b default)
- [x] Column visibility presets and localStorage column state
- [x] Per-building export dropdown (current building + all)

### 7.2 Out of Scope

- Mobile apps
- Multi-user authentication/RBAC
- Cloud deployment
- PDF annotation/editing
- Integration with external compliance systems (Salesforce direct API)
- Fine-tuning custom extraction models

## 8. Risks and Mitigations

| Risk | Original Assessment | Actual Outcome |
|------|---------------------|----------------|
| Docling fails on complex PDF layouts | Medium likelihood, High impact | **Mitigated: Multi-provider consensus (Docling + MinerU), format detectors, schema inference, regex fallback** |
| AG Grid license cost | Low likelihood, Medium impact | **Resolved: AG Grid Community edition used successfully for all features** |
| Varied document formats across states | Medium likelihood, Medium impact | **Solved: MCS sprint delivered 3+ format profiles with automatic detection (Victorian BAR, ARA, Prensa, Greencap, Clutch)** |
| Performance with large registers | Low likelihood, Medium impact | **Solved: Per-row extraction (V3.5), AG Grid virtual scrolling, SSE streaming for real-time progress** |
| Ollama model quality for extraction | Medium likelihood, Medium impact | **Mitigated: `format="json"` enforcement, truncation detection with cloud retry, per-row mode reduces context window requirements to 2048 tokens** |
| SurrealDB record ID handling | Low likelihood, High impact | **Resolved: `type::thing()` for record refs, `RecordID` to string coercion in ObjectModel, param binding patterns documented** |

## 9. Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| Open Notebook codebase | Technical | **Integrated (forked and extended)** |
| Docling library | Technical | **Integrated (PDF parsing, TableFormer)** |
| MinerU 2.x | Technical | **Integrated (merged cell handling, cross-page stitching)** |
| AG Grid React (Community) | Technical | **Installed and operational** |
| CopilotKit | Technical | **Integrated (AG-UI chat, useCoAgent)** |
| LangGraph | Technical | **Integrated (acm_extraction + supervisor graphs)** |
| SurrealDB | Technical | **Operational (Docker, named volume)** |
| Ollama | Technical | **Integrated (local-first extraction, llama3.1:8b)** |
| Langfuse (self-hosted) | Observability | **Deployed (Docker, localhost:3000)** |
| Sample ARA PDFs | Content | **10+ samples across 5 consultant formats** |

## 10. Delivery Timeline

| Phase | Epics | Focus | Status |
|-------|-------|-------|--------|
| **Phase 1** | E1-E7 | Core extraction pipeline, AG Grid integration, upload wizard | **Done** |
| **Phase 2** | E8-E16 | UX polish, enterprise readiness, search, settings, model management | **Done** |
| **Phase 3** | E17-E29 | Live intelligence, pipeline hardening, MinerU integration, observability | **Done** |
| **V3** | E30-E35 | Salesforce schema alignment, multi-provider consensus, two-view UI, SSE streaming | **Done** |
| **V3.5** | E37 | Per-row extraction pipeline (one LLM call per row, 9 fields) | **Done** |
| **V4.0** | MCS + Chat + UX sprints | Multi-consultant format support, unified chat agent with 15+ tools, auto-notebook, VAEA branding | **Done** |

## 11. Resolved Questions

1. **Q: Should we support other document types (e.g., Hazmat surveys)?**
   - **Answered:** Multi-consultant format support now handles Victorian BAR, ARA, Prensa, Greencap, and Clutch formats via automatic format detection and schema inference.

2. **Q: AG Grid Community vs Enterprise?**
   - **Answered:** AG Grid Community edition is sufficient for all implemented features including filtering, sorting, grouping, column presets, and virtual scrolling.

3. **Q: How to handle multi-page tables that span PDF pages?**
   - **Answered:** MinerU 2.x provides cross-page table stitching with merged cell handling. Docling provides DataFrames as a secondary provider. The consensus engine reconciles results from both.

## 12. Approval

| Role | Name | Status |
|------|------|--------|
| Product Owner | User | **Approved** |
| Technical Lead | Claude AI | **Approved** |
| Business Analyst | Mary | **Approved** |
| Delivery Status | -- | **Delivered (V4.0, 2026-03-31)** |
