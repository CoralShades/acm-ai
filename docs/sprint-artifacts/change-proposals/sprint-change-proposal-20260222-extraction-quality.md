# Sprint Change Proposal — Extraction Quality & Demo Validation

**Date:** 2026-02-22
**Status:** PROPOSED
**Priority:** P1 (E18-S5, E18-S6)
**Scope:** Moderate
**Risk:** Low
**Path:** Story Additions (2 new stories in existing E18)

---

## 1. Motivation

The 8-phase extraction pipeline bugfix plan has been fully implemented and committed to main.
A follow-up session fixed OpenRouter compatibility (migration 31, E2E test). E2E testing now shows
**26/31 records (84%)** extracted from the Broadmeadows Police Station SAMP — up from 8/31 (26%)
at the Feb 10 baseline.

Two capability gaps remain:

### Gap 1: 5 records not matched in E2E test

Of 31 expected records in the Broadmeadows ground truth CSV:
- **3 "fuse cartridge" items**: LLM uses equipment name (Switchboard, Auto Battery Charger) as the ACM product instead of the specific ACM component (Fuse cartridge) within that equipment. Records ARE extracted but with wrong product name, causing composite-key match to fail.
- **2 "No access" items**: LLM skips register entries marked as inaccessible ("No access"), treating them as non-inspectable rather than valid register rows.

The project already has comprehensive ACM taxonomy and enumeration files at `docs/samplePDF/instructions-sample/` that should be used to guide the extraction prompt:
- `register_enums.json` — Contains "Fuse cartridge" in the `SpecificUses` list
- `register_taxonomy.friable.json` / `register_taxonomy.nonfriable.json` — Full ACM product classification hierarchy
- `register_row.schema.json` — BAR field schema with column definitions
- `consultant_wording_rules.json` — Recommendation normalization rules (includes `height_or_access_restriction` action for "No access" items)

### Gap 2: Browser-based feature validation not completed

Upload wizard, AG Grid, export, chat, and knowledge graph features have not been validated via browser after the Phase A code fixes. A previous session found 4 failures (FAIL-001 through FAIL-004) but most validation phases were not completed.

---

## 2. Context

### Extraction Pipeline State
- **Model**: `anthropic/claude-sonnet-4.6` via OpenRouter
- **Pipeline**: STRUCTURE → PREFLIGHT → ORCHESTRATOR → EXTRACT → VALIDATE → CORRECT → STORE
- **max_tokens**: 32768 (orchestrator), 16384 (document structure)
- **Runtime**: ~144s for 20-page Broadmeadows PDF
- **Dedup**: 30 raw → 25 unique records (5 duplicates merged)

### E18 Current State
- E18-S1 (extraction provider compatibility): done
- E18-S2 (upload wizard UX): done
- E18-S3 (extraction monitor defaults): done
- E18-S4 (demo validation): in-progress (code fixes complete, validation remaining)

---

## 3. Change Proposals

### CP-1: E18-S5 — Extraction Quality: Fuse Cartridge & No-Access Records

**As a:** compliance officer extracting ACM registers from SAMP documents
**I want to:** have all register entries correctly identified including equipment-specific ACM items and inaccessible areas
**So that:** the extracted data matches the original register with 100% completeness

**Problem Analysis:**

| # | Room | Location | Expected Item | Extracted As | Root Cause |
|---|------|----------|--------------|-------------|------------|
| 1 | Switch Room (L1) | Switchboard | Fuse cartridge | Switchboard | LLM conflated equipment with ACM product |
| 2 | Switch Room (L1) | Auto Battery Charger | Fuse cartridge | Auto battery charger | Same pattern |
| 3 | Boiler Room (G) | Switchboard | Fuse cartridge | Switchboard | Same pattern |
| 4 | Lift Foyer (G) | Lift | Internal lining | *NOT EXTRACTED* | "No access" — LLM skipped entry |
| 5 | Main Foyer (G) | Room Adjacent Disabled Toilet | Unknown | *NOT EXTRACTED* | "No access" — LLM skipped entry |

