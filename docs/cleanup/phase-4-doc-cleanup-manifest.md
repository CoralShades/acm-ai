# Phase 4 Doc Cleanup Manifest

**Generated:** 2026-04-11
**Branch:** feat/sf-reconciliation-20260411
**Author:** doc-cleanup agent (sub-agent, read-only audit)
**Status:** READY FOR PARENT REVIEW

---

## Summary

| Category | Files Recommended for Deletion | Estimated Size |
|----------|-------------------------------|----------------|
| 1 — Old sprint-artifacts reports (pre-March-2026) | 7 files | ~104 KB |
| 2 — Superseded change proposals | 4 files | ~75 KB |
| 3 — Dead-link markdown | 1 file (1 dead link; rest still valid) | ~8 KB |
| 4 — BAR-only / fabricated-field docs | 2 files (high-signal) + 7 flagged for review | ~120 KB firm |
| 5 — Unrelated/scratch files at repo root (tracked) | 10 files | ~120 KB |
| **TOTAL FIRM DELETIONS** | **24 files** | **~427 KB** |
| Review-needed / borderline | 9 additional files | ~280 KB |

Screenshots under `docs/sprint-artifacts/reports/screenshots/` (19 PNGs, ~1.8 MB) are from April 2026 and still relevant to the current audit cycle — retained but flagged for review after SF reconciliation sprint is complete.

---

## Category 1: Old Sprint-Artifacts Reports

Criterion: git creation date before 2026-03-01. All of these predate the current SF reconciliation sprint and have been superseded by more recent audit passes.

| Path | Created (git date) | Reason |
|------|--------------------|--------|
| `docs/sprint-artifacts/reports/bug-extraction-status-tracking-gap.md` | 2026-02-21 | Pre-March story-level bug note; content superseded by sprint-status.yaml |
| `docs/sprint-artifacts/reports/demo-extraction-report-2026-02-22.md` | 2026-02-22 | Broadmeadows 31-record E2E baseline from feature-complete session; historical only |
| `docs/sprint-artifacts/reports/nfr-assessment-pr21-pr22.md` | 2026-02-21 | PR21/PR22 NFR assessment; both PRs long merged |
| `docs/sprint-artifacts/reports/phase4-ui-bug-report.md` | 2026-02-21 | Phase-4 UI bugs from Feb sprint; all resolved per sprint-status.yaml |
| `docs/sprint-artifacts/reports/post-merge-review-consolidated-report.md` | 2026-02-21 | Consolidated post-merge review from Feb; superseded |
| `docs/sprint-artifacts/reports/prd-cross-check-2026-02-21.md` | 2026-02-21 | PRD cross-check against sprint status; current PRD in `_bmad-output/project-planning-artifacts/` |
| `docs/sprint-artifacts/reports/ralph-sprint-verification-2026-02-22.md` | 2026-02-22 | Ralph autonomous sprint verification from feature-complete date; historical only |

**Note on reports/screenshots/:** The 19 PNGs in this subdirectory were created 2026-04-09 (same git commit as the `full-audit-2026-04-09` files). They document the Apr 9 browser audit and are recent — do NOT delete. See Category 7 for reasoning.

---

## Category 2: Superseded Change Proposals

All SCPs are drafts/proposals that led to epics now complete (per sprint-status.yaml). The four below are superseded by later SCPs or have been fully absorbed.

| Path | Superseded By | Reason |
|------|---------------|--------|
| `docs/sprint-artifacts/change-proposals/sprint-change-proposal-20260204.md` | `sprint-change-proposal-2026-02-08.md` (Generic Configurable Parser) and `sprint-change-proposal-20260207-workflow-extraction.md` | Victorian BAR Format Expansion — all scope absorbed into E8 and E12 (both done) |
| `docs/sprint-artifacts/change-proposals/sprint-change-proposal-2026-02-07.md` | `sprint-change-proposal-20260207-workflow-extraction.md` | RAG Strategy Alignment — same-week proposal, superseded by fuller workflow-extraction SCP |
| `docs/sprint-artifacts/change-proposals/sprint-change-proposal-20260220-extraction-monitor-ux.md` | `sprint-change-proposal-20260226-post-audit-fixes.md` | Extraction Monitor + UX — scope fully absorbed into E15, E16 (both done) |
| `docs/sprint-artifacts/change-proposals/sprint-change-proposal-20260222-extraction-quality.md` | `sprint-change-proposal-20260224-stakeholder-ux-redesign.md` | Extraction Quality proposal — PROPOSED status, scope absorbed into E19/E20 |

