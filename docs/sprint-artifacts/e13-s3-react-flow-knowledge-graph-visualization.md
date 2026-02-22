# E13-S3: React Flow Knowledge Graph Visualization

## Story Info
- **Epic**: E13 — Knowledge Graph Visualization
- **Status**: ready-for-dev
- **Priority**: P1
- **Size**: L (Large)
- **Created**: 2026-02-22
- **Dependencies**: E13-S2
- **Blocks**: None

## User Story

**As a** user
**I want** an interactive knowledge graph showing entity relationships for each PDF
**So that** I can visually understand document structure and identify risk areas

## Acceptance Criteria

- [ ] Knowledge Graph tab in source detail view
- [ ] React Flow canvas with custom nodes:
  - School node (top level): name, code, address
  - Building node: name, year, construction, risk summary badge
  - Room node: name, area, ACM count
  - ACM node: product, risk color (red/yellow/green), friability icon
- [ ] Interactive features: click for details, zoom/pan, expand/collapse groups, risk filter, minimap
- [ ] Performance: render 200+ nodes smoothly
- [ ] Export graph as PNG/SVG
- [ ] Toggle between graph view and spreadsheet view

## File Changes

| File | Action | Purpose |
|------|--------|---------|
| `frontend/src/components/acm/KnowledgeGraph.tsx` | CREATE | Main graph container with React Flow canvas |
| `frontend/src/components/acm/graph-nodes/SchoolNode.tsx` | CREATE | Custom school node component |
| `frontend/src/components/acm/graph-nodes/BuildingNode.tsx` | CREATE | Custom building node component |
| `frontend/src/components/acm/graph-nodes/RoomNode.tsx` | CREATE | Custom room node component |
| `frontend/src/components/acm/graph-nodes/ACMNode.tsx` | CREATE | Custom ACM record node component |
| `frontend/src/components/acm/graph-nodes/index.ts` | CREATE | Node type registry |
| `frontend/src/app/sources/[id]/page.tsx` | MODIFY | Add Knowledge Graph tab alongside spreadsheet |

## Technical Notes

- Dependencies: `@xyflow/react` (React Flow v12+), `dagre` for layout
- Custom nodes in `frontend/src/components/acm/graph-nodes/`
- Integration: Tab in source detail page alongside spreadsheet
- Use `useQuery` to fetch graph data from E13-S2 API endpoints
- Risk color mapping: same semantic tokens as ACMGrid (red/yellow/green)
