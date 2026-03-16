# Edge Case Table Fixtures

Test fixtures for the ACM per-row extraction pipeline's Row Segmentation Engine.
All fixtures use realistic Australian school ACM data from "Broadmeadows Primary School, Main Block".

## Fixture Map

| Fixture | Edge Case | What It Tests |
|---------|-----------|---------------|
| `type_a_standard.json` | Type A: Standard Single-Page Table | Basic table parsing: 1 header + 5 data rows, 8 columns, all cells row_span=1/col_span=1 |
| `type_b_multipage.json` | Type B: Multi-Page Table | Array of 2 table objects (pages 3-4), same columns, no overlap — tests multi-page merge |
| `type_b_overlap.json` | Type B: Multi-Page + Overlap | Array of 2 table objects where last row of table 1 = first row of table 2 — tests deduplication |
| `type_c_merged_room.json` | Type C: Merged Room Cell | Room "Room 101" with `row_span=3` spanning 3 items — tests span registry + carried_forward_fields |
| `type_c_merged_level.json` | Type C: Nested Merged Cells | Level "Ground Floor" `row_span=5` + Room "Room 101" `row_span=3` + Room "Library" `row_span=2` — tests hierarchical merges |
| `type_e1_multiitem.json` | Type E1: Multi-Item Cell | Material cell with `\n`-separated items — tests `needs_llm_split=True` detection |
| `type_e2_note.json` | Type E2: Note/Comment Row | Row with single cell `col_span=8` containing "Note: ..." — tests note detection and skip |
| `type_e3_subheader.json` | Type E3: Sub-Header Row | Rows with `col_span=8` text "GROUND FLOOR" and "LEVEL 2 — FIRST FLOOR" — tests level regex and current_level tracking |
| `type_g_consultant_a.json` | Type G: Standard Headers | Standard column names: Room, Location, Material, etc. — baseline for column mapping |
| `type_g_consultant_b.json` | Type G: Non-Standard Headers | Different headers: Ref, Room/Area, Product Description, F/NF, Assessment, NATA No, Analysis, Amount — tests fuzzy COLUMN_ALIASES matching |
| `type_h_split.json` | Type H: Split/Fragmented Tables | Array of 2 table objects with different `num_cols` (5 vs 4), shared "Room" column — tests cross-table JOIN |
| `type_d_hierarchical.md` | Type D: Hierarchical Text | Building/Level/Room/Item hierarchy with no table — tests markdown regex fallback |
| `type_f_not_sampled.md` | Type F: Not Sampled / No Access | Inline text entries like "Room 103 — Not Sampled" — tests synthetic row creation |

## DoclingDocument JSON Format

Each JSON fixture uses the DoclingDocument table format from `docling.document_converter.export_to_dict()`.
Top-level keys: `num_rows`, `num_cols`, `table_cells`.

Each cell in `table_cells` has:
- `text` (string) — cell content
- `row_span` / `col_span` (int) — merge span (1 = normal)
- `start_row_offset_idx` / `end_row_offset_idx` (int) — 0-indexed row range
- `start_col_offset_idx` / `end_col_offset_idx` (int) — 0-indexed column range
- `column_header` (bool) — true for header row cells

Multi-table fixtures (Types B, H) are JSON arrays of table objects, each with an optional `_page_number` metadata field.

## Reference

See `v3.5/findings.md` section 2 for the full edge case catalog with frequency estimates and handling strategies.
