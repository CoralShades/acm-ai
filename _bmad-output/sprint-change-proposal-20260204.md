# Sprint Change Proposal: Victorian BAR Format Expansion

> **Date:** 2026-02-04
> **Status:** ✅ APPROVED
> **Prepared by:** John (Product Manager)
> **Trigger:** Course Correction Analysis - PRD/Architecture/Epics alignment review

---

## 1. Issue Summary

### Problem Statement
The current PRD, Architecture, and Epics were designed for NSW School SAMP (School Asbestos Management Plan) documents with a 20-field schema. Analysis of actual input/output requirements reveals that:

1. **Input documents** are Victorian Government Asbestos Risk Assessments (multiple provider formats)
2. **Required output** is Victorian BAR (Building Asbestos Register) format requiring 43-47 fields
3. **Current schema** has only 20 fields - missing 27+ required BAR fields

### Discovery Context
- **Discovered during:** Course Correction workflow with user-provided sample documents
- **Evidence:**
  - Sample PDFs: Prensa (Broadmeadows Police), Greencap (Alexandra Hospital)
  - Sample Excel BAR outputs: 43 columns (Broadmeadows), 47 columns + 26 sheets (Alexandra)

### Impact Level
**MAJOR** - Requires schema expansion, epic modifications, and new stories

---

## 2. Impact Analysis

### 2.1 Epic Impact

| Epic | Impact | Changes Required |
|------|--------|------------------|
| E1: ACM Extraction | 🔴 HIGH | Schema expansion 20→50 fields, multi-format PDF support |
| E2: AG Grid | 🟡 MEDIUM | Column definitions expansion, visibility management |
| E3: Citations | 🟢 LOW | No major changes |
| E4: Chat | 🟢 LOW | Context builder update for new fields |
| E5: Export | 🔴 HIGH | Excel export P2→P0, BAR template compliance |
| E6: Rebranding | 🟢 LOW | No changes |
| E7: Upload Wizard | 🟡 MEDIUM | Site configuration capture step |
| E8-E10 | 🟢 LOW | No changes |

### 2.2 Artifact Changes Required

#### PRD Updates
- Section 5.1: Expand ACM Record Schema (+35 fields)
- Section 2.2: Add organization hierarchy data model
- Section 2.3: Update spreadsheet column list
- Section 4.3: Expand AG Grid configuration
- Section 5.2: Add new API endpoints for configuration
- **NEW:** BAR export format specification section
- **NEW:** Site configuration requirements section

#### Architecture Updates
- Section 3.1: Expand database schema
- Section 4.2: Expand API types
- Section 5.2: Multi-format PDF detection patterns
- Section 6.1: Expanded column definitions
- **NEW:** Site configuration data flow
- **NEW:** BAR Excel export architecture

#### Epic/Story Updates
- E1-S1: Schema expansion
- E1-S3: Multi-format extraction
- E1-S7 (NEW): Site configuration UI
- E1-S8 (NEW): Product classification
- E2-S2: 47+ columns
- E2-S3: Expanded filtering
- E2-S8 (NEW): Column visibility management
- E5-S1: Full BAR CSV
- E5-S2: P0 Excel export
- E5-S3 (NEW): Template management
- E5-S4 (NEW): Field mapping
- E7-S4: Site config during upload
- E7-S7 (NEW): Upload site configuration

---

## 3. Recommended Approach

### Selected Path: Direct Adjustment (Option 1)

**Rationale:**
1. **Incremental changes** - Can add new fields/stories without disrupting existing work
2. **Low risk** - Schema expansion is additive, not breaking
3. **Clear scope** - New requirements are well-defined from sample analysis
4. **Maintains momentum** - Team can continue current work while integrating changes

### Implementation Strategy
1. **Phase 1:** Schema expansion (E1-S1 modification)
2. **Phase 2:** Multi-format extraction (E1-S3 modification)
3. **Phase 3:** Site configuration (E1-S7, E7-S7 new stories)
4. **Phase 4:** Export compliance (E5-S2, E5-S3 new stories)
5. **Phase 5:** Spreadsheet UI (E2 modifications)

### Effort Estimate
- **Additional stories:** 7 new + 6 modified
- **Estimated additional effort:** 2-3 sprints

### Risk Assessment
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Schema migration complexity | Low | Medium | Use optional fields, additive changes |
| PDF format variations | Medium | Medium | Extensible parser pattern, provider detection |
| BAR template changes | Low | High | Template versioning, mapping configuration |

