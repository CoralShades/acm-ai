---
description: Regenerate erdantic ER diagrams and report changes
allowed-tools: Bash, Read, Glob
---

# Regenerate Diagrams

Regenerate erdantic Entity-Relationship diagrams for the ACM-AI domain models.

## Instructions

### 1. Check Prerequisites

```bash
echo "=== Checking Prerequisites ==="

# erdantic
python -c "import erdantic; print(f'erdantic: v{erdantic.__version__}')" 2>/dev/null || { echo "ERROR: erdantic not installed. Run: pip install erdantic"; exit 1; }

# Graphviz
dot -V 2>/dev/null || { echo "ERROR: Graphviz not installed. Install from https://graphviz.org/download/"; exit 1; }

echo "Prerequisites OK"
```

### 2. Record Current Diagram State

```bash
echo "=== Current Diagrams ==="
ls -la docs/diagrams/*.svg 2>/dev/null || echo "No existing diagrams found"
```

### 3. Run Generation Script

```bash
uv run python scripts/generate_model_diagrams.py
```

### 4. Report Changes

```bash
echo "=== Updated Diagrams ==="
ls -la docs/diagrams/*.svg 2>/dev/null

# Check git diff for changes
git diff --stat docs/diagrams/ 2>/dev/null || echo "No git changes detected"
```

### 5. Present Summary

```markdown
## Diagram Regeneration Report

### Diagrams Generated
| File | Size | Status |
|------|------|--------|
| {filename} | {size} | NEW / UPDATED / UNCHANGED |

### Models Included
[List of Pydantic models represented in the diagrams]

### View Diagrams
Open SVG files in browser:
- `docs/diagrams/{name}.svg`
```

## Notes

- Diagrams are generated as SVG files in `docs/diagrams/`
- erdantic traces Pydantic model relationships (fields referencing other models)
- Changes to domain models (`open_notebook/domain/`) may require diagram regeneration
- The generation script is at `scripts/generate_model_diagrams.py`
