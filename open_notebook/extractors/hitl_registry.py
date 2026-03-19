"""In-process HITL (Human-In-The-Loop) response registry.

Provides an asyncio.Event-based mechanism for the extraction pipeline to
pause and wait for user input (e.g., schema mapping confirmation), and for
API endpoints to deliver that input back.

Both the background worker and the API handler share the same asyncio event
loop (single-process architecture), so asyncio.Event is sufficient.

Story: Multi-Consultant Story 6 — HITL Mapping Confirmation UI
"""

from __future__ import annotations

import asyncio
from typing import Any, Optional

from loguru import logger


class HITLRegistry:
    """Registry for pending HITL requests.

    Each pending request is keyed by operation_id (same as the extraction's
    command_id / thread_id). The extraction pipeline awaits the Event, and
    the API endpoint sets it after storing the user's response.
    """

    def __init__(self) -> None:
        self._events: dict[str, asyncio.Event] = {}
        self._responses: dict[str, dict[str, Any]] = {}
        self._interrupt_data: dict[str, dict[str, Any]] = {}

    def register(
        self, operation_id: str, interrupt_payload: dict[str, Any]
    ) -> asyncio.Event:
        """Register a pending HITL request.

        Args:
            operation_id: Unique ID for this extraction run.
            interrupt_payload: The interrupt data to surface to the user
                (e.g., proposed column mappings).

        Returns:
            An asyncio.Event that will be set when the user responds.
        """
        event = asyncio.Event()
        self._events[operation_id] = event
        self._interrupt_data[operation_id] = interrupt_payload
        logger.info(f"[HITL] Registered pending request for operation {operation_id}")
        return event

    async def wait_for_response(
        self, operation_id: str, timeout: float = 600.0
    ) -> dict[str, Any]:
        """Wait for the user to respond to a HITL request.

        Args:
            operation_id: The operation to wait for.
            timeout: Maximum seconds to wait (default 10 minutes).

        Returns:
            The user's response dict.

        Raises:
            asyncio.TimeoutError: If no response arrives within timeout.
            KeyError: If operation_id was never registered.
        """
        event = self._events.get(operation_id)
        if event is None:
            raise KeyError(f"No pending HITL request for operation {operation_id}")

        logger.info(
            f"[HITL] Waiting for user response on operation {operation_id} "
            f"(timeout={timeout}s)"
        )
        await asyncio.wait_for(event.wait(), timeout=timeout)

        response = self._responses.pop(operation_id, {})
        self._cleanup(operation_id)
        logger.info(
            f"[HITL] Received user response for operation {operation_id}: "
            f"action={response.get('action', 'unknown')}"
        )
        return response

    def submit_response(self, operation_id: str, response: dict[str, Any]) -> bool:
        """Submit a user response to unblock a waiting extraction.

        Args:
            operation_id: The operation to respond to.
            response: The user's decision (action, mappings, etc.).

        Returns:
            True if the operation was pending and is now unblocked.
            False if no pending request exists for this operation.
        """
        event = self._events.get(operation_id)
        if event is None:
            logger.warning(
                f"[HITL] No pending request for operation {operation_id}, "
                "response ignored"
            )
            return False

        self._responses[operation_id] = response
        event.set()
        logger.info(f"[HITL] Submitted response for operation {operation_id}")
        return True

    def get_interrupt_data(self, operation_id: str) -> Optional[dict[str, Any]]:
        """Get the interrupt payload for a pending HITL request."""
        return self._interrupt_data.get(operation_id)

    def is_pending(self, operation_id: str) -> bool:
        """Check if an operation has a pending HITL request."""
        return operation_id in self._events and not self._events[operation_id].is_set()

    def list_pending(self) -> list[str]:
        """List all operation IDs with pending HITL requests."""
        return [
            op_id
            for op_id, event in self._events.items()
            if not event.is_set()
        ]

    def cancel(self, operation_id: str) -> None:
        """Cancel a pending HITL request (e.g., on timeout or extraction abort)."""
        self._cleanup(operation_id)
        logger.info(f"[HITL] Cancelled pending request for operation {operation_id}")

    def _cleanup(self, operation_id: str) -> None:
        """Remove all state for an operation."""
        self._events.pop(operation_id, None)
        self._responses.pop(operation_id, None)
        self._interrupt_data.pop(operation_id, None)


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_registry: Optional[HITLRegistry] = None


def get_hitl_registry() -> HITLRegistry:
    """Return the module-level singleton HITLRegistry instance."""
    global _registry
    if _registry is None:
        _registry = HITLRegistry()
    return _registry
