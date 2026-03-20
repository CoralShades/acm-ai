# API + Worker Log Analysis

**Date**: 2026-03-20
**Monitoring window**: 15:32 - 15:58 (26 minutes)
**Log files**: `/tmp/acm-api.log` (70 lines), `/tmp/acm-worker.log` (16 lines)

## Summary

Monitored API and worker logs during E2E tester activity. The E2E tester performed API endpoint testing and frontend navigation but did **not trigger a file upload or extraction** during the monitoring window. All observed endpoints returned 200 OK (except known `/api/health` 404 -- see below).

## Startup Health (15:32)

- API: Uvicorn started on port 5055, reloader active (WatchFiles)
- Database: version 54, no migrations needed
- Command registry: 9 commands registered (acm_extract, embed_single_item, embed_chunk, vectorize_source, rebuild_embeddings, process_text, analyze_data, generate_podcast)
- Provider registry: docling and mineru auto-registered
- AG-UI endpoints: `/api/agui/chat` and `/api/agui/crud-chat` registered
- Model provisioning: 17 models across active providers, 6 roles configured (chat, transformation, tools, large_context, extraction, embedding)
- SF schema: already at version salesforce-v1
- Worker: started, 5 concurrent task capacity, LIVE query listener active, no existing commands found

**Verdict**: Clean startup, no errors.

## API Request Timeline

| Time  | Endpoint | Status | Notes |
|-------|----------|--------|-------|
| 15:33 | `GET /api/health` | 404 | Route does not exist (see finding below) |
| 15:33 | `GET /health` | 200 | Correct health endpoint |
| 15:33 | `GET /api/sources` | 200 | E2E tester API probe |
| 15:34 | `GET /docs` | 200 | Swagger UI accessed |
| 15:34 | `GET /openapi.json` | 200 | OpenAPI spec fetched |
| 15:34 | `GET /api/sources` | 200 | Second sources probe |
| 15:35 | `GET /api/health` | 404 | Repeated incorrect health path |
| 15:35 | `GET /api/sources/{id}/live-stats` | 200 | **live-stats endpoint working** (source:34a0qlfu6mj7jwf5vh1p) |
| 15:35 | `GET /api/sources/source:doesnotexist/live-stats` | 200 | Edge case: nonexistent source returns 200 with empty stats |
| 15:35 | `GET /api/sources/{id}/live-stats` | 200 | Second hit on valid source |
| 15:35 | `GET /api/config` | 200 | Version check (current: 1.2.3, latest: 1.8.1) |
| 15:35 | `GET /api/auth/status` | 200 | Auth status (x2) |
| 15:36 | `GET /api/sources?limit=30&offset=0&sort_by=updated&sort_order=desc` | 200 | Paginated sources list (x4 total) |
| 15:36 | `GET /api/notebooks?order_by=updated+desc` | 200 | Notebooks list |
| 15:36 | `GET /api/episode-profiles` | 200 | Episode profiles |
| 15:36 | `GET /api/notebooks?archived=false&order_by=updated+desc` | 200 | Active notebooks |
| 15:36 | `GET /api/notebooks?archived=true&order_by=updated+desc` | 200 | Archived notebooks |
| 15:55 | `GET /api/sources?limit=30&offset=0&sort_by=updated&sort_order=desc` | 200 | Final sources refresh |

## Worker Activity

**None.** The worker remained idle throughout the entire monitoring window. No commands were dispatched, no extraction was triggered.

## What We Watched For vs What Happened

| Expected Event | Observed? | Details |
|----------------|-----------|---------|
| `"Using async processing path"` | NO | No upload was attempted |
| `"review_status"` mentions | NO | No source creation/update occurred |
| `extraction.docling_complete` SSE | NO | No extraction ran |
| `ai.building_saved` SSE | NO | No extraction ran |
| Grouped save messages | NO | Worker was idle |
| `/sources/*/live-stats` requests | YES | Endpoint tested 3 times, all 200 OK |
| Python tracebacks | NO | Zero errors in both logs |
| 500 errors | NO | Zero 500 responses |

## Key Findings

### 1. live-stats endpoint works correctly
The `/api/sources/{source_id}/live-stats` endpoint returned 200 OK for both valid and nonexistent source IDs. This is the expected behavior -- the endpoint returns default/empty stats when no source exists, avoiding 404 errors that would break frontend polling.

### 2. `/api/health` returns 404 (minor issue)
The correct health endpoint is `/health` (200 OK), but the E2E tester also tried `/api/health` which returns 404. This suggests either:
- The frontend or test tooling expects `/api/health` as a convention
- A proxy routing issue (Next.js `/api/*` proxy may strip the prefix before forwarding)

**Recommendation**: Add `/api/health` as an alias for `/health`, or document the correct endpoint.

### 3. No extraction was triggered
The E2E tester did not upload a PDF or trigger an extraction during this monitoring window. The worker remained idle the entire time. This means we could not observe:
- Async upload path changes
- review_status lifecycle (extracting -> pending_review)
- SSE event emissions
- Building-grouped save behavior

### 4. All API endpoints healthy
Every endpoint that was hit returned the expected status:
- Sources CRUD: 200
- Notebooks: 200
- Config: 200
- Auth: 200
- Live-stats: 200
- Swagger docs: 200

### 5. Frontend port conflict
`/tmp/acm-frontend.log` shows the start script failed with `EADDRINUSE` on port 8503 -- the frontend was already running from a prior session. This is expected behavior, not an error.

## Errors and Tracebacks

**None observed.** Both logs were clean throughout the monitoring window.

## Recommendations for Re-test

To fully validate the UX mega-pack changes, a follow-up test should:
1. Upload a PDF via the frontend or API (`POST /api/sources` with file)
2. Monitor for `review_status: 'extracting'` in the response
3. Watch worker logs for `acm_extract` command pickup
4. Monitor for SSE events on `/api/v3/stream/*` or `/api/agui/extraction/*/stream`
5. Verify `review_status` transitions to `'pending_review'` on completion
6. Hit `/api/sources/{id}/live-stats` during extraction to verify real-time stats
