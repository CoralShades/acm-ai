# Story 1.30: Dynamic Embedding Dimensions

Status: done

## Story

As a **system administrator**,
I want **the embedding pipeline to validate vector dimensions against the configured model**,
so that **switching embedding models doesn't silently produce incompatible vectors that fail at search time**.

## Acceptance Criteria

1. Embedding commands validate vector dimension against expected 1024-dim MTREE index
2. ACM embedding service logs warning when embedding dimensions don't match index
3. `get_embedding_dimensions()` method returns correct dimensions for known embedding models
4. No regression in existing mxbai-embed-large (1024-dim) pipeline

## Tasks / Subtasks

- [x] Task 1: Add dimension validation to embedding commands (AC: #1)
  - [x] 1.1 Add `EXPECTED_EMBEDDING_DIM = 1024` constant to `embedding_commands.py`
  - [x] 1.2 Validate embedding vector length after generation in `embed_chunk_command`
  - [x] 1.3 Log warning with suggestion to re-index if dimensions mismatch
- [x] Task 2: Add dimension validation to embedding service (AC: #2)
  - [x] 2.1 Add dimension check in `acm_embedding_service.py` after batch embedding
  - [x] 2.2 Log warning with actual vs expected dimensions
- [x] Task 3: Verify model lookup methods (AC: #3)
  - [x] 3.1 `get_embedding_dimensions()` covers mxbai-embed-large (1024), text-embedding-3-small (1536), text-embedding-3-large (3072), nomic-embed-text (768)
- [x] Task 4: Verification (AC: #4)
  - [x] 4.1 Backend lint passes

## Dev Notes

### Design Decision

Rather than dynamically recreating the SurrealDB MTREE vector index (which would require dropping and rebuilding the index + re-embedding all records), we opted for **validation-only** approach:

1. The MTREE index is fixed at 1024 dimensions (migration 9)
2. When a non-1024-dim model is configured, the system logs warnings
3. A future story should add a management command to re-index embeddings

This is the pragmatic choice because:
- Re-indexing is destructive (drops existing vectors)
- Most deployments use mxbai-embed-large (1024-dim)
- Warnings alert administrators before search failures occur

### Files Changed

| File | Action | Purpose |
|------|--------|---------|
| `commands/embedding_commands.py` | MODIFY | EXPECTED_EMBEDDING_DIM constant + validation |
| `api/services/acm_embedding_service.py` | MODIFY | Batch dimension validation warning |

### Dependencies

- Depends on: E1-S28 (Model Capabilities Schema — `get_embedding_dimensions()` method)

## Dev Agent Record

### Agent Model Used
Claude Opus 4.6

### Completion Notes List
- Part of Bug Triage Plan Phase 4 (Model Abstraction Layer)
- Validation-only approach chosen over dynamic index recreation
- Maps to original bugs #1 and #9 from triage (multi-model compatibility)

### File List
- commands/embedding_commands.py (EXPECTED_EMBEDDING_DIM, validation logic)
- api/services/acm_embedding_service.py (batch dimension warning)
