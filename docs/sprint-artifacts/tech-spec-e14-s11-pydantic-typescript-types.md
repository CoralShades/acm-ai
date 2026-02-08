# Tech Spec: E14-S11 - Set Up Pydantic-to-TypeScript Type Generation

> **Story:** E14-S11
> **Epic:** E14 - UX & Enterprise Readiness
> **Status:** Ready for Dev
> **Created:** 2026-02-08
> **Priority:** P2

---

## Overview

This story establishes an automated code generation pipeline to synchronize Python Pydantic models with TypeScript interfaces. Currently, the frontend maintains manually-written TypeScript types in `frontend/src/lib/types/acm.ts` that drift from the backend's Pydantic models, causing type mismatches and missing fields.

The solution generates TypeScript types from Pydantic models at build time using JSON Schema as an intermediate format, eliminating manual duplication and ensuring type safety across the stack.

## User Story

**As a** developer
**I want** TypeScript types auto-generated from Python Pydantic models
**So that** frontend and backend types are always in sync

## Acceptance Criteria

- [ ] `scripts/generate_types.py` created with JSON Schema → TypeScript conversion
- [ ] Generates TypeScript interfaces from ACMRecord, ACMExtractionOutput, and related models
- [ ] Output to `frontend/src/lib/types/generated/`
- [ ] `npm run generate:types` script in package.json
- [ ] CI workflow detects type drift on PRD model changes
- [ ] Documentation for adding new models to generation pipeline

---

## Technical Design

### 1. Architecture Overview

The type generation pipeline follows this flow:

```
Python Pydantic Models
        |
        v  model.model_json_schema()
  JSON Schema files (intermediate)
        |
        v  quicktype or custom converter
  TypeScript interfaces
        |
        v  Written to frontend/src/lib/types/generated/
  Frontend imports
```

**Key Design Decisions:**

1. **JSON Schema as Intermediate Format**: Pydantic natively exports JSON Schema, avoiding direct Python-to-TypeScript conversion complexity
2. **quicktype for Conversion**: Production-ready, supports complex schemas, better than `datamodel-code-generator` for our use case
3. **Separate Generated Directory**: Prevents accidental manual edits, clear separation of concerns
4. **Cross-Repo Awareness**: Backend code is in the same repo (not sibling), so no cross-repo dependency issues

### 2. Pydantic Models to Convert

**Priority 1 (ACM Domain Models):**

| Pydantic Model | Source File | TypeScript Output |
|----------------|-------------|-------------------|
| `ACMRecord` | `open_notebook/domain/acm.py` | `ACMRecord.ts` |
| `ACMExtractionOutput` | `open_notebook/extractors/acm_schemas.py` | `ACMExtractionOutput.ts` |
| `ACMExtractionRecord` | `open_notebook/extractors/acm_schemas.py` | `ACMExtractionRecord.ts` |
| `ACMExtractionResult` | `open_notebook/extractors/acm_schemas.py` | `ACMExtractionResult.ts` |
| `BuildingRoomContext` | `open_notebook/extractors/acm_schemas.py` | `BuildingRoomContext.ts` |
| `ConfidenceDistribution` | `open_notebook/extractors/acm_schemas.py` | `ConfidenceDistribution.ts` |
| `TableBoundingBox` | `open_notebook/extractors/acm_schemas.py` | `TableBoundingBox.ts` |
| `ExtractionConfidence` (Enum) | `open_notebook/domain/acm.py` | `ExtractionConfidence.ts` |
| `ExtractionStatus` (Enum) | `open_notebook/extractors/acm_schemas.py` | `ExtractionStatus.ts` |

**Priority 2 (Base & Common Models):**

| Pydantic Model | Source File | TypeScript Output |
|----------------|-------------|-------------------|
| `ObjectModel` (base fields) | `open_notebook/domain/base.py` | `ObjectModel.ts` |
| `Source` | `open_notebook/domain/notebook.py` | `Source.ts` |
| `Note` | `open_notebook/domain/notebook.py` | `Note.ts` |
| `Notebook` | `open_notebook/domain/notebook.py` | `Notebook.ts` |

