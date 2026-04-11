You are the EXTRACTION-PRE specialist in a 6-agent Phase 5 audit for the ACM-AI SF reconciliation sprint. READ-ONLY review. No code changes, no commits.

Working directory is /mnt/d/ailocal/acm-ai. Branch `feat/sf-reconciliation-20260411`.

## Context to read

1. `docs/cleanup/assumptions-and-decisions.md`
2. `docs/cleanup/session-log-2026-04-11.md`
3. `docs/sprint-artifacts/full-audit-2026-04-11/PHASE-1-FINDINGS.md`
4. `docs/sprint-artifacts/change-proposals/sprint-change-proposal-20260411-sf-reconciliation.md`
5. `git log --oneline main..HEAD`

## Your domain: pre-extraction (E1-S16..S19)

TOC extraction, document structure, building inventory, metadata extraction, page-level section tagging.

Inspect: `open_notebook/extractors/structure/*`, `open_notebook/extractors/metadata_extractor.py` (if exists), `open_notebook/graphs/acm_extraction.py` pre-extraction nodes, `prompts/acm/metadata_and_structure.jinja`, `page_tagging.jinja`, `building_inventory.jinja`, `metadata_extraction.jinja`.

## Questions to answer

1. Does pre-extraction populate any field that ends up in the SF export? Trace end-to-end.
2. Are the `*.jinja` prompts aligned with real SF field names per `config/sf-schema-snapshot.json`, or still asking for BAR-era fields?
3. Does BuildingInventory (E1-S17) write fields to BuildingRecord that sf_export now reads?
4. Does document metadata extraction (E1-S19) populate `BuildingRecord.date_of_audit_report`, `site_name`, etc.? Verify the connection works end-to-end.
5. Any pre-extraction outputs that NO ONE reads anymore (dead pipeline branches)? List for E38-S2.

## Output

1. Write findings to `docs/cleanup/phase-5-audit-extraction-pre.md` with sections: Scope, Findings, Recommendations, References (file:line).
2. Print a final ≤250-word summary starting with "=== EXTRACTION-PRE SUMMARY ===".

Be specific. No speculation. Exit cleanly when done.
