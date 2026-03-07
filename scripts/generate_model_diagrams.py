#!/usr/bin/env python3
"""Generate ER diagrams for ACM-AI Pydantic models.

Requires: erdantic (dev dependency) + Graphviz system install.
  Windows: winget install graphviz
  macOS: brew install graphviz
  Linux: apt install graphviz

Usage:
  uv run python scripts/generate_model_diagrams.py
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path so `api` package is importable
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

OUTPUT_DIR = Path("docs/diagrams")


def generate_all():
    try:
        import erdantic as erd
    except ImportError:
        print(
            "erdantic not installed. Run: uv pip install erdantic (requires pygraphviz + Graphviz)"
        )
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    diagrams = {}

    # Extraction schemas (BaseModel)
    try:
        from open_notebook.extractors.acm_schemas import ACMExtractionResult

        diagrams["extraction_schemas"] = ACMExtractionResult
    except ImportError as e:
        print(f"Skipping extraction_schemas: {e}")

    # V3 schemas
    try:
        from open_notebook.extractors.acm_schemas_v3 import (
            ACMItemExtractionResult,
        )

        diagrams["v3_schemas"] = ACMItemExtractionResult
    except ImportError as e:
        print(f"Skipping v3_schemas: {e}")

    # Domain models
    try:
        from open_notebook.domain.acm import ACMRecord, BuildingRecord

        diagrams["domain_acm"] = ACMRecord
        diagrams["domain_building"] = BuildingRecord
    except ImportError as e:
        print(f"Skipping domain models: {e}")

    # Provider/consensus models
    try:
        from open_notebook.extractors.providers.base import (
            NormalizedExtractionResult,
        )

        diagrams["provider_models"] = NormalizedExtractionResult
    except ImportError as e:
        print(f"Skipping provider models: {e}")

    # API response models
    try:
        from api.models import ACMRecordResponse, SourceResponse

        diagrams["api_acm"] = ACMRecordResponse
        diagrams["api_source"] = SourceResponse
    except ImportError as e:
        print(f"Skipping API models: {e}")

    if not diagrams:
        print("No models could be imported. Check your environment.")
        return

    for name, model in diagrams.items():
        out_path = OUTPUT_DIR / f"{name}.svg"
        try:
            erd.draw(model, out=str(out_path))
            print(f"  {out_path}")
        except Exception as e:
            print(f"  FAILED {name}: {e}")

    print(f"\nDiagrams generated in {OUTPUT_DIR}/")


if __name__ == "__main__":
    generate_all()
