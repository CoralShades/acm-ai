# Test Failures

All review issues resolved. See `.ralph/@review_issues.md` for details.

## Verification Results (2026-02-22)
- **ruff check**: All checks passed
- **pytest** (22 sync tests): All passed
- **Frontend lint**: No warnings or errors
- **Frontend build**: Compiled successfully

## Pre-existing Issues (not caused by sprint changes)
- `tests/test_acm_commands.py`: Requires `ai_prompter` module (not available in WSL)
- `tests/test_extraction_progress.py` async tests: Require `pytest-asyncio` plugin
- `tests/test_acm_ai_extraction.py`: Requires `ai_prompter` module
