# Mode 2: Slash Commands

> Interactive Claude Code commands for Ralph loop management. Run within a session.

## Command Reference

### `/ralph-bridge` — Generate prd.json
**Purpose**: Transform BMAD planning artifacts into machine-readable `prd.json`.

**Input**: BMAD epic/story definitions, architecture docs, sprint plan
**Output**: `prd.json` at project root

**Steps**:
1. Read source artifacts (epics doc, architecture doc, sprint plan, current status)
2. Build story objects (16 fields each — see `07-prd-and-gates.md` for schema)
3. Apply dependency map (story deps + gate deps)
4. Apply risk levels and complexity ratings
5. Apply story types (backend/frontend/both)
6. Build gates array (trigger stories, blocked epics)
7. Write prd.json with validation
8. Report: total stories, total SP, gates, first eligible story

**Validation checks**:
- Correct story count
- Correct gate count
- Entry point story has `dependencies: []`
- All gate IDs referenced in deps exist
- No circular dependencies
- All story IDs unique

---

### `/ralph-run [STORY_ID]` — Run One Story
**Purpose**: Process one story through the full BMAD cycle.

**Arguments**: Optional story ID. If omitted, auto-selects next eligible.

**10-Step Lifecycle**:

| Step | Phase | Agent | What Happens |
|------|-------|-------|-------------|
| 1 | Read State | — | Parse prd.json + ralph-config.json |
| 2 | Plan | ralph-architect | Architecture guidance (HIGH risk only) |
| 3 | SM | ralph-sm | Generate tech spec from story data |
| 4 | Dev | backend/frontend-specialist | Implement the story |
| 5 | QA | ralph-qa | Verify AC coverage, write missing tests |
| 6 | Review | ralph-reviewer | Code review + compliance check |
| 7 | Commit | — | Stage specific files, conventional commit |
| 8 | Update | — | Set passes=true, check gate triggers |
| 9 | Docs | docs-specialist | Update sprint status docs |
| 10 | Report | — | Progress summary, next eligible story |

**Auto-select logic**:
1. Filter: `passes === false` AND no "BLOCKED" in notes
2. Check deps: all satisfied
3. Sort: sprint order, then SP ascending
4. Select first eligible

**Retry logic**: Dev phase gets 2 retries, QA gets 1, Review gets 2. If still failing, story marked BLOCKED in prd.json.

**Config integration**: Reads `ralph-config.json` for model selection, phase skipping, retry limits, execution options.

---

### `/ralph-status` — Progress Report
**Purpose**: Read-only dashboard showing current Ralph progress.

**Output**:
```
╔══════════════════════════════════════════╗
║         Ralph Progress Report            ║
╠══════════════════════════════════════════╣
║ Stories: N/M done (P%)                   ║
║ Story Points: X/Y completed             ║
╠══════════════════════════════════════════╣
║ GATES                                    ║
║ ● GATE_1 — UNLOCKED                     ║
║ ○ GATE_2 — LOCKED (trigger: E1-S3)      ║
╠══════════════════════════════════════════╣
║ SPRINTS                                  ║
║ S1: 3/5 done (15 SP)                    ║
║ S2: 0/4 done (12 SP)                    ║
╠══════════════════════════════════════════╣
║ NEXT: E1-S4 — Story Title (3 SP)        ║
║ Blocked: N stories waiting on deps       ║
╚══════════════════════════════════════════╝
```

---

### `/ralph-config [show|set|reset]` — Configuration
**Purpose**: View or update Ralph loop configuration.

**Subcommands**:
- `show` — Display formatted current config
- `set <key> <value>` — Update a specific setting
- `reset` — Reset to defaults

**Config file**: `ralph-config.json` at project root.

**Settable keys**:

