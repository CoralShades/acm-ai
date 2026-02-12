import json
from typing import Any, Dict, List, Optional

from loguru import logger
from surreal_commands import get_command_status, submit_command


class CommandService:
    """Generic service layer for command operations"""

    @staticmethod
    async def submit_command_job(
        module_name: str,  # Actually app_name for surreal-commands
        command_name: str,
        command_args: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Submit a generic command job for background processing"""
        try:
            # Ensure command modules are imported before submitting
            # This is needed because submit_command validates against local registry
            try:
                import commands.podcast_commands  # noqa: F401
            except ImportError as import_err:
                logger.error(f"Failed to import command modules: {import_err}")
                raise ValueError("Command modules not available")

            # surreal-commands expects: submit_command(app_name, command_name, args)
            cmd_id = submit_command(
                module_name,  # This is actually the app name (e.g., "open_notebook")
                command_name,  # Command name (e.g., "process_text")
                command_args,  # Input data
            )
            # Convert RecordID to string if needed
            if not cmd_id:
                raise ValueError("Failed to get cmd_id from submit_command")
            cmd_id_str = str(cmd_id)
            logger.info(
                f"Submitted command job: {cmd_id_str} for {module_name}.{command_name}"
            )
            return cmd_id_str

        except Exception as e:
            logger.error(f"Failed to submit command job: {e}")
            raise

    @staticmethod
    async def _get_extraction_progress(job_id: str) -> Optional[Dict[str, Any]]:
        """Fetch extraction progress from extraction_progress table."""
        try:
            from open_notebook.database.repository import db_connection

            async with db_connection() as db:
                result = await db.query(
                    "SELECT * FROM extraction_progress WHERE command_id = $cid LIMIT 1;",
                    {"cid": job_id},
                )
                if result and isinstance(result, list):
                    rows = result[0] if isinstance(result[0], list) else result
                    if rows and isinstance(rows, list) and len(rows) > 0:
                        row = rows[0]
                        # Parse state_json into dict
                        state = None
                        if row.get("state_json"):
                            try:
                                state = json.loads(row["state_json"])
                            except (json.JSONDecodeError, TypeError):
                                pass
                        return {
                            "pipeline_status": row.get("status"),
                            "state": state,
                            "log_entries": row.get("log_entries", []),
                        }
                    if isinstance(rows, dict) and "result" in rows:
                        inner = rows["result"]
                        if inner and len(inner) > 0:
                            row = inner[0]
                            state = None
                            if row.get("state_json"):
                                try:
                                    state = json.loads(row["state_json"])
                                except (json.JSONDecodeError, TypeError):
                                    pass
                            return {
                                "pipeline_status": row.get("status"),
                                "state": state,
                                "log_entries": row.get("log_entries", []),
                            }
        except Exception as e:
            logger.debug(f"Failed to fetch extraction progress: {e}")
        return None

    @staticmethod
    async def get_command_status(job_id: str) -> Dict[str, Any]:
        """Get status of any command job, enriched with extraction progress if available."""
        try:
            status = await get_command_status(job_id)
            result = {
                "job_id": job_id,
                "status": status.status if status else "unknown",
                "result": status.result if status else None,
                "error_message": getattr(status, "error_message", None)
                if status
                else None,
                "created": str(status.created)
                if status and hasattr(status, "created") and status.created
                else None,
                "updated": str(status.updated)
                if status and hasattr(status, "updated") and status.updated
                else None,
                "progress": getattr(status, "progress", None) if status else None,
            }

            # Enrich with extraction pipeline progress
            extraction_progress = await CommandService._get_extraction_progress(job_id)
            if extraction_progress:
                result["progress"] = extraction_progress

            return result
        except Exception as e:
            logger.error(f"Failed to get command status: {e}")
            raise

    @staticmethod
    async def list_command_jobs(
        module_filter: Optional[str] = None,
        command_filter: Optional[str] = None,
        status_filter: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """List command jobs with optional filtering"""
        # This will be implemented with proper SurrealDB queries
        # For now, return empty list as this is foundation phase
        return []

    @staticmethod
    async def cancel_command_job(job_id: str) -> bool:
        """Cancel a running command job"""
        try:
            # Implementation depends on surreal-commands cancellation support
            # For now, just log the attempt
            logger.info(f"Attempting to cancel job: {job_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel command job: {e}")
            raise
