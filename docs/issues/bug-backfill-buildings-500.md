# POST /api/acm/backfill-buildings HTTP 500 — Source.name AttributeError

> **GitHub Issue**: #96
> **Discovered**: 2026-03-05 (E36-S2 browser verification)
> **Finding**: F007
> **Priority**: BLOCKER
> **Status**: Open

## Problem

`POST /api/acm/backfill-buildings` crashes with `'Source' object has no attribute 'name'`. The `Source` domain model uses `title`, not `name`. The endpoint was added in E35-S6 but never tested with a real request.

## Reproduction

```bash
curl -X POST http://localhost:5055/api/acm/backfill-buildings \
  -H "Content-Type: application/json" \
  -d '{"source_id": "source:ubbsh2i0b6ypy64vs1hh"}'
# HTTP 500: "'Source' object has no attribute 'name'"
```

## Root Cause

`api/routers/acm.py` references `source.name` but `open_notebook/domain/notebook_components.py` defines the Source model with `title` field.

## Fix

Change `source.name` → `source.title` in the backfill endpoint handler in `api/routers/acm.py`.

## Key Files

- [`api/routers/acm.py`](../../api/routers/acm.py) — backfill endpoint handler
- [`open_notebook/domain/notebook_components.py`](../../open_notebook/domain/notebook_components.py) — Source model

## Related

- GitHub Issue: [#96](https://github.com/CoralShades/acm-ai/issues/96)
- Finding: F007 in [`docs/sprint-artifacts/e36/findings.md`](../sprint-artifacts/e36/findings.md)
- Story: E35-S6 (Building Backfill)
