# Phase 1 Findings — Salesforce Schema Discovery

**Audit date:** 2026-04-11
**SF org:** `vaea-demidev` (`demi.thathsara@vaea.vic.gov.au.demidev`)
**SF instance:** `vaea--demidev.sandbox.my.salesforce.com`
**Org ID:** `00D9200000AgZd7EAF`
**Objects queried:** `Building__c`, `Item__c` (read-only)
**Raw describe JSON:** `sf-describe/Building__c.json` (14,463 lines), `sf-describe/Item__c.json` (16,203 lines)

---

## 1. Object Naming — Rename Panic Resolved

The VAEA knowledge-base at `/home/demi/gitrepo/vaea/knowledge-base/data-model/` has files named `asset-class-formerly-building.md` and `item--hazmat-item-formerly-acm.md`. This suggested a rename from `Building__c` → `Asset` and `Item__c` → `Hazmat_Item__c`.

**Reality (as of demidev snapshot 2026-04-11):**

| Layer | Building__c | Item__c |
|---|---|---|
| **API Name** (what code targets) | `Building__c` (unchanged) | `Item__c` (unchanged) |
| **User-facing Labels** | "Asset Name", "Asset Type", "Asset Code", "Asset Category" | "Hazmat Item" references appear in labels |
| **Related objects** | `building_snapshot__c`, `building_snapshot__c_hd` (history) | `Item_Snapshot__c` |

**Conclusion:** The rename is happening at the **label layer** only. SF API names are unchanged. Your PRD and code (which reference API names) are correct.

**Action:** No code rename needed. But any user-facing UI text should say "Asset" (not "Building") and "Hazmat Item" (not "ACM" or "Item") to match VAEA's vocabulary evolution.

---

## 2. Field Counts — PRD Was Massively Undercounting

| Object | PRD claim | Actual custom fields | Calculated/autoNumber | Human-editable |
|---|---|---|---|---|
| `Building__c` | "29+" | **132** | 47 | **85** |
| `Item__c` | "35+" | **144** | 31 | **113** |

The PRD's field counts understate the universe by ~3x. However, most extras are:
- Score/rating fields (formula)
- Color code fields (formula)
- Schedule 1-4 cost fields (formula/rollup, 8 currency fields)
- Geocode / address-normalization fields (auto-populated)
- System/admin flags (booleans)

**None of those are extractable from an ARA PDF** — they're computed by SF or populated by other processes. Per the user's "only extractable fields are in scope" rule, the effective target set is much smaller than the 85/113 editable universe.

---

## 3. Parent-Child Relationship (PRD FR-1402 verification)

```
Item__c.Building_Code__c  →  Building__c
  relationshipName: Building_Code__r
  referenceTo:      Building__c
  cascadeDelete:    true      ← MASTER-DETAIL confirmed
  nillable:         false     ← REQUIRED (every Item must have a parent Asset)
```

**PRD claim (FR-1402, architecture §14.1):** Master-Detail from `acm_record.building_id → building_record.id` ✅ **Matches reality.**

**Implication for extraction:** Every extracted Item row MUST have a parent Building assigned before export, or Data Loader will reject the row with `REQUIRED_FIELD_MISSING`.

---

## 4. 🚨 BLOCKER — Item__c has NO valid Data Loader upsert key

Your PRD FR-1406/FR-1407 assume the app exports CSV files that Data Loader will `upsert` into SF using an External_ID. This is NOT currently possible for Item__c.

### Comparison of `External_ID__c` on both objects

| Object | type | externalId | unique | length | Usable as upsert key? |
|---|---|---|---|---|---|
| `Building__c.External_ID__c` | `string` | **true** | false | 255 | ✅ YES |
| `Item__c.External_ID__c` | `textarea` | **false** | false | 32,768 | ❌ **NO — textarea + externalId=false** |

**Why it's broken:** A valid Data Loader external ID requires `type=string` (or `email`/`phone`/`number`) AND `externalId=true`. Textarea fields cannot be used as match keys because SF SOQL doesn't index them efficiently and Data Loader rejects them as upsert targets.

### Alternative upsert keys on Item__c — also broken

| Field | type | externalId | autoNumber | createable | Usable? |
|---|---|---|---|---|---|
| `Unique_Item_Code__c` | string (30) | true | **true** | **false** | ❌ autoNumber + non-creatable → can't INSERT with a caller-supplied value |

