import os
import re


def parse_sf_file(filepath):
    """Parse a Salesforce object descriptor file and return structured field data."""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Strip line numbers and leading whitespace (format: "   464->Fields (143)")
    cleaned = []
    for line in lines:
        m = re.match(r'^\s*\d+\u2192(.*)', line)
        if m:
            cleaned.append(m.group(1))
        else:
            cleaned.append(line.rstrip('\n'))

    # Find Fields section
    fields_start = None
    total_fields = 0
    for i, line in enumerate(cleaned):
        m = re.match(r'^Fields \((\d+)\)', line)
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

        if i + 1 < len(cleaned) and cleaned[i+1].strip().startswith('aggregatable:'):
            field_name = line
            field = {
                'name': field_name,
                'label': '',
                'type': '',
                'length': 0,
                'nillable': False,
                'custom': False,
                'calculated': False,
                'updateable': False,
                'restrictedPicklist': False,
                'referenceTo': '',
                'relationshipName': '',
                'inlineHelpText': '',
                'picklist_values': [],
                'controllerName': '',
                'dependentPicklist': False,
            }
            i += 1

            in_picklist = False
            current_pv_label = None
            pv_active = False

            while i < len(cleaned):
                attr_line = cleaned[i].strip()

                if i + 1 < len(cleaned) and cleaned[i+1].strip().startswith('aggregatable:'):
                    break

                m_pv_section = re.match(r'^Picklist Values \((\d+)\)', attr_line)
                if m_pv_section:
                    in_picklist = True
                    i += 1
                    continue

                if in_picklist:
                    if attr_line.startswith('active:'):
                        pv_active = attr_line.split(':', 1)[1].strip() == 'true'
                    elif attr_line.startswith('defaultValue:'):
                        pass
                    elif attr_line.startswith('validFor:'):
                        pass
                    elif attr_line.startswith('value:'):
                        if pv_active and current_pv_label is not None:
                            field['picklist_values'].append(current_pv_label)
                        current_pv_label = None
                        pv_active = False
                    elif attr_line.startswith('label:') and current_pv_label is not None:
                        pass
                    else:
                        current_pv_label = attr_line
                        pv_active = False
                    i += 1
                    continue

                if ':' in attr_line:
                    key, val = attr_line.split(':', 1)
                    key = key.strip()
                    val = val.strip()

                    if key == 'label':
                        field['label'] = val
                    elif key == 'type':
                        field['type'] = val
                    elif key == 'length':
                        try:
                            field['length'] = int(val)
                        except:
                            field['length'] = 0
                    elif key == 'nillable':
                        field['nillable'] = val == 'true'
                    elif key == 'custom':
                        field['custom'] = val == 'true'
                    elif key == 'calculated':
                        field['calculated'] = val == 'true'
                    elif key == 'updateable':
                        field['updateable'] = val == 'true'
                    elif key == 'restrictedPicklist':
                        field['restrictedPicklist'] = val == 'true'
                    elif key == 'referenceTo':
                        field['referenceTo'] = val
                    elif key == 'relationshipName':
                        field['relationshipName'] = val
                    elif key == 'inlineHelpText':
                        field['inlineHelpText'] = val
                    elif key == 'controllerName':
                        field['controllerName'] = val
                    elif key == 'dependentPicklist':
                        field['dependentPicklist'] = val == 'true'

                i += 1

            fields.append(field)
        else:
            i += 1

    return fields, total_fields


YEAR_PICKLIST_NAMES = {
    'Estimated_Year_Build_New__c',
    'Estimated_Year_of_Manufacture__c',
}


def yn(b):
    return 'Y' if b else ''


