# 11: Dev Story — Reusable Implementation Template

> **BMAD Command:** `/bmad-bmm-dev-story`
> **Agent:** Amelia — 💻 Developer Agent
> **Depends On:** 10-create-story (story tech spec must exist)
> **Output:** Implemented code + tests
> **Run in:** Fresh context window (one per story)
> **Repeat:** For each story in the sprint plan
> **Tools:** Context7 MCP for library documentation

---

## Pre-Read Documents

- `docs/sprint-artifacts/{STORY_FILE}.md` — Story tech spec (from Step 10)
- `docs/sprint-artifacts/sprint-status.yaml` — Current sprint status
- `_bmad-output/project-planning-artifacts/acm-ai/04-architecture.md` — Architecture context

### Story-Specific Files (from tech spec's File Changes table)
- Read all files listed in the "File Changes" section of the story tech spec

---

## Prompt Template

Copy and replace `{PLACEHOLDERS}`:

```text
/bmad-bmm-dev-story

## Implement: {EPIC_ID}-{STORY_ID} — {STORY_TITLE}

### Story Tech Spec
Read the full tech spec at: `docs/sprint-artifacts/{STORY_FILE}.md`

### Implementation Instructions

1. **Read the tech spec thoroughly** before writing any code
2. **Read all files** listed in the File Changes table
3. **Follow the technical design** specified in the tech spec
4. **Write tests alongside implementation** — not after

### V3-Specific Development Rules

#### Salesforce Field Names
- All domain model fields use SF API names as Pydantic aliases
- Database columns use SF API names
- API responses use SF API names
- Reference `V3/output/item_fields_summary.md` and `V3/output/building_fields_summary.md` for exact field definitions and picklist values

#### Provider Adapter Pattern
If this story implements or touches extraction providers:
- Implement the provider adapter interface defined in architecture
- No provider-specific imports outside the adapter module
- All provider output must be normalized to the common extraction result format
- Feature flag for provider enablement

#### Provenance Tracking
If this story creates or modifies extraction records:
- Every record must have: source_page, table_bbox, extraction_provider, extraction_model, confidence_score
- Store provenance in the architecture-specified location (embedded or separate table)

#### SSE Events
If this story involves long-running operations:
- Emit SSE events using the AG-UI event emitter pattern
- Event types must match the architecture spec
- Frontend can subscribe to `/api/agui/{operation}/{id}/stream`

#### Migration Safety
If this story includes database migrations:
- Additive only — never remove existing fields during V3 transition
- Include rollback SurrealQL script
- Test migration on existing data (BAR-shaped records must survive)

### Library Documentation
**Use Context7 MCP** to fetch current docs for any libraries you're working with:
- AG Grid (if frontend story)
- Docling (if extraction story)
- Google Document AI / PaddleOCR (if provider story)
- SurrealDB (if migration/database story)
- FastAPI (if API endpoint story)

### Build Verification (REQUIRED before marking complete)
```bash
# Backend changes
cd "$CLAUDE_PROJECT_DIR" && uv run ruff check . --fix
cd "$CLAUDE_PROJECT_DIR" && uv run ruff format .
cd "$CLAUDE_PROJECT_DIR" && uv run pytest tests/ -x

# Frontend changes
cd "$CLAUDE_PROJECT_DIR/frontend" && npm run lint
cd "$CLAUDE_PROJECT_DIR/frontend" && npm run build
```

### File Existence Check (REQUIRED)
After implementation, verify every file in the tech spec's File Changes table exists using `Glob`.

### Story Status Update
After all checks pass, update `docs/sprint-artifacts/sprint-status.yaml`:
- Change story status from `in-progress` to `review`
- Add implementation notes to the Dev Agent Record in the tech spec

### Constraints
- Follow existing patterns in the codebase
- Do NOT refactor code outside the story scope
- Do NOT add features not in the acceptance criteria
- Do NOT skip tests — every AC must have a corresponding test
- Use conventional commits: feat:, fix:, refactor:, test:
```

---

## Usage Notes

- Run **one Dev Story prompt per story** in a fresh context
- After implementation, proceed to Step 12 (QA) or Step 13 (Code Review)
- If code review (Step 13) finds issues, re-run this prompt with the review feedback appended
