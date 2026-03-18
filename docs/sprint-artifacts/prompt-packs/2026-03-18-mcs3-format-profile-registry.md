# Multi-Consultant Story 3: Consultant Format Profile Registry
# Generated via /generate-prompt --save --with-plan --tmux

**SP: 5 | Wave: 3 (parallel with Stories 4, 5) | Dependencies: Story 2 complete**
**Design doc: `docs/architecture/multi-consultant-format-design.md` Section 5.3, Section 7 Story 3**

## Skills to Load

/planning-with-files — persistent markdown plan
/fastapi-router-py — FastAPI router patterns
/pydantic-models-py — Pydantic model design
/test-driven-development — TDD
/verification-before-completion — verify before claiming done

---

## Prerequisites

- Branch: `git checkout ACMV3`
- Story 2 complete (`InferredSchema`, `RecoveryConfig` exist, schema inference node wired)
- SurrealDB running: `docker ps | grep acm-ai-db`
- API running: `curl http://localhost:5055/health`

---

## Glossary

| Term | Definition |
|------|-----------|
| Format profile | Cached mapping of PDF column headers → SF fields for a known consultant format |
| Header signature | Sorted hash of unique column header text — used as cache key |
| `consultant_format_profile` | New SurrealDB table storing cached format profiles |
| InferredSchema | Dataclass from Story 2 — column_mapping, confidence, consultant_name |
| Cache hit | Header signature matches existing profile → skip LLM inference |
| Cache miss | Unknown header signature → run LLM inference → save new profile |

---

## Key Files

**Read:**
- `docs/architecture/multi-consultant-format-design.md` — Section 5.3 (SurrealDB schema)
- `open_notebook/extractors/schema_inference.py` — Story 2 output (InferredSchema, header collection)
- `open_notebook/database/repository.py` — existing SurrealDB repository pattern
- `api/routers/acm.py` — existing ACM API router pattern
- `migrations/` — latest migration number for sequencing

**Create:**
- `migrations/NNNN_consultant_format_profile.surql` — SurrealDB migration
- `migrations/NNNN_down_consultant_format_profile.surql` — rollback migration
- `api/routers/format_profiles.py` — `GET /api/acm/format-profiles`, `POST /api/acm/format-profiles`
- `tests/test_format_profile_registry.py` — cache hit/miss tests

**Modify:**
- `open_notebook/extractors/schema_inference.py` — add cache-hit/miss logic, profile save
- `api/main.py` — register format_profiles router
- `open_notebook/database/async_migrate.py` — register new migration

---

## Plan

Create `docs/sprint-artifacts/mcs3-format-registry/task_plan.md`:
- [ ] Create SurrealDB migration (design doc Section 5.3 schema)
- [ ] Register migration in `async_migrate.py`
- [ ] Implement header signature hashing (sorted hash of unique headers + column count)
- [ ] Add cache-hit logic to `schema_inference.py` — check profile before LLM call
- [ ] Add profile auto-save on successful inference
- [ ] Add `sample_count` increment on cache hits
- [ ] Create FastAPI router: `GET /api/acm/format-profiles` (list all profiles)
- [ ] Create FastAPI endpoint: `POST /api/acm/format-profiles` (manual profile creation)
- [ ] Create FastAPI endpoint: `DELETE /api/acm/format-profiles/{id}` (delete profile)
- [ ] Write tests: cache miss → LLM called → profile saved
- [ ] Write tests: cache hit → LLM skipped → profile reused
- [ ] Write tests: hash collision resistance (same headers different order)
- [ ] Run full test suite + lint

---

## Agent Strategy: TMUX

```
Pane 0 (left):   Implementation — migration, schema_inference cache logic
Pane 1 (right):  API — format_profiles.py router
Pane 2 (bottom): Test runner — continuous pytest
```

---

## Context7 Directives

1. resolve-library-id for "surrealdb.py" → query-docs for "create select query record operations"
2. resolve-library-id for "fastapi" → query-docs for "APIRouter Depends path parameters"

---

## Verification Checklist

- [ ] Migration runs: `consultant_format_profile` table created in SurrealDB
- [ ] `GET /api/acm/format-profiles` returns empty list initially
- [ ] Cache miss: first extraction → LLM inference runs → profile saved → GET returns 1 profile
- [ ] Cache hit: second extraction same format → LLM skipped → `sample_count` incremented to 2
- [ ] `POST /api/acm/format-profiles` creates manual profile
- [ ] Hash includes column count + order (not just header text)
- [ ] `uv run pytest tests/test_format_profile_registry.py -v` — all pass
- [ ] `uv run pytest tests/ -x` — full suite passes
- [ ] `uv run ruff check .` — lint clean

---

## Commit Template

```
feat(extraction): add consultant format profile registry — cache column mappings in SurrealDB

- Create consultant_format_profile migration with header_signature index
- Implement cache-hit/miss logic in schema inference node
- Auto-save profiles on successful inference, increment sample_count on hits
- Add GET/POST/DELETE /api/acm/format-profiles endpoints
- Multi-Consultant Story 3 of 7

Co-Authored-By: Claude <noreply@anthropic.com>
```