Item__c has NO field that is all of: `type=string, externalId=true, createable=true`. This means:

- `sf data upsert --sobject Item__c --external-id X` will fail
- Data Loader's upsert wizard will fail
- Only option today is `sf data create` (insert-only), which produces duplicates on every re-run

### Remediation options (surface to SCP)

1. **[Recommended] SF admin fixes the field type**: change `Item__c.External_ID__c` from `textarea` → `string(255)` and flip `externalId=true`. Requires SF metadata deploy from VAEA repo. **Cannot be done from ACM-AI repo** (read-only access).
2. Create a NEW custom field `ACM_AI_External_ID__c` (string 255, externalId=true, unique=true) specifically for the extraction pipeline. Also requires SF metadata deploy.
3. Switch to query-then-update pattern: for each extracted row, `SELECT Id FROM Item__c WHERE ... LIMIT 1`, then `UPDATE` if found else `INSERT`. Slower, not Data Loader native, requires live SF API access (violates "one-way push via Data Loader" decision).
4. Accept INSERT-only workflow: user manually deletes existing Items before re-importing. Operationally fragile.

**This decision blocks Phase 2 code changes on the export pipeline.** We need your direction before implementing the export adapter.

---

## 5. Required Custom Fields (Export Form Gate — FR-1611)

Fields where `nillable=false` — must be populated before Data Loader import succeeds.

### Building__c (required custom fields)

| Field | Type | Likely source |
|---|---|---|
| `Building_Type__c` | picklist | **PDF** (extractable from site description) |
| `Building_Name__c` | string | **PDF** (from cover page / building header) |
| `Public_Access__c` | picklist | **FORM** (not typically in ARA PDF) |
| `Frequency_of_Use__c` | picklist | **FORM** (not typically in ARA PDF) |
| `Organisation__c` | reference (Account) | **FORM** (user selects from dropdown) |
| `ACM_Snapshot_In_Progress__c` | boolean | default=false, no user action needed |
| `Australian_Building_Address_Only__c` | boolean | default, no user action |
| `Possible_Capital_Works_Project__c` | boolean | default, no user action |
| `Is_Building_Merge_Running__c` | boolean | default, no user action |
| `No_Identified_ACMs__c` | boolean | derived from Item count |
| `Is_Duplicate_External_ID__c` | boolean | default, no user action |
| `Unique_Asset_Class_Code__c` | string | likely auto-generated (TBD — need to verify `autoNumber` flag) |

**Form gate must collect 3 fields per Building:** `Public_Access__c`, `Frequency_of_Use__c`, `Organisation__c`.

### Item__c (required custom fields)

| Field | Type | Likely source |
|---|---|---|
| `Building_Code__c` | reference → Building__c | **Auto** (set from extraction context — the building row was captured alongside item rows in the PDF) |
| `Requires_Re_Inspection__c` | boolean | default |
| `Assumed_Value__c` | boolean | default |
| `Is_Sample_NATA_Endorsed__c` | boolean | default |
| `Requires_Investigation__c` | boolean | default |
| `Assumed_Removed__c` | boolean | default |
| `Removed__c` | boolean | default |
| `ACM_Snapshot_In_Progress__c` | boolean | default |
| `Acm_Snapshot_Ready_To_Update__c` | boolean | default |
| `Awaiting_Test_Result__c` | boolean | default |
| `Immediate_Action_Required__c` | boolean | default |
| `Locked_by_Active_Audit__c` | boolean | default |
| `Flag_for_Deletion__c` | boolean | default |
| `Mark_for_Hygienist_Review__c` | boolean | default |
| `No_Access__c` | boolean | default |
| `SMF_Present__c` | boolean | default |
| `Is_Duplicate_External_ID__c` | boolean | default |
| `Unique_Item_Code__c` | string | **autoNumber** — SF generates automatically, not user-settable |

**Form gate for Item__c: zero fields require user input.** All required fields are either booleans with defaults or autoNumber strings. The only mandatory user action is confirming the parent Building is assigned (already done at extraction time).

---

## 6. Parent Object References on Item__c (beyond Building)

