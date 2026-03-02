# Building__c — Field Reference

**Object:** Building__c (label: Asset Class)  
**Total fields:** 143  **Custom fields:** 130  **Picklist fields:** 18

## Field Table

| # | API Name | Label | Type | Length | Nillable | Custom | Calc | Updateable | Notes |
|---|----------|-------|------|--------|----------|--------|------|------------|-------|
| 1 | ABAR_QR_Code__c | ABAR QR Code | string | 1300 | Y | Y | Y |  | Formula; QR Code for specific record |
| 2 | ABAR_Unique_Code__c | ABAR Unique Code | string | 255 | Y | Y |  | Y | Generate the Asset QR code for ABAR community |
| 3 | ACM_Snapshot_In_Progress__c | ACM Snapshot In Progress | boolean |  |  | Y |  | Y | This check will be checked if any ACM Snapshot batch job is in progress |
| 4 | Additional_Comments__c | Additional Comments | textarea | 131072 | Y | Y |  | Y |  |
| 5 | Addressify_Building_Name__c | Addressify Asset Name | string | 255 | Y | Y |  | Y | Addressify asset name is different to the VAEA Asset name |
| 6 | Address_Component_Flag__c | Address Component Flag | string | 255 | Y | Y |  | Y |  |
| 7 | AIRHaz_ABAR_Unique_Code__c | AIRHaz ABAR Unique Code | string | 255 | Y | Y |  | Y | Regenerate the Asset QR code for ABAR community in Airhaz app |
| 8 | Asbestos_Register_Available__c | Asbestos Register Available | picklist | 255 | Y | Y |  | Y | Restricted picklist; Is the Asbestos Register Available as required by OHS? Select Yes or No |
| 9 | Audit_Report_Available__c | Audit Report Available | picklist | 255 | Y | Y |  | Y | Restricted picklist; The Audit Report usually accompanies the asbestos register. Select yes or No. |
| 10 | Australian_Building_Address_Only__c | Australian Asset Address Only | boolean |  |  | Y | Y |  | Formula |
| 11 | BLD18CharID__c | BLD18CharID | string | 1300 | Y | Y | Y |  | Formula |
| 12 | Building_Address_LGA__c | Asset Address LGA | picklist | 255 | Y | Y |  | Y | Restricted picklist; The Local Government Area (LGA) is derived automatically using the Meshblock ... |
| 13 | Building_Address_Map__c | Asset Address Map | string | 1300 | Y | Y | Y |  | Formula; Lookup Google Maps using Asset Location or Asset Address |
| 14 | Building_Address_Region__c | Region Type | picklist | 255 | Y | Y |  | Y | Restricted picklist; The local government area in which the asset address is located |
| 15 | Building_Address__c | Asset Address | string | 255 | Y | Y |  | Y | Enter the level, number and street address for this asset |
| 16 | Building_Category__c | Asset Category | picklist | 255 | Y | Y |  | Y | Dependent on Building_Type__c; Restricted picklist; Select from the dropdown list provided in the Resource Centre Tab |
| 17 | Building_GPS_Location__c | Asset GPS Location | location |  | Y | Y |  |  | Geocodes for asset address using mobile app GPS |
| 18 | Building_GPS_Location__Latitude__s | Asset GPS Location (Latitude) | double |  | Y | Y |  | Y |  |
| 19 | Building_GPS_Location__Longitude__s | Asset GPS Location (Longitude) | double |  | Y | Y |  | Y |  |
| 20 | Building_In_Audit__c | Asset In Audit | double |  | Y | Y | Y |  | Formula |
| 21 | Building_Location__c | Asset Location | location |  | Y | Y |  |  | Geocodes for asset address |
| 22 | Building_Location__Latitude__s | Asset Location (Latitude) | double |  | Y | Y |  | Y |  |
| 23 | Building_Location__Longitude__s | Asset Location (Longitude) | double |  | Y | Y |  | Y |  |
| 24 | Building_Name__c | Asset Name (provided by Gov Agency) | string | 255 |  | Y |  | Y | Name of the Asset |
| 25 | Building_Out_Of_Scope_Comments__c | Asset Out of Scope Comments | textarea | 131072 | Y | Y |  | Y | Comments related to why Asset Out Of Scope is checked |
| 26 | Building_Out_Of_Scope_New__c | Asset Out of Scope | picklist | 255 | Y | Y |  | Y | By selecting a value, it identifies the asset as being out of VAEA’s scope fo... |
| 27 | Building_Risk_Rating_Color_Code__c | Asset Rating Color Code | string | 1300 | Y | Y | Y |  | Formula |
| 28 | Building_Risk_Rating__c | Asset Rating | string | 255 | Y | Y |  | Y | This the system generated rating for the assets level of activity usage |
| 29 | Building_Type__c | Asset Type | picklist | 255 |  | Y |  | Y | Restricted picklist; Select from the dropdown list provided in the Resource Centre Tab |
| 30 | Building_Unique_ID__c | Asset Unique ID (If Applicable) | string | 255 | Y | Y |  | Y | Enter Agency's unique Asset ID if applicable. |
| 31 | Capital_Works_Project_Provide_Details__c | Capital Works Project/ Provide Details | textarea | 131072 | Y | Y |  | Y |  |
| 32 | CoM_Full_ID__c | CoM Full ID | string | 1300 | Y | Y | Y |  | Formula |
| 33 | Com_Local_Name__c | Com Local Name | string | 255 | Y | Y |  | Y |  |
| 34 | Com_Parcel_ID__c | Com Parcel ID | string | 255 | Y | Y |  | Y |  |
| 35 | CoM_Reserved_ID__c | CoM Reserve ID | string | 255 | Y | Y |  | Y |  |
| 36 | Com_SPI__c | SPI | string | 255 | Y | Y |  | Y |  |
| 37 | Construction_Type__c | Construction Type | string | 100 | Y | Y |  | Y | Materials used in the construction of the asset’s structure. For example. ‘Fi... |
| 38 | Country__c | Country | string | 255 | Y | Y |  | Y |  |
| 39 | CreatedById | Created By ID | reference | 18 |  |  |  |  | -> User |
| 40 | CreatedDate | Created Date | datetime |  |  |  |  |  |  |
| 41 | Daily_Duration__c | Daily Duration | picklist | 255 | Y | Y |  | Y | How many hours of the day on average is the asset accessed |
| 42 | Date_of_Audit_Report__c | Date of Audit Report | date |  | Y | Y |  | Y | The date that the most recent assessment took place |
| 43 | Date_of_Inspection__c | Date of Most Recent Item Inspection | date |  | Y | Y | Y |  | Formula; Date is calculated from the latest ACM snapshot of all underlying ACMs |
| 44 | Date_of_Most_Recent_Inspection__c | Date of Most Recent Inspection | date |  | Y | Y | Y |  | Formula; Date is calculated from the latest Asset snapshot of all underlying Asset sna... |
| 45 | Demolished_Status__c | Demolished Status | picklist | 255 | Y | Y |  | Y | Restricted picklist |
| 46 | Demolition_Comments__c | Demolition Comments | textarea | 32768 | Y | Y |  | Y |  |
| 47 | Demolition_Date__c | Demolition Date | date |  | Y | Y |  | Y |  |
| 48 | Demolition_Type__c | Demolition Type | picklist | 255 | Y | Y |  | Y | Restricted picklist |
| 49 | Department_Name__c | Department Name | string | 1300 | Y | Y | Y |  | Formula |
| 50 | Department__c | Department | string | 1300 | Y | Y | Y |  | Formula |
| 51 | Dust_or_Soil_Sample_Cost__c | Dust or Soil Sample Cost | currency |  | Y | Y | Y |  | Formula; Calculates the cost of dust, debris or soil sampling based on number of those... |
| 52 | Estimated_Age__c | Estimated Asset Age | string | 1300 | Y | Y | Y |  | Formula; Calculated age of asset from Estimated Year Built |
| 53 | Estimated_Daily_Duration_of_use_Score__c | Estimated Daily Duration of Use Score | double |  | Y | Y |  | Y |  |
| 54 | Estimated_Year_Build_New__c | Estimated Year Built | picklist | 255 | Y | Y |  | Y | [Years: 1700-2029 (330 values)]; Used to calculate the estimated age of the asset. |
| 55 | Estimated_Year_Built__c | Estimated Date Built | date |  | Y | Y |  | Y | Used to calculate the estimated age of the asset |
| 56 | Est_Building_Size_m2__c | Est. Asset Size (m2) | string | 255 | Y | Y |  | Y | An estimate of the structure’s area profile in square meters. |
| 57 | Est_Daily_Duration_of_use_Perc_Score__c | Est Daily Duration of use Perc Score | double |  | Y | Y |  | Y |  |
| 58 | External_ID__c | External ID | string | 255 | Y | Y |  | Y | External ID Field to simplify the Data Migration process |
| 59 | Frequency_of_Use_Percentage_Score__c | Frequency of Use Percentage Score | double |  | Y | Y |  | Y |  |
| 60 | Frequency_of_Use_Score__c | Frequency of Use Score | double |  | Y | Y |  | Y | This is derived from the VAEA risk model, based on the frequency the asset is... |
| 61 | Frequency_of_Use__c | Frequency of Use (Asset) | picklist | 255 |  | Y |  | Y | Restricted picklist; Select the frequency that the asset is used or accessed, refer to the Resourc... |
| 62 | GNAF_Id__c | GNAF Id | string | 255 | Y | Y |  | Y |  |
| 63 | GPS_Coordinates_provided_by_metro__c | GPS Coordinates (provided by Gov Agency) | string | 20 | Y | Y |  | Y |  |
| 64 | HSR_Airhaz_Unique_Code__c | HSR Airhaz Unique Code | string | 255 | Y | Y |  | Y | Regenerate the Asset QR code for HSR community in Airhaz app |
| 65 | HSR_QR_Code__c | HSR QR Code | string | 1300 | Y | Y | Y |  | Formula |
| 66 | HSR_Unique_Code__c | HSR Unique Code | string | 255 | Y | Y |  | Y | Unique Code used to generate the Asset QR code for HSR community |
| 67 | Hygienist_Inspection_Report_Prep_Cost__c | Hygienist Inspection Report Prep Cost | currency |  | Y | Y | Y |  | Formula; Calculates the cost of preparing an asbestos survey report based on number of... |
| 68 | Hygienist_Travel_Cost__c | Hygienist Travel Cost | currency |  | Y | Y | Y |  | Formula; Calculates the cost of the hygienists travel based on the Hygienist Travel Ti... |
| 69 | Hygienist_Travel_KM_Cost__c | Hygienist Travel KM Cost | currency |  | Y | Y | Y |  | Formula; Calculates cost of travel a hygienist based on Hygienist Travel field multipl... |
| 70 | Hygienist_Travel_KM__c | Hygienist Travel KM | double |  | Y | Y |  | Y | Calculates the KMs travelled by the hygienist (from Spring St Melb to asset a... |
| 71 | Hygienist_Travel_Time_in_hours__c | Hygienist Travel Time (in hours) | double |  | Y | Y |  | Y | Calculates the estimated time (hrs) taken by the hygienist (using Google trav... |
| 72 | Id | Record ID | id | 18 |  |  |  |  |  |
| 73 | IsDeleted | Deleted | boolean |  |  |  |  |  |  |
| 74 | Is_Building_Merge_Running__c | Is Asset Merge Running | boolean |  |  | Y |  | Y | Shows whether current asset record has a ongoing asset merge (VS-501) |
| 75 | LastActivityDate | Last Activity Date | date |  | Y |  |  |  |  |
| 76 | LastModifiedById | Last Modified By ID | reference | 18 |  |  |  |  | -> User |
| 77 | LastModifiedDate | Last Modified Date | datetime |  |  |  |  |  |  |
| 78 | LastReferencedDate | Last Referenced Date | datetime |  | Y |  |  |  |  |
| 79 | LastViewedDate | Last Viewed Date | datetime |  | Y |  |  |  |  |
| 80 | Last_Print_Date__c | Last Print Date | datetime |  | Y | Y |  | Y |  |
| 81 | Level_of_Activity_Percentage_Score__c | Level of Activity Percentage Score | double |  | Y | Y |  | Y |  |
| 82 | Level_of_Activity_Score__c | Activity Score | double |  | Y | Y |  | Y |  |
| 83 | Level_of_Activity__c | Level of Activity | picklist | 255 | Y | Y |  | Y | The intensity of the activity in the asset |
| 84 | Meshblock2016__c | Meshblock2016 | string | 255 | Y | Y |  | Y |  |
| 85 | Meshblock__c | Meshblock | string | 255 | Y | Y |  | Y |  |
| 86 | Mobile_Plant_Operating_Percentage_Score__c | Mobile Plant Operating Percentage Score | double |  | Y | Y |  | Y |  |
| 87 | Mobile_Plant_Operating_Score__c | Mobile Plant Operating Score | double |  | Y | Y |  | Y |  |
| 88 | Mobile_Plant__c | Mobile Plant | picklist | 255 | Y | Y |  | Y | Whether mobile plant (e.g. forklifts, scissor lifts etc.) is used in the asse... |
| 89 | Name | Asset Code | string | 80 | Y |  |  | Y |  |
| 90 | No_Identified_ACMs_Note__c | No Identified ACMs Note | textarea | 255 | Y | Y |  | Y | Detail what assessment has occurred to determine that no ACMs are present |
| 91 | No_Identified_ACMs__c | No Identified ACMs | boolean |  |  | Y |  | Y | Select this checkbox if the asset has been identified as containing no ACMs (... |
| 92 | Number_of_ACMs__c | Number of ACMs | double |  | Y | Y | Y |  | Formula; Count of all positive ACMs in this Asset that have not been removed |
| 93 | number_of_ACM_Product_type_not_Unknown__c | number of ACM Product type not Unknown | double |  | Y | Y | Y |  | Formula |
| 94 | Number_of_ACM_Product_type_Unknown__c | Number of ACM Product type Unknown | double |  | Y | Y | Y |  | Formula |
| 95 | Number_of_Items__c | Number of Items | double |  | Y | Y | Y |  | Formula; Count of total number of items in this Building |
| 96 | Number_of_Levels__c | Number of Levels | picklist | 255 | Y | Y |  | Y | Restricted picklist; The number of levels in the asset including ground level and levels below gro... |
| 97 | Organisation_Name__c | Organisation Name | string | 1300 | Y | Y | Y |  | Formula |
| 98 | Organisation_Parent__c | Organisation Parent | reference | 18 | Y | Y |  | Y | -> Account; Hidden lookup field populated automatically with the Asset Org's Parent Org |
| 99 | Organisation_Sector_Grouping__c | Organisation Sector Grouping | string | 1300 | Y | Y | Y |  | Formula; Sector group of related organisation |
| 100 | Organisation_Sub_Type__c | Organisation Sub Type | string | 1300 | Y | Y | Y |  | Formula; Sub type of related organisation |
| 101 | Organisation_Total_Buildings_With_ACMs__c | Organisation Total Assets With ACMs | double |  | Y | Y | Y |  | Formula; Total assets count of related organisation that contain ACMs |
| 102 | Organisation__c | Organisation | reference | 18 |  | Y |  | Y | -> Account; Please choose the Agency related to the Asset |
| 103 | Owned_or_Leased__c | Owned or Leased | picklist | 255 | Y | Y |  | Y | Restricted picklist; Select the legal title status of this asset from the drop-down list provided. |
| 104 | OwnerId | Owner ID | reference | 18 |  |  |  | Y |  |
| 105 | Phase1_and_Phase_2_ACM__c | Phase1 and Phase 2 ACM | double |  | Y | Y | Y |  | Formula |
| 106 | Possible_Capital_Works_Project__c | Possible Capital Works Project | boolean |  |  | Y |  | Y |  |
| 107 | Postcode__c | Postcode | string | 255 | Y | Y |  | Y |  |
| 108 | Power_of_One__c | Asset Count | double |  | Y | Y | Y |  | Formula |
| 109 | Project_Management_Cost__c | Project Management Cost | currency |  | Y | Y | Y |  | Formula; Calculates cost of project management tasks undertaken as part of an asbestos... |
| 110 | Proportional_Total_Building_Risk_Score__c | Asset Rating Score | double |  | Y | Y | Y |  | Formula; Total asset rating score out of 100 "This is the system generated rating for ... |
| 111 | Proportional_Total_Building_Score_HT__c | Proportional Total Asset Score HT | double |  | Y | Y |  | Y |  |
| 112 | PSB_District_Region__c | PSB District/Region | string | 255 | Y | Y |  | Y | details the district or regional designation used by the PSB |
| 113 | Public_Access_Percentage_Score__c | Public Access Percentage Score | double |  | Y | Y |  | Y |  |
| 114 | Public_Access_Score__c | Public Access Score | double |  | Y | Y |  | Y |  |
| 115 | Public_Access__c | Public Access (Asset) | picklist | 255 |  | Y |  | Y | Restricted picklist; Can the public access this asset ? Select Yes or No |
| 116 | QR_Code__c | QR Code | string | 1300 | Y | Y | Y |  | Formula |
| 117 | RecordTypeId | Record Type ID | reference | 18 | Y |  |  | Y | -> RecordType |
| 118 | Responsible_Agency_Department__c | Responsible Agency/Department | string | 1300 | Y | Y | Y |  | Formula |
| 119 | Responsible_Portfolio__c | Responsible Portfolio | reference | 18 | Y | Y |  | Y | -> Account; Responsible government department for this asset. |
| 120 | Responsible_Portofolio_Name__c | Responsible Portofolio Name | string | 1300 | Y | Y | Y |  | Formula |
| 121 | Roof_Type__c | Roof Type | string | 100 | Y | Y |  | Y | The roof’s construction material. For example, ‘Metal’ or ‘Tile’ or ‘Slate’ |
| 122 | School_UID__c | School UID | string | 255 | Y | Y |  | Y |  |
| 123 | SED_Name__c | SED Name | string | 255 | Y | Y |  | Y | State Electoral Division derived from the Asset Address meshblock ID |
| 124 | Site_Name__c | Site Name (If Applicable) | string | 255 | Y | Y |  | Y | Enter the common name given to the location of the asset e.g. Park |
| 125 | Standard_Sample_Cost__c | Standard Sample Cost | currency |  | Y | Y | Y |  | Formula; Calculates the cost of standard sampling based on number of items within the ... |
| 126 | Standard_Sample_Time_Cost__c | Standard Sample Time Cost | currency |  | Y | Y | Y |  | Formula; Calculates the cost of undertaking standard sampling based on number of stand... |
| 127 | State__c | State | string | 255 | Y | Y |  | Y |  |
| 128 | Suburb__c | Suburb | string | 255 | Y | Y |  | Y |  |
| 129 | SystemModstamp | System Modstamp | datetime |  |  |  |  |  |  |
| 130 | Total_ACM_Weight__c | Total ACM Weight (tonnes) | double |  | Y | Y | Y |  | Formula; Total weight of all ACMs in the asset. |
| 131 | Total_Cost__c | Total Cost | currency |  | Y | Y | Y |  | Formula; Estimated Total Cost for Asset Verification |
| 132 | Total_Estimated_Reinspection_Cost__c | Total Estimated Reinspection Cost | currency |  | Y | Y | Y |  | Formula |
| 133 | Total_Item_Removal_Cost_Custom__c | Total ACM Removal Cost (Schedule 4) | currency |  | Y | Y | Y |  | Formula; Estimated Schedule - Generated by VAEA |
| 134 | Total_Item_Removal_Cost_std__c | Total ACM Removal Cost (Schedule 1) | currency |  | Y | Y | Y |  | Formula; Estimated Schedule - Generated by Removal Industry |
| 135 | Total_Item_Removal_Cost_VSBA_Simple__c | Total ACM Removal Cost (Schedule 3) | currency |  | Y | Y | Y |  | Formula; Estimated Schedule - Friable/Non-Friable Based on School Removal Project |
| 136 | Total_Item_Removal_Cost_VSBA__c | Total ACM Removal Cost (Schedule 2) | currency |  | Y | Y | Y |  | Formula; Estimated Schedule – Generated by multiple values based on School Removal Pro... |
| 137 | Total_Item_Weight__c | Total Item Weight (tonnes) | double |  | Y | Y | Y |  | Formula |
| 138 | Total_Number_of_Dust_or_Soil_Sample_Item__c | Total Number of Dust or Soil Sample Item | double |  | Y | Y | Y |  | Formula; Calculates the number of items classified as dust, debris or soil within the ... |
| 139 | Total_Weight__c | Total Weight (tonnes) | double |  | Y | Y | Y |  | Formula; Total weight of all items in the asset. |
| 140 | Travel_Cost_Contingency__c | Travel Cost Contingency | currency |  | Y | Y | Y |  | Formula; Add an amount equivalent to 10% of the Hygienist Travel Cost travel cost as a... |
| 141 | Unique_Asset_Class_Code__c | Unique Asset Class Code | string | 30 |  | Y |  |  | Used to generate the unique incremental ID numbers added to the Asset Code fo... |
| 142 | Verification_Cost_Contingency__c | Verification Cost Contingency | currency |  | Y | Y | Y |  | Formula; Add an amount equivalent to 15% to the costs of verifications as a contingency |
| 143 | Within_Your_Portfolio__c | Within Your Portfolio | picklist | 255 | Y | Y |  | Y | Restricted picklist; Are you responsible for this asset? Select Yes or No. |

## Picklist Fields — Full Value Lists

### Asbestos_Register_Available__c — Asbestos Register Available (restricted)
*Is the Asbestos Register Available as required by OHS? Select Yes or No*

- Yes
- No

### Audit_Report_Available__c — Audit Report Available (restricted)
*The Audit Report usually accompanies the asbestos register. Select yes or No.*

- Yes
- No

### Building_Address_LGA__c — Asset Address LGA (restricted)
*The Local Government Area (LGA) is derived automatically using the Meshblock or Postcode of the asset address. No manual input is required.*

- Alpine Shire Council
- Ararat Rural City Council
- Ballarat City Council
- Banyule City Council
- Bass Coast Shire Council
- Baw Baw Shire Council
- Bayside City Council
- Benalla Rural City Council
- Boroondara City Council
- Borough of Queenscliffe
- Brimbank City Council
- Buloke Shire Council
- Campaspe Shire Council
- Cardinia Shire Council
- Central Goldfields Shire Council
- City of Casey
- Colac-Otway Shire Council
- Corangamite Shire Council
- Darebin City Council
- East Gippsland Shire Council
- Frankston City Council
- French Island (Unincorporated)
- Gannawarra Shire Council
- Glen Eira City Council
- Glenelg Shire Council
- Golden Plains Shire Council
- Greater Bendigo City Council
- Greater Dandenong City Council
- Greater Geelong City Council
- Greater Shepparton City Council
- Hepburn Shire Council
- Hindmarsh Shire Council
- Hobsons Bay City Council
- Horsham Rural City Council
- Hume City Council
- Indigo Shire Council
- Kingston City Council
- Knox City Council
- Latrobe City Council
- Loddon Shire Council
- Macedon Ranges Shire Council
- Manningham City Council
- Mansfield Shire Council
- Maribyrnong City Council
- Maroondah City Council
- Melbourne City Council
- Melton City Council
- Merri-bek City Council
- Mildura Rural City Council
- Mitchell Shire Council
- Moira Shire Council
- Monash City Council
- Moonee Valley City Council
- Moorabool Shire Council
- Mornington Peninsula Shire Council
- Mount Alexander Shire Council
- Moyne Shire Council
- Murrindindi Shire Council
- Nillumbik Shire Council
- Northern Grampians Shire Council
- Port Phillip City Council
- Pyrenees Shire Council
- Southern Grampians Shire Council
- South Gippsland Shire Council
- Stonnington City Council
- Strathbogie Shire Council
- Surf Coast Shire Council
- Swan Hill Rural City Council
- Towong Shire Council
- Wangaratta Rural City Council
- Warrnambool City Council
- Wellington Shire Council
- West Wimmera Shire Council
- Whitehorse City Council
- Whittlesea City Council
- Wodonga City Council
- Wyndham City Council
- Yarra City Council
- Yarra Ranges Shire Council
- Yarriambiack Shire Council

### Building_Address_Region__c — Region Type (restricted)
*The local government area in which the asset address is located*

- Barwon South West
- Gippsland
- Grampians
- Hume
- Loddon - Mallee
- Metro - Eastern
- Metro - Melbourne
- Metro - Northern
- Metro - Southern
- Metro - Western

### Building_Category__c — Asset Category (restricted) (dependent on Building_Type__c)
*Select from the dropdown list provided in the Resource Centre Tab*

- Agriculture
- Commercial and retail
- Correctional and justice facilities
- Defence and emergency services
- Educational and training facilities
- Factories, warehouses and shops
- Health services
- Housing and accommodation
- IT and communications
- Offices and professional services
- Public and family services
- Transport
- Unknown/other

### Building_Out_Of_Scope_New__c — Asset Out of Scope
*By selecting a value, it identifies the asset as being out of VAEA’s scope for removal and provides a reason for being out of scope.*

- Asset Out of Scope
- Organisation Out of Scope

### Building_Type__c — Asset Type (restricted)
*Select from the dropdown list provided in the Resource Centre Tab*

- Accommodation unit
- Activities shelter
- Administration
- Aged Care
- Airbase
- Ambulance garage
- Ambulance station
- Amenities
- Apartment
- Art centre
- Assembly hall
- Band room
- Barrier or Fencing
- Basketball court
- Bicycle enclosure
- Bridge
- Building
- Building nursery
- Building room
- Bush nursing
- Business interruption
- Canteen
- Car
- CFA/FRV
- Child care
- Children’s centre
- Classroom
- Commercial
- Communication tower
- Community centre
- Community hall
- Community Health Centre
- Computer centre
- Concert hall
- Conference centre
- Consulting rooms
- Control building
- Control centre (train network)
- Control centre (tram network)
- Control room
- Court
- Crew room
- Curator house
- Day centre
- Dental clinic
- Depot
- Docklands studios
- Education centre
- Facility
- Factory
- Farm annexe
- Farm depot house
- Film vault
- Fire pump shed
- Flat
- Forklift
- Fruit shed
- Gallery
- Garage
- Grain storage shed
- Gymnasium
- Hall
- Hay shed
- Head office
- Health centre
- Hospital
- Hostel
- Hothouse
- House
- Housing - disability
- Housing - Other
- HQ
- Information centre
- Juvenile
- Leisure centre
- Level crossing
- Library
- Lodge
- Main building
- Multipurpose hall
- Museum
- Nursing home
- Office
- Other
- Pavilion
- Pipe
- Plant and equipment
- Plant room
- Police Station
- Polyhouse
- Poultry pen
- Prison
- Pump house
- Radio tower
- Ranger's office
- Reception
- Recreation and sport
- Recreation centre
- Rehab
- Research facility
- Residence
- Retail
- Roadway
- Rotunda
- School
- Shed
- Shelter
- Shelter shed
- Shipping Container
- Shop / Kiosk
- Specialist clinic
- Stables
- Stockyard
- Storage Shed
- Storeroom
- TAFE
- Teacher house
- Tennis pavilion
- Theatre
- Toilet
- Tower
- Training centre
- Train maintenance facility
- Train station
- Train station precinct
- Train substation
- Train yard
- Tram depot
- Tram substation
- Transport depot
- Truck
- Tunnel
- Van
- Visitor centre
- Warehouse
- Workshop
- Youth camp

### Daily_Duration__c — Daily Duration
*How many hours of the day on average is the asset accessed*

- 24 hours
- 12 hours
- 8 hours (typical working day)
- 4 hours
- <4 hours

### Demolished_Status__c — Demolished Status (restricted)

- Demolished
- Partially Demolished

### Demolition_Type__c — Demolition Type (restricted)

- Planned - Part of Project
- Planned - Not Part of Project
- Unplanned

### Estimated_Year_Build_New__c — Estimated Year Built (restricted)
*Used to calculate the estimated age of the asset.*

[Years: 1700-2029 (330 values)]

### Frequency_of_Use__c — Frequency of Use (Asset) (restricted)
*Select the frequency that the asset is used or accessed, refer to the Resource Centre*

- Every day
- Every day with intermittent breaks
- Once every 3–5 days
- Every 2–3 weeks
- Once every 2–3 months
- Annually or less frequently

### Level_of_Activity__c — Level of Activity
*The intensity of the activity in the asset*

- Very high
- High
- Moderate
- low
- Very low

### Mobile_Plant__c — Mobile Plant
*Whether mobile plant (e.g. forklifts, scissor lifts etc.) is used in the asset or not*

- Yes
- No

### Number_of_Levels__c — Number of Levels (restricted)
*The number of levels in the asset including ground level and levels below ground.*

- 2
- 3
- 4
- 5
- 6
- 7
- 8
- 9
- 10
- 11
- 12
- 13
- 14
- 15
- 16
- 17
- 18
- 19
- 20
- 21
- 22
- 23
- 24
- 25
- 26
- 27
- 28
- 29
- 30
- 31
- 32
- 33
- 34
- 35
- 36
- 37
- 38
- 39
- 40
- 41
- 42
- 43
- 44
- 45
- 46
- 47
- 48
- 49
- 50
- 51
- 52
- 53
- 54
- 55
- 56
- 57
- 58
- 59
- 60
- 61
- 62
- 63
- 64
- 65
- 66
- 67
- 68
- 69
- 70
- 71
- 72
- 73
- 74
- 75
- 76
- 77
- 78
- 79
- 80
- 81
- 82
- 83
- 84
- 85
- 86
- 87
- 88
- 89
- 90
- 91
- 92
- 93
- 94
- 95
- 96
- 97
- 98
- 99
- 100

### Owned_or_Leased__c — Owned or Leased (restricted)
*Select the legal title status of this asset from the drop-down list provided.*

- Owned
- Leased

### Public_Access__c — Public Access (Asset) (restricted)
*Can the public access this asset ? Select Yes or No*

- Yes
- No

### Within_Your_Portfolio__c — Within Your Portfolio (restricted)
*Are you responsible for this asset? Select Yes or No.*

- Yes
- No
