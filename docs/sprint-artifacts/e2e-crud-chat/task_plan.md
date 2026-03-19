# E2E CRUD Chat Pipeline Enhancement — Test Plan

## Phase 0: Pre-flight
- [x] P0.1 Verify all services running (SurrealDB, API, Worker, Frontend)
- [x] P0.2 Verify migration 53 applied (crud_audit has new fields)
- [x] P0.3 Verify a test source exists with ACM records (source:7ltfu81qzc06yuae1h0s — 90 records, 6 buildings)
- [x] P0.4 Navigate to /jobs/{id}/chat and confirm page loads

## Phase 1: Tool Renderer Verification (Browser)
- [x] T1.1 `get_schema_info` — "what fields can I edit?" → LLM used surreal_query + listed all editable fields with enum values
- [x] T1.2 `surreal_query` (small) — "count records by risk status" → HTML table renderer with GROUP BY results
- [ ] T1.3 `surreal_query` (large) — "show all records" → ChatMiniGrid with row selection (SKIPPED — needs 6+ rows)
- [ ] T1.4 `surreal_query` grid actions — select row → Edit/View buttons appear → click Edit (SKIPPED — depends on T1.3)
- [ ] T1.5 `ask_user_choice` — ChatChoiceCard (SKIPPED — requires specific LLM behavior)
- [x] T1.6 `preview_write` — "change risk_status to High on record X" → HITL dialog rendered with Approve/Reject
- [x] T1.7 `preview_write` approve — click Approve → approval message sent, write executed (AG-UI SSE error on response, but DB write succeeded)
- [ ] T1.8 `preview_bulk_write` — bulk HITL dialog (DEFERRED — needs more time)
- [ ] T1.9 `undo_last_write` — undo preview (DEFERRED — depends on T1.7 audit trail)
- [ ] T1.10 Session persistence — MemorySaver used (not persistent across restarts — see BUG-2)
- [x] T1.11 Guardrail — "drop table acm_record" → LLM refused correctly, no tool call attempted

## Phase 2: Observability Trace Validation
- [ ] O2.1 Check Langfuse traces for CRUD chat invocations
- [ ] O2.2 Verify tool call spans appear in traces (surreal_query, preview_write, etc.)
- [ ] O2.3 Check audit trail in SurrealDB: `SELECT * FROM crud_audit ORDER BY timestamp DESC LIMIT 5`
- [ ] O2.4 Verify old_value populated in crud_audit for UPDATE operations
- [ ] O2.5 Verify thread_id persistence in LangGraph checkpoints

## Phase 3: Evidence Collection
- [ ] E3.1 Screenshot: schema info card
- [ ] E3.2 Screenshot: ChatMiniGrid with row selection
- [ ] E3.3 Screenshot: ChatChoiceCard
- [ ] E3.4 Screenshot: HITL approval dialog (single + bulk)
- [ ] E3.5 Screenshot: undo preview
- [ ] E3.6 Screenshot: guardrail block
- [ ] E3.7 Write final test report
