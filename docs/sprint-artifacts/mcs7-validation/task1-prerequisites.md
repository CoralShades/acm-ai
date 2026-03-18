# Task 1: Services & Prerequisites Verification

**Date**: 2026-03-19
**Agent**: extraction-runner

## Service Status

| Service | URL | Status |
|---------|-----|--------|
| FastAPI Backend | localhost:5055 | RUNNING (127 endpoints, Swagger UI at /docs) |
| SurrealDB | localhost:8000 | RUNNING (HTTP 200) |
| Frontend (Next.js) | localhost:8502 | NOT RUNNING |

**Note**: `/api/health` returns 404 — no health endpoint defined, but API is operational (openapi.json loads, Swagger UI works).

## Stories 1-5 Infrastructure Verification

| Check | File/Table | Status |
|-------|-----------|--------|
| Schema inference node | `open_notebook/extractors/schema_inference.py` | EXISTS |
| `consultant_format_profile` table | SurrealDB | EXISTS (empty — no cached profiles yet) |
| `row_segmenter.py` has `extra_mappings` | Line 180+ | CONFIRMED — accepts `extra_mappings: dict[str, str] | None` |
| Format-agnostic prompts | `prompts/acm/row_extraction.jinja` | CONFIRMED — uses `{% if extraction_fields %}` / `{% for field in extraction_fields %}` |

## Test PDF Availability

| PDF | Path | Available |
|-----|------|-----------|
| Broadmeadows (DET standard) | `docs/samplePDF/Boradmeadows.pdf` | YES |
| Alexander Hospital | `docs/samplePDF/AlexanderHospital.pdf` | YES |
| Clutch Broadmeadows | `docs/samplePDF/Clutch_Broadmeadows.pdf` | YES |
| Clutch Broadmeadows 2 | `docs/samplePDF/Clutch_Broadmeadows_2.pdf` | YES |
| Ground truth fixture | `tests/e2e/fixtures/ara-documents/broadmeadows-expected-results.json` | YES |

## Summary

All prerequisites are met. Backend API and SurrealDB are operational. Frontend is not running but not required for API-driven extraction testing. All Story 1-5 infrastructure files are in place. Ready to proceed with extraction tasks.
