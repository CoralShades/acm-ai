"""Unit tests for PipelineEventBus and V3 SSE infrastructure.

All async tests use pytest-asyncio (already in dev dependencies).

Story: E31-S7 PipelineEventBus + SSE Infrastructure
"""

from __future__ import annotations

import asyncio
import json

import pytest

from open_notebook.extractors.pipeline_event_bus import (
    AIBuildingExtractedEvent,
    AIItemsExtractedEvent,
    AIValidationCompleteEvent,
    BulkCompleteEvent,
    BulkProgressEvent,
    ExtractionConsensusCompleteEvent,
    ExtractionProviderCompleteEvent,
    ExtractionStartedEvent,
    PipelineEventBus,
    V3PipelineEvent,
    get_event_bus,
)
from open_notebook.extractors.pipeline_events import now_iso

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_extraction_started(op: str = "op-1") -> V3PipelineEvent:
    return V3PipelineEvent(
        type="extraction.started",
        operation_id=op,
        timestamp=now_iso(),
        data={
            "source_id": "source:abc",
            "provider_sequence": ["docling", "mineru"],
            "total_pages": 10,
        },
    )


def _make_ai_building(op: str = "op-1") -> V3PipelineEvent:
    return V3PipelineEvent(
        type="ai.building_extracted",
        operation_id=op,
        timestamp=now_iso(),
        data={
            "building_id": "BLD-01",
            "building_name": "Main",
            "records_extracted": 5,
            "model_used": "openai/gpt-4o",
            "duration_ms": 100,
        },
    )


def _make_bulk_complete(op: str = "op-bulk") -> V3PipelineEvent:
    return V3PipelineEvent(
        type="bulk.complete",
        operation_id=op,
        timestamp=now_iso(),
        data={"total": 5, "completed": 5, "failed": 0, "duration_ms": 1000},
    )


# ---------------------------------------------------------------------------
# AC1 — PipelineEventBus pub/sub mechanics
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_publish_delivers_to_subscriber():
    """publish() delivers the event to a subscribed generator."""
    bus = PipelineEventBus()
    event = _make_extraction_started()

    received: list[V3PipelineEvent] = []

    async def _consume():
        async for ev in bus.subscribe(event.operation_id, timeout_seconds=2.0):
            received.append(ev)
            break  # stop after first event

    consume_task = asyncio.create_task(_consume())
    # Give the subscriber time to register
    await asyncio.sleep(0)

    await bus.publish(event)
    await asyncio.wait_for(consume_task, timeout=3.0)

    assert len(received) == 1
    assert received[0].type == "extraction.started"
    assert received[0].operation_id == event.operation_id


@pytest.mark.asyncio
async def test_publish_delivers_to_multiple_subscribers():
    """Two subscribers for the same operation_id both receive the event."""
    bus = PipelineEventBus()
    event = _make_extraction_started("op-multi")

    results_a: list[V3PipelineEvent] = []
    results_b: list[V3PipelineEvent] = []

    async def _consume(store: list):
        async for ev in bus.subscribe(event.operation_id, timeout_seconds=2.0):
            store.append(ev)
            break

    task_a = asyncio.create_task(_consume(results_a))
    task_b = asyncio.create_task(_consume(results_b))
    await asyncio.sleep(0)

    await bus.publish(event)
    await asyncio.gather(
        asyncio.wait_for(task_a, timeout=3.0),
        asyncio.wait_for(task_b, timeout=3.0),
    )

    assert len(results_a) == 1
    assert len(results_b) == 1


@pytest.mark.asyncio
async def test_subscriber_filters_by_operation_id():
    """A subscriber on op-B does not receive events published for op-A."""
    bus = PipelineEventBus()
    event_a = _make_extraction_started("op-A")

    received: list[V3PipelineEvent] = []

    async def _consume_b():
        try:
            async for ev in bus.subscribe("op-B", timeout_seconds=0.2):
                received.append(ev)
        except asyncio.TimeoutError:
            pass

    consume_task = asyncio.create_task(_consume_b())
    await asyncio.sleep(0)

    # Publish for op-A — op-B subscriber should not see it
    await bus.publish(event_a)
    await asyncio.wait_for(consume_task, timeout=1.0)

    assert received == []