**Kept proposals** (still have distinct active scope or are the terminal version for their chain):
- `sprint-change-proposal-2026-02-08.md` — terminal SCP for generic configurable parser (E8)
- `sprint-change-proposal-20260207-workflow-extraction.md` — terminal SCP for E12/E13 Document Intelligence
- `sprint-change-proposal-20260224-stakeholder-ux-redesign.md` — terminal SCP for E19/E20 (APPROVED)
- `sprint-change-proposal-20260226-post-audit-fixes.md` — terminal SCP for E21
- `sprint-change-proposal-20260226-post-phase67-remediation.md` — terminal SCP for E22 (distinct ID: SCP-20260226B)
- `sprint-change-proposal-20260227-tableformer.md` — terminal SCP for E24

---

## Category 3: Dead-Link Markdown

Scope checked: `docs/`, `_bmad-output/`, and root `.md` files. Checked for links to non-existent files.

| Path | Dead Targets Count | Sample Dead Link |
|------|--------------------|-----------------|
| `docs/index.md` | 1 (mild) | `e2e-testing/README.md` — `docs/e2e-testing/` directory does not exist |

**Note:** `docs/index.md` contains links to `getting-started/`, `user-guide/`, `features/`, `deployment/` — all verified to exist. The only dead link is `e2e-testing/README.md`. Since `docs/index.md` is the documentation portal root, **recommend fixing the dead link rather than deleting the file.**

Multiple sprint-artifact files (e.g. `e1-s15`, `e1-s16` ... `project-retrospective-2026-02-22.md`) reference `_bmad-output/implementation-artifacts/` paths — however that directory still exists at `_bmad-output/implementation-artifacts/` (contains `implementation-readiness-report-2026-03-03.md` and `v3-ux-design.md`), so those links may point to moved stories rather than missing files. **Flagged for review rather than deletion.**

No other firm dead-link-only deletion candidates found.

---

## Category 4: BAR-Only / Fabricated-Field Docs

The SF pivot removes BAR-originated field names (`est_building_size_m2`, `daily_duration`, `level_of_activity`, `mobile_plant`, `building_risk_rating`, `psb_district_region`) and fabricated SF field names (`ACM_Name__c`, `ACM_Description__c`, `Room_ID__c` in Item context, `Floor_Level__c`, `Hygienist_Recommendations__c`, `ACM_Labelled__c`, `Identifying_Company__c`).

**Firm deletion candidates** (exclusively BAR-schema spec docs with high match counts, no other purpose):

| Path | Matching Field Names (count) | Reason |
|------|------------------------------|--------|
| `docs/sprint-artifacts/e30-s2-building-record-table-domain-model.md` | 40 matches — `est_building_size_m2`, `daily_duration`, `level_of_activity`, `mobile_plant`, `psb_district_region`, `Daily_Duration__c`, `Level_of_Activity__c`, `Est_Building_Size_m2__c` | Tech spec for building domain model based on old BAR-derived SF field list. Story status: **done** (2026-03-03). This spec is now historical; the SF pivot (Phase 2) supersedes the field list entirely. |
| `docs/sprint-artifacts/prompt-packs/2026-03-19-mcs11-remaining-building-room-id-audit-fix.md` | 4 matches — `est_building_size_m2`, `daily_duration`, `level_of_activity`, `mobile_plant` (in field table), `Room_ID__c` | Prompt-pack for Room_ID audit fix referencing old BAR field schema table. Room_ID__c is being removed in SF pivot. |

**Review-needed** (BAR fields appear incidentally or in historical context; do not recommend deleting without human review):

| Path | Matching Field Names (count) | Notes |
|------|------------------------------|-------|
| `docs/sprint-artifacts/e30-s3-acm-record-sf-item-alignment.md` | 3 matches — `ACM_Labelled__c`, `Hygienist_Recommendations__c`, `Room_ID__c` | SF Item alignment spec (done). Fields appear as mapping targets in transition table. Story is historical but the mapping context may still be reference-worthy. |
| `docs/sprint-artifacts/e33-s2-building-grid-item-grid-two-view.md` | 5 matches — `est_building_size_m2`, `daily_duration`, `level_of_activity`, `mobile_plant` | Two-view UI spec (done). BAR fields appear in TypeScript interface definition — spec is implemented; now stale vs. SF pivot. |
| `docs/sprint-artifacts/e33-s7-building-detail-page.md` | 3 matches — `est_building_size_m2`, `daily_duration`, `level_of_activity` | Building detail page spec (done). Fields in UI field group list. |
| `docs/sprint-artifacts/e33-s8-salesforce-ready-export-ui.md` | 1 match — `ACM_Name__c`, `ACM_Description__c`, `Room_ID__c`, `Risk_Status__c` | SF-ready export UI spec (done). Fields listed as SF column names in export mapping. Low risk — single-line context. |
| `docs/sprint-artifacts/pipeline-audit/findings.md` | 5 matches — `est_building_size_m2`, `daily_duration`, `level_of_activity`, `mobile_plant`, `psb_district_region` | Pipeline audit findings (historical, undated). BAR fields appear in a schema table. Worth preserving as audit record. |
| `docs/architecture/multi-consultant-format-design.md` | 1 match — `Hygienist_Recommendations__c` | Architecture doc. Single incidental match in column-mapping table. Keep — doc has broader value. |
| `docs/sprint-artifacts/e32-s1-building-extraction-node.md` | 1 match — `est_building_size_m2` | Building extraction node spec. Single incidental mention. Not worth deleting. |

