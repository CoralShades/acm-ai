# ACM-AI Demo Validation — Findings Log

## Environment
- SurrealDB: port 8000, confirmed running via health endpoint (HTTP 200)
- FastAPI: port 5055 (user-started)
- Worker: background process (user-started)
- Frontend: port 8502 (user-started)
- **ALL LLM calls use OpenRouter** — NO direct Anthropic/OpenAI keys
- `.env` has `OPENROUTER_API_KEY=sk-or-v1-...`
- `.env` has `DEFAULT_EXTRACTION_MODEL=openrouter/deepseek/deepseek-r1-0528:free`

## Test Artifacts
- Test PDF: `docs/samplePDF/Clutch_Broadmeadows.pdf` — EXISTS
- Ground truth CSV: `docs/samplePDF/Clutch_Broadmeadows.csv` — 31 records
- E2E fixtures: `tests/e2e/fixtures/samps/broadmeadows-police-station-samp.pdf` — EXISTS
- Known baseline: 8/31 (Feb 10) → 26/31 after code fixes (Feb 22) → 27/31 after Fix A (Feb 23)

## Taxonomy Files (for E18-S5)
- `docs/samplePDF/instructions-sample/register_enums.json` — Contains "Fuse cartridge" (line 188), "Flange joints" (line 165) in SpecificUses
- `docs/samplePDF/instructions-sample/register_taxonomy.nonfriable.json` — T4: "Mastic" as product_type under Gasket group
- `docs/samplePDF/instructions-sample/register_row.schema.json` — BAR field schema
- `docs/samplePDF/instructions-sample/consultant_wording_rules.json` — Recommendation normalization rules

## Fix B Analysis: Product Vocabulary Normalization

**Root cause**: PDF text says "Fuses" (page 5 line 43). CSV expects "Fuse cartridge". The LLM may not map this abbreviation.

**Key validation**: Neither "Fuses" nor "Flange mastic" appear in SpecificUses (register_enums.json). Only "Fuse cartridge" and "Flange joints" are canonical BAR names.

**Approach**: Deterministic normalization in `_preprocess_samp_format()` BEFORE LLM sees the text.
- `\bFuses\b` → "Fuse cartridge"
- `\bFuse\b(?!\s+cartridge)` → "Fuse cartridge"
- `\bFlange\s+mastic\b` → "Flange joints"

**Insertion point**: After `processed = content` (line 304), BEFORE building/room marker injection (line 306).

## Fix C Analysis: Test Synonym Matching

**Root cause**: Record #2 (Roof / East Ductwork / Flange joints, sample 34511-039-015) may be extracted under name "Flange mastic" instead of "Flange joints".

**Three-tier matching gap**: If sample_no `34511-039-015` is split across lines and not extracted correctly, AND product name differs, Tier 2 (composite key) fails. Tier 3 (room+location) should catch it IF room name matches.

**Defense-in-depth**: Add PRODUCT_SYNONYMS between Tier 2 and Tier 3 to handle vocabulary variations without depending on Tier 3's fuzzy matching.

## Files to Modify
1. `open_notebook/graphs/acm_extraction.py` — PRODUCT_NORMALIZATIONS in _preprocess_samp_format()
2. `prompts/acm/extraction.jinja` — Vocabulary mapping table
3. `prompts/acm/building_extraction.jinja` — Vocabulary mapping table
4. `tests/test_broadmeadows_e2e.py` — PRODUCT_SYNONYMS + synonym-normalized matching
5. `tests/test_preprocess_samp.py` — Unit tests for product normalization
6. `docs/sprint-artifacts/e18-s5-extraction-quality-fuse-cartridge-no-access.md` — Status update
