# Item__c — Field Reference

**Object:** Item__c (label: Item)  
**Total fields:** 154  **Custom fields:** 142  **Picklist fields:** 23

## Field Table

| # | API Name | Label | Type | Length | Nillable | Custom | Calc | Updateable | Notes |
|---|----------|-------|------|--------|----------|--------|------|------------|-------|
| 1 | Account_Removal_Job__c | Subcontractor Removal Job | reference | 18 | Y | Y |  | Y | -> Account_Removal_Job__c; The Subcontractor Organisation Removal Job this ACM relates to |
| 2 | ACM_Classification__c | ACM Product Group | picklist | 255 | Y | Y |  | Y | Dependent on Friability_of_Material__c; Restricted picklist; Select the classification of the asbestos-containing material (dependent on f... |
| 3 | ACM_Risk_Score__c | ACM Risk Score | string | 255 | Y | Y |  | Y |  |
| 4 | ACM_Snapshot_In_Progress__c | ACM Snapshot In Progress | boolean |  |  | Y | Y |  | Formula; Indicate if building level acm snapshot is running or not |
| 5 | Acm_Snapshot_Ready_To_Update__c | Acm Snapshot Ready To Update | boolean |  |  | Y |  | Y |  |
| 6 | ACM_Sub_Classification_Rating__c | Friability Scale | double |  | Y | Y |  | Y | ACM Risk Score based on Product Type and VAEA Friability Scale |
| 7 | ACM_Sub_Classification__c | ACM Product Type | picklist | 255 | Y | Y |  | Y | Dependent on ACM_Classification__c; Restricted picklist; Select the Sub-Classification of the asbestos-containing material. (Dependent... |
| 8 | Additional_Comments__c | Additional Comments | textarea | 32768 | Y | Y |  | Y |  |
| 9 | AIRHaz_QR_Code__c | AIRHaz QR Code | textarea | 131072 | Y | Y |  | Y | Used to store a base64 text that will encode a small HTML page that includes ... |
| 10 | Asbestos_Register_Reference_No__c | Asbestos Register Reference No | string | 255 | Y | Y |  | Y |  |
| 11 | Asbestos_Removal_Notification_No__c | Asbestos Removal Notification No | string | 255 | Y | Y |  | Y |  |
| 12 | ASSEA_Survey_Guide_Risk_Level__c | ASSEA Survey Guide Risk Level | picklist | 255 | Y | Y |  | Y | This is the risk level assigned in accordance with the ASSEA Survey Guide, 3 ... |
| 13 | Assessor__c | Assessor | string | 255 | Y | Y |  | Y | Capture the person or organisation that identified/assessed the item. |
| 14 | Assumed_Removed__c | Assumed Removed | boolean |  |  | Y |  | Y |  |
| 15 | Assumed_Value__c | Is An Assumed Quantity Value | boolean |  |  | Y |  | Y |  |
| 16 | Average_Estimated_Product_Life__c | Average Estimated Product Life | double |  | Y | Y |  | Y | Average estimated product life span of the product type. |
| 17 | Awaiting_Test_Result_Start_Date__c | Awaiting Test Result Start Date | date |  | Y | Y |  | Y | When Awaiting Test Result checkbox is checked, that checked date includes in ... |
| 18 | Awaiting_Test_Result__c | Awaiting Test Result | boolean |  |  | Y |  | Y |  |
| 19 | Building_Code_Value__c | Asset Code Value | string | 1300 | Y | Y | Y |  | Formula |
| 20 | Building_Code__c | Asset Code | reference | 18 |  | Y |  | Y | -> Building__c |
| 21 | Building_Geocodes_EASTING__c | Asset Geocodes(EASTING) | string | 255 | Y | Y |  | Y |  |
| 22 | Building_Geocodes_NORTHING__c | Asset Geocodes(NORTHING) | string | 255 | Y | Y |  | Y |  |
| 23 | Building_Name__c | Asset Name (as provided by PSB) | string | 1300 | Y | Y | Y |  | Formula; Asset Name |
| 24 | Building_Rating__c | Asset Rating | string | 1300 | Y | Y | Y |  | Formula |
| 25 | Clearance_Certificates_Available__c | Clearance Certificates Available | picklist | 255 | Y | Y |  | Y | Restricted picklist; Certificate stating that particular asbestos items have been removed from the... |
| 26 | Clearance_Certificate__c | Clearance Certificate | reference | 18 | Y | Y |  | Y | -> Clearance_Certificate__c; Lookup to Clearance Certificate |
| 27 | Condition_Rating__c | Condition Rating | double |  | Y | Y |  | Y |  |
| 28 | Condition__c | Condition | picklist | 255 | Y | Y |  | Y | Restricted picklist; Select the condition of the asbestos from the drop-down list provided. Furthe... |
| 29 | CreatedById | Created By ID | reference | 18 |  |  |  |  | -> User |
| 30 | CreatedDate | Created Date | datetime |  |  |  |  |  |  |
| 31 | Days_Awaiting_Test_Result__c | Days Awaiting Test Result | double |  | Y | Y | Y |  | Formula; Number of days that ACM has been awaiting test result. |
| 32 | Department_Name__c | Department Name | string | 1300 | Y | Y | Y |  | Formula |
| 33 | Department__c | Department | string | 1300 | Y | Y | Y |  | Formula |
| 34 | Disturbance_Potential_of_Material__c | Disturbance Potential | picklist | 255 | Y | Y |  | Y | Restricted picklist; Occupational Health and Safety Regulations 2017 - regulation 226(4)(c)(iv) re... |
| 35 | DoT_RAM_ACM_Removal_Priority_Rating__c | DoT RAM ACM Removal Priority Rating | string | 255 | Y | Y |  | Y | DoT ACM Removal Priority Rating |
| 36 | DoT_RAM_ACM_Removal_Priority__c | DoT RAM ACM Removal Priority | string | 255 | Y | Y |  | Y | DoT ACM Removal Priority |
| 37 | DPOM_Rating__c | Disturbance Potential Rating | double |  | Y | Y |  | Y |  |
| 38 | Duplicate_Check_1__c | Duplicate Check 1 | string | 255 | Y | Y |  | Y | Hidden field used for finding potential duplicate items |
| 39 | Duplicate_Check_2__c | Duplicate Check 2 | string | 255 | Y | Y |  | Y | Hidden field used for finding potential duplicate items |
| 40 | Duplicate_Check_3__c | Duplicate Check 3 | string | 255 | Y | Y |  | Y | Hidden field used for finding potential duplicate items |
| 41 | Empty_Room_or_Not_Accessed_Room__c | Empty Room or Not Accessed Room | picklist | 255 | Y | Y |  | Y | Restricted picklist; Choose "Empty Space/Area" for rooms confirmed empty. Select "Not Accessed Spa... |
| 42 | EPA_Waste_Transport_Certificate_No__c | EPA Waste Record | string | 255 | Y | Y |  | Y |  |
| 43 | Estimated_Reinspection_Cost__c | Estimated Reinspection Cost | currency |  | Y | Y |  | Y |  |
| 44 | Estimated_Year_of_Manufacture__c | Estimated Year of Manufacture | picklist | 255 | Y | Y |  | Y | [Years: 1700-2029 (330 values)]; Capture the estimated year of manufacture of the hazardous material item. |
| 45 | External_ID__c | External ID | textarea | 32768 | Y | Y |  | Y | External ID Field to simplify the Data Migration process |
| 46 | Flag_for_Deletion__c | Flag for Deletion | boolean |  |  | Y |  | Y | Select this checkbox only if the ACM is a duplicate or created in error. Add ... |
| 47 | Frequency_of_Use__c | Frequency of Use (ACM) | picklist | 255 | Y | Y |  | Y | Restricted picklist; Select the Frequency of use for this room from the drop-down list provided. |
| 48 | Friability_of_Material__c | Friability of Material | picklist | 255 | Y | Y |  | Y | Restricted picklist; Friable ACMs can be easily reduced to powder by hand when dry. Non-friable or... |
| 49 | FullID18Char__c | FullID18Char | string | 1300 | Y | Y | Y |  | Formula |
| 50 | Hazard_Rating__c | Risk Rating | string | 1300 | Y | Y | Y |  | Formula; Risk Rating calculation |
| 51 | Highest_Wins_DP_Air_Exchange__c | Highest Wins -DP (Air Exchange) | string | 255 | Y | Y |  | Y |  |
| 52 | Hygiene_Firm__c | Hygiene Firm | reference | 18 | Y | Y |  | Y | -> Account; Hygiene firm that issued Clearance Certificate |
| 53 | Hygiene_Lab_Number__c | Hygiene Lab Number | string | 1300 | Y | Y | Y |  | Formula; Removed from all page layouts and mobile app UIs July 2023 VS-116 |
| 54 | Hygiene_Lab_Suburb__c | Hygiene Lab Suburb | string | 1300 | Y | Y | Y |  | Formula; Removed from all page layouts and mobile app UIs July 2023 VS-116 |
| 55 | Hygiene_Lab__c | Hygiene Lab Name | reference | 18 | Y | Y |  | Y | -> Hygiene_Lab__c; Removed from all page layouts and mobile app UIs July 2023 VS-116 |
| 56 | Hygienist_Recommendations__c | Hygienist Recommendations | textarea | 1000 | Y | Y |  | Y |  |
| 57 | Id | Record ID | id | 18 |  |  |  |  |  |
| 58 | Identifying_Hygiene_Consulting_Company__c | Identifying Hygiene / Consulting Company | string | 255 | Y | Y |  | Y | Enter the most recent hygiene or consulting company that conducted an inspect... |
| 59 | Identify_Hygiene_Consulting_Company__c | Identifying Hygiene / Consulting Company | reference | 18 | Y | Y |  | Y | -> Account; Enter the most recent hygiene or consulting company that conducted an inspect... |
| 60 | ID_provided_by_metro__c | PSB Supplied Item ID | string | 100 | Y | Y |  | Y |  |
| 61 | If_Other_Item_Name__c | If Other Please Specify the ACM Name | string | 255 | Y | Y |  | Y | If you can't find your Item Name in the list above, specify it here. |
| 62 | Immediate_Action_Required__c | Immediate Action Required | boolean |  |  | Y |  | Y |  |
| 63 | Internal_External__c | Internal / External | picklist | 255 | Y | Y |  | Y | Restricted picklist; Location of asbestos in relation to the asset. Select from drop-down list pro... |
| 64 | IsDeleted | Deleted | boolean |  |  |  |  |  |  |
| 65 | Is_Sample_NATA_Endorsed__c | Is Sample NATA Endorsed | boolean |  |  | Y |  | Y |  |
| 66 | Item_Life_Span__c | Item Life Span | string | 1300 | Y | Y | Y |  | Formula; Product Life Span Status. |
| 67 | Item_Name_Search_Copy__c | ACM Name Search Copy | string | 255 | Y | Y |  | Y | Item Name is a picklist and is not searchable but users will need to search b... |
| 68 | Item_Name__c | Item Name | picklist | 255 | Y | Y |  | Y | Restricted picklist; Select specific item, application or product from the dropdown list. If 'Othe... |
| 69 | Item_Removal_Cost_Custom_temp__c | VAEA Schedule 4 (Cost temp) | currency |  | Y | Y |  | Y |  |
| 70 | Item_Removal_Cost_Custom__c | VAEA Schedule 4 (Cost) | currency |  | Y | Y | Y |  | Formula; Estimated Schedule Cost - Generated by VAEA |
| 71 | Item_Removal_Cost_std_temp__c | VAEA Schedule 1 (Cost temp) | currency |  | Y | Y |  | Y |  |
| 72 | Item_Removal_Cost_std__c | Sch. A - Industry Removal Est. (Cost) | currency |  | Y | Y | Y |  | Formula; Estimated Removal Cost - Based on removal industry quotes |
| 73 | Item_Removal_Cost_VSBA_Simple_temp__c | VAEA Schedule 3 (Cost temp) | currency |  | Y | Y |  | Y |  |
| 74 | Item_Removal_Cost_VSBA_Simple__c | Sch. C - VAEA Removal Est. (Cost) | currency |  | Y | Y | Y |  | Formula; Estimated Removal Cost - Based on VSBA four values |
| 75 | Item_Removal_Cost_VSBA_temp__c | VAEA Schedule 2 (Cost temp) | currency |  | Y | Y |  | Y |  |
| 76 | Item_Removal_Cost_VSBA__c | Sch. B - Program Removal Est. (Cost) | currency |  | Y | Y | Y |  | Formula; Estimated Removal Cost - Based on program removals |
| 77 | Item_Removal_Priority_Rating_HT__c | ACM Removal Priority Rating HT | double |  | Y | Y |  | Y |  |
| 78 | Item_Removal_Priority_Rating_Revised__c | ACM Removal Priority Rating Revised | string | 255 | Y | Y |  | Y |  |
| 79 | Item_Removal_Priority_Rating__c | ACM Removal Priority Rating | string | 255 | Y | Y |  | Y |  |
| 80 | Item_Removal_Unit_Price_Custom__c | VAEA Schedule 4 (Unit) | currency |  | Y | Y | Y |  | Formula; Estimated Schedule - Generated by VAEA |
| 81 | Item_Removal_Unit_Price_std__c | Sch. A - Industry Removal Est. (Unit) | currency |  | Y | Y | Y |  | Formula; Estimated Removal Unit - Based on removal industry quotes |
| 82 | Item_Removal_Unit_Price_VSBA_Simple__c | Sch. C - VAEA Removal Est. (Unit) | currency |  | Y | Y | Y |  | Formula; Estimated Removal Cost - Based on VSBA four values |
| 83 | Item_Removal_Unit_Price_VSBA__c | Sch. B - Program Removal Est. (Unit) | currency |  | Y | Y | Y |  | Formula; Estimated Removal Cost - Based on program removals |
| 84 | Item_Weight__c | ACM or Item Weight (tonnes) | double |  | Y | Y |  | Y |  |
| 85 | Labelled_Details__c | Label Details | string | 255 | Y | Y |  | Y | Add label details if item is labelled |
| 86 | Labelled__c | Labelled | picklist | 255 | Y | Y |  | Y | Restricted picklist; Is the item labelled or not? If Yes, please enter details. |
| 87 | LastActivityDate | Last Activity Date | date |  | Y |  |  |  |  |
| 88 | LastModifiedById | Last Modified By ID | reference | 18 |  |  |  |  | -> User |
| 89 | LastModifiedDate | Last Modified Date | datetime |  |  |  |  |  |  |
| 90 | LastReferencedDate | Last Referenced Date | datetime |  | Y |  |  |  |  |
| 91 | LastViewedDate | Last Viewed Date | datetime |  | Y |  |  |  |  |
| 92 | Last_Print_Date__c | Last Print Date | datetime |  | Y | Y |  | Y |  |
| 93 | Level__c | Level | string | 255 | Y | Y |  | Y | Enter the level/floor of the building that contains asbestos. |
| 94 | Licence_Class__c | Licence Class | picklist | 255 | Y | Y |  | Y | Restricted picklist |
| 95 | Line_s_serviced__c | Line(s) serviced | string | 255 | Y | Y |  | Y |  |
| 96 | Location_in_Room__c | Location in Room/Area | string | 255 | Y | Y |  | Y | The location of asbestos within the room or area listed above |
| 97 | Locked_by_Active_Audit__c | Locked by Active Audit | boolean |  |  | Y |  | Y |  |
| 98 | Lot_No__c | Lot No | string | 255 | Y | Y |  | Y |  |
| 99 | Mark_for_Hygienist_Review__c | Mark for Hygienist Review | boolean |  |  | Y |  | Y | Check this check box to tell hygienist to review the item. |
| 100 | Maximum_Estimated_Product_Life__c | Maximum Estimated Product Life | double |  | Y | Y |  | Y | Maximum estimated product life span of the product type. |
| 101 | Minimum_Estimated_Product_Life__c | Minimum Estimated Product Life | double |  | Y | Y |  | Y | Minimum Estimated Product Life of the product type |
| 102 | Name | Item Code | string | 80 | Y |  |  | Y |  |
| 103 | NATA_Endorsed_Sample_no__c | Sample no (if applicable) | string | 255 | Y | Y |  | Y | Enter the National Association of Testing Authorities (NATA) sample no. or re... |
| 104 | No_Access__c | No Access | boolean |  |  | Y |  | Y | Select this checkbox if the ACM is unable to be physically accessed. |
| 105 | Organisation_Name__c | Organisation Name | string | 1300 | Y | Y | Y |  | Formula |
| 106 | Organisation_Sub_Type__c | Organisation Sub Type | string | 1300 | Y | Y | Y |  | Formula |
| 107 | Other_Hygiene_Company__c | Other Hygiene Lab | string | 255 | Y | Y |  | Y | Removed from all page layouts and mobile app UIs July 2023 VS-116 |
| 108 | Out_of_scope__c | Out of Scope | picklist | 255 | Y | Y |  | Y | Restricted picklist |
| 109 | Photo_Ref__c | Photo Ref | string | 255 | Y | Y |  | Y |  |
| 110 | Pricing__c | Pricing | reference | 18 | Y | Y |  | Y | -> Pricing__c |
| 111 | Product_Type_Life_Span__c | Product Type Life Span | reference | 18 | Y | Y |  | Y | -> Product_Type_Life_Span__c; Product Type Life span object data |
| 112 | Prod_Item_Code__c | Prod ACM Code | string | 255 | Y | Y |  | Y |  |
| 113 | Prod_Item_ID__c | Prod ACM ID | string | 255 | Y | Y |  | Y |  |
| 114 | Program__c | Project | reference | 18 | Y | Y |  | Y | -> Program__c; Project of removal works |
| 115 | Proportional_Total_Building_Risk_Score__c | Proportional Total Asset Risk Score | double |  | Y | Y | Y |  | Formula |
| 116 | Public_Access__c | Public Access (ACM) | picklist | 255 | Y | Y |  | Y | Restricted picklist; Can the public access this room? Select Yes or No |
| 117 | QR_Code__c | QR Code | string | 1300 | Y | Y | Y |  | Formula |
| 118 | Quantity_Removed__c | Quantity Removed | double |  | Y | Y |  | Y |  |
| 119 | Quantity__c | Quantity | double |  | Y | Y |  | Y |  |
| 120 | Reason_for_Investigation__c | Reason for Investigation | textarea | 32768 | Y | Y |  | Y |  |
| 121 | Reason_for_Unknown__c | Reason for Unknown | picklist | 255 | Y | Y |  | Y | Restricted picklist; This field is required if any of the following fields have a value of "Unknow... |
| 122 | Recent_Inspection__c | Date of Most Recent Inspection | date |  | Y | Y | Y |  | Formula; Date is calculated from the latest ACM snapshot |
| 123 | RecordTypeId | Record Type ID | reference | 18 | Y |  |  | Y | -> RecordType |
| 124 | Remaining_ACM_Comments__c | Remaining ACM Comments | textarea | 32768 | Y | Y |  | Y | Hidden field used to capture Clearance Certificate form inputs |
| 125 | Remaining_ACM_Quantity__c | Remaining ACM Quantity | double |  | Y | Y |  | Y | Hidden field used to capture Clearance Certificate form inputs |
| 126 | Remediation_Actions_Taken__c | Remediation Actions Taken | textarea | 3000 | Y | Y |  | Y | A brief description of the actions taken in handling the item with P1 Risk Ra... |
| 127 | Removal_Comments__c | Removal Comments | textarea | 131072 | Y | Y |  | Y |  |
| 128 | Removal_Company__c | Removal Company | string | 255 | Y | Y |  | Y |  |
| 129 | Removal_Job_Supervisor__c | Removal Job Supervisor | string | 255 | Y | Y |  | Y |  |
| 130 | Removal_Job__c | Removal Job | reference | 18 | Y | Y |  | Y | -> Removal_Job__c; Removal Job associated with a Removalist organisation |
| 131 | Removal_Limitations__c | Removal Limitations | picklist | 255 | Y | Y |  | Y | Restricted picklist; Hidden field used to capture Clearance Certificate form inputs |
| 132 | Removal_Status__c | Removal Status | picklist | 255 | Y | Y |  | Y | Restricted picklist |
| 133 | Removed_Date__c | Date of Removal | date |  | Y | Y |  | Y |  |
| 134 | Removed__c | Removed | boolean |  |  | Y |  | Y |  |
| 135 | Requires_Investigation__c | Requires Investigation | boolean |  |  | Y |  | Y |  |
| 136 | Requires_Re_Inspection__c | Requires reinspection | boolean |  |  | Y | Y |  | Formula |
| 137 | Responsible_Agency_Department__c | Responsible Agency/Department | string | 1300 | Y | Y | Y |  | Formula |
| 138 | Risk_of_Fibre_Release__c | Risk of Fibre Release | string | 255 | Y | Y |  | Y | Auto-populated from Friability of Material and ACM Classification |
| 139 | Risk_Rating_Color_Code__c | ACM Removal Priority Color Code | string | 1300 | Y | Y | Y |  | Formula |
| 140 | Risk_Rating__c | ACM Removal Priority | string | 255 | Y | Y |  | Y |  |
| 141 | Room_or_Area__c | Room or Area | string | 255 | Y | Y |  | Y | Relates to the room i.e. a room on a specific floor. |
| 142 | Sample_Analysis_Result_Material_Status__c | Sample Result | picklist | 255 | Y | Y |  | Y | Restricted picklist; Select the result of sample analysis from the drop-down list provided. |
| 143 | Schools_A_Rating__c | Schools A Rating | picklist | 255 | Y | Y |  | Y | Restricted picklist; Used for VSBA Schools only |
| 144 | SMF_Present__c | SMF Present | boolean |  |  | Y |  | Y | Has been identified as containing Synthetic Mineral Fibres (SMF) |
| 145 | Specific_Item_Rating__c | VAEA ACM Rating | double |  | Y | Y |  | Y | Based on ACM's accessibility,maintenance,weathering,fixed/installed status |
| 146 | Status__c | Status | picklist | 255 | Y | Y |  | Y | Restricted picklist |
| 147 | Statutory_Line__c | Statutory Line | string | 255 | Y | Y |  | Y |  |
| 148 | Survey_Date__c | Survey Date | date |  | Y | Y |  | Y |  |
| 149 | SystemModstamp | System Modstamp | datetime |  |  |  |  |  |  |
| 150 | Unable_to_remove_reason__c | Unable To Remove Reason | picklist | 255 | Y | Y |  | Y | Restricted picklist; Unable To Remove Reason |
| 151 | Unique_Item_Code__c | Unique Item Code | string | 30 |  | Y |  |  | Used to generate the unique incremental ID numbers added to the Item Code (Na... |
| 152 | Units_of_Measure__c | Units of Measure | string | 255 | Y | Y |  | Y | Auto-populated based on ACM classification |
| 153 | VAEA_Friability_Scale__c | VAEA Friability Scale | string | 1300 | Y | Y | Y |  | Formula; VAEA friability based on friablity scale |
| 154 | Weight_Conversion__c | User owned items | reference | 18 | Y | Y |  | Y | -> Weight_Conversion__c |

## Picklist Fields — Full Value Lists

### ACM_Classification__c — ACM Product Group (restricted) (dependent on Friability_of_Material__c)
*Select the classification of the asbestos-containing material (dependent on friability).*

- Bitumen products
- Bitumen products (f)
- Cement products
- Cement products (f)
- Coatings
- Coatings (f)
- Gasket, friction products and adhesives
- Gasket, friction products and adhesives (f)
- Insulation Products
- Insulation products (f)
- Other
- Other (f)
- Reinforced plastics/resins (excluding bitumen products)
- Reinforced plastics/resins (excluding bitumen products) (f)
- Textiles
- Textiles (f)
- Vinyl products
- Vinyl products (f)

### ACM_Sub_Classification__c — ACM Product Type (restricted) (dependent on ACM_Classification__c)
*Select the Sub-Classification of the asbestos-containing material. (Dependent on ACM Classification)*

- Acoustic pad
- Adhesive or glue
- Asbestos coated metal sheet (Galbestos)
- Asphalt
- Bitumen coated paper
- Bitumen coated polystyrene
- Bitumen coating
- Bitumen washer
- Bituminous adhesive (BlackJack)
- Bituminous membrane
- Boiler insulation
- Brake pads
- CAF gasket(s)
- CAF gasket debris
- Calico wrap
- Cardboard
- Carpet
- Caulking
- Ceiling tiles
- Cellulose fibre product
- Cement flue
- Cement pipe
- Cement product debris
- Cement strapping
- Ceramic fibre
- Cloth
- Clutch plates
- Communications pit
- Compressed electrical panels
- Compressed flat sheeting
- Concrete
- Concrete levelling compound
- Contaminated carpet underlay
- Contaminated materials
- Contaminated soil (friable debris)
- Contaminated soil (non-friable debris)
- Corrugated roof sheeting
- Corrugated sheeting
- Debris
- Doonas
- Dust
- Dust and debris
- Electrical arc shields
- Electrical cable shrouding
- Electrical terminal block
- Faux brick cladding
- Faux timber sheeting
- Fibrous cement electrical components
- Fire blanket
- Fire brick
- Fire curtains
- Fire door core
- Fire-fighting clothing
- Fireproof pillows
- Fire rated material
- Flat sheeting
- Flue cap
- Foam insulation
- Fuse holder
- Gauze mats
- Gland packing
- Gloves
- Granular material
- Grout
- Gutter deposits
- Hessian
- Hessian backed vinyl sheet
- Horsehair
- HRC fuse
- Insulation product dust and debris
- Internal insulation (suspected)
- Internal lining
- Lagging
- Laminated cement sheeting (Tilux)
- Limit switch
- Loose fill insulation
- Low density asbestos fibre board (asbestos insulated board)
- Malthoid
- Masonite
- Masonry
- Mastic
- Mattresses
- Metal
- Millboard
- Millboard or paper-backed vinyl sheet
- Mineral fibre tiles
- Mortar
- Moulded cement products
- Moulded sheet
- Naturally occurring
- Non-fibrous backed vinyl sheet and adhesive
- Paint
- Paper
- Pebble rendered cement sheeting
- Pipe lagging residues
- Plaster
- Plastic
- Polyester
- Polystyrene
- Profiled roof sheeting
- Putty
- Rainwater guttering
- Render
- Resinous block
- Ridge capping
- Roof tiles
- Rope and string
- Rope or braided gasket
- Rubber gasket
- Rubber product debris
- Rubber products
- Silicone
- SMF
- SMF insulation
- Sprayed insulation
- Sprayed insulation (Limpet)
- Strawboard
- Strawboard lined with millboard
- Strawboard with cement sheet lining
- Tape
- Terrazzo
- Textured coating
- Timber
- Unknown
- Unknown source
- Valley guttering
- Vermiculite
- Vermiculite (plaster)
- Vinyl sheet
- Vinyl tiles
- Vinyl tiles and adhesive
- Water tanks
- Woven product

### ASSEA_Survey_Guide_Risk_Level__c — ASSEA Survey Guide Risk Level
*This is the risk level assigned in accordance with the ASSEA Survey Guide, 3 values High, Medium, Low*

- High
- Medium
- Low

### Clearance_Certificates_Available__c — Clearance Certificates Available (restricted)
*Certificate stating that particular asbestos items have been removed from the asset. Select Yes or No*

- Yes
- No

### Condition__c — Condition (restricted)
*Select the condition of the asbestos from the drop-down list provided. Further information can be found in the ACM Condition Fact Sheet in the Resource Centre*

- Poor
- Fair
- Stable
- Unknown
- N/A (negative)
- N/A (assumed negative)

### Disturbance_Potential_of_Material__c — Disturbance Potential (restricted)
*Occupational Health and Safety Regulations 2017 - regulation 226(4)(c)(iv) requires an asbestos register to identify 'whether the asbestos-containing material is likely to sustain damage or deterioration. This is commonly known as disturbance potential*

- Low
- Moderate
- High
- N/A (negative)
- Unknown
- N/A (assumed negative)

### Empty_Room_or_Not_Accessed_Room__c — Empty Room or Not Accessed Room (restricted)
*Choose "Empty Space/Area" for rooms confirmed empty. Select "Not Accessed Space/Area" for rooms not yet inspected.*

- Empty Space/Area
- Not Accessed Space/Area

### Estimated_Year_of_Manufacture__c — Estimated Year of Manufacture (restricted)
*Capture the estimated year of manufacture of the hazardous material item.*

[Years: 1700-2029 (330 values)]

### Frequency_of_Use__c — Frequency of Use (ACM) (restricted)
*Select the Frequency of use for this room from the drop-down list provided.*

- Every day
- Every day with intermittent breaks
- Once every 3–5 days
- Every 2–3 weeks
- Once every 2–3 months
- Annually or less frequently

### Friability_of_Material__c — Friability of Material (restricted)
*Friable ACMs can be easily reduced to powder by hand when dry. Non-friable or bonded ACMs are materials where the asbestos is firmly bound in the material.*

- Non-friable
- Friable

### Internal_External__c — Internal / External (restricted)
*Location of asbestos in relation to the asset. Select from drop-down list provided.*

- Internal
- External
- External & Internal

### Item_Name__c — Item Name (restricted)
*Select specific item, application or product from the dropdown list. If 'Other' then please specify.*

- Access hatch
- Air conditioning re-heat unit
- Air conditioning trunking
- Air handling unit
- Architrave
- Arc Shield
- Awning lining
- Backing panel
- Baffle
- Bagged waste
- Bain marie
- Ballustrade
- Basin
- Bath surround panels
- Batten(s)
- BBQ Top
- Beams
- Behind heater
- Bench top
- Benchtop lining
- Beneath carpet
- Beneath floor covering
- Beneath render
- Beneath roof
- Beneath sink
- Beneath slab(s)
- Board
- Boiler
- Boiler gasket
- Boxing
- Brake lining
- Bulkhead
- Cabinet lining
- Cable tray
- Calorifier
- Capping
- Ceiling
- Ceiling and awning
- Ceiling and vertical infill panel
- Ceiling and walls
- Ceiling cavity
- Ceiling Lining
- Ceiling Strapping
- Ceiling tiles
- Chalk board
- Chiller unit
- Chimney
- Cistern
- Cistern boxing
- Cladding
- Cladding brackets
- Clerestorey eaves
- Clutch pad
- Coils (electrical)
- Cold water service
- Columns
- Communications pit
- Compressor(s)
- Conduit
- Contact panel
- Contaminated soil
- Core sample
- Cornices
- Counter top
- Cover
- Cover battens
- Cubicle partition(s)
- Culvert cover
- Cupboard
- Dado wall
- Debris
- Decking
- Desk
- Door
- Door frame
- Door seal
- Down pipe
- Drain cover
- Draining board
- Drip Guard
- Duct cover
- Ductwork
- Ductwork flange joint
- Ductwork insulation
- Dumb waiter
- Dust
- Dust and debris
- Eave and awning
- Eave and porch ceiling
- Eave lining
- Electrical board
- Electrical cupboard
- Electrical cupboard door
- Electrical cupboard lining
- Electrical cables
- Electrical components
- Electrical meter
- Electrical terminal block
- End caps
- Engine/motor
- Exhaust
- Expansion joint
- Extraction cover
- Fascia
- Fencing
- Filing cabinet
- Fire blanket
- Fire curtain
- Fire door(s)
- Fire door frame
- Fire fighting equipment
- Fire hose cupboard lining
- Fireplace
- Fireproof cupboard
- Fire proofing
- Flammable good cabinet
- Flange joints
- Flash guards
- Flashing
- Floor
- Floor (below screed)
- Floor and walls
- Floor Cavity/void
- Floor covering
- Floor covering (beneath carpet)
- Floor covering (lower layer)
- Floor covering (upper layer)
- Floor covering adhesive
- Floor covering lining
- Flooring
- Floor penetration
- Floor underlay
- Flower Pot(s)
- Flue
- Formwork
- Framework (timber/metal)
- Fume cupboard
- Furnace
- Fuse box
- Fuse cartridge
- Gable lining
- Gasket(s)
- Gas mask
- Gas meter
- Gatic
- Gatic cover
- Gauze mats
- Gland Packing
- Glove
- Gutter
- Gutter debris
- Header tank
- Heater
- Heater flue
- Heating coils
- Heat mats
- Hessian
- Hot plate
- Hot water system
- HRC Fuse
- Illegal dump
- Incinerator
- Incinerator flue
- Incubator lining
- In cupboard
- Infill panels
- Infill panels below windows
- Inspection hatch
- Insulation
- Internal components
- Internal lining
- Ironing board
- Joint
- Kickboards
- Kiln lining
- Lid
- Lift car
- Lift landing doors
- Lift motor
- Light fitting
- Lightswitch
- Lining
- Lining to ceramic tiles
- Lining to tiles
- Louvres
- Lower walls
- Membrane
- Meter box
- Naturally occuring
- Other
- Oven
- Oven door seal
- Overspray
- Packing material
- Panel(s)
- Parapet wall
- Partitions
- Partition Wall(s)
- Pebblecrete joint
- Penetration packing
- Penetration sealant
- Pie warmer
- Pipework
- Pipework brackets
- Pipework flange joints
- Pipework insulation
- Pipework joint
- Pit
- Plant and equipment
- Plinth
- Porch
- Porch ceiling
- Porch floor
- Porch stoop
- Pothead pitch
- Pump flange joints
- Rainwater goods
- Reheat unit (to ductwork)
- Residual debris
- Retaining wall
- Return air plenum
- Ridge capping
- Riser
- Rock sample
- Roof
- Roof cavity
- Roof covering
- Roofing
- Safe
- Sanitary incinerator
- Seal
- Seat
- Sewer Pit
- Shelving
- Shower and bath surrounds
- Shower Cubicle
- Shower screen
- Sign
- Sink unit
- Skirting
- Soffit
- Soffit penetration
- Soil debris
- Speaker
- Splashback
- Splashback lining
- Stairwell
- Stored item(s)
- Strapping/beading
- Stump packing
- Subfloor
- Suspended ceiling
- Switch (Pitch)
- Switchboard
- Switchboard cupboard lining
- Switchboard insulation
- Switchboard internal wall linings
- Switchboard lining
- Table top
- Textured coating
- Throughout
- Tile backing
- Toilet cistern
- Toilet seat
- Trolley
- Underside of bath
- Underside of floor
- Underside of roof
- Unknown
- Upper wall(s)
- Urinal
- Urinal backing
- Valve
- Vent
- Vent cover
- Verandah
- Void
- Wall(s)
- Wall and gable lining
- Wall beading
- Wall cavity/void
- Wall cladding
- Wall covering
- Wall lining
- Wall panelling
- Walls and ceiling
- Washer
- Waste pipe
- Water pipe
- Waterproofing
- Water tank
- Window frame
- Window infill panels
- Window sill

### Labelled__c — Labelled (restricted)
*Is the item labelled or not? If Yes, please enter details.*

- Yes
- No

### Licence_Class__c — Licence Class (restricted)

- Class A
- Class B

### Out_of_scope__c — Out of Scope (restricted)

- ACM Out of Scope
- Asset Out of Scope
- Organisation Out of Scope

### Public_Access__c — Public Access (ACM) (restricted)
*Can the public access this room? Select Yes or No*

- Yes
- No

### Reason_for_Unknown__c — Reason for Unknown (restricted)
*This field is required if any of the following fields have a value of "Unknown": ACM Product Type, Condition, Disturbance Potential, or Item Name.*

- Biological hazard
- Confined/restricted space
- Demolition or dismantling required
- Electrical hazard
- Energised plant/equipment
- Entry point obstructed
- Height/fall risk
- Heritage restrictions
- Located below ground
- Locked
- No entry point
- Not authorised to access
- Occupied at time of survey
- Under third party management

### Removal_Limitations__c — Removal Limitations (restricted)
*Hidden field used to capture Clearance Certificate form inputs*

- Yes
- No

### Removal_Status__c — Removal Status (restricted)

- Assumed Removed
- Removed
- Unable To Be Removed

### Sample_Analysis_Result_Material_Status__c — Sample Result (restricted)
*Select the result of sample analysis from the drop-down list provided.*

- Positive
- Assumed Positive
- Negative
- Assumed Negative
- Negative - Treated as Positive

### Schools_A_Rating__c — Schools A Rating (restricted)
*Used for VSBA Schools only*

- A1
- A2
- A3
- A4
- A5

### Status__c — Status (restricted)

- Identified
- Assumed Removed
- Removed
- Disposed

### Unable_to_remove_reason__c — Unable To Remove Reason (restricted)
*Unable To Remove Reason*

- Damage To Sub Structure
- Fixed/Permanent Barrier To The ACM
- Inaccessibility
- Impact On Critical Infrastructure
- Hazard Can’t Be Addressed
- Disruption Of Core Operations
