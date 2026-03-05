"""In-process asyncio pub/sub event bus for V3 pipeline events.

Provides a singleton PipelineEventBus that allows producers (extraction nodes,
consensus engine, bulk command handlers) to publish typed V3PipelineEvent
instances and consumers (SSE generators) to subscribe per operation_id.

Events are ephemeral — no persistence. Authoritative state is in SurrealDB.

Story: E31-S7 PipelineEventBus + SSE Infrastructure
"""

from __future__ import annotations

import asyncio
from typing import Any, AsyncGenerator, Dict, List, Literal, Optional

from loguru import logger
from pydantic import BaseModel, Field

from open_notebook.extractors.pipeline_events import now_iso

# ---------------------------------------------------------------------------
# V3 event data payloads
# ---------------------------------------------------------------------------


class ExtractionStartedData(BaseModel):
    """Payload for extraction.started."""

    source_id: str
    provider_sequence: List[str]
    total_pages: int = 0


class ExtractionProviderCompleteData(BaseModel):
    """Payload for extraction.provider_complete."""

    provider: str
    records_extracted: int
    duration_ms: int
    pages_processed: int


class ExtractionConsensusCompleteData(BaseModel):
    """Payload for extraction.consensus_complete (terminal)."""

    records_final: int
    records_docling_only: int
    records_mineru_only: int
    records_agreed: int
    consensus_duration_ms: int


class AIBuildingExtractedData(BaseModel):
    """Payload for ai.building_extracted."""

    building_id: str
    building_name: str
    records_extracted: int
    model_used: str
    duration_ms: int


class AIItemsExtractedData(BaseModel):
    """Payload for ai.items_extracted."""

    building_id: str
    items_count: int
    items_rejected: int


class AIValidationCompleteData(BaseModel):
    """Payload for ai.validation_complete (terminal)."""

    records_valid: int
    records_corrected: int
    records_rejected: int
    validation_duration_ms: int


class BulkProgressData(BaseModel):
    """Payload for bulk.progress."""

    total: int
    completed: int
    failed: int
    percent: float


class BulkCompleteData(BaseModel):
    """Payload for bulk.complete (terminal)."""

    total: int
    completed: int
    failed: int
    duration_ms: int


# ---------------------------------------------------------------------------
# V3 event envelope and typed subclasses
# ---------------------------------------------------------------------------


class V3PipelineEvent(BaseModel):
    """Base envelope for all V3 pipeline events.

    Typed subclasses use Literal discriminators on `type` and a typed `data`
    field.  The base class accepts `data: Dict[str, Any]` for generic handling
    (e.g. SSE serialization, filtering) without needing to know the subtype.
    """

    type: str
    operation_id: str
    timestamp: str = Field(default_factory=now_iso)
    data: Dict[str, Any] = Field(default_factory=dict)


class ExtractionStartedEvent(V3PipelineEvent):
    """Emitted when a dual-provider extraction begins."""

    type: Literal["extraction.started"] = "extraction.started"
    data: ExtractionStartedData  # type: ignore[assignment]


class ExtractionProviderCompleteEvent(V3PipelineEvent):
    """Emitted when one provider finishes its extraction pass."""

    type: Literal["extraction.provider_complete"] = "extraction.provider_complete"
    data: ExtractionProviderCompleteData  # type: ignore[assignment]


class ExtractionConsensusCompleteEvent(V3PipelineEvent):
    """Emitted when consensus merging finishes (terminal for extraction)."""

    type: Literal["extraction.consensus_complete"] = "extraction.consensus_complete"
    data: ExtractionConsensusCompleteData  # type: ignore[assignment]


class AIBuildingExtractedEvent(V3PipelineEvent):
    """Emitted when LLM extraction completes for one building block."""

    type: Literal["ai.building_extracted"] = "ai.building_extracted"
    data: AIBuildingExtractedData  # type: ignore[assignment]


class AIItemsExtractedEvent(V3PipelineEvent):
    """Emitted when item-level extraction completes for a building section."""

    type: Literal["ai.items_extracted"] = "ai.items_extracted"
    data: AIItemsExtractedData  # type: ignore[assignment]


class AIValidationCompleteEvent(V3PipelineEvent):
    """Emitted when the final validation pass finishes (terminal for ai)."""

    type: Literal["ai.validation_complete"] = "ai.validation_complete"
    data: AIValidationCompleteData  # type: ignore[assignment]


