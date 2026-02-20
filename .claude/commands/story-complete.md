Verify and finalize a completed story in the Ralph loop.

## Steps

### 1. Verify Fix Plan
- Read `.ralph/@fix_plan.md`
- Parse all task checkboxes (`- [ ]` and `- [x]`)
- Count total tasks and checked tasks
- If ANY task is unchecked, report which ACs are incomplete and STOP — do NOT commit

### 2. Run Full Test Suite
Execute all verification commands:

```bash
# Python lint
ruff check .

# Backend tests
pytest tests/ -x

# Frontend lint and build
cd frontend && npm run lint && npm run build

# E2E tests (if configured)
npx playwright test
```

For each command:
- Report PASS or FAIL
- If FAIL, capture the specific error output
- If `npx playwright test` fails because Playwright is not installed, note it as a warning (not a blocker)

### 3. Evaluate Results
**All PASS (ignoring warnings for unconfigured test runners):**
- Proceed to commit

**Any FAIL:**
- Report exactly which checks failed with error details
- Report which ACs may be affected
- Do NOT commit
- Output: "Story incomplete. Fix the failures above and re-run /story-complete"

### 4. Commit and Push (only if all pass)
```bash
# Stage only tracked files to avoid accidentally committing secrets or artifacts
git add -u
git commit -m "feat(story-id): [story title summary]"
git push -u origin [current-branch]
```

### 5. Output Merge Instructions
```
Story [ID] complete!

Branch: [branch-name]
Commit: [commit-hash]
Tests: All passing

To merge:
  git checkout main
  git merge --no-ff [branch-name]
  git push origin main

Or create a PR:
  gh pr create --title "[Story ID]: [Title]" --body "Closes story [ID]"
```

### 6. Trigger Docs Update
After successful commit, note that the docs-specialist should be invoked to update progress.md, task_plan.md, and any affected documentation.
