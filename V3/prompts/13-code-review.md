# 13: Code Review — Reusable Template

> **BMAD Command:** `/bmad-bmm-code-review`
> **Agent:** Amelia — 💻 Developer Agent
> **Depends On:** 11-dev-story (implementation) + optionally 12-qa-automation (tests)
> **Output:** Review feedback or approval
> **Run in:** Fresh context window
> **Repeat:** For each story after implementation

---

## Pre-Read Documents

- `docs/sprint-artifacts/{STORY_FILE}.md` — Story tech spec (acceptance criteria to verify)
- All files modified by the story (from tech spec's File Changes table)
- Test files created in Step 12

---

## Prompt Template

```text
/bmad-bmm-code-review

## Code Review: {EPIC_ID}-{STORY_ID} — {STORY_TITLE}

### Story Tech Spec
Read: `docs/sprint-artifacts/{STORY_FILE}.md`

### Review Checklist

#### 1. Acceptance Criteria Verification
For each AC in the story:
- [ ] Implementation satisfies the AC
- [ ] A test exists that validates the AC
- [ ] Test passes

#### 2. V3 Compliance Checks
- [ ] SF API field names used consistently (not BAR names)
- [ ] Pydantic aliases match SF field names where applicable
- [ ] Dependent picklist validation present for constrained fields
- [ ] Provenance metadata captured for new/modified records
- [ ] SSE events emitted for long-running operations (if applicable)
- [ ] Migration is additive (no field removals during V3 transition)
- [ ] Feature flags used for new provider integrations

#### 3. Code Quality
- [ ] Follows existing codebase patterns (repository pattern, domain models, command pattern)
- [ ] No security vulnerabilities (OWASP top 10)
- [ ] No hardcoded values that should come from config
- [ ] Error handling for external service calls (providers, LLM APIs)
- [ ] Type hints on all public functions
- [ ] No unnecessary imports or dead code

#### 4. Test Quality
- [ ] Unit tests cover core logic
- [ ] Integration tests cover API endpoints
- [ ] Edge cases tested (null values, empty data, invalid picklist values)
- [ ] No test pollution (each test independent)

#### 5. Build Verification
```bash
# Must all pass
cd "$CLAUDE_PROJECT_DIR" && uv run ruff check .
cd "$CLAUDE_PROJECT_DIR" && uv run pytest tests/ -x
cd "$CLAUDE_PROJECT_DIR/frontend" && npm run build  # if frontend changes
```

#### 6. File Existence Verification
Use `Glob` to verify every file in the tech spec's File Changes table exists.

### Review Outcomes
- **APPROVED**: All checks pass → update story status to `done` in sprint-status.yaml
- **CHANGES REQUESTED**: Issues found → document issues, story loops back to Dev Story (Step 11)
- **BLOCKED**: External dependency or design issue → escalate to architect or SM

### Story Status Update (if APPROVED)
Update `docs/sprint-artifacts/sprint-status.yaml`:
- Change story status from `review` to `done`
- Update Dev Agent Record with review notes

### Constraints
- Review ONLY the files changed by this story
- Do NOT suggest refactoring outside story scope
- Do NOT approve if any AC is untested
- Do NOT approve if build fails
```
