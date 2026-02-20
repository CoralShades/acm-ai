You are implementing a feature for ACM-AI, an intelligent Asbestos Containing Material compliance management system.

Read `.ralph/@fix_plan.md` for your current tasks.
Read `CLAUDE.md` in the project root for conventions and architecture.

## Rules

1. Pick the next unchecked task from `@fix_plan.md`
2. Read the relevant source files BEFORE making any changes
3. Implement the task following the patterns described in `CLAUDE.md`
4. Route work to specialist agents via the Task tool based on file paths:
   - `/api/**`, `/open_notebook/**`, `/migrations/**`, `/commands/**` → `backend-specialist`
   - `/frontend/**` → `frontend-specialist`
   - `/tests/**` → `qa-specialist`
5. Run verification after each change:
   - Python: `ruff check .`
   - Backend tests: `pytest tests/ -x`
   - Frontend lint: `cd frontend && npm run lint`
   - Frontend build: `cd frontend && npm run build`
6. If all verification passes, check off the task in `@fix_plan.md` and commit with a conventional commit message
7. If verification fails, fix the issue and retry (max 3 retries per task)
8. After 3 failed retries on the same task, output `<promise>BLOCKED</promise>: [specific reason and error details]`
9. Output `<promise>COMPLETE</promise>` when ALL tasks in `@fix_plan.md` are checked off AND all tests pass

## Important

- NEVER skip tests or linting
- NEVER mark a task complete without verification passing
- NEVER modify files outside the scope of the current task
- NEVER change database migrations without explicit approval in the story
- Always write tests alongside implementation
- Commit after each successfully completed task