Item__c has 14 reference fields to other SF objects. Most are out-of-scope (user said "Building + Item only") but worth noting for the SCP:

```
Building_Code__c          → Building__c                 (master-detail, REQUIRED)
Pricing__c                → Pricing__c                  (lookup, config data)
Hygiene_Lab__c            → Hygiene_Lab__c              (lookup, master data)
Weight_Conversion__c      → Weight_Conversion__c        (lookup, config)
Program__c                → Program__c                  (lookup, project parent)
Removal_Job__c            → Removal_Job__c              (lookup, workflow state)
Clearance_Certificate__c  → Clearance_Certificate__c    (lookup, workflow state)
Account_Removal_Job__c    → Account_Removal_Job__c      (lookup)
Hygiene_Firm__c           → Account                     (lookup)
Identify_Hygiene_Consulting_Company__c → Account        (lookup)
Product_Type_Life_Span__c → Product_Type_Life_Span__c   (lookup, config)
```

**Extraction in scope only needs to populate `Building_Code__c`.** The other 13 references are either (a) populated by SF workflow after import or (b) left null (all are `nillable=true`).

---

## 7. Extractable Field Targets (Preliminary — needs picklist validation in Phase 2)

### Building__c — extractable from typical ARA PDF cover page + site description

1. `Building_Name__c` (string, REQUIRED) ✅
2. `Building_Address__c` (string) ✅
3. `Suburb__c` (string) ✅
4. `Postcode__c` (string) ✅
5. `State__c` (string, default "VIC") ✅
6. `Building_Type__c` (picklist, REQUIRED, dependent picklist controller) ✅
7. `Building_Category__c` (picklist, dependent on Building_Type) ✅
8. `Site_Name__c` (string) ✅
9. `Building_Unique_ID__c` (string) ✅
10. `Estimated_Year_Built__c` (date) or `Estimated_Year_Build_New__c` (picklist) ⚠️ two competing fields
11. `Asbestos_Register_Available__c` (picklist yes/no) ✅
12. `Audit_Report_Available__c` (picklist yes/no) ✅
13. `Date_of_Audit_Report__c` (date) ✅
14. `Additional_Comments__c` (textarea) ✅
15. `Site_Name__c` (string) ✅
16. `Owned_or_Leased__c` (picklist) ✅
17. `School_UID__c` (string) ✅ (when extracting school ARA reports)
18. `Responsible_Agency_Department__c` (string) ✅
19. `GPS_Coordinates_provided_by_metro__c` (string) ✅

**Estimated target fieldset: ~19 Building__c fields from PDF.**

### Item__c — extractable from table rows

1. `Building_Code__c` (ref, auto-set from extraction context, REQUIRED)
2. `Item_Name__c` (picklist) — material name
3. `If_Other_Item_Name__c` (string) — fallback when Item_Name picklist doesn't match
4. `Friability_of_Material__c` (picklist, controller for ACM_Classification)
5. `ACM_Classification__c` (picklist, dependent on Friability)
6. `ACM_Sub_Classification__c` (picklist, dependent on ACM_Classification)
7. `Condition__c` (picklist)
8. `Disturbance_Potential_of_Material__c` (picklist)
9. `Quantity__c` (double)
10. `Units_of_Measure__c` (string)
11. `Sample_Analysis_Result_Material_Status__c` (picklist: positive/negative/assumed)
12. `NATA_Endorsed_Sample_no__c` (string)
13. `Internal_External__c` (picklist)
14. `Level__c` (string)
15. `Room_or_Area__c` (string)
16. `Location_in_Room__c` (string)
17. `Labelled__c` (picklist yes/no)
18. `Labelled_Details__c` (string)
19. `Photo_Ref__c` (string)
20. `Asbestos_Register_Reference_No__c` (string)
21. `Lot_No__c` (string)
22. `Survey_Date__c` (date)
23. `Clearance_Certificates_Available__c` (picklist)
24. `Identifying_Hygiene_Consulting_Company__c` (string) — consultant company
25. `Additional_Comments__c` (textarea)

**Estimated target fieldset: ~25 Item__c fields from PDF.**

**Combined extraction surface: ~44 fields across both objects.**

Compare to current code in `open_notebook/domain/acm_row_schemas.py` which extracts ~13 Item__c fields per row. **The schema is under-covering by ~50%.** Phase 2 must extend the extraction schema to cover the additional fields.

