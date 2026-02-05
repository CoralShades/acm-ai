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
