# ACM-AI Demo Validation — Progress Journal

## Session: 2026-02-22

### Completed
- Created evidence directory: `_bmad-output/demo-validation-2026-02-22/evidence/`
- Created tracking files: `failures.md`, `findings.md`
- Verified test PDF and ground truth exist
- **Phase 0**: Environment verified — SurrealDB (8000), API (5055), Frontend (8502) all running
- **Phase 2**: Document uploaded via API — source:m4mzywnujebfm0w1lxps, 33,595 chars, 23 chunks
  - Notebook created: notebook:nmxfu0ge6o38k0tht96y
  - Source processing completed in 2.6s
- **Browser screenshots captured**: 00-app-loaded.png, 01-sidebar-notebooks.png, 02-upload-dialog.png
- **Phase 9 (API-level)**: Settings endpoints validated
  - extraction settings: 8 config keys ✓
  - field config: fields, enums, business rules ✓
  - field mapping: 47 mappings ✓
  - BAR templates: endpoint works (0 templates) ✓
  - models: 51 models configured ✓
- **Phase 6 (API-level)**: Graph endpoints work (empty until extraction)
- **Phase 7 (API-level)**: AG-UI chat health OK (supervisor agent)
- **Phase 8 (API-level)**: Export endpoints return 404 with no records (finding logged)

### Blockers
1. **Worker not running** — extraction commands submit but don't execute. Worker health shows "unknown, pid: null"
2. **Playwright MCP crashed** — `browser_run_code` caused MCP disconnection. Need restart for browser screenshots.

### Failures Logged
- FAIL-001: Turbopack _buildManifest.js race condition (P2)
- FAIL-002: Landing CTA links to /sources not /documents (P3)
- FAIL-003: Worker not running — blocks extraction (P0)
- FAIL-004: Export 404 on empty records (P3)

### Reboot Check
1. **Last milestone**: API-level validation of settings, graph, chat, export endpoints
2. **Active task**: Phase 3 blocked on worker startup
3. **Blockers**: Worker process needed; Playwright MCP needs restart
4. **Last modified files**: `failures.md`, `progress.md`, `findings.md`
5. **Next action**: Once worker starts → re-trigger extraction → validate extraction pipeline → AG Grid → exports

### Key IDs
- Notebook: `notebook:nmxfu0ge6o38k0tht96y`
- Source: `source:m4mzywnujebfm0w1lxps`
- Extraction command: `command:7307hhxff0zlzfxwi68v`

---

## Session: 2026-02-23 (E18-S5 — Extraction Quality)

### Completed
- **E18-S5 Tasks 1-2**: Prompt template improvements applied to BOTH `building_extraction.jinja` and `extraction.jinja`
  - ACM item vs equipment/location distinction (with examples table)
  - "No Access" inclusion rule (extraction rule 7)
  - ACM Product Vocabulary Guide (30+ canonical SpecificUses)
- **E2E test matching**: Upgraded to three-tier strategy (sample_no → composite key → room+location fuzzy)
- **Fallback JSON parser**: Handles OpenRouter structured output failures (extracts JSON from markdown code blocks)
- **max_tokens**: Increased fallback from 8192 to 16384
- **E2E result**: 27/31 (87%), up from 26/31 (84%)
- **Commits**: `dce30de`, `0b05bda`, `a5d57cb` pushed to main

### Deep Research: 4 Remaining Misses
- Read raw PDF text (PyMuPDF) for all 4 missing records
- Analyzed content preprocessing pipeline (`_preprocess_samp_format`)
- Cross-referenced with ground truth CSV
- Documented root causes and 5 fix methods in `extraction-quality-research.md`

### Key Findings
1. **No Access items** (#3, #4): Preprocessor has NO marker for "No access" text — only `ACM DETECTED` and `NO ASBESTOS` markers exist. LLM sees 12+ dashes then "No access" text — treats as non-entry.
2. **Auto Battery Charger fuse** (#1): PDF says "Fuses" not "Fuse cartridge" — vocabulary mapping needed.
3. **East Ductwork flange** (#2): PDF says "Flange mastic" but CSV expects "Flange joints" — likely a test matching issue, not extraction issue.
4. **OpenRouter compatibility**: `with_structured_output()` fails consistently — fallback parser now handles this.

### Next Steps
1. Implement Fix A: Inject `>>> NO ACCESS: ...` markers in `_preprocess_samp_format()`
2. Investigate Fix C: Check if record #2 is extracted under different name
3. Implement Fix B: "Fuses" → "Fuse cartridge" vocabulary mapping
4. Re-run E2E test to validate
5. Update E18-S5 story based on results