**Excluded Models (manual types preferred):**
- API request/response models (`api/models.py`) - these use FastAPI schemas, not Pydantic domain models
- UI-specific types (`frontend/src/lib/types/common.ts`) - these have no backend equivalent

### 3. Generation Script Implementation

**File:** `scripts/generate_types.py`

```python
#!/usr/bin/env python3
"""
Generate TypeScript interfaces from Pydantic models.

This script exports Pydantic models to JSON Schema, then converts them to TypeScript
using quicktype. Generated types are written to frontend/src/lib/types/generated/.

Usage:
    python scripts/generate_types.py
    npm run generate:types  # From frontend directory
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import List, Type

from loguru import logger
from pydantic import BaseModel

# Import all Pydantic models to convert
from open_notebook.domain.acm import ACMRecord, ExtractionConfidence
from open_notebook.extractors.acm_schemas import (
    ACMExtractionOutput,
    ACMExtractionRecord,
    ACMExtractionResult,
    BuildingRoomContext,
    ConfidenceDistribution,
    ExtractionStatus,
    TableBoundingBox,
)

# Directories
SCHEMA_DIR = Path("schemas/generated")
TS_OUTPUT_DIR = Path("frontend/src/lib/types/generated")

# Models to convert (order matters for dependencies)
MODELS_TO_CONVERT: List[Type[BaseModel]] = [
    # Enums first (no dependencies)
    ExtractionConfidence,
    ExtractionStatus,
    # Simple types next
    TableBoundingBox,
    ConfidenceDistribution,
    BuildingRoomContext,
    # Complex types last
    ACMExtractionRecord,
    ACMExtractionResult,
    ACMExtractionOutput,
    ACMRecord,
]


def check_quicktype_installed() -> bool:
    """Check if quicktype is installed globally or in node_modules."""
    try:
        subprocess.run(
            ["npx", "quicktype", "--version"],
            capture_output=True,
            check=True,
            cwd=Path("frontend"),
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def export_json_schema(model: Type[BaseModel], output_path: Path) -> None:
    """Export a Pydantic model to JSON Schema."""
    schema = model.model_json_schema()

    # Add metadata for better TypeScript output
    schema["$schema"] = "http://json-schema.org/draft-07/schema#"

    # Write formatted JSON
    output_path.write_text(json.dumps(schema, indent=2))
    logger.info(f"Exported schema: {model.__name__} → {output_path}")


def generate_typescript(schema_path: Path, output_path: Path, type_name: str) -> None:
    """Convert JSON Schema to TypeScript using quicktype."""
    try:
        result = subprocess.run(
            [
                "npx",
                "quicktype",
                "--src", str(schema_path),
                "--out", str(output_path),
                "--lang", "typescript",
                "--just-types",  # No runtime validation code
                "--prefer-types",  # Use 'type' instead of 'interface' for better composability
                "--nice-property-names",  # Convert snake_case to camelCase
                "--acronym-style", "original",  # Keep ACM as ACM, not Acm
            ],
            capture_output=True,
            text=True,
            check=True,
            cwd=Path("frontend"),
        )
        logger.info(f"Generated TypeScript: {type_name} → {output_path}")
    except subprocess.CalledProcessError as e:
        logger.error(f"quicktype failed for {type_name}:")
        logger.error(f"stdout: {e.stdout}")
        logger.error(f"stderr: {e.stderr}")
        raise


def generate_index_file(output_dir: Path, models: List[Type[BaseModel]]) -> None:
    """Generate index.ts to re-export all generated types."""
    exports = []
    for model in models:
        filename = f"{model.__name__}.ts"
        exports.append(f"export * from './{model.__name__}';")

    index_content = "\n".join([
        "/**",
        " * Auto-generated TypeScript types from Pydantic models.",
        " * DO NOT EDIT MANUALLY - regenerate with 'npm run generate:types'",
        " */",
        "",
        *sorted(exports),
        "",
    ])

    index_path = output_dir / "index.ts"
    index_path.write_text(index_content)
    logger.info(f"Generated index file: {index_path}")


def main() -> int:
    """Main generation pipeline."""
    logger.info("Starting Pydantic → TypeScript type generation")

    # Check dependencies
    if not check_quicktype_installed():
        logger.error("quicktype is not installed. Run: npm install -D quicktype")
        return 1

    # Create output directories
    SCHEMA_DIR.mkdir(parents=True, exist_ok=True)
    TS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Generate .gitkeep for schema directory (schemas are intermediate artifacts)
    (SCHEMA_DIR / ".gitkeep").touch()

    # Add warning header to generated directory
    warning_file = TS_OUTPUT_DIR / "README.md"
    warning_file.write_text(
        "# Auto-Generated Types\n\n"
        "This directory contains TypeScript types auto-generated from Python Pydantic models.\n\n"
        "**DO NOT EDIT FILES IN THIS DIRECTORY MANUALLY**\n\n"
        "To regenerate types:\n"
        "```bash\n"
        "npm run generate:types\n"
        "```\n"
    )

    # Process each model
    for model in MODELS_TO_CONVERT:
        try:
            # Export JSON Schema
            schema_path = SCHEMA_DIR / f"{model.__name__}.json"
            export_json_schema(model, schema_path)

            # Generate TypeScript
            ts_path = TS_OUTPUT_DIR / f"{model.__name__}.ts"
            generate_typescript(schema_path, ts_path, model.__name__)

        except Exception as e:
            logger.error(f"Failed to process {model.__name__}: {e}")
            return 1

    # Generate index file
    generate_index_file(TS_OUTPUT_DIR, MODELS_TO_CONVERT)

    logger.success(f"✅ Generated {len(MODELS_TO_CONVERT)} TypeScript types")
    logger.info(f"Output directory: {TS_OUTPUT_DIR}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
```

### 4. NPM Script Integration

**File:** `frontend/package.json` (additions)

```json
{
  "scripts": {
    "generate:types": "cd .. && uv run python scripts/generate_types.py",
    "build": "npm run generate:types && next build",
    "dev": "next dev --turbopack"
  },
  "devDependencies": {
    "quicktype": "^23.0.100"
  }
}
```

**Key Changes:**
1. Add `generate:types` script that runs the Python generator
2. Integrate into `build` pipeline (types generated before build)
3. Add `quicktype` as dev dependency for JSON Schema → TypeScript conversion

### 5. Output Structure

**Directory Layout:**

```
frontend/src/lib/types/
├── generated/                    # Auto-generated (DO NOT EDIT)
│   ├── README.md                # Warning about manual edits
│   ├── index.ts                 # Re-exports all types
│   ├── ACMRecord.ts
│   ├── ACMExtractionOutput.ts
│   ├── ACMExtractionRecord.ts
│   ├── ACMExtractionResult.ts
│   ├── BuildingRoomContext.ts
│   ├── ConfidenceDistribution.ts
│   ├── TableBoundingBox.ts
│   ├── ExtractionConfidence.ts
│   └── ExtractionStatus.ts
├── acm.ts                       # Manual types (API requests, UI-specific)
├── api.ts
├── common.ts
└── ...
```

**Sample Generated Output:**

`frontend/src/lib/types/generated/ACMRecord.ts`:

```typescript
/**
 * Auto-generated from Pydantic model: ACMRecord
 * DO NOT EDIT MANUALLY - regenerate with 'npm run generate:types'
 */

export type ExtractionConfidence = "high" | "medium" | "low";

export type ACMRecord = {
    id?: string | null;
    created?: string | null;  // ISO datetime string
    updated?: string | null;
    source_id: string;
    school_name: string;
    school_code?: string | null;
    building_id: string;
    building_name?: string | null;
    building_year?: number | null;
    building_construction?: string | null;
    room_id?: string | null;
    room_name?: string | null;
    room_area?: number | null;
    area_type?: string | null;
    product: string;
    material_description: string;
    extent?: string | null;
    location?: string | null;
    friable?: string | null;
    material_condition?: string | null;
    risk_status?: string | null;
    result: string;
    page_number?: number | null;
    table_bbox?: {
        x?: number | null;
        y?: number | null;
        width?: number | null;
        height?: number | null;
        page?: number | null;
    } | null;
    disturbance_potential?: string | null;
    sample_no?: string | null;
    sample_result?: string | null;
    identifying_company?: string | null;
    quantity?: string | null;
    acm_labelled?: boolean | null;
    acm_label_details?: string | null;
    hygienist_recommendations?: string | null;
    psb_supplied_acm_id?: string | null;
    removal_status?: string | null;
    date_of_removal?: string | null;
    extraction_confidence?: ExtractionConfidence | null;
    data_issues?: string[] | null;
    acm_product_group?: string | null;
    acm_product_type?: string | null;
    classification_confidence?: number | null;
    classification_override?: boolean | null;
    classification_method?: string | null;
    embedding?: number[] | null;
    embedding_text?: string | null;
    embedding_model?: string | null;
    embedded_at?: string | null;
};
```

**Frontend Usage:**

```typescript
// Import generated types
import type { ACMRecord, ACMExtractionOutput, ConfidenceDistribution } from '@/lib/types/generated';

// Use in components
interface ACMRecordTableProps {
  records: ACMRecord[];
  onRecordClick: (record: ACMRecord) => void;
}

// Use in API client
async function fetchACMRecords(sourceId: string): Promise<ACMRecord[]> {
  const response = await fetch(`/api/acm/records?source_id=${sourceId}`);
  return response.json();  // TypeScript knows this is ACMRecord[]
}
```

### 6. CI Workflow for Type Drift Detection

**File:** `.github/workflows/type-check.yml`

```yaml
name: Type Drift Check

on:
  pull_request:
    paths:
      - 'open_notebook/domain/**/*.py'
      - 'open_notebook/extractors/**/*.py'
      - 'scripts/generate_types.py'
      - 'frontend/src/lib/types/generated/**/*.ts'

permissions:
  contents: read
  pull-requests: write

jobs:
  check-type-drift:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install uv
        uses: astral-sh/setup-uv@v4

      - name: Install dependencies
        run: uv sync

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install frontend dependencies
        working-directory: frontend
        run: npm ci

      - name: Regenerate TypeScript types
        run: uv run python scripts/generate_types.py

      - name: Check for type drift
        id: drift
        run: |
          if git diff --quiet frontend/src/lib/types/generated/; then
            echo "drift=false" >> $GITHUB_OUTPUT
            echo "✅ Generated types are up to date"
          else
            echo "drift=true" >> $GITHUB_OUTPUT
            echo "❌ Generated types are out of sync with Pydantic models"
            git diff frontend/src/lib/types/generated/
          fi

      - name: Comment on PR if drift detected
        if: steps.drift.outputs.drift == 'true'
        uses: actions/github-script@v7
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `## ⚠️ Type Drift Detected

              The Pydantic models have changed, but the generated TypeScript types are out of sync.

              **To fix:**
              \`\`\`bash
              npm run generate:types
              git add frontend/src/lib/types/generated/
              git commit -m "chore: regenerate TypeScript types"
              \`\`\`

              **Changed models:**
              - Check the diff in the workflow logs for details
              `
            })

      - name: Fail if drift detected
        if: steps.drift.outputs.drift == 'true'
        run: exit 1
