# E17-S5: A2A Agent Card & Task Lifecycle

## Story Info
- **Epic**: E17 — Live Extraction Intelligence
- **Status**: drafted
- **Priority**: P1
- **Size**: S (Small)
- **Created**: 2026-02-22
- **Dependencies**: None
- **Blocks**: None

## Description

Expose the ACM extraction service as an A2A-compatible agent with a discoverable agent card and task lifecycle endpoints.

## Acceptance Criteria

- [ ] `GET /.well-known/agent.json` returns valid A2A agent card
- [ ] `POST /api/a2a/tasks` accepts extraction task, returns task_id
- [ ] `GET /api/a2a/tasks/{task_id}` returns status (submitted/working/completed/failed)
- [ ] A2A task maps to existing `acm_extract` surreal-command internally

## File Changes

| File | Action | Purpose |
|------|--------|---------|
| `api/routers/a2a.py` | CREATE | A2A endpoints: agent card, task create, task status |
| `api/static/.well-known/agent.json` | CREATE | A2A agent card JSON |
| `api/main.py` | MODIFY | Register a2a router, add static mount for /.well-known/ |