**Protected files with BAR fields (do not delete — covered by protected list):**
- `_bmad-output/project-planning-artifacts/acm-ai/03-prd.md` — 1 match, protected
- `_bmad-output/project-planning-artifacts/acm-ai/04-architecture.md` — 8 matches, protected
- `_bmad-output/project-planning-artifacts/acm-ai/05-epics-and-stories.md` — 2 matches, protected
- `docs/samplePDF/analysis/acm_ai_pdf_extraction_stack_analysis.md` — under `docs/samplePDF/`, protected

---

## Category 5: Unrelated/Scratch Files at Repo Root

These are tracked in git but clearly belong to transient sessions, debug runs, or should live in `docs/sprint-artifacts/` or `scripts/` if needed at all.

| Path | Reason |
|------|--------|
| `findings.md` | Root-level session scratch file — chat debug session 2026-03-31. Proper location: `docs/sprint-artifacts/chat-debug-2026-03-31.md` (duplicate exists there). |
| `progress.md` | Root-level session scratch — chat debug 2026-03-31 progress tracker. |
| `task_plan.md` | Root-level session scratch — chat debug 2026-03-31 task plan. |
| `findings-ACM-FeatureComplete.md` | Root-level session scratch — feature-complete sprint (2026-02-22). Historical status summary now superseded by `docs/sprint-artifacts/project-retrospective-2026-02-22.md`. |
| `task_plan-ACM-FeatureComplet.md` | Root-level session scratch — feature-complete sprint. Superseded by retrospective. |
| `progress--ACM-FeatureComplet.md` | Root-level session scratch — feature-complete sprint. Superseded. (Note: has encoding artifact in content — `Ã¢â‚¬â€`.) |
| `acm-page-test.mjs` | One-off Playwright test script pointing to deleted `_bmad-output/implementation-artifacts/screenshots` path. Not part of the test suite (`tests/`). |
| `acm-page-test2.mjs` | Second one-off Playwright test script. Same issue. |
| `check_out.txt` | Empty file (0 bytes) containing only a Python `sys.path` check output. Zero utility. |
| `pytest_out.txt` | Captured pytest run output (1 KB). Transient debug artifact — not part of any report. |

**Not flagged (borderline, see Category 7):**
- `batch_fix_services.py` — was used for a mypy fix pass; may still be reference value. See Category 7.
- `mcp_port_summary.md` — MCP porting summary document. Has operational value as setup reference.
- `start_docs.md` — Setup verification checklist. Has ongoing value as ops reference.
- `broadmeadows_register.json`, `broadmeadows_text_mid.json` — Test fixture data referenced by tests.
- `source_dump.json` — 0-byte file; unambiguously stale but low priority.
- `files.zip` — 15 KB archive; unclear provenance, tracked, non-obvious what it contains. See Category 7.
- `broadmeadows-police-station-samp.pdf` — 1.8 MB test PDF at root; may duplicate `docs/samplePDF/`. See Category 7.

---

## Do NOT Delete (Flagged as Keep — Borderline)

