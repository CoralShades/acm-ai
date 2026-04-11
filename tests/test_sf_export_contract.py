"""Contract tests for open_notebook/extractors/exporters/sf_export.py.

THIS is the test that would have caught the Phase 2b bug: ~21 fabricated
SF field names in ITEM_SF_MAPPING that didn't exist in the live Salesforce
schema. Without these tests the export would happily produce CSVs that
Data Loader would reject on every row.

Rule: every SF field name in the mapping tables MUST exist in the raw
SF describe dump. Every Python attribute on the right side MUST exist
on the corresponding domain model.
"""

from __future__ import annotations

import pytest

# ---------------------------------------------------------------------------
# Imports delayed into test bodies so import errors surface as test failures
# rather than collection errors.
# ---------------------------------------------------------------------------


def _describe_field_names(describe: dict) -> set[str]:
    return {f["name"] for f in describe["fields"]}


def _model_field_names(model_cls) -> set[str]:
    return set(model_cls.model_fields.keys())


# ---------------------------------------------------------------------------
# Building__c mapping contract
# ---------------------------------------------------------------------------


def test_building_sf_mapping_is_non_empty():
    from open_notebook.extractors.exporters.sf_export import BUILDING_SF_MAPPING
    assert len(BUILDING_SF_MAPPING) > 0


def test_building_sf_mapping_uses_real_sf_fields(sf_describe_building):
    """Every SF name in BUILDING_SF_MAPPING must exist on Building__c."""
    from open_notebook.extractors.exporters.sf_export import BUILDING_SF_MAPPING

    real_fields = _describe_field_names(sf_describe_building)
    missing = []
    for sf_name, _python_field in BUILDING_SF_MAPPING:
        if "." in sf_name:
            # Relationship lookup syntax (e.g., Building__r.External_ID__c)
            continue
        if sf_name not in real_fields:
            missing.append(sf_name)

    assert not missing, (
        f"BUILDING_SF_MAPPING references {len(missing)} fabricated SF field names "
        f"that do not exist on Building__c: {missing}"
    )


def test_building_sf_mapping_python_fields_exist_on_model():
    from open_notebook.domain.acm import BuildingRecord
    from open_notebook.extractors.exporters.sf_export import BUILDING_SF_MAPPING

    model_fields = _model_field_names(BuildingRecord)
    missing = []
    for sf_name, python_field in BUILDING_SF_MAPPING:
        if python_field not in model_fields:
            missing.append((sf_name, python_field))

    assert not missing, (
        f"BUILDING_SF_MAPPING references {len(missing)} Python fields that do "
        f"not exist on BuildingRecord: {missing}"
    )


def test_building_sf_mapping_includes_required_fields(sf_schema_snapshot):
    """The export CSV must include the SF required fields — Data Loader will
    reject any row missing one of them."""
    from open_notebook.extractors.exporters.sf_export import BUILDING_SF_MAPPING

    mapped_sf_names = {sf for sf, _ in BUILDING_SF_MAPPING}
    required = set(sf_schema_snapshot["objects"]["Building__c"]["required_custom_fields"])
    # Organisation__c is a reference lookup populated at export time via site_config, not mapping
    required.discard("Organisation__c")
    missing = required - mapped_sf_names
    assert not missing, f"BUILDING_SF_MAPPING missing required fields: {missing}"


# ---------------------------------------------------------------------------
# Item__c mapping contract
# ---------------------------------------------------------------------------


def test_item_sf_mapping_is_non_empty():
    from open_notebook.extractors.exporters.sf_export import ITEM_SF_MAPPING
    assert len(ITEM_SF_MAPPING) > 0


def test_item_sf_mapping_uses_real_sf_fields(sf_describe_item):
    """The regression test that would have caught the Phase 2b bug."""
    from open_notebook.extractors.exporters.sf_export import ITEM_SF_MAPPING

    real_fields = _describe_field_names(sf_describe_item)
    missing = []
    for sf_name, _python_field in ITEM_SF_MAPPING:
        if "." in sf_name:
            continue  # relationship lookup syntax
        if sf_name not in real_fields:
            missing.append(sf_name)

    assert not missing, (
        f"ITEM_SF_MAPPING references {len(missing)} fabricated SF field names "
        f"that do not exist on Item__c: {missing}"
    )


def test_item_sf_mapping_python_fields_exist_on_model():
    from open_notebook.domain.acm import ACMRecord
    from open_notebook.extractors.exporters.sf_export import ITEM_SF_MAPPING

    model_fields = _model_field_names(ACMRecord)
    missing = []
    for sf_name, python_field in ITEM_SF_MAPPING:
        # The building_external_id placeholder is injected at export time,
        # not stored on ACMRecord — skip it.
        if python_field == "building_external_id":
            continue
        if python_field not in model_fields:
            missing.append((sf_name, python_field))

    assert not missing, (
        f"ITEM_SF_MAPPING references {len(missing)} Python fields that do "
        f"not exist on ACMRecord: {missing}"
    )


def test_item_mapping_uses_building_r_external_id_for_parent():
    """Item__c.External_ID__c is misconfigured in demidev; the parent link
    must flow through Building__r.External_ID__c instead."""
    from open_notebook.extractors.exporters.sf_export import ITEM_SF_MAPPING

    sf_names = {sf for sf, _ in ITEM_SF_MAPPING}
    assert "Building__r.External_ID__c" in sf_names


# ---------------------------------------------------------------------------
# Header helpers
# ---------------------------------------------------------------------------


def test_header_helpers_return_ordered_lists():
    from open_notebook.extractors.exporters.sf_export import (
        BUILDING_SF_MAPPING,
        ITEM_SF_MAPPING,
        get_building_sf_headers,
        get_item_sf_headers,
    )

    building_headers = get_building_sf_headers()
    assert building_headers == [sf for sf, _ in BUILDING_SF_MAPPING]

    item_headers = get_item_sf_headers()
    assert item_headers == [sf for sf, _ in ITEM_SF_MAPPING]


def test_headers_are_unique():
    from open_notebook.extractors.exporters.sf_export import (
        get_building_sf_headers,
        get_item_sf_headers,
    )

    bh = get_building_sf_headers()
    assert len(bh) == len(set(bh)), "duplicate SF column headers in Building mapping"

    ih = get_item_sf_headers()
    assert len(ih) == len(set(ih)), "duplicate SF column headers in Item mapping"