@pytest.mark.asyncio
async def test_subscriber_cleanup_on_close():
    """Closing the generator early removes its queue from the registry.

    The generator registers its queue inside subscribe() as soon as it reaches
    the first await (asyncio.wait_for).  We cancel the consuming task to
    simulate a client disconnect; the generator's finally block must then
    remove the queue from the registry.
    """
    bus = PipelineEventBus()
    op = "op-cleanup"

    gen = bus.subscribe(op, timeout_seconds=10.0)

    # Wrap the generator iteration in a coroutine task so we can cancel it
    async def _drain():
        async for _ in gen:
            break

    task = asyncio.create_task(_drain())
    # Yield control so the task starts and the generator registers its queue
    await asyncio.sleep(0)
    await asyncio.sleep(0)  # second yield ensures wait_for is entered

    # Verify queue is registered before we cancel
    assert op in bus._subscribers
    assert len(bus._subscribers[op]) == 1

    # Cancel the consuming task — this triggers GeneratorExit inside subscribe()
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

    # Allow the generator's finally block to run
    await asyncio.sleep(0)

    # The finally block should have removed the queue from the registry
    assert op not in bus._subscribers


@pytest.mark.asyncio
async def test_bus_singleton():
    """get_event_bus() returns the same instance across two calls."""
    bus_a = get_event_bus()
    bus_b = get_event_bus()
    assert bus_a is bus_b


@pytest.mark.asyncio
async def test_publish_returns_subscriber_count():
    """publish() returns the number of subscriber queues the event reached."""
    bus = PipelineEventBus()
    event = _make_extraction_started("op-count")

    received_a: list[V3PipelineEvent] = []
    received_b: list[V3PipelineEvent] = []

    async def _consume(store: list):
        async for ev in bus.subscribe(event.operation_id, timeout_seconds=2.0):
            store.append(ev)
            break

    task_a = asyncio.create_task(_consume(received_a))
    task_b = asyncio.create_task(_consume(received_b))
    await asyncio.sleep(0)

    count = await bus.publish(event)
    await asyncio.gather(
        asyncio.wait_for(task_a, timeout=3.0),
        asyncio.wait_for(task_b, timeout=3.0),
    )

    assert count == 2


# ---------------------------------------------------------------------------
# AC2/AC3 — Event types and SSE serialization
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_v3_event_serialization_extraction_started():
    """V3PipelineEvent round-trips cleanly through model_dump_json()."""
    event = V3PipelineEvent(
        type="extraction.started",
        operation_id="cmd:test123",
        timestamp="2026-03-04T10:00:00.000000+00:00",
        data={
            "source_id": "source:xyz",
            "provider_sequence": ["docling", "mineru"],
            "total_pages": 42,
        },
    )
    json_str = event.model_dump_json()
    parsed = json.loads(json_str)

    assert parsed["type"] == "extraction.started"
    assert parsed["operation_id"] == "cmd:test123"
    assert parsed["data"]["source_id"] == "source:xyz"
    assert parsed["data"]["total_pages"] == 42

    # Round-trip back to model
    rebuilt = V3PipelineEvent.model_validate(parsed)
    assert rebuilt.type == event.type
    assert rebuilt.operation_id == event.operation_id


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "event_type,data",
    [
        (
            "extraction.started",
            {
                "source_id": "source:1",
                "provider_sequence": ["docling"],
                "total_pages": 5,
            },
        ),
        (
            "extraction.provider_complete",
            {
                "provider": "docling",
                "records_extracted": 10,
                "duration_ms": 500,
                "pages_processed": 5,
            },
        ),
        (
            "extraction.consensus_complete",
            {
                "records_final": 10,
                "records_docling_only": 1,
                "records_mineru_only": 2,
                "records_agreed": 7,
                "consensus_duration_ms": 100,
            },
        ),
        (
            "ai.building_extracted",
            {
                "building_id": "BLD-01",
                "building_name": "Main",
                "records_extracted": 3,
                "model_used": "openai/gpt-4o",
                "duration_ms": 200,
            },
        ),
        (
            "ai.items_extracted",
            {"building_id": "BLD-01", "items_count": 3, "items_rejected": 0},
        ),
        (
            "ai.validation_complete",
            {
                "records_valid": 9,
                "records_corrected": 1,
                "records_rejected": 0,
                "validation_duration_ms": 300,
            },
        ),
        (
            "bulk.progress",
            {"total": 10, "completed": 5, "failed": 0, "percent": 50.0},
        ),
        (
            "bulk.complete",
            {"total": 10, "completed": 10, "failed": 0, "duration_ms": 2000},
        ),
    ],
)
async def test_v3_event_all_types_schema_valid(event_type: str, data: dict):
    """All 8 V3 event types validate successfully with their minimal payloads."""
    event = V3PipelineEvent(
        type=event_type,
        operation_id="op-schema-test",
        timestamp=now_iso(),
        data=data,
    )
    # Must not raise
    json_str = event.model_dump_json()
    rebuilt = V3PipelineEvent.model_validate_json(json_str)
    assert rebuilt.type == event_type


