You are initializing a story for the ACM-AI Ralph sprint loop.

## Your Task

1. Read `CLAUDE.md` in the project root for conventions and architecture
2. Read the tech spec at: `docs/sprint-artifacts/SPEC_FILE_PLACEHOLDER`
3. Based on the tech spec, generate `.ralph/@fix_plan.md` with:
   - Every acceptance criterion as a checkable task `- [ ] ...`
   - Implementation subtasks derived from the "File Changes" table
   - Verification tasks (lint, test, build) at the end
4. Output the total task count when done

## Rules

- Tasks should be ordered logically: setup → implementation → tests → verification
- Each task should be specific and atomic (one clear action)
- Include file paths in task descriptions where applicable
- Group related tasks under markdown headers if there are many
- Do NOT start implementing — only generate the fix plan

## Output

When the fix plan is ready, output: `INIT_COMPLETE`
If the tech spec cannot be found or is unreadable, output: `INIT_FAILED: [reason]`
