# E9-S3: Document Actions & Bulk Operations

## Story Info
- **Epic**: E9 — Document Library Management
- **Status**: done
- **Priority**: P0
- **Size**: M (Medium)
- **Created**: 2026-02-22
- **Dependencies**: E9-S1 (done), E9-S2 (done)
- **Blocks**: None
- **Tech Spec**: `docs/sprint-artifacts/tech-spec-e9-s3-document-actions-bulk-operations.md`

## User Story

**As a** user
**I want** to perform actions on documents individually and in bulk
**So that** I can efficiently manage my document collection

## Acceptance Criteria

- [ ] Individual document actions: View details, Open spreadsheet, Re-extract ACM, Delete
- [ ] Bulk actions: Delete selected, Re-process selected, Export selected
- [ ] Confirmation dialogs for destructive actions
- [ ] Progress feedback for bulk operations
- [ ] Undo capability for recent deletions (soft delete with grace period)
- [ ] Archive functionality (hide without delete)
- [ ] Document metadata editing (rename, add tags/notes)

## File Changes

| File | Action | Purpose |
|------|--------|---------|
| `frontend/src/components/documents/DocumentActions.tsx` | CREATE | Individual document action dropdown menu |
| `frontend/src/components/documents/BulkActionBar.tsx` | CREATE | Bulk action toolbar with selection count |
| `frontend/src/components/documents/ConfirmDeleteDialog.tsx` | CREATE | Confirmation dialog for destructive actions |
| `frontend/src/components/documents/DocumentMetadataEditor.tsx` | CREATE | Inline metadata editing (rename, tags) |
| `api/routers/sources.py` | MODIFY | Add bulk delete, bulk re-extract, archive endpoints |
| `frontend/src/components/documents/DocumentLibrary.tsx` | MODIFY | Integrate actions and bulk toolbar |

## Technical Notes

- See full tech spec: `docs/sprint-artifacts/tech-spec-e9-s3-document-actions-bulk-operations.md`
- Soft delete: Set `archived: true` field, exclude from default queries
- Bulk operations: Use `Promise.allSettled()` for parallel execution with individual error handling
- Re-extract: Reuse existing `acm_extract` surreal-command