```

**Workflow Behavior:**
1. Triggers on PRs that modify Pydantic models or generated types
2. Regenerates types from current Pydantic models
3. Compares generated output with committed files
4. Posts PR comment with fix instructions if drift detected
5. Fails the check to prevent merge until fixed

### 7. Pre-Commit Hook (Optional)

For local validation, add a pre-commit hook:

**File:** `.pre-commit-config.yaml` (append)

```yaml
repos:
  - repo: local
    hooks:
      - id: check-type-sync
        name: Check TypeScript type sync
        entry: bash -c 'uv run python scripts/generate_types.py && git diff --exit-code frontend/src/lib/types/generated/'
        language: system
        pass_filenames: false
        always_run: false
        files: '^(open_notebook/domain/.*\.py|open_notebook/extractors/.*\.py)$'
```

Developers can enable this with `pre-commit install`.

### 8. Migration Strategy

**Phase 1: Generate alongside manual types**
- Add generation script and CI check
- Generate types to `frontend/src/lib/types/generated/`
- Keep existing manual types in `frontend/src/lib/types/acm.ts`
- No frontend code changes yet

**Phase 2: Migrate imports**
- Update imports to use generated types:
  ```typescript
  // Before
  import type { ACMRecord } from '@/lib/types/acm';

  // After
  import type { ACMRecord } from '@/lib/types/generated';
  ```
- Verify build passes with new types
- Identify any mismatches (e.g., `extraction_confidence` is `string` in backend but was `number` in manual types)

**Phase 3: Remove manual types**
- Delete redundant definitions from `frontend/src/lib/types/acm.ts`
- Keep UI-specific types that have no backend equivalent
- Update documentation

---

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `scripts/generate_types.py` | CREATE | Python script to export JSON schemas and generate TypeScript |
| `frontend/package.json` | MODIFY | Add `generate:types` script and `quicktype` dependency |
| `frontend/src/lib/types/generated/README.md` | CREATE | Warning about auto-generated files |
| `frontend/src/lib/types/generated/index.ts` | CREATE | Re-export all generated types |
| `frontend/src/lib/types/generated/ACMRecord.ts` | CREATE | Generated type (output) |
| `frontend/src/lib/types/generated/ACMExtractionOutput.ts` | CREATE | Generated type (output) |
| `frontend/src/lib/types/generated/*.ts` | CREATE | 7 additional generated type files |
| `.github/workflows/type-check.yml` | CREATE | CI workflow for drift detection |
| `.pre-commit-config.yaml` | MODIFY | Add local type sync hook (optional) |
| `schemas/generated/.gitkeep` | CREATE | Keep intermediate schema directory in git |
| `.gitignore` | MODIFY | Add `schemas/generated/*.json` (intermediate artifacts) |
| `docs/development/contributing.md` | MODIFY | Add section on type generation workflow |

---

## Dependencies

**Required:**
- Existing Pydantic models in `open_notebook/domain/` and `open_notebook/extractors/`
- Python 3.11+ with `uv` package manager
- Node.js 20+ with `npm`

**New Dependencies:**
- `quicktype` (npm package, added as devDependency)

**No Backend Code Changes Required:**
- Pydantic models already support `.model_json_schema()` (Pydantic v2 feature)
- No additional Python packages needed

---

## Testing

### 1. Unit Tests (Python)

**File:** `tests/test_type_generation.py`

```python
import json
from pathlib import Path
import pytest
from scripts.generate_types import export_json_schema, SCHEMA_DIR
from open_notebook.domain.acm import ACMRecord


def test_json_schema_export():
    """Test that ACMRecord exports valid JSON Schema."""
    output_path = Path("test_schema.json")
    try:
        export_json_schema(ACMRecord, output_path)

        # Verify file exists and is valid JSON
        assert output_path.exists()
        schema = json.loads(output_path.read_text())

        # Verify schema structure
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "source_id" in schema["properties"]
        assert "building_id" in schema["properties"]

    finally:
        if output_path.exists():
            output_path.unlink()


def test_all_models_have_schemas():
    """Test that all models in MODELS_TO_CONVERT can export schemas."""
    from scripts.generate_types import MODELS_TO_CONVERT

    for model in MODELS_TO_CONVERT:
        schema = model.model_json_schema()
        assert schema is not None
        assert "properties" in schema or "enum" in schema  # Objects or Enums
```

### 2. Integration Tests

**Manual Verification:**

```bash
# 1. Run type generation
npm run generate:types

# 2. Verify output files exist
ls -la frontend/src/lib/types/generated/

# 3. Check TypeScript compiles
cd frontend && npm run build

# 4. Verify no TypeScript errors
cd frontend && npx tsc --noEmit
```

**Expected Output:**
```
✅ Generated 9 TypeScript types
Output directory: frontend/src/lib/types/generated
```

### 3. CI Checks

The GitHub Actions workflow will:
1. Run type generation on every PR touching Pydantic models
2. Fail if generated types don't match committed files
3. Post comment with fix instructions

### 4. Test Cases

| Test Case | Expected Result |
|-----------|-----------------|
| Add new field to `ACMRecord` | CI fails, prompts to regenerate types |
| Regenerate types locally | Types update, CI passes |
| Manually edit generated file | CI fails, file overwritten on regeneration |
| Change field type (str → int) | TypeScript compiler error in frontend code |

---

## Estimated Complexity

**Story Points:** 5

**Breakdown:**
- Script development: 2 points (JSON schema export, quicktype integration)
- CI workflow setup: 1 point (GitHub Actions configuration)
- Testing & verification: 1 point (manual testing, schema validation)
- Documentation: 1 point (README, contributing guide updates)

**Risks:**
1. **Low Risk:** quicktype may produce unexpected TypeScript for complex schemas
   - *Mitigation:* Test with all models, manual review of initial output
2. **Low Risk:** Enum handling differences between Python and TypeScript
   - *Mitigation:* Use quicktype's `--prefer-types` flag, test enum conversions
3. **Medium Risk:** Developers may forget to regenerate types after Pydantic changes
   - *Mitigation:* CI check catches this, pre-commit hook for proactive detection

---

## Implementation Notes

### Adding New Models to Generation

To add a new Pydantic model to the generation pipeline:

1. Import the model in `scripts/generate_types.py`:
   ```python
   from open_notebook.domain.my_module import MyNewModel
   ```

2. Add to `MODELS_TO_CONVERT` list (order by dependencies):
   ```python
   MODELS_TO_CONVERT = [
       # ... existing models ...
       MyNewModel,  # Add at appropriate position
   ]
   ```

3. Regenerate types:
   ```bash
   npm run generate:types
   ```

4. Commit generated output:
   ```bash
   git add frontend/src/lib/types/generated/MyNewModel.ts
   git commit -m "feat: add TypeScript types for MyNewModel"
   ```

### Handling Type Mismatches

If the generated TypeScript types don't match existing usage:

1. **Check Pydantic model is source of truth**: The backend model is authoritative
2. **Update frontend code to match**: Fix TypeScript usage to align with Pydantic
3. **If backend is wrong**: Fix Pydantic model first, then regenerate

**Example:**

```typescript
// Manual type had incorrect type
extraction_confidence?: number | null  // ❌ Wrong

// Generated type is correct (matches Pydantic Enum)
extraction_confidence?: "high" | "medium" | "low" | null  // ✅ Correct
```

### Customizing quicktype Output

If default quicktype output needs adjustment, modify `generate_typescript()` flags:

```python
# Example: Use interfaces instead of types
"--just-types",           # Remove for full validation
"--prefer-types",         # Change to --prefer-interfaces
"--nice-property-names",  # Remove to keep snake_case
```

---

## References

- [AG-UI Pipeline Spec - Section 7](../ag-ui-pipeline-spec.md#7-pydantic-to-typescript-code-generation)
- [Pydantic JSON Schema Export](https://docs.pydantic.dev/latest/concepts/json_schema/)
- [quicktype Documentation](https://quicktype.io/)
- [Epic 14 Change Proposal](./change-proposal-epic-14.md)

---

## Success Metrics

- **Zero manual type duplication**: All ACM types generated from single source
- **CI enforcement**: 100% of PRs with Pydantic changes checked for type drift
- **Build integration**: TypeScript build fails if types out of sync
- **Developer experience**: Adding new models takes <2 minutes

---

**Last Updated:** 2026-02-08
**Tech Spec Author:** Technical Writer Agent
**Reviewer:** Dev Lead (Pending)
