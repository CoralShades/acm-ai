# 12: QA Automation — Test Generation Template

> **BMAD Command:** `/bmad-bmm-qa-automate`
> **Agent:** Quinn — 🧪 QA Engineer
> **Depends On:** 11-dev-story (implementation complete, in `review` status)
> **Output:** Test files in `tests/` and/or `frontend/` test directories
> **Run in:** Fresh context window (one per story or per epic batch)
> **Tools:** Context7 MCP for test framework docs

---

## Pre-Read Documents

- `docs/sprint-artifacts/{STORY_FILE}.md` — Story tech spec (acceptance criteria are the test requirements)
- Implementation files created in Step 11

### Test Framework Context (scan these for patterns)
- `tests/` — Existing pytest test structure and patterns
- `tests/conftest.py` — Existing fixtures
- `frontend/playwright.config.ts` — E2E test configuration (if it exists)

---

## Prompt Template

```text
/bmad-bmm-qa-automate

## Generate Tests: {EPIC_ID}-{STORY_ID} — {STORY_TITLE}

### Story Tech Spec
Read: `docs/sprint-artifacts/{STORY_FILE}.md`
Focus on: Acceptance Criteria section + Test Plan section

### V3-Specific Test Requirements

#### Salesforce Validation Tests
If the story involves SF fields or picklists:
- Test all valid picklist values (exact case-sensitive SF values)
- Test dependent picklist chains: Friability → ACM_Classification → ACM_Sub_Classification
- Test Building_Type → Building_Category chains
- Test invalid combinations are caught (warn or reject per architecture spec)
- Test "Good" → "Stable" vocabulary mapping (BAR legacy)
- Reference `V3/output/item_fields_summary.md` for exact valid values

#### Multi-Provider Tests
If the story involves extraction providers:
- Test provider adapter normalizes output to common format
- Test consensus layer with mock data (2 providers agree, 1 disagrees)
- Test confidence scoring thresholds
- Test provider failure handling (one provider fails, others succeed)
- Test feature flag toggles providers on/off

#### Provenance Tests
If the story creates extraction records:
- Test provenance metadata is stored (page, bbox, provider, model, confidence)
- Test provenance retrieval API returns correct lineage
- Test edit history is recorded on modification

#### SSE Tests
If the story involves streaming:
- Test SSE endpoint emits expected event types
- Test event format matches AG-UI protocol
- Test progress events are emitted in correct sequence
- Test connection cleanup on client disconnect

#### Migration Tests
If the story includes database migrations:
- Test migration applies cleanly on empty database
- Test migration applies on database with existing BAR-shaped records
- Test BAR records remain readable after migration
- Test rollback script works

### Test Categories to Generate

1. **Unit Tests** — Pure logic, no database. Mock external dependencies.
2. **Integration Tests** — Database + API. Use test fixtures.
3. **E2E Tests** — If UI story: Playwright tests for the page flow.

### Existing Test Patterns
Follow the patterns in existing test files:
- Use `pytest` with `@pytest.mark.asyncio` for async tests
- Use fixtures from `tests/conftest.py`
- Use `httpx.AsyncClient` for API tests
- Frontend E2E: Playwright with `test.describe` blocks

### Build Verification
```bash
# Run the new tests
cd "$CLAUDE_PROJECT_DIR" && uv run pytest tests/{NEW_TEST_FILE} -v

# Run full suite to check for regressions
cd "$CLAUDE_PROJECT_DIR" && uv run pytest tests/ -x

# Frontend E2E (if applicable)
cd "$CLAUDE_PROJECT_DIR/frontend" && npx playwright test {TEST_FILE}
```

### Acceptance Criteria Coverage Matrix
For each AC in the story, list:
| AC # | Description | Test File | Test Function | Status |
|------|-------------|-----------|---------------|--------|

Every AC MUST have at least one test. If an AC is untestable, flag it.

### Constraints
- Do NOT write tests for code outside this story's scope
- Do NOT skip edge cases (null values, empty arrays, boundary conditions)
- Do NOT mock the database in integration tests — use actual SurrealDB test instance
- Test files named: `test_{story_feature}.py` (e.g., `test_sf_schema_config.py`)
```

---

## Usage Notes

- Can batch multiple related stories for QA if they're in the same epic
- After QA, proceed to Step 13 (Code Review)
- If tests reveal implementation bugs, loop back to Step 11 (Dev Story)
