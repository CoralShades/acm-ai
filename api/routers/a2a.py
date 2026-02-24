"""A2A (Agent-to-Agent) protocol endpoints.

Exposes the ACM extraction service as an A2A-compatible agent
with discoverable agent card and task lifecycle endpoints.

Story: E17-S5 A2A Agent Card & Task Lifecycle
"""

import json
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from loguru import logger
from pydantic import BaseModel

from open_notebook.database.repository import db_connection, repo_query

router = APIRouter()

# Load agent card from static file
_AGENT_CARD_PATH = (
    Path(__file__).parent.parent / "static" / ".well-known" / "agent.json"
)
_agent_card: Optional[dict] = None


def _load_agent_card() -> dict:
    global _agent_card
    if _agent_card is None:
        with open(_AGENT_CARD_PATH) as f:
            _agent_card = json.load(f)
    return _agent_card


class A2ATaskRequest(BaseModel):
    """A2A task creation request."""

    skill_id: str = "acm_extraction"
    input: dict  # Must contain source_id, optionally model_id and force


class A2ATaskResponse(BaseModel):
    """A2A task status response."""

    task_id: str
    status: str  # submitted, working, completed, failed
    result: Optional[dict] = None


@router.get("/.well-known/agent.json")
async def get_agent_card():
    """Return the A2A agent card for discovery."""
    return _load_agent_card()


@router.post("/a2a/tasks", response_model=A2ATaskResponse)
async def create_a2a_task(request: A2ATaskRequest):
    """Create a new A2A extraction task.

    Maps to the existing `acm_extract` surreal-command internally.
    """
    source_id = request.input.get("source_id")
    if not source_id:
        raise HTTPException(status_code=400, detail="source_id is required in input")

    model_id = request.input.get("model_id")
    force = request.input.get("force", True)

    task_id = str(uuid.uuid4())

    try:
        # Create a surreal-command to trigger extraction in the worker
        command_data = {
            "command_type": "acm_extract",
            "source_id": source_id,
            "model_id": model_id,
            "force": force,
            "a2a_task_id": task_id,
        }

        async with db_connection() as db:
            # Store A2A task mapping
            await db.query(
                """
                CREATE a2a_tasks SET
                    task_id = $task_id,
                    status = 'submitted',
                    skill_id = $skill_id,
                    input = $input,
                    created_at = time::now();
                """,
                {
                    "task_id": task_id,
                    "skill_id": request.skill_id,
                    "input": request.input,
                },
            )

            # Dispatch the extraction command via surreal-commands
            await db.query(
                """
                CREATE surreal_command SET
                    command = 'acm_extract',
                    args = $args,
                    status = 'pending',
                    created_at = time::now();
                """,
                {
                    "args": json.dumps(command_data),
                },
            )

        logger.info(f"A2A task created: {task_id} for source {source_id}")
        return A2ATaskResponse(task_id=task_id, status="submitted")

    except Exception as e:
        logger.error(f"Failed to create A2A task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/a2a/tasks/{task_id}", response_model=A2ATaskResponse)
async def get_a2a_task(task_id: str):
    """Get the status of an A2A task."""
    try:
        result = await repo_query(
            "SELECT * FROM a2a_tasks WHERE task_id = $task_id LIMIT 1;",
            {"task_id": task_id},
        )

        if not result:
            raise HTTPException(status_code=404, detail="Task not found")

        task = result[0]
        return A2ATaskResponse(
            task_id=task["task_id"],
            status=task.get("status", "unknown"),
            result=task.get("result"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get A2A task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
