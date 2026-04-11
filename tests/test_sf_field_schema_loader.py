"""Contract tests for E38-S0 — load_sf_field_schema() reads from the snapshot.

Phase 5 audit (docs/cleanup/phase-5-aggregate-report.md §2.2) found that
config/sf-schema-snapshot.json was INERT at runtime. The picklist validator
and SF normalizer were still enforcing the stale V3/output/*.md schema, so
any E38-S2 field drop would have broken the validator.

E38-S0 wires the snapshot into load_sf_field_schema(). These tests guarantee
the wiring stays correct.
"""

from __future__ import annotations

import importlib


def test_bundle_version_is_v2():
    """Loader must return the snapshot version, not the legacy one."""
    # Re-import to reset the module-level cache between tests
    import open_notebook.extractors.parsers.config_loader as loader
    importlib.reload(loader)

    bundle = loader.load_sf_field_schema()
    assert bundle.version.startswith("salesforce-v2-"), (
        f"Expected snapshot-sourced version starting with 'salesforce-v2-', "
        f"got '{bundle.version}' — loader may have fallen back to legacy markdown"
    )


def test_extractable_field_counts_match_snapshot(sf_schema_snapshot):
    """Field counts must match the snapshot's extractable_fields maps."""
    import open_notebook.extractors.parsers.config_loader as loader
    importlib.reload(loader)

    bundle = loader.load_sf_field_schema()

    expected_building = len(
        sf_schema_snapshot["objects"]["Building__c"]["extractable_fields"]
    )
    expected_item = len(
        sf_schema_snapshot["objects"]["Item__c"]["extractable_fields"]
    )

    assert len(bundle.building_fields.fields) == expected_building
    assert len(bundle.item_fields.fields) == expected_item


def test_field_names_match_snapshot(sf_schema_snapshot):
    """Every field in the bundle must appear in the snapshot's extractable map."""
    import open_notebook.extractors.parsers.config_loader as loader
    importlib.reload(loader)

    bundle = loader.load_sf_field_schema()

    snapshot_building = set(
        sf_schema_snapshot["objects"]["Building__c"]["extractable_fields"].keys()
    )
    snapshot_item = set(
        sf_schema_snapshot["objects"]["Item__c"]["extractable_fields"].keys()
    )

    bundle_building = {f.api_name for f in bundle.building_fields.fields}
    bundle_item = {f.api_name for f in bundle.item_fields.fields}

    assert bundle_building == snapshot_building
    assert bundle_item == snapshot_item


def test_condition_picklist_has_real_sf_values():
    """The Condition__c picklist must contain the real SF values, not BAR values.

    This is the authoritative proof that the snapshot-backed loader is
    returning live-describe data. The legacy markdown loader returned
    BAR-era values; the real SF picklist has 'Stable' instead of 'Good',
    which is the mapping enshrined in config/bar_to_sf_mapping.yaml.
    """
    import open_notebook.extractors.parsers.config_loader as loader
    importlib.reload(loader)

    bundle = loader.load_sf_field_schema()
    condition_values = bundle.picklists.get("Condition__c")
    assert condition_values is not None, "Condition__c picklist missing from bundle"

    # Must include the real SF values
    assert "Stable" in condition_values, (
        f"Condition__c should include 'Stable' (real SF value); "
        f"got {condition_values}"
    )
    assert "Poor" in condition_values
    assert "Fair" in condition_values

    # Must NOT include BAR-era values that don't exist in SF
    assert "Good" not in condition_values, (
        "Condition__c should NOT include 'Good' — that's a BAR term. "
        "The real SF value is 'Stable'. If this test fails, either the "
        "loader fell back to legacy markdown, or the snapshot is stale."
    )


def test_disturbance_picklist_uses_moderate_not_medium():
    """Disturbance_Potential_of_Material__c picklist uses 'Moderate' in SF.

    BAR consultants write 'Medium'; the real SF picklist has 'Moderate'.
    config/bar_to_sf_mapping.yaml encodes the mapping.
    """
    import open_notebook.extractors.parsers.config_loader as loader
    importlib.reload(loader)

    bundle = loader.load_sf_field_schema()
    disturbance = bundle.picklists.get("Disturbance_Potential_of_Material__c")
    assert disturbance is not None

    assert "Moderate" in disturbance
    assert "Medium" not in disturbance, (
        "Disturbance_Potential_of_Material__c should NOT contain 'Medium'. "
        "That's a BAR term; the real SF value is 'Moderate'."
    )


def test_labelled_picklist_uses_mixed_case():
    """Labelled__c picklist uses 'Yes'/'No' (mixed case) in SF, not 'YES'/'NO'."""
    import open_notebook.extractors.parsers.config_loader as loader
    importlib.reload(loader)

    bundle = loader.load_sf_field_schema()
    labelled = bundle.picklists.get("Labelled__c")
    assert labelled is not None

    assert "Yes" in labelled
    assert "No" in labelled
    assert "YES" not in labelled
    assert "NO" not in labelled


def test_dependent_picklist_chains_built():
    """The 3 dependent picklist chains must be present with populated mappings.

    - Building_Type__c (137 values) -> Building_Category__c (13 values)
    - Friability_of_Material__c (2) -> ACM_Classification__c (18)
    - ACM_Classification__c (18) -> ACM_Sub_Classification__c (133)
    """
    import open_notebook.extractors.parsers.config_loader as loader
    importlib.reload(loader)

    bundle = loader.load_sf_field_schema()

    chains_by_dependent = {c.dependent_api_name: c for c in bundle.dependencies}

    assert "Building_Category__c" in chains_by_dependent
    assert chains_by_dependent["Building_Category__c"].controller_api_name == "Building_Type__c"

    assert "ACM_Classification__c" in chains_by_dependent
    assert (
        chains_by_dependent["ACM_Classification__c"].controller_api_name
        == "Friability_of_Material__c"
    )

    assert "ACM_Sub_Classification__c" in chains_by_dependent
    assert (
        chains_by_dependent["ACM_Sub_Classification__c"].controller_api_name
        == "ACM_Classification__c"
    )

    # Every chain should have a non-empty mapping (the curated pairings).
    # Empty mappings would indicate a chain discovered in the describe but
    # with no curated builder — that's a warning state the parent session
    # should look into.
    for chain in bundle.dependencies:
        assert chain.mapping, (
            f"Dependency chain {chain.controller_api_name} -> "
            f"{chain.dependent_api_name} has empty mapping. Add a builder "
            f"in config_loader.py or supply the pairing table."
        )


def test_every_field_def_has_required_attributes():
    """Every SFFieldDef in the bundle must have the attributes callers depend on."""
    import open_notebook.extractors.parsers.config_loader as loader
    importlib.reload(loader)

    bundle = loader.load_sf_field_schema()

    for obj_config in (bundle.building_fields, bundle.item_fields):
        for f in obj_config.fields:
            assert f.api_name, f"field missing api_name: {f}"
            assert f.label, f"field missing label: {f.api_name}"
            assert f.field_type, f"field missing field_type: {f.api_name}"
            assert isinstance(f.nillable, bool)
            assert isinstance(f.is_restricted_picklist, bool)
            assert isinstance(f.is_dependent, bool)


def test_loader_is_cached():
    """Second call returns the same instance (module-level cache)."""
    import open_notebook.extractors.parsers.config_loader as loader
    importlib.reload(loader)

    b1 = loader.load_sf_field_schema()
    b2 = loader.load_sf_field_schema()
    assert b1 is b2, "load_sf_field_schema() should return a cached instance"
