# E13-S2: Knowledge Graph API & Data Service

## Story Info
- **Epic**: E13 — Knowledge Graph Visualization
- **Status**: ready-for-dev
- **Priority**: P1
- **Size**: M (Medium)
- **Created**: 2026-02-22
- **Dependencies**: E13-S1 (done)
- **Blocks**: E13-S3

## User Story

**As a** frontend developer
**I want** API endpoints that return graph-structured data for React Flow
**So that** the frontend can render entity relationship diagrams

## Acceptance Criteria

- [ ] API endpoints:
  - `GET /api/graph/source/{source_id}` — Full graph for a source
  - `GET /api/graph/school/{school_id}` — School-centric graph
  - `GET /api/graph/building/{building_id}` — Building-centric graph
  - `GET /api/graph/stats/{source_id}` — Graph statistics
- [ ] Response format: React Flow compatible nodes and edges JSON
- [ ] Auto-layout calculation (hierarchical top-down via dagre)
- [ ] Risk summary aggregation per node
- [ ] Filter options: by risk level, by building, by ACM status

## File Changes

| File | Action | Purpose |
|------|--------|---------|
| `api/routers/graph.py` | CREATE | Graph API router with 4 endpoints |
| `api/graph_service.py` | CREATE | Graph data service — SurrealDB graph traversal, dagre layout |
| `api/main.py` | MODIFY | Register graph router |
| `open_notebook/database/graph_repository.py` | CREATE | Repository for graph entity queries |

## Technical Notes

- Graph service layer: `api/graph_service.py`
- Use SurrealDB graph traversal (`->` and `<-` operators) for data fetching
- Auto-layout: dagre algorithm (server-side layout calculation)
- Response schema: `{ nodes: ReactFlowNode[], edges: ReactFlowEdge[] }`
- Risk aggregation: sum ACM records per building/room, derive risk level from highest-risk item
