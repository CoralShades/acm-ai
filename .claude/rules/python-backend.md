---
paths:
  - "**/*.py"
  - "api/**/*"
  - "open_notebook/**/*"
  - "commands/**/*"
---

# Python Backend Rules for ACM-AI

## Code Style
- **Formatter**: Ruff with 88 character line length
- **Type hints**: Required for all function parameters and returns
- **Docstrings**: Google-style docstrings

## Import Order
1. Standard library
2. Third-party packages
3. Local imports (from . or from open_notebook)

## Architecture Patterns

### Repository Pattern
Database access through `open_notebook/database/` repositories:
```python
from open_notebook.database.repository import NotebookRepository
```

### Domain Models
Entities in `open_notebook/domain/`:
- Notebook, Source, Note, Model, Transformation

### Command Pattern
Background jobs in `commands/`:
- Each command is a separate module
- Use surreal-commands worker

## Testing
- Tests in `tests/` directory
- Use pytest fixtures
- Mock external services

## Error Handling
- Use custom exceptions from domain layer
- Always log errors with context
- Return appropriate HTTP status codes in API layer

## Multi-Venv Pattern (MinerU)

The project uses two Python environments:
- **Main**: `.venv/` — `uv run ...` for all production code
- **MinerU**: `.venv-mineru/` — `pip`-managed, isolated from main venv

### When writing code that touches MinerU:
- Call via `scripts/mineru_runner.py` subprocess bridge — never import `magic_pdf` directly
- Use `MINERU_ENABLED` env var to gate the MinerU path
- The bridge Python path: `.venv-mineru\Scripts\python.exe` (Windows) / `.venv-mineru/bin/python` (Linux)
- Research scripts under `scripts/research/` may import from `.venv-mineru` when run inside it
