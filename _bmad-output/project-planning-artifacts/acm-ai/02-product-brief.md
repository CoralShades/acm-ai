# Product Brief - ACM-AI

> **Product Name:** ACM-AI (Asbestos Containing Material - Artificial Intelligence)
> **Version:** 1.0
> **Date:** 2025-12-07
> **Author:** Mary (Business Analyst)

## 1. Executive Summary

**ACM-AI** transforms the Open Notebook platform into a specialized compliance and document intelligence tool for asbestos management. It enables facility managers, compliance officers, and contractors to upload School Asbestos Management Plans (SAMPs) and similar regulatory documents, automatically extract structured ACM Register data into an interactive spreadsheet, and query the data through AI-powered chat with full citation support.

## 2. Problem Statement

### Current Pain Points

| Stakeholder | Pain Point | Impact |
|-------------|------------|--------|
| Facility Managers | Manual data entry from PDFs to spreadsheets | Hours of tedious work, error-prone |
| Compliance Officers | No quick way to query ACM status across buildings | Delayed risk assessments |
| Contractors | Must manually search PDFs before any work | Time wasted, compliance risk |
| Regulators | Inconsistent data formats across schools | Difficult auditing |

### Root Cause
Asbestos Register data is locked inside PDF documents with no programmatic access. Existing solutions require cloud processing or expensive commercial tools.

## 3. Vision Statement

> **ACM-AI brings intelligence to asbestos compliance** - transforming static PDF reports into queryable, structured data with AI-powered insights, while keeping all processing local and private.

## 4. Goals and Success Metrics

### 4.1 Primary Goals

| Goal | Description | Success Metric |
|------|-------------|----------------|
| **G1: Automate Extraction** | Automatically parse ACM Register tables from PDFs | 90%+ extraction accuracy on target documents |
| **G2: Enable Querying** | Allow natural language questions about ACM data | Users can ask "What materials need attention in Building A?" |
| **G3: Maintain Traceability** | Every data point links back to source PDF | 100% of cells have citation metadata |
| **G4: Local-First** | All processing happens locally | Zero external API calls for document processing |

### 4.2 Secondary Goals

| Goal | Description |
|------|-------------|
| **G5: Export Capability** | Export filtered data to Excel/CSV |
| **G6: Multi-Document** | Compare ACM data across multiple schools |
| **G7: Rebrand** | Transition from "Open Notebook" to "ACM-AI" brand |

## 5. Target Users

### 5.1 Primary Users

| Persona | Role | Key Need |
|---------|------|----------|
| **Sarah** | School Facility Manager | Quick lookup of ACM locations before maintenance |
| **Mike** | Compliance Officer | Generate reports, track risk status across schools |
| **Lisa** | Asbestos Assessor | Verify register accuracy, update findings |

### 5.2 User Journey (Sarah - Facility Manager)

```
1. Sarah receives a work order to repair ceiling in Room B00A-R0003
2. Opens ACM-AI, uploads/selects the school's SAMP PDF
3. System extracts ACM Register into spreadsheet view
4. Sarah filters by Building "B00A" and Room "R0003"
5. Sees: "Ceiling Structures/Linings - Flat AC Sheeting - Non Friable - Good Condition - Low Risk"
6. Clicks the cell → sees highlighted location in original PDF
7. Sarah knows work can proceed with standard precautions
8. Asks chat: "What precautions for work near non-friable AC sheeting?"
9. AI responds with guidance, citing the SAMP policy sections
```

## 6. Proposed Solution

### 6.1 High-Level Features

| Feature | Description | Priority |
|---------|-------------|----------|
| **F1: PDF Upload & Processing** | Upload SAMP PDFs, extract via Docling | P0 (MVP) |
| **F2: AG Grid Spreadsheet View** | Interactive table with filtering, sorting, grouping | P0 (MVP) |
| **F3: Cell Citations** | Click cell → view source in PDF | P0 (MVP) |
| **F4: Chat with ACM Context** | Ask questions, get cited answers | P0 (MVP) |
| **F5: Export to Excel** | Download filtered data | P1 |
| **F6: Multi-School Support** | Manage multiple SAMPs in one workspace | P1 |
| **F7: Risk Dashboard** | Visual summary of risk levels | P2 |
| **F8: Change Tracking** | Compare register versions over time | P2 |

### 6.2 Solution Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        ACM-AI Frontend                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Source Panel │  │ AG Grid      │  │ Chat Panel   │          │
│  │ (PDF list)   │  │ (ACM Data)   │  │ (AI queries) │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │   FastAPI Backend │
                    └─────────┬─────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────┴───────┐   ┌─────────┴─────────┐   ┌──────┴──────┐
│ Docling       │   │ ACM Extraction    │   │ SurrealDB   │
│ (PDF Parse)   │   │ Pipeline          │   │ (Storage)   │
└───────────────┘   └───────────────────┘   └─────────────┘
```

## 7. Scope

### 7.1 In Scope (MVP)

- [x] Rebrand UI to ACM-AI
- [x] Upload and process SAMP PDFs
- [x] Extract ACM Register tables to structured data
- [x] Display in AG Grid with filtering/sorting
- [x] Cell-level citations linking to PDF page
- [x] Chat queries with spreadsheet context
- [x] Basic export (CSV)

### 7.2 Out of Scope (MVP)

- Mobile apps
- Multi-user authentication/RBAC
- Cloud deployment
- PDF annotation/editing
- Integration with external compliance systems
- Fine-tuning custom extraction models

## 8. Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Docling fails on complex PDF layouts | Medium | High | Fallback to manual correction UI |
| AG Grid license cost | Low | Medium | Use Community edition, evaluate Enterprise later |
| Varied SAMP formats across states | Medium | Medium | Start with NSW DoE format, add others iteratively |
| Performance with large registers | Low | Medium | Pagination, virtual scrolling in AG Grid |

## 9. Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| Open Notebook codebase | Technical | Available |
| Docling library | Technical | Integrated |
| AG Grid React | Technical | To install |
| Sample SAMP PDFs | Content | 3 samples available |

## 10. Timeline Considerations

### MVP Phases

| Phase | Focus |
|-------|-------|
| **Phase 1** | AG Grid integration + basic ACM extraction |
| **Phase 2** | Cell citations + PDF viewer integration |
| **Phase 3** | Chat context enhancement + export |
| **Phase 4** | Rebranding + polish |

## 11. Open Questions

1. **Q: Should we support other document types (e.g., Hazmat surveys)?**
   - Defer to v1.1, focus on SAMP format first

2. **Q: AG Grid Community vs Enterprise?**
   - Start with Community, evaluate Enterprise for Excel export feature

3. **Q: How to handle multi-page tables that span PDF pages?**
   - Docling should handle this; verify with sample PDFs

## 12. Approval

| Role | Name | Status |
|------|------|--------|
| Product Owner | User | Pending |
| Technical Lead | TBD | Pending |
| Business Analyst | Mary | Approved |
