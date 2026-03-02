## Ground Truth CSVs

### Clutch_Broadmeadows.csv
- **Source PDF**: Clutch_Broadmeadows Police Station Div 5 34511-039 V2_done.pdf
- **Consultant**: Prensa Pty Ltd
- **Records**: 31
- **Buildings**: 1 (Broadmeadows Police Station)
- **Columns**: 43 (standard BAR format)

### Clutch_Alexandra.csv
- **Source PDF**: Clucth_Alexander_District_Hospital_Asbestos_Risk_Assessment_2020-09-07.pdf
- **Source BAR**: Clucth_Alexandra_District_BAR.xlsm (DATA ENTRY sheet, header row 3)
- **Consultant**: Greencap Pty Ltd
- **Records**: 43
- **Buildings**: 5 (Old Alexandra Hospital: 29, Mortuary Buildings: 7, VMO Accommodations: 4, Myrtle Street Clinic: 2, Pathology Department: 1)
- **Columns**: 47 (Greencap extended BAR format — 4 extra columns vs Broadmeadows)
- **Sample results**: Assumed Positive (17), Negative (14), Positive (8), Assumed Negative (4)
- **Note**: DB currently has 52 records (9 over-extracted). Ground truth is 43.

### Column Differences

Alexander (Greencap) has 4 extra columns not in Broadmeadows (Prensa):
- `FIRABILITY NAME EXCEL` (col 25)
- `ACM GROUP NAME EXCEL` (col 27)
- `Removal Comments` (col 45)
- `Photo Reference Number` (col 46)

All 43 Broadmeadows columns are present in Alexander. The shared columns use the same names. These differences are expected — different BAR template versions from different consultants.
