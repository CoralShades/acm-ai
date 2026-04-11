"""Invariants for config/bar_to_sf_mapping.yaml.

The mapping table is the only allowed form of value transformation under
the literal-only extraction rule (DEC-005). These tests assert the table
is well-formed and every non-null right-hand value is a legitimate SF
picklist value per the snapshot.
"""

from __future__ import annotations


def test_mapping_has_both_object_sections(bar_mapping):
    assert "Building__c" in bar_mapping
    assert "Item__c" in bar_mapping


def test_condition_good_maps_to_stable(bar_mapping):
    """PRD FR-1405 contract, verified against live picklist 2026-04-11."""
    assert bar_mapping["Item__c"]["Condition__c"]["Good"] == "Stable"


def test_disturbance_medium_maps_to_moderate(bar_mapping):
    """CSV says 'Medium', SF picklist says 'Moderate'."""
    assert bar_mapping["Item__c"]["Disturbance_Potential_of_Material__c"]["Medium"] == "Moderate"


def test_yes_no_case_normalized(bar_mapping):
    """CSV uses 'YES'/'NO' caps, SF picklist uses 'Yes'/'No' mixed case."""
    assert bar_mapping["Item__c"]["Labelled__c"]["YES"] == "Yes"
    assert bar_mapping["Item__c"]["Labelled__c"]["NO"] == "No"
    assert bar_mapping["Building__c"]["Public_Access__c"]["YES"] == "Yes"
    assert bar_mapping["Building__c"]["Public_Access__c"]["NO"] == "No"


def test_building_yes_no_fields_all_normalized(bar_mapping):
    """All boolean-picklist Building__c fields should normalize YES/NO."""
    yes_no_fields = [
        "Public_Access__c",
        "Asbestos_Register_Available__c",
        "Audit_Report_Available__c",
        "Within_Your_Portfolio__c",
    ]
    for field in yes_no_fields:
        assert field in bar_mapping["Building__c"], f"missing field: {field}"
        assert bar_mapping["Building__c"][field].get("YES") == "Yes"
        assert bar_mapping["Building__c"][field].get("NO") == "No"


def test_all_nonnull_targets_are_valid_sf_picklist_values(bar_mapping, sf_schema_snapshot):
    """CRITICAL: every right-side value (where not null) must appear in the
    SF picklist values for that field per the snapshot. Catches drift
    between the mapping table and the SF schema."""
    errors = []

    for obj_name in ("Item__c", "Building__c"):
        obj_mapping = bar_mapping.get(obj_name, {})
        obj_schema = sf_schema_snapshot["objects"][obj_name]["extractable_fields"]

        for field_name, translations in obj_mapping.items():
            if not isinstance(translations, dict):
                continue
            field_schema = obj_schema.get(field_name, {})
            valid_values = field_schema.get("values")
            if not valid_values:
                # Field isn't in the extractable set, or is an open picklist,
                # or the snapshot only recorded value_count without values
                continue

            valid_set = set(valid_values)
            for bar_value, sf_value in translations.items():
                if sf_value is None:
                    continue
                if sf_value not in valid_set:
                    errors.append(
                        f"{obj_name}.{field_name}: '{bar_value}' -> '{sf_value}' "
                        f"is not in SF picklist {valid_set}"
                    )

    assert not errors, "BAR->SF mapping values drift from SF schema:\n" + "\n".join(errors)


def test_drop_values_section_present(bar_mapping):
    """Tests that the drop_values list (values filtered from SF payload) exists."""
    assert "drop_values" in bar_mapping
    assert isinstance(bar_mapping["drop_values"], list)
    assert len(bar_mapping["drop_values"]) > 0


def test_mapping_left_side_values_are_strings(bar_mapping):
    """YAML coerces some keys to non-string types; ensure all mapping keys are strings."""
    for obj_name in ("Item__c", "Building__c"):
        for field_name, translations in bar_mapping.get(obj_name, {}).items():
            if not isinstance(translations, dict):
                continue
            for bar_value in translations.keys():
                assert isinstance(bar_value, str), (
                    f"{obj_name}.{field_name}: key {bar_value!r} is {type(bar_value).__name__}, expected str"
                )
