"""Integrity checks for config/sf-schema-snapshot.json.

The snapshot is the runtime compact projection of the raw SF describe
dumps. These tests ensure it stays consistent with the raw source of
truth at docs/sprint-artifacts/full-audit-2026-04-11/sf-describe/.
"""

from __future__ import annotations

import pytest


def test_snapshot_has_required_top_level_keys(sf_schema_snapshot):
    required = {"version", "generated", "generated_from", "objects", "dependent_picklist_chains"}
    missing = required - set(sf_schema_snapshot.keys())
    assert not missing, f"snapshot missing top-level keys: {missing}"


def test_snapshot_covers_building_and_item(sf_schema_snapshot):
    assert "Building__c" in sf_schema_snapshot["objects"]
    assert "Item__c" in sf_schema_snapshot["objects"]


def test_building_section_shape(sf_schema_snapshot):
    building = sf_schema_snapshot["objects"]["Building__c"]
    assert building["api_name"] == "Building__c"
    assert building["upsert_key"]["usable_for_upsert"] is True
    assert building["upsert_key"]["field"] == "External_ID__c"
    assert "required_custom_fields" in building
    assert "extractable_fields" in building
    assert len(building["extractable_fields"]) > 0


def test_item_section_documents_upsert_blocker(sf_schema_snapshot):
    """Item__c.External_ID__c is misconfigured in demidev. The snapshot
    MUST document this so downstream code can branch on it."""
    item = sf_schema_snapshot["objects"]["Item__c"]
    assert item["upsert_key"]["usable_for_upsert"] is False
    assert "blocker" in item["upsert_key"]
    assert item["upsert_key"]["blocker"]  # non-empty


def test_item_parent_relationship_is_master_detail(sf_schema_snapshot):
    item = sf_schema_snapshot["objects"]["Item__c"]
    parent = item["parent_relationship"]
    assert parent["field"] == "Building_Code__c"
    assert parent["parent_object"] == "Building__c"
    assert parent["type"] == "master-detail"
    assert parent["cascade_delete"] is True
    assert parent["required"] is True


@pytest.mark.parametrize("obj_name,describe_fixture", [
    ("Building__c", "sf_describe_building"),
    ("Item__c", "sf_describe_item"),
])
def test_every_extractable_field_exists_in_raw_describe(
    obj_name, describe_fixture, sf_schema_snapshot, request
):
    """Every field name in extractable_fields must appear in the raw describe."""
    describe = request.getfixturevalue(describe_fixture)
    describe_field_names = {f["name"] for f in describe["fields"]}

    snapshot_fields = sf_schema_snapshot["objects"][obj_name]["extractable_fields"]
    missing = set(snapshot_fields.keys()) - describe_field_names
    assert not missing, (
        f"{obj_name} snapshot references fields not in raw describe: {missing}"
    )


def test_dependent_picklist_chains_are_documented(sf_schema_snapshot):
    chains = sf_schema_snapshot["dependent_picklist_chains"]
    assert len(chains) >= 2

    chain_strings = [" -> ".join(c["chain"]) for c in chains]
    assert any("Friability_of_Material__c" in s and "ACM_Classification__c" in s for s in chain_strings)
    assert any("Building_Type__c" in s and "Building_Category__c" in s for s in chain_strings)


def test_friability_chain_matches_describe(sf_schema_snapshot, sf_describe_item):
    """The controller/dependent relationship in the snapshot must match the
    actual controllerName / dependentPicklist flags in the describe."""
    fields_by_name = {f["name"]: f for f in sf_describe_item["fields"]}

    acm_class = fields_by_name["ACM_Classification__c"]
    assert acm_class["controllerName"] == "Friability_of_Material__c"
    assert acm_class["dependentPicklist"] is True

    sub_class = fields_by_name["ACM_Sub_Classification__c"]
    assert sub_class["controllerName"] == "ACM_Classification__c"
    assert sub_class["dependentPicklist"] is True
