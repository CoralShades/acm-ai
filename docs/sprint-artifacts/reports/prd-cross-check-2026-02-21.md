# PRD vs Sprint-Status Cross-Check Report

**Date:** 2026-02-21
**Sources compared:**
- PRD: `_bmad-output/project-planning-artifacts/acm-ai/05-epics-and-stories.md` (last updated 2026-02-20)
- Sprint-Status: `docs/sprint-artifacts/sprint-status.yaml` (last updated 2026-02-21)

---

## 1. Stories in sprint-status.yaml but NOT defined in PRD

These stories exist in tracking but have no story definition section in the PRD file.

### Epic 1 — 12 stories missing from PRD
| Story ID | YAML Key | Sprint Status | Notes |
|----------|----------|---------------|-------|
| E1-S7 | `e1-s7-ai-powered-acm-extraction` | done | Referenced in PRD dependency graph but never has a `### E1-S7` section |
| E1-S13 | `e1-s13-fix-page-reference-tracking` | done | Added via RAG Strategy Alignment SCP (2026-02-07); no PRD section |
| E1-S14 | `e1-s14-contextual-embedding-enrichment` | done | Same RAG SCP; no PRD section |
| E1-S15 | `e1-s15-corrective-rag-validation-loop` | done | Same RAG SCP; no PRD section |
| E1-S20 | `e1-s20-agentic-orchestrator` | done | Mentioned in E1 pipeline intro narrative (line 71) but no story section |
| E1-S21 | `e1-s21-extraction-pipeline-observability` | done | Post-PRD story; no definition |
| E1-S22 | `e1-s22-extraction-output-token-limit-fix` | done | Hotfix story; no PRD definition |
| E1-S23 | `e1-s23-token-limit-quality-validation` | ready-for-dev | Post-merge review story; no PRD definition |
| E1-S24 | `e1-s24-fix-assumed-positive-detection` | done | E2E gap fix sprint; no PRD definition |
| E1-S25 | `e1-s25-fix-external-internal-merging` | done | E2E gap fix sprint; no PRD definition |
| E1-S26 | `e1-s26-reduce-false-positive-extraction` | done | E2E gap fix sprint; no PRD definition |
| E1-S27 | `e1-s27-handle-duplicate-room-items` | done | E2E gap fix sprint; no PRD definition |

### Epic 2 — 4 stories missing from PRD
| Story ID | YAML Key | Sprint Status | Notes |
|----------|----------|---------------|-------|
| E2-S9 | `e2-s9-acm-grid-ux-improvements` | done | Post-PRD UX story; no definition |
| E2-S10 | `e2-s10-fix-test-portability` | done | Hotfix; no PRD definition |
| E2-S11 | `e2-s11-bar-field-type-safety` | ready-for-dev | Added via course correction; no PRD section |
| E2-S12 | `e2-s12-missing-bar-fields-in-grid` | done | E2E gap fix; no PRD definition |

### Epic 8 — 1 story missing from PRD
| Story ID | YAML Key | Sprint Status | Notes |
|----------|----------|---------------|-------|
| E8-S11 | `e8-s11-acm-register-grid-ui-polish` | done | PRD E8 defines S1-S10 (all archived); S11 added outside PRD process |

### Epic 11 — ENTIRE EPIC missing from PRD
The PRD Epic Overview table references E11 ("Search & Retrieval Enhancement", 2 stories), but there is **no `## Epic 11` section** with story definitions in the PRD file.

| Story ID | YAML Key | Sprint Status | Notes |
|----------|----------|---------------|-------|
| E11-S1 | `e11-s1-parent-document-retrieval` | done | Epic section missing entirely from PRD |
| E11-S2 | `e11-s2-hybrid-search-service` | drafted | Epic section missing entirely from PRD |

### Standalone (not part of any epic in PRD)
| Key | Sprint Status | Notes |
|-----|---------------|-------|
| `bug-extraction-status-tracking-gap` | done | Bug fix; no PRD story |
| `e2e-ci-github-actions-setup` | done | Infrastructure; no PRD story |

**Total: 21 sprint-status entries with no PRD story definition**

---

## 2. Stories in PRD but NOT in sprint-status.yaml

After careful review, **all stories defined with a `### ExY-SZ` section in the PRD have corresponding entries in sprint-status.yaml**. No PRD stories are missing from tracking.

---

## 3. Title Mismatches

Stories where the PRD section title differs significantly from the sprint-status YAML key slug.

| Story ID | PRD Title | Sprint-Status YAML Key Slug | Verdict |
|----------|-----------|----------------------------|---------|
| E1-S3 | "Implement Two-Stage ACM Extraction Pipeline" | `implement-acm-extraction-transformation` | **Mismatch** — YAML key uses old title from before 2026-02-05 update |
| E1-S10 | "MinerU Table Extraction Integration" | `mineru-table-extraction` | Minor abbreviation; acceptable |
| E1-S11 | "Generic Configurable Parser with BAR Field Schema" | `generic-configurable-parser` | Abbreviated; acceptable |

**Action needed:** E1-S3 YAML key slug is outdated. The key `e1-s3-implement-acm-extraction-transformation` should ideally be `e1-s3-implement-two-stage-acm-extraction-pipeline` to match the PRD. (Low priority since key is stable.)

---

## 4. Epic Status Mismatches