class BulkProgressEvent(V3PipelineEvent):
    """Emitted periodically during bulk batch operations."""

    type: Literal["bulk.progress"] = "bulk.progress"
    data: BulkProgressData  # type: ignore[assignment]


class BulkCompleteEvent(V3PipelineEvent):
    """Emitted when a bulk batch operation finishes (terminal for bulk)."""

    type: Literal["bulk.complete"] = "bulk.complete"
    data: BulkCompleteData  # type: ignore[assignment]


# Convenience export for typed-subclass consumers
V3_EVENT_TYPES = (
    ExtractionStartedEvent,
    ExtractionProviderCompleteEvent,
    ExtractionConsensusCompleteEvent,
    AIBuildingExtractedEvent,
    AIItemsExtractedEvent,
    AIValidationCompleteEvent,
    BulkProgressEvent,
    BulkCompleteEvent,
)


# ---------------------------------------------------------------------------
# PipelineEventBus
# ---------------------------------------------------------------------------


class PipelineEventBus:
    """Asyncio.Queue-based in-memory pub/sub event bus.

    - Keyed by operation_id (maps to command_id for extractions, or a bulk
      batch UUID).
    - Each call to subscribe() creates an isolated asyncio.Queue so multiple
      concurrent SSE connections for the same operation receive all events.
    - Thread safety: operates entirely within the asyncio event loop of a
      single API worker process.
    """

    def __init__(self) -> None:
        self._subscribers: Dict[
            str, List[asyncio.Queue[Optional[V3PipelineEvent]]]
        ] = {}

    async def publish(self, event: V3PipelineEvent) -> int:
        """Dispatch event to all subscribers for the event's operation_id.

        Args:
            event: The V3PipelineEvent to publish.

        Returns:
            The number of subscriber queues the event was delivered to.
        """
        queues = self._subscribers.get(event.operation_id, [])
        for q in queues:
            await q.put(event)
        if queues:
            logger.debug(
                f"[EventBus] Published {event.type} to {len(queues)} subscriber(s) "
                f"for operation {event.operation_id}"
            )
        return len(queues)

    async def subscribe(
        self,
        operation_id: str,
        timeout_seconds: float = 300.0,
    ) -> AsyncGenerator[V3PipelineEvent, None]:
        """Subscribe to events for a given operation_id.

        Creates a new asyncio.Queue, registers it under operation_id, and
        yields events as they arrive.  The generator cleans up its queue on
        normal exit, GeneratorExit, and asyncio.TimeoutError.

        Args:
            operation_id: The operation to subscribe to.
            timeout_seconds: Seconds to wait for each event before timing out.

        Yields:
            V3PipelineEvent instances published for this operation_id.

        Raises:
            asyncio.TimeoutError: If no event arrives within timeout_seconds.
        """
        queue: asyncio.Queue[Optional[V3PipelineEvent]] = asyncio.Queue()

        # Register queue
        if operation_id not in self._subscribers:
            self._subscribers[operation_id] = []
        self._subscribers[operation_id].append(queue)
        logger.debug(
            f"[EventBus] New subscriber for operation {operation_id} "
            f"(total: {len(self._subscribers[operation_id])})"
        )

        try:
            while True:
                event = await asyncio.wait_for(queue.get(), timeout=timeout_seconds)
                if event is None:
                    # Sentinel — bus is signalling shutdown for this operation
                    break
                yield event
        except asyncio.TimeoutError:
            logger.debug(
                f"[EventBus] Subscriber timed out after {timeout_seconds}s "
                f"for operation {operation_id}"
            )
            raise
        except GeneratorExit:
            logger.debug(
                f"[EventBus] Subscriber closed early for operation {operation_id}"
            )
        finally:
            self._cleanup_queue(operation_id, queue)

    def _cleanup_queue(
        self,
        operation_id: str,
        queue: asyncio.Queue[Optional[V3PipelineEvent]],
    ) -> None:
        """Remove a queue from the subscriber registry."""
        if operation_id in self._subscribers:
            try:
                self._subscribers[operation_id].remove(queue)
            except ValueError:
                pass
            if not self._subscribers[operation_id]:
                del self._subscribers[operation_id]
        logger.debug(
            f"[EventBus] Cleaned up subscriber queue for operation {operation_id}"
        )


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_bus: Optional[PipelineEventBus] = None


def get_event_bus() -> PipelineEventBus:
    """Return the module-level singleton PipelineEventBus instance."""
    global _bus
    if _bus is None:
        _bus = PipelineEventBus()
    return _bus
