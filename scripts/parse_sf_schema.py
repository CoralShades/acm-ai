"""
Parse Salesforce object descriptor files and generate a JSON schema file.

Input files:
  - V3/building-list.txt  (Building__c object)
  - V3/item-list.txt      (Item__c object)

Output:
  - output/salesforce_field_schema.json

File format (no indentation, no line-number prefix):
  Fields (143)
  FieldApiName__c
  aggregatable: true
  ...
  label: Some Label
  name: FieldApiName__c
  nillable: true
  type: string
  ...
  Picklist Values (N)
  ValueLabel
  active: true
  defaultValue: false
  label: ValueLabel
  value: ValueLabel
  NextField__c
  aggregatable: true
  ...
"""

import json
import re
import sys
from pathlib import Path


def col_letter(n: int) -> str:
    """Convert 1-based column number to Excel letter(s)."""
    result = ""
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        result = chr(65 + remainder) + result
    return result


def is_field_name_line(line: str, next_nonempty: str) -> bool:
    """
    A field name line has no colon in it and is followed by 'aggregatable:' on
    the next non-empty line.
    """
    return (
        bool(line)
        and ":" not in line
        and next_nonempty.startswith("aggregatable:")
    )


def get_next_nonempty(lines: list[str], start: int) -> str:
    """Return the stripped content of the next non-empty line from start."""
    for j in range(start, len(lines)):
        s = lines[j].strip()
        if s:
            return s
    return ""


def parse_sf_descriptor(filepath: str) -> list[dict]:
    """Parse a Salesforce object descriptor file and return a list of field dicts."""
    with open(filepath, "r", encoding="utf-8") as f:
        raw_lines = f.readlines()

    # Strip any Read-tool line-number prefix (format: "   N→content")
    # Also strip trailing newlines.
    lines: list[str] = []
    for line in raw_lines:
        match = re.match(r"^\s*\d+\u2192(.*)$", line)
        if match:
            lines.append(match.group(1))
        else:
            lines.append(line.rstrip("\n"))

    # Find where the Fields section starts.
    fields_start = -1
    for i, line in enumerate(lines):
        if re.match(r"^Fields \(\d+\)", line.strip()):
            fields_start = i + 1
            break

    if fields_start == -1:
        print(f"WARNING: Could not find 'Fields (N)' in {filepath}", file=sys.stderr)
        return []

    field_lines = lines[fields_start:]
    n = len(field_lines)

    fields: list[dict] = []
    i = 0

    while i < n:
        raw = field_lines[i]
        line = raw.strip()

        # Determine next non-empty line for look-ahead
        nxt = get_next_nonempty(field_lines, i + 1)

        if not is_field_name_line(line, nxt):
            i += 1
            continue

        # ---- Start of a new field ----
        field: dict = {
            "name": line,
            "label": "",
            "type": "",
            "nillable": True,
            "custom": False,
            "calculated": False,
            "updateable": False,
            "referenceTo": [],
            "picklist_values": [],
        }

        i += 1  # move past the field-name line

        while i < n:
            raw = field_lines[i]
            attr = raw.strip()

            if not attr:
                i += 1
                continue

            # Check whether this line starts a new field
            nxt = get_next_nonempty(field_lines, i + 1)
            if is_field_name_line(attr, nxt):
                # Do NOT advance i — outer loop will handle it
                break

            # ---- Section headers without colons — check before the colon test ----

            # "Reference To (N)" — multi-value reference list
            # Lines following are bare object names (no colon) until next field.
            if attr.startswith("Reference To"):
                i += 1
                while i < n:
                    rline = field_lines[i].strip()
                    if not rline:
                        i += 1
                        continue
                    rnxt = get_next_nonempty(field_lines, i + 1)
                    if is_field_name_line(rline, rnxt):
                        break  # new field — do NOT advance i
                    if ":" not in rline and not rline.startswith("Picklist Values"):
                        # Bare object name
                        if rline:
                            field["referenceTo"].append(rline)
                        i += 1
                        continue
                    # Hit an attribute line — stop the reference-to block
                    break
                continue

            # Line looks like: "Picklist Values (N)"
            if attr.startswith("Picklist Values"):
                i += 1
                # Parse each picklist value block until we hit a new field or
                # fall out of the picklist section.
                while i < n:
                    pline = field_lines[i].strip()

                    if not pline:
                        i += 1
                        continue

                    # Check for new field boundary
                    pnxt = get_next_nonempty(field_lines, i + 1)
                    if is_field_name_line(pline, pnxt):
                        break  # new field starts — do NOT advance i

                    if ":" not in pline:
                        # Picklist value label line (e.g. "Yes", "No",
                        # "Alpine Shire Council") — skip; we collect 'value:'
                        i += 1
                        continue

                    pkey, _, pval = pline.partition(":")
                    pkey = pkey.strip()
                    pval = pval.strip()

                    if pkey == "value" and pval:
                        field["picklist_values"].append(pval)
                    # Skip active, defaultValue, label, validFor, etc.
                    i += 1

                # After the picklist inner loop, i points at the next field
                # name (or end of file).  Do NOT increment here.
                continue

            if ":" not in attr:
                # Not an attribute, not a field name, not a picklist header →
                # unknown / skip (should not normally occur in outer loop).
                i += 1
                continue

            # ---- Key:value attribute parsing ----
            key, _, val = attr.partition(":")
            key = key.strip()
            val = val.strip()

            if key == "label":
                field["label"] = val
            elif key == "name":
                # 'name' attribute echoes the API name — we already have it
                pass
            elif key == "type":
                field["type"] = val
            elif key == "nillable":
                field["nillable"] = val == "true"
            elif key == "custom":
                field["custom"] = val == "true"
            elif key == "calculated":
                field["calculated"] = val == "true"
            elif key == "updateable":
                field["updateable"] = val == "true"
            elif key == "referenceTo":
                if val:
                    field["referenceTo"].append(val)
            # All other attributes (aggregatable, byteLength, …) are ignored.

            i += 1

        fields.append(field)
        # i is already positioned at the next candidate line (do not increment)

    return fields


