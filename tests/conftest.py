"""Shared fixtures for the Phase 3A rebuilt test suite.

All fixtures are pure-Python file loads with no DB, no network, no LLM.
If a test needs a running service, it belongs in the E38-S3 incremental
rebuild, not here.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
SF_DESCRIBE_DIR = REPO_ROOT / "docs" / "sprint-artifacts" / "full-audit-2026-04-11" / "sf-describe"
CONFIG_DIR = REPO_ROOT / "config"


@pytest.fixture(scope="session")
def sf_describe_building() -> dict:
    """Raw SF describe JSON for Building__c from the 2026-04-11 audit."""
    path = SF_DESCRIBE_DIR / "Building__c.json"
    return json.loads(path.read_text())


@pytest.fixture(scope="session")
def sf_describe_item() -> dict:
    """Raw SF describe JSON for Item__c from the 2026-04-11 audit."""
    path = SF_DESCRIBE_DIR / "Item__c.json"
    return json.loads(path.read_text())


@pytest.fixture(scope="session")
def sf_schema_snapshot() -> dict:
    """Compact runtime schema snapshot at config/sf-schema-snapshot.json."""
    path = CONFIG_DIR / "sf-schema-snapshot.json"
    return json.loads(path.read_text())


@pytest.fixture(scope="session")
def bar_mapping() -> dict:
    """Deterministic BAR->SF vocabulary mapping at config/bar_to_sf_mapping.yaml."""
    path = CONFIG_DIR / "bar_to_sf_mapping.yaml"
    return yaml.safe_load(path.read_text())


@pytest.fixture
def sample_building_dict() -> dict:
    """Minimal valid kwargs for constructing a BuildingRecord.

    `internal_id` must start with `BLD#` (validated in acm.py:953).
    """
    return {
        "internal_id": "BLD#test_001",
        "source_id": "source:test_fixture",
    }


@pytest.fixture
def sample_acm_dict() -> dict:
    """Minimal valid kwargs for constructing an ACMRecord."""
    return {
        "source_id": "source:test_fixture",
        "building_id": "BLD#test_001",
        "product": "Floor covering",
        "material_description": "Vinyl sheet",
        "result": "Negative",
    }