**Work Items:**
1. **Extraction prompt refinement** (`open_notebook/extractors/orchestrator.py` or `prompts/`):
   - Add guidance to distinguish equipment/location (Switchboard) from specific ACM item within it (Fuse cartridge)
   - Reference the `register_enums.json` SpecificUses list as canonical ACM item vocabulary
   - Add explicit instruction to include ALL register entries including those marked "No access", "Height restriction", or "Restricted Access"
   - Reference `consultant_wording_rules.json` `height_or_access_restriction` action
2. **Taxonomy integration**: Copy taxonomy files from `docs/samplePDF/instructions-sample/` to a location accessible by the extraction pipeline, or load them as prompt context
3. **E2E test matching improvements**: Add fuzzy room+location match for "Not Sampled" records where item name may differ
4. **E2E test assertion**: Update to pass with 31/31 records

**Acceptance Criteria:**
- [ ] E2E test extracts and matches all 31 Broadmeadows records
- [ ] Fuse cartridge items correctly identified as "Fuse cartridge" not equipment name
- [ ] "No access" items included in extraction output
- [ ] Taxonomy files referenced in extraction prompt or loaded as context

**Files:**
| File | Change |
|------|--------|
| `open_notebook/extractors/orchestrator.py` | Extraction prompt refinement |
| `prompts/` | Extraction prompt templates (if separate) |
| `tests/test_broadmeadows_e2e.py` | Matching improvements + 31/31 assertion |
| `docs/samplePDF/instructions-sample/*.json` | Source taxonomy (copied if needed) |

---

### CP-2: E18-S6 — Browser Demo Validation

**As a:** product owner reviewing ACM-AI for demo readiness
**I want to:** verify all user-facing features work correctly via browser
**So that:** I can confidently demonstrate the system to stakeholders

**Work Items:**
1. Run through all 10 demo validation phases via Playwright/browser automation
2. Verify: upload wizard (title editing, ACM focus, auto-redirect)
3. Verify: extraction pipeline via UI (7 stage pills, progress tracking)
4. Verify: AG Grid (records, building tabs, column headers, stats cards)
5. Verify: Export CSV/Excel
6. Verify: Cell click → PDF viewer
7. Verify: Chat with ACM context
8. Compile pass/fail report with screenshots

**Acceptance Criteria:**
- [ ] All P0 phases pass (upload, extraction, grid, export)
- [ ] Failure report with severity classifications
- [ ] Screenshots as evidence in `_bmad-output/demo-validation-2026-02-22/evidence/`

**Files:**
| File | Change |
|------|--------|
| `_bmad-output/demo-validation-2026-02-22/` | Evidence directory |
| `.claude/skills/planning-with-files/` | Planning files updated |

---

### CP-3: Update E18 Sprint Status

Update `docs/sprint-artifacts/sprint-status.yaml`:
- Mark E18-S4 scope as narrowed (code fixes done, browser validation split to E18-S6)
- Add E18-S5 (extraction quality) as `drafted`
- Add E18-S6 (browser validation) as `drafted`
- Update sprint summary counts

---

## 4. Impact Analysis

### Dependencies

| Story | Depends On | Blocks |
|-------|-----------|--------|
| E18-S5 | E18-S1 (done — OpenRouter compat) | — |
| E18-S6 | E18-S1..S3 (done — code fixes) | — |

### No Breaking Changes

All changes are additive — prompt refinements improve extraction quality without affecting existing API contracts or database schema.

### Database Changes

None required.

---

## 5. Updated Story Counts

| Category | Before | After |
|----------|--------|-------|
| Total stories | 126 | 128 |
| Done | 115 | 115 |
| In-Progress | 1 | 1 (E18-S4) |
| Drafted | 0 | 2 (E18-S5, E18-S6) |
| Archived | 10 | 10 |

---

## 6. Implementation Order (Recommended)

```
Sprint A — Extraction quality (high value, unblocks demo confidence):
  E18-S5  (Extraction Quality — prompt refinement + taxonomy integration)

Sprint B — Browser validation (depends on S5 for extraction completeness):
  E18-S6  (Browser Demo Validation)

E18-S4 remains in-progress (code fixes done, scoped to pipeline validation)
```

---

## 7. Files Changed by This Proposal

| File | Change |
|------|--------|
| `docs/sprint-artifacts/sprint-status.yaml` | Add E18-S5, E18-S6; update summary |
| `docs/sprint-artifacts/change-proposals/sprint-change-proposal-20260222-extraction-quality.md` | This file |