def generate_markdown(obj_name, obj_label, fields, total_fields, out_path):
    custom_count = sum(1 for f in fields if f['custom'])
    picklist_count = sum(1 for f in fields if f['type'] == 'picklist')

    lines = []
    lines.append(f'# {obj_name} — Field Reference')
    lines.append('')
    lines.append(f'**Object:** {obj_name} (label: {obj_label})  ')
    lines.append(f'**Total fields:** {len(fields)}  **Custom fields:** {custom_count}  **Picklist fields:** {picklist_count}')
    lines.append('')
    lines.append('## Field Table')
    lines.append('')
    lines.append('| # | API Name | Label | Type | Length | Nillable | Custom | Calc | Updateable | Notes |')
    lines.append('|---|----------|-------|------|--------|----------|--------|------|------------|-------|')

    for idx, f in enumerate(fields, 1):
        notes_parts = []
        if f['calculated']:
            notes_parts.append('Formula')
        if f['referenceTo']:
            notes_parts.append(f'-> {f["referenceTo"]}')
        if f['dependentPicklist'] and f['controllerName']:
            notes_parts.append(f'Dependent on {f["controllerName"]}')
        if f['name'] in YEAR_PICKLIST_NAMES:
            notes_parts.append('[Years: 1700-2029 (330 values)]')
        if f['type'] == 'picklist' and f['name'] not in YEAR_PICKLIST_NAMES:
            rp = 'restricted' if f['restrictedPicklist'] else ''
            if rp:
                notes_parts.append('Restricted picklist')
        if f['inlineHelpText']:
            # Truncate long help text in table
            ht = f['inlineHelpText']
            if len(ht) > 80:
                ht = ht[:77] + '...'
            notes_parts.append(ht)

        notes = '; '.join(notes_parts)
        length_str = str(f['length']) if f['length'] > 0 else ''

        row = (f"| {idx} | {f['name']} | {f['label']} | {f['type']} | {length_str} | "
               f"{'Y' if f['nillable'] else ''} | {'Y' if f['custom'] else ''} | "
               f"{'Y' if f['calculated'] else ''} | {'Y' if f['updateable'] else ''} | {notes} |")
        lines.append(row)

    # Picklist sections
    picklist_fields = [f for f in fields if f['type'] == 'picklist']
    if picklist_fields:
        lines.append('')
        lines.append('## Picklist Fields — Full Value Lists')

        for f in picklist_fields:
            lines.append('')
            restricted_tag = ' (restricted)' if f['restrictedPicklist'] else ''
            dep_tag = ''
            if f['dependentPicklist'] and f['controllerName']:
                dep_tag = f' (dependent on {f["controllerName"]})'
            lines.append(f'### {f["name"]} — {f["label"]}{restricted_tag}{dep_tag}')
            if f['inlineHelpText']:
                lines.append(f'*{f["inlineHelpText"]}*')
            lines.append('')

            if f['name'] in YEAR_PICKLIST_NAMES:
                lines.append('[Years: 1700-2029 (330 values)]')
            else:
                for val in f['picklist_values']:
                    lines.append(f'- {val}')

    lines.append('')

    with open(out_path, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(lines))

    print(f"Written: {out_path}")


# Parse both files
print("Parsing building-list.txt...")
building_fields, building_total = parse_sf_file("D:/ailocal/acm-ai/V3/building-list.txt")
print(f"  {len(building_fields)} fields parsed")

print("Parsing item-list.txt...")
item_fields, item_total = parse_sf_file("D:/ailocal/acm-ai/V3/item-list.txt")
print(f"  {len(item_fields)} fields parsed")

# Generate output
os.makedirs("D:/ailocal/acm-ai/V3/output", exist_ok=True)

print("Generating building_fields_summary.md...")
generate_markdown(
    obj_name='Building__c',
    obj_label='Asset Class',
    fields=building_fields,
    total_fields=building_total,
    out_path="D:/ailocal/acm-ai/V3/output/building_fields_summary.md"
)

print("Generating item_fields_summary.md...")
generate_markdown(
    obj_name='Item__c',
    obj_label='Item',
    fields=item_fields,
    total_fields=item_total,
    out_path="D:/ailocal/acm-ai/V3/output/item_fields_summary.md"
)

print("Done!")
