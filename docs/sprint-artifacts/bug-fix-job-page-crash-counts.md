# Bug Fix 13 — Job Page Crash, Missing Counts, Chat Freeze

**Date**: 2026-03-21
**Commit**: `ad3379ef`
**Branch**: `main`

## Issues Fixed

### 1. Building/Record Counts Always 0 on Job Cards

**Severity**: BLOCKER
**File**: `api/routers/sources.py`

**Problem**: All job cards displayed `building_count=0`, `records_count=null`, `tables_count=null` even when data existed in SurrealDB.

**Root Cause**: Four aggregate queries used `WHERE source_id INSIDE $source_ids` with plain string IDs (e.g., `"source:abc"`). SurrealDB's `INSIDE` operator silently returns 0 rows when the column is typed as `record<source>` but the comparison values are plain strings.

**Fix**: Converted string source IDs to `type::thing()` calls:
```sql
-- Before (broken):
WHERE source_id INSIDE $source_ids

-- After (fixed):
WHERE source_id INSIDE [type::thing('source:abc'), type::thing('source:def')]
```

Four queries fixed: building counts, table counts, record counts, intelligence metadata.

**Verification**: `building_count=1, records_count=55, tables_count=9` returned correctly.

### 2. Chat Panel Freezes Page

**Severity**: BLOCKER
**File**: `frontend/src/lib/hooks/useSmartChat.ts`

**Problem**: Opening the chat panel on `/jobs/[id]` froze the browser tab in an infinite re-render loop.

**Root Cause**: CopilotKit's `useCoAgent` hook returns a new `setState` reference on every render. This was listed in the `useEffect` dependency array, causing the effect to re-fire → call `setState` → trigger re-render → new `setState` ref → effect fires again → infinite loop.

**Fix**: Used `useRef` to hold a stable `setState` reference + `didSyncRef` guard (same pattern already used in `JobCrudChatPanel`).

### 3. Empty Document Metadata Card

**Severity**: LOW
**File**: `frontend/src/components/jobs/JobOverviewTab.tsx`

**Problem**: Document Metadata card rendered as an empty box when `document_meta` was `{}` (truthy empty object with all null fields).

**Fix**: Added field-level check — card only renders when at least one of: `consultant_name`, `site_name`, `site_address`, `report_date`, or `document_type` is populated.

### 4. Langfuse Observability Stack Not Running

**Severity**: MEDIUM (non-blocking but noisy)

**Problem**: `LANGFUSE_ENABLED=true` in `.env` but Docker containers not started. OTel span exports flooded logs with `ConnectionRefusedError` to `localhost:3000`.

**Fix**: Started the full Langfuse v3 stack:
```bash
docker compose -f docker-compose.yml -f docker-compose.observability.yml up -d
```
7 containers: langfuse, langfuse-worker, postgres, clickhouse, redis, minio, jsoncrack.

## Patterns Documented

- **SurrealDB INSIDE with record references**: Always use `type::thing()` when building `INSIDE` clauses with string source IDs against `record<table>` columns.
- **CopilotKit useCoAgent setState**: Always stabilize with `useRef`, never put in `useEffect` deps.
