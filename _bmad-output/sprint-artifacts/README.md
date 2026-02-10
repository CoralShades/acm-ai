# Sprint Artifacts Directory

**Updated:** 2026-02-10
**Location:** `_bmad-output/sprint-artifacts/`

This directory contains **current** sprint artifacts for the ACM-AI project. All sprint-related specifications and documentation are centralized here under `_bmad-output/`.

---

## Current Contents

### Tech Specs (Epic 14 - Current)

Epic 14 tech specs (created 2026-02-08) reflecting the latest UX & Enterprise Readiness requirements:
- `tech-spec-e14-s1-vaea-branding-design-tokens.md` through `tech-spec-e14-s11-pydantic-typescript-types.md` (11 files)

### Documentation

- `change-proposal-epic-14.md` - Epic 14 change proposal
- `concurrent-workflow-protocol.md` - Lane A/B workflow documentation
- `implementation-report-acm-frontend-2025-12-15.md` - Implementation report
- `api-docs-verified.png` - API documentation screenshot

---

## Archive & Migration (2026-02-10)

### What Was Archived

**47 outdated tech specs** (created before 2026-02-08) were archived to:
```
_bmad-output/archived-specs/pre-2026-02-08/
```

These specs reflected pre-course-correction requirements and were superseded by updated PRD, Architecture, and Epics & Stories documents on 2026-02-08.

See the archive index for details:
```
_bmad-output/archived-specs/pre-2026-02-08/ARCHIVE_INDEX.md
```

### What Was Migrated

**Story artifacts and implementation specs** were moved to:
```
_bmad-output/implementation-artifacts/
```

This includes:
- Epic 1 stories: e1-s7 through e1-s20 (14 files)
- Epic 2 stories: e2-s8
- Epic 5 stories: e5-s3, e5-s4
- Epic 7 stories: e7-s7
- Epic 11 stories: e11-s1
- Sprint status: `sprint-status.yaml`

---

## Canonical Locations

For **current** sprint artifacts, use these locations:

| Artifact Type | Location |
|--------------|----------|
| **Current Tech Specs (E14)** | `_bmad-output/sprint-artifacts/tech-spec-e14-*.md` |
| **Implementation Stories** | `_bmad-output/implementation-artifacts/e*-s*.md` |
| **Sprint Status** | `_bmad-output/implementation-artifacts/sprint-status.yaml` |
| **BMM Workflow Status** | `_bmad-output/bmm-workflow-status.yaml` |
| **BMM Index** | `_bmad-output/bmm-index.md` |
| **Archived Specs** | `_bmad-output/archived-specs/pre-2026-02-08/` |

---

## BMAD Workflow Configuration

BMAD workflows now reference:
```yaml
output_folder: "{project-root}/_bmad-output"
```

All BMAD-generated artifacts (stories, specs, status tracking) are written to `_bmad-output/` subdirectories.

---

## Future Tech Specs

New tech specs created after 2026-02-08 should be placed in:
- `_bmad-output/sprint-artifacts/` for specifications
- `_bmad-output/implementation-artifacts/` for implementation stories

Follow the existing naming conventions:
- Tech specs: `tech-spec-e{epic}-s{story}-{description}.md`
- Stories: `e{epic}-s{story}-{description}.md`

---

## References

- **PRD:** `_bmad-output/project-planning-artifacts/acm-ai/03-prd.md`
- **Epics & Stories:** `_bmad-output/project-planning-artifacts/acm-ai/05-epics-and-stories.md`
- **Architecture:** `_bmad-output/project-planning-artifacts/acm-ai/04-architecture.md`
- **Sprint Change Proposal (2026-02-08):** `_bmad-output/planning-artifacts/sprint-change-proposal-2026-02-08.md`
- **Archive Index:** `_bmad-output/archived-specs/pre-2026-02-08/ARCHIVE_INDEX.md`
