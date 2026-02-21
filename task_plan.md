# Task Plan — Sprint Artifact Consolidation + Remaining Stories

Updated: 2026-02-21 (Sprint Artifact Cleanup added)
Source of truth: `docs/sprint-artifacts/sprint-status.yaml`

---

## ACTIVE: Sprint Artifact Consolidation (2026-02-21)

### Phase 1: PRD Cross-Check [AGENT: prd-researcher / sonnet]
- [ ] Read `_bmad-output/project-planning-artifacts/acm-ai/05-epics-and-stories.md`
- [ ] Cross-check all stories vs `docs/sprint-artifacts/sprint-status.yaml`
- [ ] Identify: stories in PRD not in sprint-status, vice versa, title mismatches
- [ ] Write findings to `docs/sprint-artifacts/reports/prd-cross-check-2026-02-21.md`

### Phase 2: File Migration [AGENT: file-organizer / sonnet]
- [ ] Create `docs/sprint-artifacts/change-proposals/` directory
- [ ] Move all sprint change proposals from `_bmad-output/` root + `planning-artifacts/` → `docs/sprint-artifacts/change-proposals/`
- [ ] Create `docs/sprint-artifacts/reports/` directory
- [ ] Move historical reports from `_bmad-output/implementation-artifacts/` → `docs/sprint-artifacts/reports/`
- [ ] Copy unique done-story files from `implementation-artifacts/` → `docs/sprint-artifacts/`
  - e1-s11-generic-configurable-parser.md
  - e1-s13-fix-page-reference-tracking.md
  - e1-s14-contextual-embedding-enrichment.md
  - e1-s15-corrective-rag-validation-loop.md
  - e1-s16-document-structure-toc-extraction.md
  - e1-s17-building-inventory-compilation.md
  - e1-s18-page-level-section-tagging.md
  - e1-s19-document-metadata-extraction-enhancement.md
  - e1-s20-agentic-extraction-orchestrator.md
  - e1-s21-extraction-pipeline-observability.md
  - e1-s22-extraction-output-token-limit-fix.md
  - e11-s1-parent-document-retrieval.md
  - e2-s9-acm-grid-ux-improvements.md
  - e5-s4-export-field-mapping-configuration.md
  - e8-s11-acm-register-grid-ui-polish.md

### Phase 3: Git Cleanup [AGENT: file-organizer / sonnet]
- [ ] `git rm` all duplicate tech-spec-*.md from `_bmad-output/implementation-artifacts/` (57 files)
- [ ] `git rm` duplicate story e*.md files from `_bmad-output/implementation-artifacts/` that now exist in docs/
- [ ] `git rm` stale sprint-status.yaml from `_bmad-output/implementation-artifacts/`
- [ ] `git rm` progress.md, task_plan.md, findings.md from `_bmad-output/implementation-artifacts/`
- [ ] `git rm` sprint change proposals from `_bmad-output/` root (3 files)
- [ ] `git rm` sprint change proposals from `_bmad-output/planning-artifacts/` (2 files)
- [ ] `git rm` `_bmad-output/bmm-workflow-status.yaml` (keep only in project-planning-artifacts)
- [ ] `git add` all new files in `docs/sprint-artifacts/change-proposals/` and `reports/`

### Phase 4: BMAD Config Updates [AGENT: config-updater / haiku]
- [ ] Create `_bmad/bmm/config.yaml` with `implementation_artifacts: "{project-root}/docs/sprint-artifacts"`
- [ ] Update `.claude/agents/orchestrator.md` - change `_bmad-output/implementation-artifacts/` → `docs/sprint-artifacts/`
- [ ] Update `docs/sprint-artifacts/sprint-status.yaml` - update `story_location` field

### Phase 5: CLAUDE.md Update [orchestrator / main session]
- [ ] Update `CLAUDE.md` story_location references
- [ ] Ensure Ralph Loop section remains intact (do NOT touch Ralph loop config)
- [ ] Update `progress.md` with session summary
- [ ] Update `task_plan.md` (this file) to reflect clean state

### Phase 6: Commit & Push [main session - confirm with user first]
- [ ] Review git diff for all changes
- [ ] Create conventional commit
- [ ] Push to remote (removes files from GitHub cloud)

---

## Remaining Stories (from sprint-status.yaml)

### P0 — Tier 1: Ready for Dev
| # | Story | Title | Size |
|---|-------|-------|------|
| 1 | E15-S1 | Extraction Log Panel in Document Library | M |
| 2 | E9-S3 | Document Actions & Bulk Operations | M |
| 3 | E16-S1 | Dashboard Home Page with ACM Stats | L |
| 4 | E16-S3 | Empty States & Onboarding Hints | S |
| 5 | E10-S1 | Simplify Navigation | S |
| 6 | E2-S8 | Column Visibility Management | M |
| 7 | E5-S3 | BAR Template Management | M |
| 8 | E1-S23 | Token Limit Quality Validation | M |
| 9 | E2-S11 | BAR Field Type Safety | S |

### P1 — Tier 2: Drafted (need promotion)
| # | Story | Title | Blocked By |
|---|-------|-------|------------|
| 10 | E12-S1 | Extraction Method Settings UI | — |
| 11 | E13-S1 | SurrealDB Graph Entity Schema | — |
| 12 | E15-S2 | Extraction Monitor Page | E15-S1 |
| 13 | E5-S4 | Export Field Mapping Config | E5-S3 |
| 14 | E12-S2..S4 | Settings UI suite | E12-S1 |
| 15 | E11-S2 | Hybrid Search Service | — |
