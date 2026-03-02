"""Pytest fixtures for benchmark tests."""

import json
from pathlib import Path

import pytest

GROUND_TRUTH_DIR = Path(__file__).parent / "ground_truth"


@pytest.fixture
def ground_truth_dir():
    """Return the ground truth directory path."""
    return GROUND_TRUTH_DIR


@pytest.fixture
def broadmeadows_ground_truth():
    """Load Broadmeadows ground truth (31 records, 1 building)."""
    path = GROUND_TRUTH_DIR / "broadmeadows.json"
    if not path.exists():
        pytest.skip(f"Ground truth not found: {path}")
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def alexander_ground_truth():
    """Load Alexander ground truth (43 records, 5 buildings)."""
    path = GROUND_TRUTH_DIR / "alexander.json"
    if not path.exists():
        pytest.skip(f"Ground truth not found: {path}")
    with open(path) as f:
        return json.load(f)
