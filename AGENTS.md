# AGENTS.md — ACM-AI Coding Guide

ACM-AI is an Asbestos Containing Material (ACM) compliance management system.
Monorepo: Python 3.11+ FastAPI backend + Next.js 15 frontend.

For full architecture and workflow details see `CLAUDE.md` and `docs/index.md`.
For domain-specific rules see `.claude/rules/` (python-backend, nextjs-frontend, langgraph-ai, surrealdb, docker-compose, mcp-servers).

When searching docs, use the `context7` MCP tool. If unsure how to do something, use `gh_grep` to search code examples on GitHub.

---

## Services

| Service   | Port  | Start command                                      |
|-----------|-------|----------------------------------------------------|
| SurrealDB | 8000  | `docker compose up -d surrealdb`                   |
| API       | 5055  | `uv run run_api.py`                                |
| Worker    | —     | `uv run run_worker.py --import-modules commands`   |
| Frontend  | 8502  | `cd frontend && npm run dev`                       |

**Windows one-liner:** `start-all.bat` / `stop-all.bat`

---

## Build, Lint & Test

### Backend (Python)

```bash
uv sync                                                          # install deps

# Tests
uv run pytest                                                    # all tests
uv run pytest tests/test_acm_extractor.py                       # single file
uv run pytest tests/test_acm_extractor.py::TestClass::test_name # single test
uv run pytest -x                                                 # stop on first failure
uv run pytest --cov=open_notebook                               # with coverage

# Lint & format
uv run ruff check .                                              # lint
uv run ruff check . --fix                                        # lint + auto-fix
uv run ruff format .                                             # format
uv run mypy .                                                    # type check
```

### Frontend (Next.js)

```bash
cd frontend
npm install           # install deps
npm run dev           # dev server on :8502 (Turbopack)
npm run build         # production build — MUST pass before marking stories done
npm run lint          # ESLint
npm run generate:types  # regenerate Python→TypeScript types (run after Pydantic changes)
```

---

## Python Code Style

**Formatter/linter:** Ruff — line length 88.
**Rule profile:** `E`, `F`, `I`; ignores `E501`, `E402`, `E722`, `F401`, `F541`, `F841`.

### Imports
stdlib → third-party → local, separated by blank lines (`isort` black profile).
Inside test methods, import locally to avoid side-effect ordering issues.

### Types
- All functions must have type hints.
- Use `Optional[X]`, `List[X]`, `Dict[K, V]` (not PEP 604 `X | Y` union syntax).
- Domain models: Pydantic v2 with `ClassVar[str]` for table names.

### Naming
| Construct      | Convention           |
|----------------|----------------------|
| Classes        | `PascalCase`         |
| Functions/vars | `snake_case`         |
| Constants      | `UPPER_SNAKE_CASE`   |
| Private attrs  | `_leading_underscore`|
| Files/modules  | `snake_case`         |

### Logging
Use `loguru.logger` — **never** stdlib `logging`.

```python
from loguru import logger
logger.info("Processing source {source_id}", source_id=source_id)
logger.error(f"Failed to extract records: {e}")
```

### Exceptions
Custom hierarchy lives in `open_notebook/exceptions.py`. Always log before re-raising.

```python
# Raise domain exceptions, not generic ones
raise DatabaseOperationError(f"Failed to save record: {e}")
raise InvalidInputError("source_id is required")

# FastAPI layer converts to HTTPException
raise HTTPException(status_code=404, detail="Notebook not found")
```

### Async
All database operations are `async/await`. Use context managers for DB connections.

### Docstrings
Google-style docstrings on all public functions and classes.

---

## TypeScript / Next.js Code Style

**Config:** strict mode, target ES2017, path alias `@/*` → `./src/*`.
**Linter:** ESLint `next/core-web-vitals` + `next/typescript`.

### Naming
| Construct            | Convention     |
|----------------------|----------------|
| Components / files   | `PascalCase`   |
| Hooks / utils        | `kebab-case`   |
| Props interfaces     | `{Component}Props` |

### Import order
React → Next.js → internal API (`@/lib/api/`) → types → UI components → hooks → icons → utils.

### State management
- **Server state:** React Query v5 (`useQuery`, `useMutation`)
- **Client state:** Zustand v5
- **Forms:** React Hook Form v7 + Zod v4

### Styling
Tailwind CSS v4. Use `cn()` utility for conditional classes. Use CVA for component variants.

### API calls
Use the shared `apiClient` from `lib/api/client.ts` (Axios). Never create new Axios instances.

### Component pattern
Pages use `ErrorBoundary` wrapper + inner `Content` component:

```tsx
export default function MyPage() {
  return (
    <ErrorBoundary>
      <MyPageContent />
    </ErrorBoundary>
  )
}
```

---

## Testing Conventions

- Group tests in classes: `class TestFeatureName`
- Mock with `@patch` decorators; use `AsyncMock` for async methods
- Mark integration tests: `@pytest.mark.integration` (require live services)
- FastAPI tests use `TestClient`; auth is disabled in `conftest.py`

---

## Type Generation Pipeline

Pydantic models → TypeScript via `scripts/generate_types.py` (uses `quicktype`).

```bash
cd frontend && npm run generate:types
```

Generated output lands in `frontend/src/lib/types/generated/` (ESLint-ignored).
CI checks for drift in `frontend/src/lib/types/acm.ts` — run this after any Pydantic model change.

---

## Story Completion Checklist

Before marking **any** story done:

1. `cd frontend && npm run build` — must pass (no missing imports/files)
2. `uv run ruff check .` — no lint errors
3. `uv run pytest` — all tests pass
4. For UI changes: navigate to affected page in browser and verify DOM with snapshot
5. Verify every file listed in the tech spec's "File Changes" table actually exists

---

## Superpowers Integration

This project uses [obra/superpowers](https://github.com/obra/superpowers) for development workflow enforcement.

### Mandatory Skills (always invoke)
- `superpowers:test-driven-development` — for ALL coding tasks (RED-GREEN-REFACTOR)
- `superpowers:systematic-debugging` — for ALL debugging (4-phase root cause analysis)
- `superpowers:requesting-code-review` — before marking stories complete

### Workflow Skills (invoke based on task)
- `superpowers:brainstorming` — feature-level design within BMAD epics
- `superpowers:writing-plans` — create implementation plans from BMAD stories
- `superpowers:executing-plans` — batch execution with checkpoints
- `superpowers:subagent-driven-development` — autonomous task execution

### Routing Rule
- PROJECT planning (epics, architecture): BMAD agents
- STORY implementation: Superpowers skills
- Plans saved to `docs/plans/`, BMAD artifacts in `_bmad-output/`

See `docs/SUPERPOWERS-INTEGRATION.md` for full setup across Claude Code, Codex, and OpenCode.

---

## Environment Variables

Required in `.env` (see `.env.example` for full list):

```bash
SURREAL_URL=ws://localhost:8000/rpc
SURREAL_USER=root
SURREAL_PASSWORD=root
SURREAL_NAMESPACE=open_notebook
SURREAL_DATABASE=development
OPENAI_API_KEY=sk-...   # at least one AI provider key required
```
