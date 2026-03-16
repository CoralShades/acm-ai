"""
SF Picklist Normalization for ACMExtractionRecord objects.

Normalizes enum fields to SF-canonical values before validation,
eliminating unnecessary LLM correction calls for trivial picklist mismatches.
"""

from typing import Optional

from loguru import logger


def normalize_extraction_record(record, schema_bundle=None) -> list[str]:
    """Normalize all SF picklist fields on an ACMExtractionRecord in-place.

    Steps:
    1. Build dict from record attributes
    2. Apply normalize_record_to_sf() for SF picklist normalization
    3. Apply normalize_enum_value() for remaining synonym expansion
    4. Business rule: negative results clear condition/disturbance
    5. Write modified values back to record attributes
    6. Append change notes to record.data_issues

    Args:
        record: ACMExtractionRecord instance (mutated in-place).
        schema_bundle: Optional pre-loaded SFSchemaBundle.

    Returns:
        List of modified field names.
    """
    modified: list[str] = []

    try:
        # Fields to normalize
        field_names = [
            "sample_result",
            "material_condition",
            "friable",
            "disturbance_potential",
        ]

        # Snapshot original values
        originals = {}
        for f in field_names:
            originals[f] = getattr(record, f, None)

        # Build dict for normalize_record_to_sf
        record_dict = {f: originals[f] for f in field_names if originals[f] is not None}

        # Step 1: SF picklist normalization (case + value mapping)
        try:
            from open_notebook.extractors.validators.sf_picklist_validator import (
                normalize_record_to_sf,
            )

            normalize_record_to_sf(record_dict, schema_bundle)
        except (ImportError, OSError) as e:
            logger.debug(f"SF normalization skipped (schema unavailable): {e}")

        # Step 2: Synonym expansion for fields not yet fixed
        from open_notebook.extractors.normalizers.enums import normalize_enum_value

        enum_field_map = {
            "sample_result": "sample_result",
            "material_condition": "condition",
            "friable": "friability",
            "disturbance_potential": "disturbance_potential",
        }
        for field_name, enum_key in enum_field_map.items():
            current = record_dict.get(field_name, originals[field_name])
            if current is None:
                continue
            normalized = normalize_enum_value(current, enum_key)
            if normalized != current:
                record_dict[field_name] = normalized

        # Step 3: Business rule — negative results clear condition/disturbance
        result_val = record_dict.get("sample_result") or getattr(record, "result", None)
        if result_val in {"Negative", "Assumed Negative"}:
            na_value = (
                "N/A (negative)"
                if result_val == "Negative"
                else "N/A (assumed negative)"
            )
            for clear_field in ("material_condition", "disturbance_potential"):
                current = record_dict.get(clear_field, originals.get(clear_field))
                if current and current not in {
                    "N/A (negative)",
                    "N/A (assumed negative)",
                }:
                    record_dict[clear_field] = na_value

        # Step 4: Write back modified values and track changes
        change_messages: list[str] = []
        for f in field_names:
            new_val = record_dict.get(f)
            old_val = originals[f]
            if new_val is not None and new_val != old_val:
                setattr(record, f, new_val)
                modified.append(f)
                change_messages.append(f"SF normalized: {f} '{old_val}' -> '{new_val}'")

        # Step 5: Append to data_issues (non-fatal)
        if change_messages:
            try:
                existing = getattr(record, "data_issues", None)
                if existing is None:
                    existing = []
                elif isinstance(existing, str):
                    existing = [existing] if existing.strip() else []
                else:
                    existing = list(existing)
                for msg in change_messages:
                    if msg not in existing:
                        existing.append(msg)
                record.data_issues = existing
            except Exception:
                pass  # data_issues tracking is best-effort

    except Exception as e:
        logger.warning(f"SF normalization failed (non-fatal): {e}")

    return modified


def normalize_extraction_records(records, schema_bundle=None) -> dict[str, int]:
    """Batch normalize SF picklist fields on a list of ACMExtractionRecords.

    Args:
        records: List of ACMExtractionRecord instances.
        schema_bundle: Optional pre-loaded SFSchemaBundle.

    Returns:
        Stats dict: {total_records, records_modified, fields_modified}
    """
    total = len(records)
    records_modified = 0
    fields_modified = 0

    # Pre-load schema bundle once for all records
    loaded_bundle: Optional[object] = schema_bundle
    if loaded_bundle is None:
        try:
            from open_notebook.extractors.parsers.config_loader import (
                load_sf_field_schema,
            )

            loaded_bundle = load_sf_field_schema()
        except (ImportError, OSError) as e:
            logger.debug(f"SF schema unavailable for batch normalization: {e}")

    for record in records:
        changed = normalize_extraction_record(record, loaded_bundle)
        if changed:
            records_modified += 1
            fields_modified += len(changed)

    return {
        "total_records": total,
        "records_modified": records_modified,
        "fields_modified": fields_modified,
    }
