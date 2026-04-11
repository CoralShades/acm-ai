"""Smoke tests for the core domain models + key module imports.

If any of these fail, the branch is broken at import time and no other
test can run. Keep them trivially fast.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

# ---------------------------------------------------------------------------
# Import smoke — catches syntax errors / bad references in the hot path
# ---------------------------------------------------------------------------


def test_domain_acm_imports():
    import open_notebook.domain.acm  # noqa: F401


def test_sf_export_imports():
    import open_notebook.extractors.exporters.sf_export  # noqa: F401


def test_acm_extraction_graph_imports():
    """acm_extraction.py is the load-bearing file Phase 2a surgically edited."""
    import open_notebook.graphs.acm_extraction  # noqa: F401


def test_observability_config_imports():
    import open_notebook.observability.langfuse_config  # noqa: F401
    import open_notebook.observability.logfire_config  # noqa: F401


# ---------------------------------------------------------------------------
# BuildingRecord
# ---------------------------------------------------------------------------


def test_building_record_instantiates(sample_building_dict):
    from open_notebook.domain.acm import BuildingRecord
    b = BuildingRecord(**sample_building_dict)
    assert b.internal_id == "BLD#test_001"
    assert b.source_id == "source:test_fixture"


def test_building_record_requires_internal_id():
    from open_notebook.domain.acm import BuildingRecord
    with pytest.raises(ValidationError):
        BuildingRecord(source_id="source:abc")


def test_building_record_requires_source_id():
    from open_notebook.domain.acm import BuildingRecord
    with pytest.raises(ValidationError):
        BuildingRecord(internal_id="BLD#1")


def test_building_record_rejects_bad_internal_id_prefix():
    """acm.py:953 enforces internal_id must start with 'BLD#'."""
    from open_notebook.domain.acm import BuildingRecord
    from open_notebook.exceptions import InvalidInputError
    with pytest.raises(InvalidInputError):
        BuildingRecord(internal_id="bld_wrong_prefix", source_id="source:abc")


def test_building_record_accepts_optional_fields(sample_building_dict):
    from open_notebook.domain.acm import BuildingRecord
    b = BuildingRecord(
        **sample_building_dict,
        building_name="Broadmeadows Police Station",
        building_type="Police Station",
        suburb="Broadmeadows",
        postcode="3047",
    )
    assert b.building_name == "Broadmeadows Police Station"
    assert b.suburb == "Broadmeadows"


# ---------------------------------------------------------------------------
# ACMRecord
# ---------------------------------------------------------------------------


def test_acm_record_instantiates(sample_acm_dict):
    from open_notebook.domain.acm import ACMRecord
    r = ACMRecord(**sample_acm_dict)
    assert r.product == "Floor covering"
    assert r.source_id == "source:test_fixture"
    assert r.building_id == "BLD#test_001"


def test_acm_record_requires_source_id(sample_acm_dict):
    from open_notebook.domain.acm import ACMRecord
    del sample_acm_dict["source_id"]
    with pytest.raises(ValidationError):
        ACMRecord(**sample_acm_dict)


def test_acm_record_requires_building_id(sample_acm_dict):
    from open_notebook.domain.acm import ACMRecord
    del sample_acm_dict["building_id"]
    with pytest.raises(ValidationError):
        ACMRecord(**sample_acm_dict)


def test_acm_record_validation_errors_tracked(sample_acm_dict):
    from open_notebook.domain.acm import ACMRecord
    r = ACMRecord(**sample_acm_dict)
    assert r.validation_errors == []
    assert r.correction_attempts == 0
