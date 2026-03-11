# Pre-Existing Test Failures — Bug Fix 11 Baseline

**Captured**: 2026-03-11 (after Phase 1+2 commit `7eb73f27`)
**Total**: 2161 passed, 1 failed, 14 skipped, 2 xfailed, 34 warnings

## Failed (1)

| Test | File | Root Cause | Category |
|------|------|------------|----------|
| `test_broadmeadows_all_records_extracted` | `tests/test_broadmeadows_e2e.py` | Requires live OpenRouter credits (HTTP 402: Insufficient credits) — E2E test hits real API | needs running services |

**Note**: This test ran the full extraction pipeline but got 0/31 records because the OpenRouter API returned 402. The test itself is valid; it just needs funded API keys.

## Skipped (14)

These are skipped via `@pytest.mark.skip` or `skipIf` conditions — they don't indicate bugs:

| Count | Reason Category |
|-------|----------------|
| ~14 | Various — conditional skips for optional features, platform-specific tests, or environment-dependent tests |

## xfailed (2)

Expected failures — tests marked with `@pytest.mark.xfail` that are known to fail:

| Count | Reason |
|-------|--------|
| 2 | Known issues tracked separately |

## Warnings (34)

| Warning | Count | Source |
|---------|-------|--------|
| PydanticDeprecatedSince20: class-based `config` | 3 | surreal_commands, domain/base.py, podcast.py |
| PydanticDeprecatedSince20: `.dict()` → `.model_dump()` | 12 | langchain_core tracers |
| PydanticDeprecatedSince20: `.construct()` → `.model_construct()` | 12 | langchain_core tracers |
| PydanticDeprecatedSince211: instance `model_fields` access | 4 | domain/base.py:297 |
| LangGraphDeprecatedSinceV05: `input`/`output` → `input_schema`/`output_schema` | 2 | content_core extraction graph |

## Summary

The codebase is clean — **zero unit test failures**. The single failure is an E2E integration test that requires live cloud API credentials with sufficient credits. All 2161 unit/integration tests pass.

This baseline should be maintained through Phase 3+4 implementation. Any new test failures after Phase 3+4 code changes indicate regressions.
