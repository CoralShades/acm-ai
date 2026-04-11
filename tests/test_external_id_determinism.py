"""Stability tests for generate_external_id().

Re-extracting the same PDF must produce identical External_ID__c values
so SF upsert updates in place instead of creating duplicate records.
Without determinism, every re-run would fork history.
"""

from __future__ import annotations

import re
from types import SimpleNamespace

from open_notebook.extractors.exporters.sf_export import generate_external_id

HASH_PATTERN = re.compile(r"^ACM_[0-9a-f]{16}$")


def _building(name=None, external_id=None, unique_id=None, building_code=None, internal_id=None):
    return SimpleNamespace(
        building_name=name,
        external_id=external_id,
        building_unique_id=unique_id,
        building_code=building_code,
        internal_id=internal_id,
    )


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


def test_same_input_produces_same_id():
    b1 = _building(name="Broadmeadows Police Station")
    b2 = _building(name="Broadmeadows Police Station")
    assert generate_external_id(b1, "source:abc123") == generate_external_id(b2, "source:abc123")


def test_different_source_produces_different_id():
    b = _building(name="Broadmeadows Police Station")
    id_a = generate_external_id(b, "source:abc123")
    id_b = generate_external_id(b, "source:xyz789")
    assert id_a != id_b


def test_different_building_name_produces_different_id():
    b1 = _building(name="Broadmeadows Police Station")
    b2 = _building(name="Alexander District Hospital")
    assert generate_external_id(b1, "source:same") != generate_external_id(b2, "source:same")


def test_id_is_stable_across_many_invocations():
    """Calling the same inputs 100 times must produce the exact same value."""
    b = _building(name="Test Building")
    first = generate_external_id(b, "source:stability_test")
    for _ in range(100):
        assert generate_external_id(b, "source:stability_test") == first


# ---------------------------------------------------------------------------
# Format
# ---------------------------------------------------------------------------


def test_generated_id_matches_hash_format():
    b = _building(name="Broadmeadows Police Station")
    assert HASH_PATTERN.match(generate_external_id(b, "source:abc123"))


def test_id_length_within_sf_limit():
    """Building__c.External_ID__c is Text(255). Generated IDs must fit."""
    b = _building(name="A" * 10000)  # pathologically long name
    result = generate_external_id(b, "source:" + "B" * 10000)
    assert len(result) <= 255


# ---------------------------------------------------------------------------
# Resolution order
# ---------------------------------------------------------------------------


def test_stored_external_id_is_honoured():
    """If building.external_id is already set, use it verbatim."""
    b = _building(name="anything", external_id="PRE_SET_ID")
    assert generate_external_id(b, "source:abc") == "PRE_SET_ID"


def test_stored_building_unique_id_used_when_no_external_id():
    b = _building(name="anything", unique_id="CONSULTANT_ID_42")
    assert generate_external_id(b, "source:abc") == "CONSULTANT_ID_42"


def test_hash_fallback_when_no_stored_ids():
    """With neither external_id nor building_unique_id, fall back to hash."""
    b = _building(name="Broadmeadows")
    result = generate_external_id(b, "source:abc")
    assert HASH_PATTERN.match(result)


def test_external_id_takes_precedence_over_unique_id():
    b = _building(name="anything", external_id="WINS", unique_id="LOSES")
    assert generate_external_id(b, "source:abc") == "WINS"
