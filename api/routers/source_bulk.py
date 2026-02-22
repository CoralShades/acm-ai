from typing import List

from fastapi import APIRouter
from loguru import logger
from pydantic import BaseModel

from open_notebook.database.repository import ensure_record_id, repo_query

router = APIRouter()


class BulkOperationRequest(BaseModel):
    source_ids: List[str]


class BulkOperationResponse(BaseModel):
    success: List[str]
    failed: List[str]
    message: str


@router.post("/sources/bulk/delete", response_model=BulkOperationResponse)
async def bulk_delete(request: BulkOperationRequest):
    """Soft-delete sources (sets deleted_at and status='deleted')."""
    success = []
    failed = []
    for source_id in request.source_ids:
        try:
            result = await repo_query(
                "UPDATE $id SET deleted_at = time::now(), status = 'deleted'",
                {"id": ensure_record_id(source_id)},
            )
            if result:
                success.append(source_id)
            else:
                failed.append(source_id)
        except Exception as e:
            logger.error(f"Failed to soft-delete {source_id}: {e}")
            failed.append(source_id)
    return BulkOperationResponse(
        success=success,
        failed=failed,
        message=f"Deleted {len(success)} documents, {len(failed)} failed",
    )


@router.post("/sources/bulk/undo-delete", response_model=BulkOperationResponse)
async def bulk_undo_delete(request: BulkOperationRequest):
    """Restore soft-deleted sources within 30-minute grace period."""
    success = []
    failed = []
    for source_id in request.source_ids:
        try:
            result = await repo_query(
                """UPDATE $id SET deleted_at = NONE, status = 'active'
                   WHERE deleted_at != NONE
                     AND deleted_at > time::now() - 30m""",
                {"id": ensure_record_id(source_id)},
            )
            if result:
                success.append(source_id)
            else:
                failed.append(source_id)
        except Exception as e:
            logger.error(f"Failed to undo delete for {source_id}: {e}")
            failed.append(source_id)
    return BulkOperationResponse(
        success=success,
        failed=failed,
        message=f"Restored {len(success)} documents, {len(failed)} failed",
    )


@router.post("/sources/bulk/reprocess", response_model=BulkOperationResponse)
async def bulk_reprocess(request: BulkOperationRequest):
    """Queue re-extraction for selected sources."""
    from api.command_service import CommandService
    from commands.source_commands import SourceProcessingInput
    from open_notebook.domain.notebook import Source

    success = []
    failed = []
    for source_id in request.source_ids:
        try:
            source = await Source.get(source_id)
            if not source:
                failed.append(source_id)
                continue

            content_state = {}
            if source.asset:
                if source.asset.file_path:
                    content_state = {"file_path": source.asset.file_path, "delete_source": False}
                elif source.asset.url:
                    content_state = {"url": source.asset.url}
            elif source.full_text:
                content_state = {"content": source.full_text}

            if not content_state:
                failed.append(source_id)
                continue

            command_input = SourceProcessingInput(
                source_id=str(source.id),
                content_state=content_state,
                notebook_ids=[],
                transformations=[],
                embed=True,
            )

            command_id = await CommandService.submit_command_job(
                "open_notebook",
                "process_source",
                command_input.model_dump(),
            )

            source.command = ensure_record_id(command_id)
            await source.save()
            success.append(source_id)
        except Exception as e:
            logger.error(f"Failed to reprocess {source_id}: {e}")
            failed.append(source_id)
    return BulkOperationResponse(
        success=success,
        failed=failed,
        message=f"Queued {len(success)} documents for reprocessing, {len(failed)} failed",
    )


@router.post("/sources/bulk/archive", response_model=BulkOperationResponse)
async def bulk_archive(request: BulkOperationRequest):
    """Archive sources (hide without delete)."""
    success = []
    failed = []
    for source_id in request.source_ids:
        try:
            result = await repo_query(
                "UPDATE $id SET archived_at = time::now(), status = 'archived'",
                {"id": ensure_record_id(source_id)},
            )
            if result:
                success.append(source_id)
            else:
                failed.append(source_id)
        except Exception as e:
            logger.error(f"Failed to archive {source_id}: {e}")
            failed.append(source_id)
    return BulkOperationResponse(
        success=success,
        failed=failed,
        message=f"Archived {len(success)} documents, {len(failed)} failed",
    )


@router.post("/sources/bulk/unarchive", response_model=BulkOperationResponse)
async def bulk_unarchive(request: BulkOperationRequest):
    """Restore archived sources."""
    success = []
    failed = []
    for source_id in request.source_ids:
        try:
            result = await repo_query(
                "UPDATE $id SET archived_at = NONE, status = 'active'",
                {"id": ensure_record_id(source_id)},
            )
            if result:
                success.append(source_id)
            else:
                failed.append(source_id)
        except Exception as e:
            logger.error(f"Failed to unarchive {source_id}: {e}")
            failed.append(source_id)
    return BulkOperationResponse(
        success=success,
        failed=failed,
        message=f"Unarchived {len(success)} documents, {len(failed)} failed",
    )


@router.post("/sources/bulk/export", response_model=BulkOperationResponse)
async def bulk_export(request: BulkOperationRequest):
    """Validate sources exist for export (actual ZIP export deferred)."""
    from open_notebook.domain.notebook import Source

    success = []
    failed = []
    for source_id in request.source_ids:
        try:
            source = await Source.get(source_id)
            if source:
                success.append(source_id)
            else:
                failed.append(source_id)
        except Exception as e:
            logger.error(f"Failed to validate {source_id} for export: {e}")
            failed.append(source_id)
    return BulkOperationResponse(
        success=success,
        failed=failed,
        message=f"{len(success)} documents ready for export, {len(failed)} not found",
    )
