# PR #55 Fix Session — BMAD Prompt

Use this prompt to start a dev session targeting the issues found in PR #55.
Load in a Claude Code session open to `/mnt/d/ailocal/acm-ai` (main branch dev environment).

---

## Session Starter Prompt

```
/bmad:mmm:workflows:dev-story

Context for this session:

I need you to fix a set of confirmed bugs and missing tests identified in a peer code review
of PR #55 ("Release: Sprint Feature Complete"). The full findings are in:

  docs/issues/pr55-qwen25-extraction-quality-review.md

The changes are in the release branch of the production repo (acm-ai-production), but we
are implementing fixes here on main so they land cleanly. The production branch will be
rebased or cherry-picked once fixes are verified here.

## Affected files (already in codebase — do NOT create new abstractions):
- open_notebook/graphs/acm_extraction.py   ← primary target
- open_notebook/graphs/utils.py            ← utility functions
- open_notebook/extractors/orchestrator.py ← Qwen error handling
- api/model_provisioning.py               ← DB record inconsistency
- tests/test_preprocess_samp.py           ← MUST CREATE (missing)
- tests/test_qwen_extraction.py           ← MUST CREATE (missing)

## Priority order (fix in this sequence):
1. C1: NO_ACCESS_PHRASES cascade bug in _preprocess_samp_format()
   — Use a single combined regex alternation, longest-first, single-pass
   — Update test_no_double_markers_for_longer_phrase to assert == 1 (not >= 1)

2. CREATE tests/test_preprocess_samp.py
   — 14 tests as spec'd in sprint artifact e18-s5
   — Cover: phrase injection, ordering invariant, double-marker prevention, product normalization

3. CREATE tests/test_qwen_extraction.py
   — Cover: _is_qwen_model() (ollama format, openrouter format, qwen3 exclusion, non-qwen)
   — Cover: parse_json_response() (fenced block, raw brace match, raises ValueError when no JSON)

4. C2: Initialize model_family = "default" before try block in extract_records()

5. C3: Replace bare except Exception with specific catches + raise CancelledError

6. C4: Add try/except inside Qwen block in _llm_extract_building()

7. H2: Move _is_qwen_model() from acm_extraction.py → utils.py (remove circular import)

8. H1: Replace hasattr temperature mutation with temperature param at provision time

9. H3: Split except (ValidationError, Exception) into separate clauses

10. H5/H6/V1: Improve fallback logging, fix JSONDecodeError wrapping, add return type

## Acceptance criteria:
- uv run pytest tests/test_preprocess_samp.py -v   → all pass
- uv run pytest tests/test_qwen_extraction.py -v   → all pass
- uv run pytest tests/ -x                          → full suite passes
- uv run ruff check open_notebook/                 → no violations
- python -c "from open_notebook.graphs.acm_extraction import extract_records"  → no ImportError
- python -c "from open_notebook.extractors.orchestrator import plan_extraction" → no ImportError

## What NOT to do:
- Do not refactor beyond what is listed above
- Do not add features or new abstractions
- Do not touch frontend, migrations, or prompts/ unless explicitly needed
- Do not commit — Demi will review and commit

Start with issue C1 (the NO_ACCESS cascade bug). Read acm_extraction.py first,
find _preprocess_samp_format(), understand the full NO_ACCESS_PHRASES loop,
then implement the single-pass regex fix. Run the existing no_access tests
before and after to confirm the fix.
```

---

## Alternative: Quick Dev workflow (if you want faster iteration without full story structure)

```
/bmad:mmm:workflows:quick-dev

Fix the bugs identified in docs/issues/pr55-qwen25-extraction-quality-review.md.

Start with the CRITICAL section (C1-C4), then HIGH severity (H1-H3), then create
the two missing test files (T1, T2). Use the priority table at the bottom of the
issue file to sequence the work. Run pytest after each fix. Do not commit.
```

---

## Notes for BMAD Agents

- **Main branch context:** This is the `main` branch development environment (`/mnt/d/ailocal/acm-ai`). The reviewed code lives in the `release` branch of `/mnt/d/ailocal/acm-ai-production`. You may need to read the production code to understand context, but write fixes here.
- **BMAD memory:** Check `_bmad/_memory/` for any prior context on extraction graph architecture.
- **Sprint artifacts:** See `docs/sprint-artifacts/e18-s5-extraction-quality-fuse-cartridge-no-access.md` and `e18-s7-qwen25-32b-support.md` for the original sprint specs that drove these changes.
- **Test patterns:** Existing tests in `tests/test_taxonomy.py` show the expected test structure. Unit tests must not require API keys or DB connections. Integration tests should be marked `@pytest.mark.integration`.
- **Circular import resolution:** `_is_qwen_model` must land in `open_notebook/graphs/utils.py`. Update imports in both `acm_extraction.py` and `orchestrator.py`.
