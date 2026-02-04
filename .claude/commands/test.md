---
description: Run ACM-AI tests
allowed-tools: Bash
argument-hint: [test-path]
---

# Run ACM-AI Tests

Run the test suite for ACM-AI.

## Test Commands

### Run All Backend Tests
```bash
uv run pytest
```

### Run Specific Test File
```bash
uv run pytest tests/test_specific.py
```

### Run with Coverage
```bash
uv run pytest --cov=open_notebook
```

### Run with Verbose Output
```bash
uv run pytest -v
```

## Instructions

1. **If test path provided**, run specific test:
   ```bash
   uv run pytest $1 -v
   ```

2. **If no argument**, run all tests:
   ```bash
   uv run pytest
   ```

3. Report test results with pass/fail counts and any failures.

## Notes
- Tests are in the `tests/` directory
- Coverage reports to `htmlcov/` directory
- Use `-x` flag to stop on first failure
