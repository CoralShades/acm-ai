# Concurrent Development Workflow Protocol

> **Created:** 2026-02-08
> **Purpose:** Enable parallel development across two Claude Code sessions

---

## Architecture: Two Swim Lanes

### Lane A: Backend/Extraction
- **Worktree:** `/mnt/d/ailocal/acm-ai/` (main)
- **Branch:** `main` → creates `feature/e1-sXX` branches per story
- **Directories:** `open_notebook/`, `api/`, `commands/`, `prompts/`, `migrations/`, `tests/`
- **Owns:** migrations, sprint-status.yaml updates, backend tests

### Lane B: Frontend/UI
- **Worktree:** `/mnt/d/ailocal/acm-ai-frontend/`
- **Branch:** `lane-b` → creates `feature/eX-sXX` branches per story
- **Directories:** `frontend/src/`, `frontend/public/`
- **Owns:** frontend components, UI tests, frontend build

---

## Story Queues

### Lane A Priority Order (14 backend stories):
1. **E1-S11** → code-review + merge (unblocks E1-S12, E12-S4)
2. **E1-S12** (Wording Normalization)
3. **E1-S13** (Fix Page Reference Tracking)
4. **E1-S20** (Agentic Orchestrator) → then E1-S15
5. **E1-S14** (Contextual Enrichment)
6. **E1-S16** → **E1-S17** → **E1-S18** → **E1-S19** (Document Intelligence chain)
7. **E11-S1** (Parent Doc Retrieval) → **E11-S2** (Hybrid Search, after E1-S14 done)
8. **E13-S1** (Graph Schema)

### Lane B Priority Order (10 frontend stories):
1. **E2-S8** (Column Visibility)
2. **E9-S3** (Document Actions & Bulk Ops)
3. **E10-S1** (Navigation Simplification)
4. **E5-S3** (BAR Template Management)
5. **E5-S4** (Field Mapping Config)
6. **E12-S4** (Parser Config UI) — *after Lane A merges E1-S11*
7. **E12-S1** (Extraction Settings UI) — *after Lane A finishes E1-S16..S19*
8. **E12-S2**, **E12-S3** (Model + Processing Config)
9. **E13-S2** → **E13-S3** (Knowledge Graph UI) — *after Lane A finishes E13-S1*

---

## Cross-Lane Handoff Points

| When Lane A Completes | Lane B Can Start |
|-----------------------|------------------|
| E1-S11 merged to main | E12-S4 (Parser Config UI) |
| E1-S16/17/18/19 done | E12-S1 → E12-S2/S3 (Settings UI) |
| E13-S1 done | E13-S2 → E13-S3 (Knowledge Graph) |
| E5-S3 backend API | E5-S3 frontend (or Lane B does full-stack) |

---

## Git Workflow

### Branch Strategy
```bash
# Lane A (from /mnt/d/ailocal/acm-ai/)
git checkout -b feature/e1-s12
# ... implement story ...
git push -u origin feature/e1-s12
# Create PR → merge to main

# Lane B (from /mnt/d/ailocal/acm-ai-frontend/)
git checkout -b feature/e2-s8
# ... implement story ...
git push -u origin feature/e2-s8
# Create PR → merge to main
```

### Sync Protocol
- Before starting a cross-lane dependent story, pull latest `main`:
  ```bash
  git fetch origin
  git rebase origin/main
  ```
- Lane A owns `migrations/` exclusively — Lane B never creates migration files
- Lane A owns `sprint-status.yaml` — Lane B reports completion via PR description

### Conflict Prevention Rules
1. **Never edit the same file in both lanes simultaneously**
2. Lane A: backend Python files, migrations, API routes, tests, prompts
3. Lane B: frontend TypeScript/TSX files, CSS, frontend config
4. Shared files (`CLAUDE.md`, `docs/`) — coordinate before editing

---

## File Collision Risk Matrix

| File/Directory | Lane A | Lane B | Risk |
|---------------|--------|--------|------|
| `open_notebook/` | All E1 stories | None | SAFE |
| `api/` | E5-S3, E11-S1 | None | SAFE |
| `frontend/src/` | None | All Lane B stories | SAFE |
| `migrations/` | E1-S14, E11-S1, E13-S1 | None | SAFE |
| `docs/sprint-artifacts/` | Status updates | Status updates | MEDIUM |
| `CLAUDE.md` | Possible | Possible | MEDIUM |

---

## Immediate Start Stories (zero unfinished deps)

| Story | Lane | Domain |
|-------|------|--------|
| E1-S11 | A | Review → merge |
| E1-S13 | A | Fix page reference tracking |
| E1-S14 | A | Contextual embedding enrichment |
| E1-S16 | A | Document structure & TOC |
| E1-S20 | A | Agentic extraction orchestrator |
| E11-S1 | A | Parent document retrieval |
| E13-S1 | A | SurrealDB graph entity schema |
| E2-S8 | B | Column visibility management |
| E5-S3 | B | BAR template management |
| E9-S3 | B | Document actions & bulk ops |
| E10-S1 | B | Navigation simplification |

---

## Sequential Dependency Chains

```
E1-S11 (review) → E1-S12 → E12-S4
E1-S20 → E1-S15
E1-S16 → E1-S17 → E1-S18
E1-S16 → E1-S19
E1-S16+17+18+19 → E12-S1 → E12-S2, E12-S3
E1-S14 + E11-S1 → E11-S2
E5-S3 → E5-S4
E13-S1 → E13-S2 → E13-S3
```
