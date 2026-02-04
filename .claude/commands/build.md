---
description: Build ACM-AI frontend and run backend checks
allowed-tools: Bash
argument-hint: [target]
---

# Build ACM-AI

Build and verify the project.

## Build Targets

### Frontend Build (Default)
```bash
cd frontend && npm run build
```

### Backend Lint Check
```bash
uv run ruff check .
```

### Backend Format Check
```bash
uv run ruff format --check .
```

### Type Check
```bash
uv run mypy .
```

## Instructions

1. **If target is `frontend` or no argument**:
   ```bash
   cd frontend && npm run build
   ```

2. **If target is `backend`**:
   ```bash
   uv run ruff check . && uv run ruff format --check .
   ```

3. **If target is `all`**:
   Run both frontend build and backend checks.

4. Report any build errors with file locations.
