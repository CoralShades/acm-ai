# Task Plan: Pipeline Fix Integrity Audit (2026-03-17)

## Objective

Verify that all fixes from 3 prior debug sessions (pipeline-debug, pdf-format-audit, docling-json-fix) survived ~25 subsequent commits. If any fix was overwritten or regressed, restore it.

---

## Phase 1 — Fix Inventory & Spot Check

- [x] **1.1** Build complete fix inventory from prior sessions (RC1-RC8, C1-C3, H1, M2, Migration 51)
- [x] **1.2** Grep each fix signature in current HEAD — present/absent/modified → **16/16 PRESENT**
- [x] **1.3** Check migration 51 applied in running SurrealDB → **NOT APPLIED (version=49)**
- [x] **1.4** Check per-row extraction path still reachable (acm_extraction.py ~line 1024) → **Code exists but data empty**
- [x] **1.5** Check `_get_docling_tables()` page overlap logic intact (orchestrator.py) → **PRESENT lines 58-59**
- [x] **1.6** Check `ensure_record_id()` calls in acm_commands.py stale detection → **PRESENT lines 185, 244, 246**

## Phase 2 — Data Flow Trace (Docling → DB → Graph)

- [x] **2.1** Query `acm_table_section` — is `docling_document_json` populated? → **NO, all 28 rows = {}**
- [x] **2.2** Query `building_record` — are buildings stored with clean names? → **1/11 clean, 10 corrupted**
- [x] **2.3** Query `acm_record` — count records vs ground truth → **142 total (but stale data)**
- [x] **2.4** Check `_store_docling_tables()` maps `docling_json` → `docling_document_json` → **CORRECT (line 220)**
- [x] **2.5** Check `_merge_provider_tables()` preserves `docling_json` → **CORRECT (lines 343-490)**

## Phase 3 — Regression Fix

- [x] **3.1** Add migrations 50-52 to AsyncMigrationManager in async_migrate.py
- [x] **3.2** Apply migrations 50, 51, 52 to running SurrealDB → **DB now at version 52**
- [x] **3.3** Verify FLEXIBLE keyword in schema → **CONFIRMED via INFO FOR TABLE**

## Phase 4 — Test & Lint

- [x] **4.1** Run `uv run pytest tests/ -x` → **2018 passed, 1 pre-existing failure**
- [x] **4.2** Run `uv run ruff check .` → **All checks passed**

## Phase 5 — Documentation

- [x] **5.1** Update findings.md with complete audit results
- [x] **5.2** Update progress.md with session summary
- [x] **5.3** Update task_plan.md checkboxes