---

## 8. Dependent Picklists (not yet fully extracted — Phase 2 will parse via Python)

Critical controller-dependent chains that the frontend AG Grid must enforce:

- `Friability_of_Material__c` → controls `ACM_Classification__c`
- `ACM_Classification__c` → controls `ACM_Sub_Classification__c`
- `Building_Type__c` → controls `Building_Category__c`

Your PRD FR-1604 mentions these. Phase 2 verification will confirm the actual allowed value pairings from the live describe output.

---

## 9. Gaps vs PRD (Preliminary)

| PRD item | Claim | Reality | Gap |
|---|---|---|---|
| FR-1402 Master-Detail | Building ←m/d→ Item | ✅ confirmed | none |
| FR-1406 Upsert Item__c via External_ID__c | exports CSV → Data Loader upsert | **Item__c External_ID__c is textarea, not usable** | 🚨 BLOCKER — remediation options above |
| FR-1405 Picklist validation | "BAR 'Good' → SF 'Stable'" | Need to verify Condition__c picklist values | Phase 2 to confirm |
| FR-1408 Load SF schema from JSON config | Parse from `building_list.txt` / `item_list.txt` | Those files may be stale; should regenerate from live describe | Phase 2 to diff |
| FR-1611 Building detail page "29+ fields" | 29+ Building__c fields | **132 custom fields, 85 editable, ~19 extractable from PDF** | PRD field count undercounts; likely needs re-scoping |
| FR-1410 Two-phase extraction | Building fields, then Item fields | Current schema extracts ~13 Item fields, 0 Building fields | Need to add Building__c extraction phase |

---

## 10. Gaps vs Current Code (Preliminary)

Based on what's in `open_notebook/domain/acm_row_schemas.py` and `open_notebook/domain/acm.py` (Phase 2 will do full line-by-line diff):

- **Row schema extracts ~13 Item__c fields** — missing ~12 extractable fields from the target list above
- **No Building__c extraction schema exists** — Building data is currently derived from Source metadata, not extracted from PDF content
- **`ACM_Classification__c` / `ACM_Sub_Classification__c` dependent picklist enforcement may not be active** — need to verify `SalesforcePicklistValidator` uses live schema
- **Export pipeline targets `External_ID__c` for Item__c** — will fail per Section 4 blocker

---

## 11. Recommended Phase 2 Plan

Given the findings above, Phase 2 (code changes) should proceed in this order:

1. **⏸ BLOCKED — Export upsert key**: Wait for SF admin decision on `Item__c.External_ID__c` fix (Section 4). OR switch to INSERT-only mode for Item__c with user-visible warning.
2. **Extend row schema** in `acm_row_schemas.py` from 13 → ~25 Item__c fields.
3. **Create new Building extraction schema** at `open_notebook/domain/acm_building_schemas.py` (~19 fields).
4. **Regenerate `config/sf-schema-snapshot.json`** from live describe output using a Python script (committed to repo, manually refreshable).
5. **Implement BAR→SF mapping layer** at `config/bar_to_sf_mapping.yaml` for vocabulary translation (especially Condition values).
6. **Wire deterministic External_ID__c generator** (hash(source_id + building_name) for Building, hash(source_id + building_name + row_index) for Item) — works for Building now, blocked for Item until Section 4 resolves.
7. **Add form gate** for 3 required Building__c fields (Public_Access, Frequency_of_Use, Organisation).
8. **Hard-delete non-SF fields** from existing code per user's "scorched earth" directive (scope TBD after Phase 2 diff).

---

## 12. Unknowns Still Outstanding (for Phase 2 investigation)

- Full picklist values for all target picklists (deferred from Phase 1 due to jq tooling issues)
- Dependent picklist `validFor` bitmaps (controller-dependent pairings)
- Whether `Unique_Asset_Class_Code__c` is `autoNumber` (suspected but not verified)
- Whether `Item_Name__c` picklist is restricted or free-form (affects `If_Other_Item_Name__c` fallback logic)
- Picklist values for Condition__c (to confirm the "Good → Stable" mapping claim in PRD FR-1405)
- Whether `Organisation__c` lookup on Building__c has filter rules / RecordType restrictions