# ---------------------------------------------------------------------------
# Salesforce → JSON Schema type mapping
# ---------------------------------------------------------------------------

SF_TYPE_MAP: dict[str, str] = {
    "string": "string",
    "picklist": "string",
    "multipicklist": "string",
    "textarea": "string",
    "richtextarea": "string",
    "encryptedstring": "string",
    "email": "string",
    "phone": "string",
    "url": "string",
    "id": "string",
    "reference": "string",
    "boolean": "boolean",
    "double": "number",
    "currency": "number",
    "percent": "number",
    "int": "number",
    "integer": "number",
    "long": "number",
    "date": "string",
    "datetime": "string",
    "time": "string",
    "location": "string",
    "address": "string",
    "combobox": "string",
    "base64": "string",
    "anytype": "string",
    "complexvalue": "string",
}

DATE_FORMATS = {"date": "date", "datetime": "date-time", "time": "time"}


def sf_type_to_json(sf_type: str) -> str:
    return SF_TYPE_MAP.get(sf_type.lower(), "string")


# ---------------------------------------------------------------------------
# Schema builder
# ---------------------------------------------------------------------------


def build_schema(
    building_fields: list[dict], item_fields: list[dict]
) -> dict:
    """Combine both field lists into a single JSON Schema document.

    When the same API name appears in both objects, the property key is
    prefixed with the object name to avoid collisions, e.g.:
      Building__c.Organisation__c  →  "Building__c__Organisation__c"
      Item__c.Organisation__c      →  "Item__c__Organisation__c"
    """
    properties: dict = {}
    all_required: list[str] = []
    field_specs: list[dict] = []
    col_idx = 1

    # Pre-compute names that exist in both objects to detect collisions
    building_names = {f["name"] for f in building_fields}
    item_names = {f["name"] for f in item_fields}
    shared_names = building_names & item_names

    def make_prop_key(name: str, source_object: str) -> str:
        """Return the JSON Schema property key for a field."""
        if name in shared_names:
            # Disambiguate: strip trailing "__c" from object name and prepend
            prefix = source_object.replace("__c", "")
            return f"{prefix}__{name}"
        return name

    def process_fields(fields: list[dict], source_object: str) -> None:
        nonlocal col_idx
        for field in fields:
            name = field["name"]
            label = field["label"] or name
            sf_type = field["type"]
            nillable = field["nillable"]
            custom = field["custom"]
            calculated = field["calculated"]
            updateable = field["updateable"]

            json_type = sf_type_to_json(sf_type)
            prop_key = make_prop_key(name, source_object)

            prop: dict = {
                "type": [json_type, "null"],
                "description": f"{source_object}.{name} - {label}",
                "x_salesforce": {
                    "source_object": source_object,
                    "api_name": name,
                    "salesforce_type": sf_type,
                    "label": label,
                    "nillable": nillable,
                    "custom": custom,
                    "calculated": calculated,
                    "updateable": updateable,
                },
            }

            # Add format hint for temporal types
            if sf_type in DATE_FORMATS:
                prop["format"] = DATE_FORMATS[sf_type]

            # Enum for picklist types
            if sf_type in ("picklist", "multipicklist") and field["picklist_values"]:
                prop["enum"] = field["picklist_values"] + [None]

            # Reference info at top-level per spec
            if sf_type == "reference" and field["referenceTo"]:
                prop["x_salesforce_reference"] = field["referenceTo"]

            properties[prop_key] = prop

            # Required: non-nullable custom fields
            is_required = not nillable and custom
            if is_required:
                all_required.append(prop_key)

            field_specs.append(
                {
                    "col_index": col_idx,
                    "col_letter": col_letter(col_idx),
                    "prop_key": prop_key,
                    "name": name,
                    "label": label,
                    "source_object": source_object,
                    "required": is_required,
                    "optional": nillable,
                    "salesforce_type": sf_type,
                    "updateable": updateable,
                    "calculated": calculated,
                }
            )
            col_idx += 1

    process_fields(building_fields, "Building__c")
    process_fields(item_fields, "Item__c")

    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Salesforce Building__c + Item__c Field Schema",
        "description": (
            "Auto-generated from Salesforce object descriptors. "
            "Building fields first, then Item fields."
        ),
        "type": "object",
        "additionalProperties": False,
        "properties": properties,
        "required": all_required,
        "x_excel": {
            "source_objects": ["Building__c", "Item__c"],
            "generated_from": [
                "V3/building-list.txt",
                "V3/item-list.txt",
            ],
            "field_specs": field_specs,
        },
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parent.parent

    building_file = str(repo_root / "V3" / "building-list.txt")
    item_file = str(repo_root / "V3" / "item-list.txt")
    output_file = str(repo_root / "output" / "salesforce_field_schema.json")

    # Ensure output directory exists
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)

    print(f"Parsing {building_file} ...", file=sys.stderr)
    building_fields = parse_sf_descriptor(building_file)
    print(f"  Found {len(building_fields)} Building__c fields", file=sys.stderr)

    print(f"Parsing {item_file} ...", file=sys.stderr)
    item_fields = parse_sf_descriptor(item_file)
    print(f"  Found {len(item_fields)} Item__c fields", file=sys.stderr)

    schema = build_schema(building_fields, item_fields)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)

    total_props = len(schema["properties"])
    total_required = len(schema["required"])
    total_specs = len(schema["x_excel"]["field_specs"])

    print(f"\nWritten to {output_file}", file=sys.stderr)
    print(f"  Total properties : {total_props}", file=sys.stderr)
    print(f"  Required fields  : {total_required}", file=sys.stderr)
    print(f"  Field specs      : {total_specs}", file=sys.stderr)

    # Quick validation: counts should match descriptor headers
    print("\nField count validation:", file=sys.stderr)
    print(
        f"  Building__c: {len(building_fields)} "
        f"(expected 143 per descriptor header)",
        file=sys.stderr,
    )
    print(
        f"  Item__c    : {len(item_fields)} "
        f"(expected 154 per descriptor header)",
        file=sys.stderr,
    )

    # Print per-object type breakdown
    for obj_name, flist in [("Building__c", building_fields), ("Item__c", item_fields)]:
        types: dict[str, int] = {}
        for f in flist:
            t = f["type"] or "(unknown)"
            types[t] = types.get(t, 0) + 1
        print(f"\n  {obj_name} field types:", file=sys.stderr)
        for t, cnt in sorted(types.items()):
            print(f"    {t}: {cnt}", file=sys.stderr)
