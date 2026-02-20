Initialize a Ralph autonomous coding loop for an ACM-AI story.

## Arguments
- `$ARGUMENTS` — Path to a story file in `_bmad-output/implementation-artifacts/` (e.g., `e1-s13-fix-page-reference-tracking.md`)

## Steps

### 1. Locate and Read the Story
- If `$ARGUMENTS` is a full path, read that file directly
- If `$ARGUMENTS` is a story ID like `e1-s13`, find the matching file in `_bmad-output/implementation-artifacts/`
- If no argument provided, read `task_plan.md` and pick the top (next priority) story
- Read the full story file and extract:
  - Story title (from the `# Story` heading)
  - Story ID (from the filename, e.g., `e1-s13`)
  - All acceptance criteria (lines matching `**AC\d+:` or numbered criteria)
  - Status (from `Status:` line — abort if already `done`)

### 2. Generate .ralph/@fix_plan.md
Write the fix plan file at `.ralph/@fix_plan.md`:

```markdown
# Fix Plan: [Story Title]

## Source
- **Story file**: [full path to story file]
- **Story ID**: [e.g., E1-S13]
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

### 3. Create Feature Branch
```bash
git checkout -b feature/story-[id]-[slug]
```
Where `[slug]` is derived from the story title (lowercase, hyphens, max 40 chars).

### 4. Report
Output a summary:
```
Ralph initialized for: [Story Title]
Branch: feature/story-[id]-[slug]
Tasks: [N] acceptance criteria
Fix plan: .ralph/@fix_plan.md

To start the loop:
  .ralph/ralph_loop.sh

To run manually:
  claude --prompt-file .ralph/PROMPT.md
```
