#!/usr/bin/env python3
"""
Generate TypeScript interfaces from Pydantic models.

Exports Pydantic models to JSON Schema, then converts to TypeScript
using quicktype. Generated types are written to frontend/src/lib/types/generated/.

Usage:
    uv run python scripts/generate_types.py
    npm run generate:types  # From frontend directory

Adding new models:
    1. Import the Pydantic model at the top of this file
    2. Add it to MODELS_TO_CONVERT (for BaseModel subclasses)
       or ENUMS_TO_CONVERT (for str/Enum types)
    3. Run `npm run generate:types` from frontend/
    4. Commit the generated .ts files in frontend/src/lib/types/generated/
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
    TableBoundingBox,
    ConfidenceDistribution,
    BuildingRoomContext,
    ACMExtractionRecord,
    ACMExtractionResult,
    ACMExtractionOutput,
    ACMRecord,
]

# Enums to convert separately (quicktype handles these differently)
ENUMS_TO_CONVERT = [
    ExtractionConfidence,
    ExtractionStatus,
]


def check_quicktype_installed() -> bool:
    """Check if quicktype is available via npx."""
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
    schema["$schema"] = "http://json-schema.org/draft-07/schema#"
    output_path.write_text(json.dumps(schema, indent=2))
    logger.info(f"Exported schema: {model.__name__} -> {output_path}")


def generate_typescript(schema_path: Path, output_path: Path, type_name: str) -> None:
    """Convert JSON Schema to TypeScript using quicktype."""
    # Use absolute paths since quicktype runs from frontend/ directory
    abs_schema = schema_path.resolve()
    abs_output = output_path.resolve()
    try:
        subprocess.run(
            [
                "npx",
                "quicktype",
                "--src-lang", "schema",
                "--src", str(abs_schema),
                "--out", str(abs_output),
                "--lang", "typescript",
                "--just-types",
                "--prefer-types",
                "--acronym-style", "original",
            ],
            capture_output=True,
            text=True,
            check=True,
            cwd=Path("frontend"),
        )
        logger.info(f"Generated TypeScript: {type_name} -> {output_path}")
    except subprocess.CalledProcessError as e:
        logger.error(f"quicktype failed for {type_name}:")
        logger.error(f"stderr: {e.stderr}")
        raise


def generate_enum_file(enum_cls, output_path: Path) -> None:
    """Generate TypeScript enum from Python Enum class."""
    members = [(m.name, m.value) for m in enum_cls]
    lines = [
        f"// Auto-generated from {enum_cls.__name__}",
        f"// DO NOT EDIT MANUALLY - regenerate with 'npm run generate:types'",
        "",
        f"export type {enum_cls.__name__} =",
    ]
    for i, (_, value) in enumerate(members):
        suffix = ";" if i == len(members) - 1 else ""
        lines.append(f'  | "{value}"{suffix}')
    lines.append("")

    output_path.write_text("\n".join(lines))
    logger.info(f"Generated enum: {enum_cls.__name__} -> {output_path}")


def generate_index_file(output_dir: Path, models: list, enums: list) -> None:
    """Generate index.ts to re-export only the primary type from each file."""
    exports = []
    for model in models:
        # Use named export to avoid conflicts from quicktype's inline types
        exports.append(f"export type {{ {model.__name__} }} from './{model.__name__}';")
    for enum_cls in enums:
        exports.append(f"export type {{ {enum_cls.__name__} }} from './{enum_cls.__name__}';")

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
    logger.info("Starting Pydantic -> TypeScript type generation")

    if not check_quicktype_installed():
        logger.error("quicktype is not installed. Run: cd frontend && npm install -D quicktype")
        return 1

    # Create output directories
    SCHEMA_DIR.mkdir(parents=True, exist_ok=True)
    TS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Process Pydantic models
    for model in MODELS_TO_CONVERT:
        try:
            schema_path = SCHEMA_DIR / f"{model.__name__}.json"
            export_json_schema(model, schema_path)

            ts_path = TS_OUTPUT_DIR / f"{model.__name__}.ts"
            generate_typescript(schema_path, ts_path, model.__name__)
        except Exception as e:
            logger.error(f"Failed to process {model.__name__}: {e}")
            return 1

    # Process enums
    for enum_cls in ENUMS_TO_CONVERT:
        try:
            ts_path = TS_OUTPUT_DIR / f"{enum_cls.__name__}.ts"
            generate_enum_file(enum_cls, ts_path)
        except Exception as e:
            logger.error(f"Failed to process enum {enum_cls.__name__}: {e}")
            return 1

    # Generate index file
    generate_index_file(TS_OUTPUT_DIR, MODELS_TO_CONVERT, ENUMS_TO_CONVERT)

    total = len(MODELS_TO_CONVERT) + len(ENUMS_TO_CONVERT)
    logger.success(f"Generated {total} TypeScript types")
    logger.info(f"Output directory: {TS_OUTPUT_DIR}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
