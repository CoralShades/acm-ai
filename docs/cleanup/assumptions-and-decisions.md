# Assumptions & Decisions — SF Reconciliation Sprint

Captured from the 6-round user interview at session start (2026-04-11).
These are durable decisions that should remain authoritative until
explicitly revisited. If any of these stops holding, pause and ask.

## Scope & Goal

**DEC-001 — Object scope:** Building__c + Item__c only. Other VAEA SF
objects (Project_ACM, Audit, Clearance Certificate, Removal Job, etc.)
are explicitly out of scope. Only fields literally extractable from ARA
PDFs count — no assumptions, no auto-defaults for fields the document
doesn't contain.

**DEC-002 — Object names:** Audit discovers canonical names from live
`sf sobject list`. Discovered: Building__c and Item__c are unchanged at
the API layer. The "Asset" / "Hazmat Item" vocabulary is a label-layer
rename only. No code rename needed.

**DEC-003 — Sync direction:** One-way push from ACM-AI → Salesforce via
Data Loader CSV export. No live REST API writes. No bidirectional pull
of existing SF records.

**DEC-004 — Non-SF fields disposition:** Hard-delete from code + DB.
No gradual deprecation. Deletions execute on a feature branch so they
can be reviewed before merge.

## Extraction Rules

**DEC-005 — Extraction is literal-only + deterministic mapping:** The
LLM extracts literal values from PDF rows/cover pages. Translation to
SF-accepted picklist values happens via a codified `bar_to_sf_mapping.yaml`
table. No free-form LLM reasoning over context, no inference.

**DEC-006 — Corrective RAG disposition (E1-S15):** Option C from research.
Keep E1-S14 contextual embeddings (clean — writes only to `enriched_text`
and `embedding` vector, not to SF-bound fields). Delete the LLM path in
E1-S15 (`_llm_correct_records` at `acm_extraction.py:1811`) that was
inferring values for four SF-bound fields (sample_result,
material_condition, friable, disturbance_potential). Surgical 1-line
removal per the research subagent's recommendation.

## Data Loader / Upsert

**DEC-007 — External_ID__c strategy:** Deterministic hash.
`ACM_{sha256(source_id + building_name)[:16]}`. Re-extracting the same
PDF produces identical IDs, so SF upsert updates in place instead of
creating duplicates.

**DEC-008 — Multi-PDF handling:** Each PDF = one Source = one extraction
= one export CSV. User links related PDFs manually via project code at
export time. No merge logic, no parent Project container. Out of scope
for this sprint.

**DEC-009 — Picklist sync:** Snapshot to `config/sf-schema-snapshot.json`,
committed to repo, refreshed manually via a command (TBD). No live fetch
on every extraction. No nightly cron. Deterministic, reviewable in PRs.

## Blockers

**DEC-010 — Item__c upsert blocker remediation:** Option (a) — VAEA SF
admin will fix `Item__c.External_ID__c` (`type=Text Area` →
`type=Text(255), externalId=true`). ACM-AI code is written assuming the
fix will land. Until it does, Item__c export stays dormant behind a
feature check or falls back to INSERT-only mode. This is an external
dependency the parent project must resolve out-of-band.

## Code Changes & Breaking Changes

**DEC-011 — Schema extension:** Deferred. Keep the existing 13 Item__c
fields in the row extraction schema. Extending to the full ~25
extractable fields is a follow-up story. Phase 2 does not extend schema.

**DEC-012 — Form gate for required Building fields:** Deferred to
follow-up story. All three required fields (Public_Access__c,
Frequency_of_Use__c, Organisation__c lookup) are actually present in the
Broadmeadows ground-truth CSV, so a form gate is a fallback feature, not
a hard prerequisite.

**DEC-013 — Chat edit scope:** CopilotKit chat is read-only Q&A +
propose-edits. Chat surfaces proposed cell edits as action cards; user
clicks Apply to commit. No direct write access from chat.

**DEC-014 — BAR→SF mapping UI:** User wants a frontend management UI
(says "we already have some parts made but not functioning"). Out of
scope for this session — flagged as follow-up story. Parent session
should grep for existing partial UI before building new.

## Testing

**DEC-015 — Test scorched earth:** `tests/` is listed as PROTECTED in
CLAUDE.md and the session banner. User explicitly authorized scorched
earth: delete everything under `tests/` + `frontend/tests/` + `*.spec.ts`
and rebuild via an agent team with access to tools, skills, MCP, and
context7. This decision overrides the protected-directory policy.

Deferred to a fresh session (context budget in current session too
pressured to run the rebuild agent team at quality).

## Branching & Commits

**DEC-016 — Branch strategy:** Feature branch
`feat/sf-reconciliation-20260411` off main. Not pushed to remote.
User reviews locally before opening a PR.

**DEC-017 — Commit strategy for pre-existing uncommitted work:** Single
snapshot commit `chore: snapshot before SF reconciliation` containing
the 66 modified/new files that existed before the session started.
Accepted the opacity trade-off because the user explicitly chose this
option in the interview.

## Session Execution

**DEC-018 — Checkpoint cadence:** Pause at the end of each phase for
user review. Phases 1, 2a, 2b, 4, 6 completed in-session. Phases 2c, 3,
5 deferred to fresh sessions.

**DEC-019 — Agent team model policy:** Per CLAUDE.md rule — team members
run on Sonnet or Haiku only, never Opus. Main thread stays on Opus for
synthesis and judgment calls.

**DEC-020 — RAG enrichment is chat-only, not extraction-path:** E1-S14
contextual embeddings feeds `enriched_text` and embeddings used by chat
and search. It does NOT write to fields that end up in the SF export.
Verified by RAG research subagent against `ITEM_SF_MAPPING` (which now
lives in `sf_export.py`). Safe to keep. Documented here so future
sessions don't re-litigate.