| Category | Key | Values | Default |
|----------|-----|--------|---------|
| Models | `model.sm` | haiku/sonnet/opus | sonnet |
| Models | `model.dev` | haiku/sonnet/opus | sonnet |
| Models | `model.qa` | haiku/sonnet/opus | sonnet |
| Models | `model.reviewer` | haiku/sonnet/opus | sonnet |
| Models | `model.architect` | haiku/sonnet/opus | sonnet |
| Models | `model.docs` | haiku/sonnet/opus | haiku |
| Models | `model.all` | haiku/sonnet/opus | — |
| Limits | `limit.iterations` | 1-100 | 40 |
| Limits | `limit.dev-retries` | 0-5 | 2 |
| Limits | `limit.qa-retries` | 0-3 | 1 |
| Limits | `limit.review-retries` | 0-5 | 2 |
| Phases | `phase.architect` | on/off | on |
| Phases | `phase.qa` | on/off | on |
| Phases | `phase.review` | on/off | on |
| Phases | `phase.commit` | on/off | on |
| Phases | `phase.docs` | on/off | on |
| Execution | `exec.dry-run` | on/off | off |
| Execution | `exec.auto-commit` | on/off | on |
| Execution | `exec.branch` | direct/feature | direct |
| Execution | `exec.verbose` | on/off | off |
| Execution | `exec.pause-commit` | on/off | off |
| Execution | `exec.pause-phases` | on/off | off |
| Selection | `select.sort` | sprint-then-sp/sp-asc/risk-desc | sprint-then-sp |
| Selection | `select.small-wins` | on/off | on |
| Selection | `select.max-sp` | 0-13 | 0 |

**Examples**:
```
/ralph-config set model.all opus
/ralph-config set limit.iterations 20
/ralph-config set phase.qa off
/ralph-config set exec.dry-run on
```

---

### `/ralph-gate [show|unlock|lock] [GATE_ID]` — Gate Control
**Purpose**: Manually control dependency gates.

**Gate IDs**: Defined in prd.json gates array (e.g., `SCHEMA_FREEZE`, `EXTRACTION_COMPLETE`)

**Actions**:
- `show` — Display all gates with status, triggers, blocked stories
- `unlock GATE_ID` — Manually unlock (warns about bypassing natural flow)
- `lock GATE_ID` — Re-lock (warns about downstream impact)

**Confirmation**: Both unlock and lock show impact analysis and require user confirmation.

---

### `/ralph-batch [sequential|parallel|sprint] [OPTIONS]` — Multi-Story
**Purpose**: Run multiple stories in sequence or generate parallel session commands.

**Modes**:

| Mode | Behavior |
|------|----------|
| `sequential` | Run N stories back-to-back via `/ralph-run` |
| `parallel` | Generate terminal commands for parallel sessions |
| `sprint S1` | Run all stories in a sprint in dependency order |

**Sequential options**: `--count N`, `--max-sp N`, `--sprint S1`
**Parallel output**: Terminal commands (does NOT run — user copies to parallel terminals)

---

### `/ralph-init [STORY_ID|PATH]` — Initialize Story
**Purpose**: Generate `@fix_plan.md` from a story file.

**Steps**:
1. Locate story file (by ID or path in `docs/sprint-artifacts/`)
2. Extract acceptance criteria
3. Generate `.ralph/@fix_plan.md` with checkbox tasks
4. Verify on main branch
5. Report task count and loop start command

---

### `/ralph-retry STORY_ID [--run]` — Retry Blocked Story
**Purpose**: Clear block reason and re-enable a story.

**Steps**: Read notes → show block reason → clear notes → check deps → report eligibility
**Optional**: `--run` immediately invokes `/ralph-run` after clearing

---

### `/ralph-skip STORY_ID <block|done|defer> "REASON"` — Skip Story
**Purpose**: Manually block, complete, or defer a story.

| Action | Effect | Undo |
|--------|--------|------|
| `block` | `notes = "BLOCKED: reason"` | `/ralph-retry` |
| `done` | `passes = true` + auto-unlock gates | `/ralph-reset` |
| `defer` | `notes = "DEFERRED: reason"` | `/ralph-retry` |

---

### `/ralph-reset STORY_ID [--keep-spec] [--keep-code]` — Reset Story
**Purpose**: Reset a completed story for re-run.

**Flags**:
- No flags: full reset (clear passes, date, notes, tech spec)
- `--keep-spec`: reset but preserve tech spec file path
- `--keep-code`: only reset prd.json state (code stays, re-run QA/Review)

**Warnings**: Shows downstream impact (stories depending on this one), gate trigger warnings.

## prd.json Schema Reference

See `07-prd-and-gates.md` for complete field-by-field schema documentation.

## ralph-config.json Schema Reference

See the default config structure in `/ralph-config show` output above, or `templates/ralph-config.json.template` for a copy-paste ready template.
