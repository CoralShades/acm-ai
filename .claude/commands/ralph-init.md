Initialize a Ralph autonomous coding loop for an ACM-AI story.

## Arguments
- `$ARGUMENTS` — Path to a story file in `docs/sprint-artifacts/` (e.g., `e2-s8-column-visibility-management.md`) or a story ID like `e2-s8`

## Steps

### 1. Locate and Read the Story
- If `$ARGUMENTS` is a full path, read that file directly
- If `$ARGUMENTS` is a story ID like `e2-s8`, find the matching file in `docs/sprint-artifacts/`
- If no argument provided, read `task_plan.md` and pick the top (next priority) story
- Read the full story file and extract:
  - Story title (from the `# Story` heading)
  - Story ID (from the filename, e.g., `e2-s8`)
  - All acceptance criteria (lines matching `**AC\d+:` or numbered criteria)
  - Status (from `Status:` line — abort if already `done`)

### 2. Generate .ralph/@fix_plan.md
Write the fix plan file at `.ralph/@fix_plan.md`:

```markdown
# Fix Plan: [Story Title]

## Source
- **Story file**: [full path to story file]
- **Story ID**: [e.g., E2-S8]
- **Generated**: [ISO timestamp]

## Tasks
- [ ] AC1: [acceptance criterion description]
- [ ] AC2: [acceptance criterion description]
- [ ] ...
- [ ] ACN: [acceptance criterion description]

## Completion Criteria
- All tasks above are checked off
- All tests passing: `pytest tests/ -x`
- No lint errors: `ruff check .`
- Frontend builds: `cd frontend && npm run lint && npm run build`
- Changes committed with conventional commit message
```

### 3. Verify on Main Branch
Ensure we are on the `main` branch. This loop commits directly to main — no feature branches.
```bash
git checkout main  # if not already on main
```

### 4. Report
Output a summary:
```
Ralph initialized for: [Story Title]
Branch: main (direct commits)
Tasks: [N] acceptance criteria
Fix plan: .ralph/@fix_plan.md

To start the loop:
  .ralph/ralph_loop.sh

To run the full sprint:
  .ralph/ralph_sprint.sh
```

### 5. Superpowers Integration
The generated fix plan and Ralph PROMPT.md include mandatory superpowers skill invocations:
- `superpowers:test-driven-development` — invoked before each implementation task
- `superpowers:systematic-debugging` — invoked when debugging failures
- `superpowers:requesting-code-review` — invoked after all tasks complete

These are enforced by the PROMPT.md template's "MANDATORY SKILL INVOCATIONS" section.