| Path | Why Almost Flagged | Why Keeping |
|------|-------------------|-------------|
| `docs/sprint-artifacts/reports/screenshots/` (19 PNGs, ~1.8 MB) | Created 2026-04-09 (recent) | Documents the Apr 9 browser audit that preceded the SF reconciliation sprint. Relevant provenance. Review after sprint closes. |
| `docs/sprint-artifacts/full-audit-2026-04-09/` | Untracked, created 2026-04-09 | This is the audit that led to the current sprint. Keep as audit provenance. |
| `batch_fix_services.py` | Root-level Python utility, not in `scripts/` | Used for a mypy fix pass (563977ab); may be re-run. Recommend moving to `scripts/` rather than deleting. Flag as MOVE not DELETE. |
| `mcp_port_summary.md` | Operational doc at root | Has ongoing value if MCP servers need re-porting. Move to `docs/` subdirectory. |
| `start_docs.md` | Setup checklist at root | Ongoing ops reference. Move to `docs/getting-started/` or `docs/development/`. |
| `broadmeadows_register.json`, `broadmeadows_text_mid.json` | JSON data at root | These appear to be test fixture data used by E2E tests or manual runs. Move to `tests/fixtures/` rather than delete. |
| `source_dump.json` | 0-byte file | Zero-byte but tracked. Probably safe to delete but confirm with tests first. |
| `files.zip` | Unknown provenance | 15 KB zip at root, tracked. Content unknown without unzipping. Do not delete without inspecting contents. |
| `broadmeadows-police-station-samp.pdf` | 1.8 MB PDF at root | Likely duplicates `docs/samplePDF/Clutch_Broadmeadows.pdf` or similar. Verify before deleting — if duplicate, safe to remove. |
| `docs/architecture/multi-consultant-format-design.md` | 1 BAR field match | Only incidental BAR field mention; doc has broader architectural value for consultant format decisions. |
| `_bmad-output/planning-artifacts/v3-ux-design.md` | 1 BAR field match | UX design doc for V3. Single incidental match. Keep — `_bmad-output/planning-artifacts/` not listed as protected but is authoritative design record. |
| `_bmad-output/planning-artifacts/implementation-readiness-report-2026-03-03.md` | Historical readiness report | Documents gate decision for V3 Epics 30-34. Historical value. |
| `docs/sprint-artifacts/e33-s2-building-grid-item-grid-two-view.md` | 5 BAR field matches | Story is done; fields appear in TypeScript interface snippet. The spec documents the two-tab UI that is still in production. Review-needed rather than delete. |

---

## Commands for Parent Session to Execute

Review each command before running. Commands are ordered from lowest to highest risk.

### Category 1: Old Sprint-Artifacts Reports

```bash
git rm docs/sprint-artifacts/reports/bug-extraction-status-tracking-gap.md
git rm docs/sprint-artifacts/reports/demo-extraction-report-2026-02-22.md
git rm docs/sprint-artifacts/reports/nfr-assessment-pr21-pr22.md
git rm docs/sprint-artifacts/reports/phase4-ui-bug-report.md
git rm docs/sprint-artifacts/reports/post-merge-review-consolidated-report.md
git rm docs/sprint-artifacts/reports/prd-cross-check-2026-02-21.md
git rm docs/sprint-artifacts/reports/ralph-sprint-verification-2026-02-22.md
```

### Category 2: Superseded Change Proposals

```bash
git rm docs/sprint-artifacts/change-proposals/sprint-change-proposal-20260204.md
git rm docs/sprint-artifacts/change-proposals/sprint-change-proposal-2026-02-07.md
git rm docs/sprint-artifacts/change-proposals/sprint-change-proposal-20260220-extraction-monitor-ux.md
git rm docs/sprint-artifacts/change-proposals/sprint-change-proposal-20260222-extraction-quality.md
```

### Category 3: Dead-Link Markdown

No firm deletions — recommend fixing dead link in `docs/index.md` instead:
```bash
# Fix action: remove or update the line referencing e2e-testing/README.md in docs/index.md
# (line ~XX — search for "e2e-testing" in that file)
```

### Category 4: BAR-Only / Fabricated-Field Docs (firm deletions only)

```bash
git rm docs/sprint-artifacts/e30-s2-building-record-table-domain-model.md
git rm "docs/sprint-artifacts/prompt-packs/2026-03-19-mcs11-remaining-building-room-id-audit-fix.md"
```

### Category 5: Root-Level Scratch Files

```bash
git rm findings.md
git rm progress.md
git rm task_plan.md
git rm findings-ACM-FeatureComplete.md
git rm task_plan-ACM-FeatureComplet.md
git rm "progress--ACM-FeatureComplet.md"
git rm acm-page-test.mjs
git rm acm-page-test2.mjs
git rm check_out.txt
git rm pytest_out.txt
```

### Optional — Confirm Before Running

```bash
# Only if confirmed duplicate of docs/samplePDF/ equivalent:
# git rm broadmeadows-police-station-samp.pdf

# Only if contents confirmed non-essential:
# git rm files.zip

# Only if confirmed not referenced by any test:
# git rm source_dump.json

# Fix dead link in docs/index.md (edit, don't delete)
# grep -n "e2e-testing" docs/index.md
```
