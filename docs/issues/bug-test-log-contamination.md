# Test pipeline logs contaminate production log files

> **GitHub Issue**: #98
> **Discovered**: 2026-03-05 (E36-S3 log sentinel session)
> **Finding**: F010
> **Priority**: CONCERN
> **Status**: Open

## Problem

Pytest test runs write their logs — including `AsyncMock` errors, `PROVIDER MISMATCH` warnings, and test-specific source IDs (e.g., `source:test_e2e_123`) — to the shared production log files `logs/api-error.log` and `logs/api.log`. This contaminates production logs and makes automated error pattern detection unreliable.

## Evidence

Log sentinel scan during E36-S3 found:
- **24** `AsyncMock` occurrences in production logs (all from pytest)
- **203** `PROVIDER MISMATCH` entries (vast majority from test runs)
- Test source IDs like `source:test_e2e_123` mixed with real source IDs

## Impact

- Log sentinel reports false positives (test errors appear as production issues)
- Manual log review must filter out test noise before triaging real errors
- No functional impact on extraction correctness

## Fix

**Option A**: Add a `conftest.py` fixture to redirect file handler output:
```python
@pytest.fixture(autouse=True)
def redirect_test_logs():
    # Redirect file handlers to logs/api-test.log during tests
    import logging
    for handler in logging.root.handlers:
        if isinstance(handler, logging.FileHandler):
            handler.baseFilename = "logs/api-test.log"
```

**Option B**: Configure via `pyproject.toml`:
```ini
[tool.pytest.ini_options]
log_file = "logs/api-test.log"
log_file_level = "DEBUG"
```

**Option C**: Use environment variable to switch log file path:
```python
# In logging config
LOG_FILE = os.getenv("LOG_FILE", "logs/api.log")
# Tests set LOG_FILE=logs/api-test.log
```

## Key Files

- [`conftest.py`](../../conftest.py) — pytest configuration
- [`open_notebook/utils/logging_config.py`](../../open_notebook/utils/logging_config.py) — logging setup (if exists)
- `logs/api.log`, `logs/api-error.log` — contaminated production logs

## Related

- GitHub Issue: [#98](https://github.com/CoralShades/acm-ai/issues/98)
- Finding: F010 in [`docs/sprint-artifacts/e36/findings.md`](../sprint-artifacts/e36/findings.md)
- Evidence: [`docs/sprint-artifacts/e36/evidence/log-sentinel-e36s3.md`](../sprint-artifacts/e36/evidence/log-sentinel-e36s3.md) section 3.1 and 3.5
