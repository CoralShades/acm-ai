You are fixing issues found during code review and testing for ACM-AI.

## Your Task

1. Read `CLAUDE.md` in the project root for conventions and architecture
2. Read `.ralph/@review_issues.md` for code review issues (if it exists)
3. Read `.ralph/@test_failures.md` for test/lint/build failures (if it exists)
4. Fix each issue one at a time:
   - Read the relevant source files BEFORE making changes
   - Apply the fix following project conventions
   - Run verification after each fix:
     - Python: `uv run ruff check .`
     - Backend tests: `uv run pytest tests/ --ignore=tests/test_broadmeadows_e2e.py -x`
     - Frontend lint: `cd frontend && npm run lint`
     - Frontend build: `cd frontend && npm run build`
5. After fixing each issue, mark it resolved (strikethrough or remove from the issues file)
6. Commit after each successful fix with a conventional commit message

## Rules

- NEVER skip tests or linting after a fix
- NEVER introduce new issues while fixing existing ones
- If a fix requires changes beyond the current branch scope, note it and move on
- Max 3 attempts per individual issue before marking it as unresolvable

## Output

When all issues are resolved and all tests pass:
- Output: `<promise>COMPLETE</promise>`

If any issue cannot be resolved after 3 attempts:
- Output: `<promise>BLOCKED</promise>: [specific issue and what was tried]`
