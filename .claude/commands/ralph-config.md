View or update Ralph loop configuration.

## Arguments
- `$ARGUMENTS` — One of: `show`, `set <key> <value>`, `reset`

If no arguments, defaults to `show`.

---

## Configuration File

Ralph config lives at `ralph-config.json` in the project root. If it doesn't exist, create it with defaults.

### Default Configuration

```json
{
  "version": "1.0",
  "models": {
    "sm": "sonnet",
    "dev": "sonnet",
    "qa": "sonnet",
    "reviewer": "sonnet",
    "architect": "sonnet",
    "docs": "haiku"
  },
  "limits": {
    "maxIterations": 40,
    "devRetries": 2,
    "qaRetries": 1,
    "reviewRetries": 2,
    "agentMaxTurns": {
      "sm": 20,
      "dev": 50,
      "qa": 30,
      "reviewer": 15,
      "architect": 12,
      "docs": 10
    }
  },
  "phases": {
    "architect": true,
    "sm": true,
    "dev": true,
    "qa": true,
    "review": true,
    "commit": true,
    "docUpdate": true
  },
  "execution": {
    "dryRun": false,
    "autoCommit": true,
    "branchStrategy": "direct",
    "verbose": false,
    "pauseBeforeCommit": false,
    "pauseBetweenPhases": false
  },
  "selection": {
    "sortBy": "sprint-then-sp",
    "preferSmallWins": true,
    "maxStoryPoints": 0
  }
}
```

---

## `show` — Display Current Config

Read `ralph-config.json` and display it in a formatted table:

```
Ralph Configuration
═══════════════════

Models:
  SM Agent:        sonnet
  Dev Agent:       sonnet
  QA Agent:        sonnet
  Reviewer Agent:  sonnet
  Architect Agent: sonnet
  Docs Agent:      haiku

Limits:
  Max Iterations:  40
  Dev Retries:     2
  QA Retries:      1
  Review Retries:  2

Phases (enabled):
  ✓ Architect  ✓ SM  ✓ Dev  ✓ QA  ✓ Review  ✓ Commit  ✓ Doc Update

Execution:
  Dry Run:              false
  Auto Commit:          true
  Branch Strategy:      direct (commits to current branch)
  Verbose:              false
  Pause Before Commit:  false
  Pause Between Phases: false

Selection:
  Sort By:            sprint-then-sp
  Prefer Small Wins:  true
  Max Story Points:   0 (no limit)
```

---

## `set` — Update a Config Value

Supported keys and their valid values:

### Model Keys
- `model.sm <model>` — SM agent model (`sonnet`, `haiku`, `opus`)
- `model.dev <model>` — Dev agent model
- `model.qa <model>` — QA agent model
- `model.reviewer <model>` — Reviewer agent model
- `model.architect <model>` — Architect agent model
- `model.docs <model>` — Docs agent model
- `model.all <model>` — Set ALL agent models at once

### Limit Keys
- `limit.iterations <N>` — Max Ralph loop iterations (1-100)
- `limit.dev-retries <N>` — Dev phase retry limit (0-5)
- `limit.qa-retries <N>` — QA phase retry limit (0-3)
- `limit.review-retries <N>` — Review phase retry limit (0-5)
- `limit.turns.sm <N>` — SM agent max turns
- `limit.turns.dev <N>` — Dev agent max turns
- `limit.turns.qa <N>` — QA agent max turns
- `limit.turns.reviewer <N>` — Reviewer agent max turns

### Phase Keys (toggle on/off)
- `phase.architect <on|off>` — Skip architect phase (useful for MEDIUM/LOW risk)
- `phase.qa <on|off>` — Skip QA phase (dangerous, use for spike/prototype stories)
- `phase.review <on|off>` — Skip review phase
- `phase.commit <on|off>` — Skip auto-commit (leaves changes staged)
- `phase.docs <on|off>` — Skip doc update

### Execution Keys
- `exec.dry-run <on|off>` — Walk through phases without writing code or committing
- `exec.auto-commit <on|off>` — Auto-commit after review passes
- `exec.branch <direct|feature>` — `direct` = commit to current branch, `feature` = create `ralph/{story-id}` branch
- `exec.verbose <on|off>` — Extra logging between phases
- `exec.pause-commit <on|off>` — Pause and ask user before committing
- `exec.pause-phases <on|off>` — Pause between each phase for user review

### Selection Keys
- `select.sort <sprint-then-sp|sp-asc|sprint-only|risk-desc>` — Story selection priority
- `select.small-wins <on|off>` — Prefer lower SP stories within a sprint
- `select.max-sp <N>` — Only auto-select stories with SP <= N (0 = no limit)

### Examples
```
/ralph-config set model.all opus
/ralph-config set model.dev sonnet
/ralph-config set limit.iterations 20
/ralph-config set phase.qa off
/ralph-config set exec.dry-run on
/ralph-config set exec.branch feature
/ralph-config set select.max-sp 3
```

After setting, confirm the change and show the updated value.

---

## `reset` — Reset to Defaults

Reset `ralph-config.json` to all default values. Confirm before overwriting.

---

## How ralph-run Uses Config

The `/ralph-run` command reads `ralph-config.json` at startup (Step 1) and uses it throughout:

1. **Model selection**: Each agent spawn uses `models.<phase>` to set the model
2. **Retry limits**: Dev/QA/Review phases respect `limits.*Retries`
3. **Phase skipping**: If `phases.<phase>` is false, that phase is skipped entirely
4. **Dry run**: If `execution.dryRun` is true, agents describe what they would do but don't write files
5. **Branch strategy**: If `execution.branchStrategy` is "feature", creates `ralph/{story-id}` branch before dev phase
6. **Pause points**: If `execution.pauseBeforeCommit` is true, uses AskUserQuestion before committing
7. **Story selection**: If `selection.maxStoryPoints > 0`, filters out stories above that SP threshold