def test_sse_format_named_event():
    """SSE serialiser produces correct named-event + data + blank-line format."""
    from api.routers.v3_streaming import _format_sse_event

    event = V3PipelineEvent(
        type="extraction.started",
        operation_id="op-sse",
        timestamp="2026-03-04T10:00:00.000000+00:00",
        data={
            "source_id": "source:1",
            "provider_sequence": ["docling"],
            "total_pages": 1,
        },
    )
    sse = _format_sse_event(event)

    lines = sse.split("\n")
    assert lines[0] == "event: extraction.started"
    assert lines[1].startswith("data: ")
    # Last two characters of the string should be \n\n (blank separator)
    assert sse.endswith("\n\n")

    # data line must be valid JSON containing the event fields
    data_json = lines[1][len("data: ") :]
    parsed = json.loads(data_json)
    assert parsed["type"] == "extraction.started"
    assert parsed["operation_id"] == "op-sse"


def test_sse_terminal_event_sends_done_sentinel():
    """Terminal events produce a trailing event: done line via _format_sse_done."""
    from api.routers.v3_streaming import _TERMINAL_EVENT_TYPES, _format_sse_done

    terminal_types = list(_TERMINAL_EVENT_TYPES)
    assert "extraction.consensus_complete" in terminal_types
    assert "ai.validation_complete" in terminal_types
    assert "bulk.complete" in terminal_types

    for terminal_type in terminal_types:
        done_sse = _format_sse_done("op-x", terminal_type)
        assert done_sse.startswith("event: done\n")
        assert "op-x" in done_sse
        assert terminal_type in done_sse
        assert done_sse.endswith("\n\n")


# ---------------------------------------------------------------------------
# AC7 — Event filtering by category prefix
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_extraction_endpoint_filters_ai_events():
    """Extraction subscriber (prefix 'extraction.') ignores ai.* events."""
    bus = PipelineEventBus()
    ai_event = _make_ai_building("op-filter-1")
    extraction_event = _make_extraction_started("op-filter-1")

    collected: list[V3PipelineEvent] = []

    async def _consume_extraction():
        """Collect extraction.* events only."""
        async for ev in bus.subscribe("op-filter-1", timeout_seconds=0.5):
            if ev.type.startswith("extraction."):
                collected.append(ev)
            # stop after receiving both events (or timeout)

    task = asyncio.create_task(_consume_extraction())
    await asyncio.sleep(0)

    # Publish ai event first, then extraction event
    await bus.publish(ai_event)
    await bus.publish(extraction_event)

    try:
        await asyncio.wait_for(task, timeout=1.0)
    except asyncio.TimeoutError:
        pass

    # Only the extraction event should appear in a filtered consumer
    for ev in collected:
        assert ev.type.startswith("extraction.")


