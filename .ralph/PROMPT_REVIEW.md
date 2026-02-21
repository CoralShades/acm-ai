You are performing an adversarial code review for ACM-AI.

## Your Task

1. Read `CLAUDE.md` in the project root for project conventions
2. Read `.ralph/@fix_plan.md` to understand what was implemented
3. For each task that was checked off, review the modified files for:
   - **Security issues**: injection, XSS, exposed secrets, unsafe operations
   - **Correctness**: logic errors, off-by-one, null/undefined handling, race conditions
   - **Pattern violations**: deviations from project conventions documented in CLAUDE.md
   - **Missing tests**: new functionality without corresponding test coverage
   - **Broken imports**: references to files/modules that don't exist
   - **Style violations**: naming, formatting, file organization
   - **Performance**: unnecessary re-renders, N+1 queries, unbounded loops
4. Be thorough but fair — only flag real issues, not style preferences

## Output

If issues found:
- Write each issue to `.ralph/@review_issues.md` in this format:
  ```
  ## Issue N: [Title]
  - **File**: path/to/file.ext:line
  - **Severity**: critical | major | minor
  - **Description**: What's wrong and why
  - **Suggested fix**: How to fix it
  ```
- Output: `REVIEW_ISSUES`

If no issues found:
- Output: `REVIEW_PASS`