---

## 4. Detailed Change Proposals (Approved)

### CP#1: Expand ACM Record Schema ✅ APPROVED
- Add 35 fields for Victorian BAR support
- Organization hierarchy, location metadata, ACM classification, removal tracking
- All new fields optional for backward compatibility

### CP#2: Update Epic 1 Stories ✅ APPROVED
- Modify E1-S1: Schema expansion
- Modify E1-S3: Multi-format extraction
- NEW E1-S7: Site Configuration Data Entry
- NEW E1-S8: ACM Product Classification

### CP#3: Upgrade Epic 5 (Export) ✅ APPROVED
- E5-S2: PROMOTE from P2 to P0 (critical for BAR export)
- Modify E5-S1: Full BAR column export
- NEW E5-S3: BAR Template Management
- NEW E5-S4: Export Field Mapping Configuration

### CP#4: Update Epic 2 (Spreadsheet) ✅ APPROVED
- Modify E2-S2: 47+ columns with grouping
- Modify E2-S3: Expanded filtering
- NEW E2-S8: Column Visibility Management

### CP#5: Update Epic 7 (Upload Wizard) ✅ APPROVED
- Modify E7-S4: Site configuration during upload
- NEW E7-S7: Site Configuration During Upload

---

## 5. PRD MVP Impact

### MVP Scope Change
**EXPAND** - MVP now includes full Victorian BAR compliance

### Updated MVP Checklist
- ✅ ACM data extraction from PDFs (multi-format)
- ✅ Site configuration for non-extractable fields (NEW)
- ✅ Spreadsheet view with 47+ columns (EXPANDED)
- ✅ CSV export (EXPANDED to full BAR columns)
- ✅ **Excel BAR export (PROMOTED from post-MVP)** (NEW CRITICAL)
- ✅ Cell citations and PDF viewer
- ✅ Chat with ACM context

### What Moves to Post-MVP
- BAR template upload/management (can use default template)
- Advanced field mapping configuration (can use default mappings)

---

## 6. Implementation Handoff

### Change Scope Classification
**MODERATE** - Backlog reorganization needed

### Handoff Recipients

| Role | Responsibility |
|------|----------------|
| **PM (John)** | Update PRD with expanded schema and requirements |
| **Architect** | Update Architecture document with new data flows |
| **Scrum Master** | Reorganize backlog with new/modified stories |
| **Development Team** | Implement expanded schema and new stories |

### Immediate Actions
1. PM: Update PRD Sections 5.1, 2.2, 2.3, 4.3, 5.2
2. Architect: Update Architecture Sections 3.1, 4.2, 5.2, 6.1
3. SM: Add 7 new stories, modify 6 existing stories in backlog
4. Dev: Begin E1-S1 schema migration preparation

### Success Criteria
- [ ] All 47 BAR columns representable in schema
- [ ] PDF extraction works for Prensa and Greencap formats
- [ ] Site configuration UI captures non-extractable fields
- [ ] Excel export produces BAR-compliant spreadsheet
- [ ] User can upload PDF and export BAR Excel within 5 clicks

---

## 7. Approval

**User Approval Status:** ✅ APPROVED (2026-02-04)

All 5 individual change proposals have been approved incrementally:
- ✅ CP#1: Schema Expansion
- ✅ CP#2: Epic 1 Updates
- ✅ CP#3: Epic 5 Updates
- ✅ CP#4: Epic 2 Updates
- ✅ CP#5: Epic 7 Updates

**Final Approval:** ✅ APPROVED by User - Ready for implementation handoff

---

## Appendix A: Complete Field Mapping

See `findings.md` for detailed PDF → BAR field mapping analysis.

## Appendix B: Sample Document Analysis

### Input PDFs Analyzed
1. **Clutch_Broadmeadows Police Station** (Prensa Pty Ltd) - 19 pages, 20 register columns
2. **Clucth_Alexandra District Hospital** (Greencap) - 34 pages, 16 register columns

### Output Excel BAR Analyzed
1. **Clutch_Broadmeadows_Police_BAR.xlsx** - 1 sheet, 43 columns, 32 rows
2. **Clucth_Alexandra_District_BAR.xlsm** - 26 sheets, 47 columns, 533 rows

---

*Generated by Course Correction Workflow - BMad Method*