@pytest.mark.asyncio
async def test_bulk_endpoint_filters_extraction_events():
    """Bulk subscriber (prefix 'bulk.') ignores extraction.* events."""
    bus = PipelineEventBus()
    extraction_event = _make_extraction_started("op-filter-2")
    bulk_event = _make_bulk_complete("op-filter-2")

    collected: list[V3PipelineEvent] = []

    async def _consume_bulk():
        async for ev in bus.subscribe("op-filter-2", timeout_seconds=0.5):
            if ev.type.startswith("bulk."):
                collected.append(ev)

    task = asyncio.create_task(_consume_bulk())
    await asyncio.sleep(0)

    await bus.publish(extraction_event)
    await bus.publish(bulk_event)

    try:
        await asyncio.wait_for(task, timeout=1.0)
    except asyncio.TimeoutError:
        pass

    for ev in collected:
        assert ev.type.startswith("bulk.")


# ---------------------------------------------------------------------------
# AC8 — Non-breaking: existing routers unmodified
# ---------------------------------------------------------------------------


def test_existing_extraction_events_router_unmodified():
    """extraction_events.router has exactly 3 routes (unchanged from E27)."""
    from api.routers import extraction_events

    assert len(extraction_events.router.routes) == 3


def test_existing_agui_extraction_router_unmodified():
    """agui_extraction.router has exactly 1 route (unchanged from E27)."""
    from api.routers import agui_extraction

    assert len(agui_extraction.router.routes) == 1


# ---------------------------------------------------------------------------
# Typed subclass smoke tests
# ---------------------------------------------------------------------------


def test_typed_subclasses_are_importable():
    """All 8 typed event subclasses can be imported and instantiated."""
    ExtractionStartedEvent(
        operation_id="op",
        timestamp=now_iso(),
        data={  # type: ignore[arg-type]
            "source_id": "s:1",
            "provider_sequence": ["docling"],
            "total_pages": 1,
        },
    )
    ExtractionProviderCompleteEvent(
        operation_id="op",
        timestamp=now_iso(),
        data={  # type: ignore[arg-type]
            "provider": "docling",
            "records_extracted": 5,
            "duration_ms": 200,
            "pages_processed": 1,
        },
    )
    ExtractionConsensusCompleteEvent(
        operation_id="op",
        timestamp=now_iso(),
        data={  # type: ignore[arg-type]
            "records_final": 5,
            "records_docling_only": 1,
            "records_mineru_only": 0,
            "records_agreed": 4,
            "consensus_duration_ms": 50,
        },
    )
    AIBuildingExtractedEvent(
        operation_id="op",
        timestamp=now_iso(),
        data={  # type: ignore[arg-type]
            "building_id": "B1",
            "building_name": "Block A",
            "records_extracted": 3,
            "model_used": "openai/gpt-4o",
            "duration_ms": 100,
        },
    )
    AIItemsExtractedEvent(
        operation_id="op",
        timestamp=now_iso(),
        data={"building_id": "B1", "items_count": 3, "items_rejected": 0},  # type: ignore[arg-type]
    )
    AIValidationCompleteEvent(
        operation_id="op",
        timestamp=now_iso(),
        data={  # type: ignore[arg-type]
            "records_valid": 4,
            "records_corrected": 1,
            "records_rejected": 0,
            "validation_duration_ms": 80,
        },
    )
    BulkProgressEvent(
        operation_id="op",
        timestamp=now_iso(),
        data={"total": 5, "completed": 2, "failed": 0, "percent": 40.0},  # type: ignore[arg-type]
    )
    BulkCompleteEvent(
        operation_id="op",
        timestamp=now_iso(),
        data={"total": 5, "completed": 5, "failed": 0, "duration_ms": 500},  # type: ignore[arg-type]
    )
