Run ONE V3 story through the full BMAD cycle (SM -> Dev -> QA -> Review -> Commit -> Doc).

## Arguments
- `$ARGUMENTS` — Optional story ID (e.g., `E30-S1`). If omitted, auto-selects next eligible story.

---

## Step 1: Read State

Read `prd.json` from the project root. If missing, abort: "Run `/ralph-bridge` first."
Read `ralph-config.json` from the project root. If missing, use defaults (see `/ralph-config`).

Parse the stories and gates arrays. Apply config overrides:
- **Models**: Use `config.models.<phase>` for each agent spawn (default: sonnet)
- **Phase skipping**: If `config.phases.<phase>` is false, skip that phase entirely
- **Retry limits**: Use `config.limits.devRetries`, `qaRetries`, `reviewRetries`
- **Max turns**: Use `config.limits.agentMaxTurns.<phase>` for each agent
- **Dry run**: If `config.execution.dryRun` is true, describe actions without executing
- **Branch**: If `config.execution.branchStrategy` is "feature", create `ralph/{story-id}` branch
- **Pause points**: If `config.execution.pauseBeforeCommit`, use AskUserQuestion before Step 7
- **Pause between**: If `config.execution.pauseBetweenPhases`, use AskUserQuestion after each phase
- **Selection**: If `config.selection.maxStoryPoints > 0`, filter auto-select candidates by SP

**Auto-select logic** (if no story ID provided):
1. Filter stories where `passes === false` AND `notes` does not contain "BLOCKED"
2. Check dependency satisfaction for each candidate:
   - All story deps must have `passes === true`
   - All gate deps must have `unlocked === true`
3. Sort eligible stories by: sprint order first (V3-1, V3-2, ...), then story points ascending (small wins first)
4. Select the first eligible story

If `$ARGUMENTS` is provided, find that story ID in prd.json. Verify its deps are satisfied. If not, warn but allow override.

Report: `Starting: {STORY_ID} — {TITLE} ({SP} SP, {RISK} risk, {TYPE} type)`

---

## Step 2: Plan (HIGH risk only)

If the story's `riskLevel` is `HIGH`:

Spawn the `ralph-architect` agent with:
- Story ID
- Story data (title, ACs, dependencies, keyFiles)
- The full story definition from the epics doc

Read the architect's output and carry it forward as context for SM and Dev phases.

If risk is not HIGH, skip this step.

---

## Step 3: SM Phase (Tech Spec Creation)

If the story's `techSpecFile` is null (no tech spec yet):

Determine the output path: `docs/sprint-artifacts/e{epic_num}-s{story_num}-{slug}.md`
- `slug` = lowercase, hyphenated title (e.g., "sf-schema-config-loader")

Spawn the `ralph-sm` agent with:
- Story ID
- Story data from prd.json
- Output path for tech spec
- Architect guidance (if Step 2 ran)

After SM completes:
- Verify the tech spec file exists using Glob
- Update prd.json: set `techSpecFile` to the file path
- Read the tech spec to carry forward as context

If `techSpecFile` already exists, read it and proceed.

---

## Step 4: Dev Phase (Implementation)

Read the tech spec fully. Determine the specialist based on `storyType`:

- `backend` → Spawn `backend-specialist` agent
- `frontend` → Spawn `frontend-specialist` agent
- `both` → Spawn `backend-specialist` first, wait for completion, then spawn `frontend-specialist`

Provide to each specialist:
- The full tech spec content
- Architect guidance (if available)
- Key instruction: "Implement the story per the tech spec. Follow all V3 rules (SF field names, provider pattern, provenance, additive migrations). Write tests alongside implementation. Run build verification before reporting done."

**Retry logic**: If the specialist reports failure (build errors, missing files):
- Read the error output
- Spawn the same specialist again with the error context
- Max 2 retry cycles. If still failing after 2 retries, set `notes: "BLOCKED: Dev failed after 2 retries — {error summary}"` in prd.json and abort.

---

## Step 5: QA Phase

Spawn the `ralph-qa` agent with:
- Story ID
- Tech spec path

Read the QA verdict:

- **PASS** → Proceed to Step 6
- **FAIL** → Read the failure details. Spawn the appropriate specialist to fix the issues. Re-run QA once. If still FAIL, set `notes: "BLOCKED: QA failed — {failure summary}"` and abort.

Max 1 fix+re-QA cycle.

---

## Step 6: Review Phase

Spawn the `ralph-reviewer` agent with:
- Story ID
- Tech spec path

Read the review verdict:

- **APPROVED** → Proceed to Step 7
- **CHANGES_REQUESTED** → Read the issues. Spawn the appropriate specialist to fix. Re-run review. Max 2 fix+re-review cycles. If still not approved, set `notes: "BLOCKED: Review failed — {issues}"` and abort.

---

## Step 7: Commit

Stage only the specific files changed by this story. NEVER use `git add .` or `git add -A`.

Identify files to stage:
1. New/modified source files (from tech spec File Changes table)
2. New test files
3. The tech spec file itself
4. prd.json (will be updated in Step 8)

Create a conventional commit:
```bash
git add [specific files]
git commit -m "feat({story_id_lower}): {title} — {STORY_ID}

Implements {STORY_ID} ({SP} SP):
- [brief summary of what was implemented]

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

Use `feat:` for new features, `fix:` for bug fixes, `refactor:` for refactoring, `test:` for test-only changes, `docs:` for doc-only changes.

---

## Step 8: Update prd.json

Update the story in prd.json:
- Set `passes: true`
- Set `implementedDate` to today's ISO date
- Set `notes: "Completed"`

**Gate check**: If this story is a gate trigger (check `gates[].triggerStory`):
- Set the gate's `unlocked: true`
- Report: `GATE UNLOCKED: {gate_name}`

Write the updated prd.json.

---

## Step 9: Doc Update

Spawn the `docs-specialist` agent with:
- Story ID and title
- Instruction to update:
  1. `docs/sprint-artifacts/sprint-status.yaml` — set story status to `done`
  2. `docs/sprint-artifacts/v3-progress.md` — add row to Completed Stories table, update sprint summary counts

---

## Step 10: Completion Check

Read updated prd.json. Count stories:
- Done (`passes === true`)
- Remaining (`passes === false`)
- Blocked (deps not satisfied)
- Eligible (deps satisfied, not blocked)

Report:
```
╔══════════════════════════════════════════╗
║ Story Complete: {STORY_ID} — {TITLE}     ║
║ Progress: {done}/33 ({pct}%)             ║
║ Next eligible: {next_id} — {next_title}  ║
║ Blocked: {N} stories                     ║
╚══════════════════════════════════════════╝
```

If all 33 stories done:
```
<promise>COMPLETE</promise>
All 33 V3 stories implemented. 97 SP delivered across 7 sprints.
```

If all remaining stories are blocked and none are eligible:
```
<promise>BLOCKED</promise>
No eligible stories. {N} stories blocked. Check gate status with /ralph-status.
```

---

## Error Handling

- If any phase aborts, the story's `notes` field in prd.json is updated with the reason
- The session can be re-run with the same story ID to retry
- To manually unblock, edit prd.json to clear the `notes` field
- WIP commits are allowed at any point using `wip:` prefix (bypasses gate guard)

## Ralph Loop Config
- **Max iterations**: 40 (per CLAUDE.md)
- **Completion signal**: `<promise>COMPLETE</promise>`
- **Blocked signal**: `<promise>BLOCKED</promise>`
