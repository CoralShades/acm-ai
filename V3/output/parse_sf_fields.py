import os
import re


def parse_sf_file(filepath):
    """Parse a Salesforce object descriptor file and return structured field data."""
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Strip line numbers and leading whitespace (format: "   464->Fields (143)")
    cleaned = []
    for line in lines:
        # Remove the line number prefix (digits followed by arrow char u2192)
        m = re.match(r"^\s*\d+\u2192(.*)", line)
        if m:
            cleaned.append(m.group(1))
        else:
            cleaned.append(line.rstrip("\n"))

    # Find Fields section
    fields_start = None
    total_fields = 0
    for i, line in enumerate(cleaned):
        m = re.match(r"^Fields \((\d+)\)", line)
        if m:
            fields_start = i + 1
            total_fields = int(m.group(1))
            break

    if fields_start is None:
        raise ValueError(f"Could not find Fields section in {filepath}")

    fields = []
    i = fields_start

    while i < len(cleaned):
        line = cleaned[i].strip()

        # A field starts with a line that is an API name
        # We detect this by: the next line starts with "aggregatable:"
        if i + 1 < len(cleaned) and cleaned[i + 1].strip().startswith("aggregatable:"):
            field_name = line
            field = {
                "name": field_name,
                "label": "",
                "type": "",
                "length": 0,
                "nillable": False,
                "custom": False,
                "calculated": False,
                "updateable": False,
                "restrictedPicklist": False,
                "referenceTo": "",
                "relationshipName": "",
                "inlineHelpText": "",
                "picklist_values": [],
                "controllerName": "",
                "dependentPicklist": False,
            }
            i += 1

            in_picklist = False
            current_pv_label = None
            pv_active = False

            while i < len(cleaned):
                attr_line = cleaned[i].strip()

                # Check if this is the start of a new field
                if i + 1 < len(cleaned) and cleaned[i + 1].strip().startswith(
                    "aggregatable:"
                ):
                    break

                # Check for Picklist Values section
                m_pv_section = re.match(r"^Picklist Values \((\d+)\)", attr_line)
                if m_pv_section:
                    in_picklist = True
                    i += 1
                    continue

                if in_picklist:
                    if attr_line.startswith("active:"):
                        pv_active = attr_line.split(":", 1)[1].strip() == "true"
                    elif attr_line.startswith("defaultValue:"):
                        pass
                    elif attr_line.startswith("validFor:"):
                        pass
                    elif attr_line.startswith("value:"):
                        val = attr_line.split(":", 1)[1].strip()
                        if pv_active and current_pv_label is not None:
                            field["picklist_values"].append(current_pv_label)
                        current_pv_label = None
                        pv_active = False
                    elif (
                        attr_line.startswith("label:") and current_pv_label is not None
                    ):
                        # this is label attribute of current picklist value, skip
                        pass
                    else:
                        # This is a new picklist value entry (the display label line)
                        current_pv_label = attr_line
                        pv_active = False
                    i += 1
                    continue

                # Parse regular attributes
                if ":" in attr_line:
                    key, val = attr_line.split(":", 1)
                    key = key.strip()
                    val = val.strip()

                    if key == "label":
                        field["label"] = val
                    elif key == "type":
                        field["type"] = val
                    elif key == "length":
                        try:
                            field["length"] = int(val)
                        except:
                            field["length"] = 0
                    elif key == "nillable":
                        field["nillable"] = val == "true"
                    elif key == "custom":
                        field["custom"] = val == "true"
                    elif key == "calculated":
                        field["calculated"] = val == "true"
                    elif key == "updateable":
                        field["updateable"] = val == "true"
                    elif key == "restrictedPicklist":
                        field["restrictedPicklist"] = val == "true"
                    elif key == "referenceTo":
                        field["referenceTo"] = val
                    elif key == "relationshipName":
                        field["relationshipName"] = val
                    elif key == "inlineHelpText":
                        field["inlineHelpText"] = val
                    elif key == "controllerName":
                        field["controllerName"] = val
                    elif key == "dependentPicklist":
                        field["dependentPicklist"] = val == "true"

                i += 1

            fields.append(field)
        else:
            i += 1

    return fields, total_fields


print("Parsing building-list.txt...")
building_fields, building_total = parse_sf_file(
    "D:/ailocal/acm-ai/V3/building-list.txt"
)
print(f"Found {len(building_fields)} fields (declared: {building_total})")

print("Parsing item-list.txt...")
item_fields, item_total = parse_sf_file("D:/ailocal/acm-ai/V3/item-list.txt")
print(f"Found {len(item_fields)} fields (declared: {item_total})")

print("\nFirst 5 Building fields:")
for f in building_fields[:5]:
    print(
        f"  {f['name']} | {f['label']} | {f['type']} | len={f['length']} | picklist={len(f['picklist_values'])}"
    )

print("\nFirst 5 Item fields:")
for f in item_fields[:5]:
    print(
        f"  {f['name']} | {f['label']} | {f['type']} | len={f['length']} | picklist={len(f['picklist_values'])}"
    )

bld_picklist = [f for f in building_fields if f["type"] == "picklist"]
itm_picklist = [f for f in item_fields if f["type"] == "picklist"]
print(f"\nBuilding picklist fields: {len(bld_picklist)}")
print(f"Item picklist fields: {len(itm_picklist)}")

bld_custom = [f for f in building_fields if f["custom"]]
itm_custom = [f for f in item_fields if f["custom"]]
print(f"Building custom fields: {len(bld_custom)}")
print(f"Item custom fields: {len(itm_custom)}")

print("\nAll Building field names:")
for i, f in enumerate(building_fields, 1):
    print(
        f"  {i}. {f['name']} ({f['type']}) picklist_count={len(f['picklist_values'])}"
    )

print("\nAll Item field names:")
for i, f in enumerate(item_fields, 1):
    print(
        f"  {i}. {f['name']} ({f['type']}) picklist_count={len(f['picklist_values'])}"
    )
