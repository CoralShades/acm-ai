# E36-S2: E35 Fix Re-verification

## Story Metadata
| Field | Value |
|-------|-------|
| Story ID | E36-S2 |
| Title | E35 Fix Re-verification |
| Epic | E36 — E2E Verification & Benchmarking |
| Sprint | E36 |
| Story Points | 5 |
| Risk | MEDIUM |
| Type | verification |
| Dependencies | E36-S1 (completed) |

## Background

Sprint V3-8 (E35) delivered 8 bug fixes and hardening stories. These were implemented and unit-tested but lack end-to-end browser verification with screenshot evidence. This story systematically re-verifies each E35 fix through a combination of:
- API endpoint testing (curl/fetch)
- Browser UI testing (agent-browser / chrome-devtools)
- Log analysis
- Screenshot evidence collection

## Acceptance Criteria Mapping

| AC | Description | E35 Story | Verification Method |
|----|-------------|-----------|-------------------|
| AC1 | Each E35 fix browser-tested with screenshot evidence | All S1-S8 | Browser + screenshots |
| AC2 | Sync upload completes without asyncio error | E35-S1 | API call + log check |
| AC3 | Model defaults persist across API restart | E35-S2 | API call before/after restart |
| AC4 | Ollama extraction completes with format=json | E35-S3 | Extraction run + log check |
| AC5 | Provider priority order verified in logs | E35-S4 | Log grep |
| AC6 | SSE shows Complete for finished jobs | E35-S5 | Browser SSE check |
| AC7 | Building backfill returns data for pre-V3 sources | E35-S6 | API call |
| AC8 | SF picklist values used in extracted records | E35-S7 | API call + data check |
| AC9 | Empty state shown for source with 0 buildings | E35-S8 | Browser screenshot |

## Verification Plan

### V1: E35-S1 — Sync Upload (AC2)
- **Code check**: Verify `commands/source_commands.py` uses `await` not `asyncio.run()`
- **API test**: `POST /api/sources` with `async_processing=false` and a small test file
- **Pass criteria**: 200 response, no RuntimeError in logs
- **Evidence**: `docs/sprint-artifacts/e36/evidence/e35-s1/api-response.json`, log excerpt

### V2: E35-S2 — Model Defaults Persistence (AC3)
- **API test**: `PUT /api/models/defaults` with test values, then `GET /api/models/defaults`
- **Persistence test**: Verify values survive by checking GET returns same values
- **Pass criteria**: PUT returns 200, GET returns persisted values
- **Evidence**: `docs/sprint-artifacts/e36/evidence/e35-s2/defaults-persistence.json`

### V3: E35-S3 — Ollama Extraction Hardening (AC4)
- **Code check**: Verify `_apply_ollama_extraction_settings()` sets `format="json"`
- **Code check**: Verify `_split_content_by_char_budget()` uses character-based multi-chunking
- **Requires**: Ollama running with a model (optional — code verification sufficient if Ollama unavailable)
- **Pass criteria**: Code paths confirmed, unit tests pass
- **Evidence**: `docs/sprint-artifacts/e36/evidence/e35-s3/code-verification.md`

### V4: E35-S4 — Provider Priority (AC5)
- **Code check**: Verify `provision_langchain_model()` follows Ollama→Anthropic→OpenRouter order
- **Code check**: Verify `ACM_ANTHROPIC_API_KEY` used (not bare `ANTHROPIC_API_KEY`)
- **Unit test check**: Run relevant tests
- **Pass criteria**: Provider chain correct in code, tests pass
- **Evidence**: `docs/sprint-artifacts/e36/evidence/e35-s4/provider-chain.md`

### V5: E35-S5 — SSE Terminal Event (AC6)
- **Code check**: Verify SSE endpoint returns `{type: "complete"}` for completed jobs
- **Browser test**: Navigate to completed extraction, check SSE connection closes cleanly
- **Pass criteria**: No console errors on completed extraction page
- **Evidence**: `docs/sprint-artifacts/e36/evidence/e35-s5/sse-terminal.md`

### V6: E35-S6 — Building Backfill (AC7)
- **API test**: `GET /api/acm/buildings?source_id=X` for any existing source
- **Pass criteria**: Returns building data (or empty array if no sources exist)
- **Evidence**: `docs/sprint-artifacts/e36/evidence/e35-s6/backfill-response.json`

### V7: E35-S7 — SF-First Validation (AC8)
- **Code check**: Verify SF validation runs before BAR validation
- **Code check**: Verify picklist values used in normalizers
- **Unit test check**: Run validation tests
- **Pass criteria**: Tests pass, validation order correct
- **Evidence**: `docs/sprint-artifacts/e36/evidence/e35-s7/validation-order.md`

### V8: E35-S8 — Frontend Empty State (AC9)
- **Browser test**: Navigate to source page with no buildings
- **Pass criteria**: Shows "No buildings extracted yet" (not error/crash)
- **Evidence**: `docs/sprint-artifacts/e36/evidence/e35-s8/empty-state.md`

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `docs/sprint-artifacts/e36/evidence/e35-s1/verification.md` | Create | S1 verification results |
| `docs/sprint-artifacts/e36/evidence/e35-s2/verification.md` | Create | S2 verification results |
| `docs/sprint-artifacts/e36/evidence/e35-s3/verification.md` | Create | S3 verification results |
| `docs/sprint-artifacts/e36/evidence/e35-s4/verification.md` | Create | S4 verification results |
| `docs/sprint-artifacts/e36/evidence/e35-s5/verification.md` | Create | S5 verification results |
| `docs/sprint-artifacts/e36/evidence/e35-s6/verification.md` | Create | S6 verification results |
| `docs/sprint-artifacts/e36/evidence/e35-s7/verification.md` | Create | S7 verification results |
| `docs/sprint-artifacts/e36/evidence/e35-s8/verification.md` | Create | S8 verification results |
| `docs/sprint-artifacts/e36/progress.md` | Create | Overall progress tracking |

## Risks
- Frontend returning 500 may block browser-based verifications (AC1, AC6, AC9)
- Ollama may not be running, limiting AC4 to code-only verification
- No test PDF data may limit AC2 (sync upload) and AC7 (backfill) to API-level checks