| Epic | PRD Overview Status | Sprint-Status Epic Status | Verdict |
|------|--------------------|-----------------------------|---------|
| E1 | "Done (26), Ready (1)" | `in-progress` | **Consistent** (26 done + 1 ready-for-dev = in-progress) |
| E2 | "Done (10), Ready (2)" | `in-progress` | **Consistent** |
| E3 | "Done" | `done` | Match |
| E4 | "Done" | `done` | Match |
| E5 | "Done (2), Ready (2)" | `in-progress` | **Consistent** (though sprint-status shows S4 as `drafted` not `ready-for-dev`) |
| E6 | "Done" | `done` | Match |
| E7 | "Done" | `done` | Match |
| E8 | "Archived" | `archived` | Match |
| E9 | "Done (2), Ready (1)" | `in-progress` | **Consistent** |
| E10 | "Ready" | `backlog` | **Mismatch** — PRD overview says "Ready" implying story is ready-for-dev; sprint-status epic-level is "backlog". Story E10-S1 is correctly "ready-for-dev" in sprint-status. Epic-level label discrepancy. |
| E11 | "Done (1), Backlog (1)" | `in-progress` | **Mismatch** — E11-S2 is `drafted` in sprint-status, not `backlog` as PRD overview states. Also PRD lacks E11 story sections entirely. |
| E12 | "Backlog" | `backlog` | **Consistent** (all 4 stories are `drafted` in sprint-status) |
| E13 | "Backlog" | `backlog` | Match |
| E14 | "Done" | `done` | Match |
| E15 | "Backlog" | `backlog` | **Mostly consistent** — sprint-status shows E15-S1 as `ready-for-dev`, E15-S2 as `drafted`, epic marked `backlog`. PRD was updated 2026-02-20 before E15-S1 was promoted. |
| E16 | "Backlog" (0/3) | `in-progress` | **TRUE MISMATCH** — E16-S2 completed 2026-02-21, sprint-status shows `in-progress` (1/3). PRD still shows "Backlog (0/3)". PRD not yet updated to reflect E16-S2 completion. |

---

## 5. PRD Structural Gaps

### 5.1 Epic 11 Section Missing Entirely
The PRD `## Epic 11: Search & Retrieval Enhancement` section **does not exist** in the file. The Epic Overview table acknowledges 2 stories, but there are no `### E11-S1` or `### E11-S2` story definition blocks. These stories were added by the RAG Strategy SCP (2026-02-07).

### 5.2 E1 Story Count Inconsistency
- PRD Epic Overview says **27 stories** for E1
- PRD has story sections defined for only **15 E1 stories** (S1-S6, S8-S12, S16-S19)
- Sprint-status tracks **27 E1 stories** (S1-S27)
- The PRD E1 intro narrative (line 79) says "20/20 stories complete as of 2026-02-08" — **stale count** (now 27 exist)

### 5.3 PRD Does Not Capture Post-Implementation Stories
12 E1 stories and 4 E2 stories were added during implementation (hotfixes, E2E gap fixes, post-merge validation) and were never backported to the PRD. This is expected behavior but creates a divergence.

### 5.4 E5-S4 Status Inconsistency
- PRD: E5 overview says "Done (2), Ready (2)" — implying S3 and S4 are both ready-for-dev
- Sprint-status: E5-S3 is `ready-for-dev`, E5-S4 is `drafted`
- E5-S4 was downgraded to `drafted` on 2026-02-21 (no tech-spec file exists); PRD overview still shows "Ready (2)"

---

## 6. Summary

### What Needs Reconciliation

| Priority | Action | Scope |
|----------|--------|-------|
| **High** | Add `## Epic 11` section to PRD with E11-S1 and E11-S2 story definitions | PRD missing Epic 11 entirely |
| **High** | Update PRD E16 status from "Backlog (0/3)" to "In-Progress (1/3)" — E16-S2 completed 2026-02-21 | PRD stale |
| **Medium** | Add PRD story definitions for E1-S13, S14, S15 (RAG Strategy stories, now done) | 3 done stories undocumented in PRD |
| **Medium** | Add PRD story definitions for E1-S20 (Agentic Orchestrator, now done) | Referenced in narrative, no story section |
| **Medium** | Update PRD E5 overview: S4 is `drafted` not `ready-for-dev` | Minor inaccuracy |
| **Medium** | Update PRD E10 overview: epic-level status alignment | Minor label discrepancy |
| **Medium** | Update PRD E11 overview: E11-S2 is `drafted` not `backlog` | Stale status |
| **Low** | Add PRD story definitions for E1-S21..S27 and E2-S9..S12, E8-S11 | Implementation-time stories; informational |
| **Low** | Fix E1-S3 YAML key slug: `implement-acm-extraction-transformation` → should reflect updated title | Cosmetic |
| **Low** | Update PRD E1 intro narrative: "20/20 stories" → accurate count | Stale narrative |

### Story Count Summary

| Source | Total Stories |
|--------|--------------|
| PRD (defined sections) | ~82 (15 E1 + 8 E2 + 4 E3 + 4 E4 + 4 E5 + 4 E6 + 7 E7 + 10 E8 + 3 E9 + 1 E10 + 0 E11 + 4 E12 + 3 E13 + 11 E14 + 2 E15 + 3 E16) |
| Sprint-Status (tracked) | 104 (102 stories + 1 bug + 1 infra) |
| **Gap** | **22 entries in sprint-status with no PRD story definition** |
