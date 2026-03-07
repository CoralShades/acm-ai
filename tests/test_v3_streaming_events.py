"""Tests for E34-S1: Record-by-Record Streaming — backend event publishing."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from open_notebook.extractors.pipeline_event_bus import (
    AIBuildingExtractedData,
    AIBuildingExtractedEvent,
    AIItemsExtractedData,
    AIItemsExtractedEvent,
    AIValidationCompleteData,
    AIValidationCompleteEvent,
    PipelineEventBus,
    get_event_bus,
)


class TestPipelineEventBusEventTypes:
    """Verify the event types used in E34-S1 are properly defined."""

    def test_ai_building_extracted_event_fields(self):
        data = AIBuildingExtractedData(
            building_id="BLD#ABC_001",
            building_name="Building A",
            records_extracted=5,
            model_used="claude-sonnet-4-6",
            duration_ms=1500,
        )
        event = AIBuildingExtractedEvent(operation_id="test-op-1", data=data)
        assert event.operation_id == "test-op-1"
        assert event.data.building_id == "BLD#ABC_001"
        assert event.data.records_extracted == 5
        assert event.data.duration_ms == 1500

    def test_ai_items_extracted_event_fields(self):
        data = AIItemsExtractedData(
            building_id="BLD#ABC_001",
            items_count=5,
            items_rejected=0,
        )
        event = AIItemsExtractedEvent(operation_id="test-op-1", data=data)
        assert event.operation_id == "test-op-1"
        assert event.data.building_id == "BLD#ABC_001"
        assert event.data.items_count == 5

    def test_ai_validation_complete_event_fields(self):
        data = AIValidationCompleteData(
            records_valid=31,
            records_corrected=2,
            records_rejected=0,
            validation_duration_ms=800,
        )
        event = AIValidationCompleteEvent(operation_id="test-op-1", data=data)
        assert event.operation_id == "test-op-1"
        assert event.data.records_valid == 31
        assert event.data.validation_duration_ms == 800

    def test_get_event_bus_returns_singleton(self):
        """get_event_bus() returns the same instance on repeated calls."""
        bus1 = get_event_bus()
        bus2 = get_event_bus()
        assert bus1 is bus2


@pytest.mark.asyncio
class TestPipelineEventBusPublish:
    """Verify publish works and subscribers receive events."""

    async def test_publish_delivers_to_subscriber(self):
        """publish() delivers the event to a subscribed queue."""
        import asyncio

        bus = PipelineEventBus()

        # Manually register a queue (like subscribe() does internally)
        queue: asyncio.Queue = asyncio.Queue()
        bus._subscribers["test-op"] = [queue]

        data = AIBuildingExtractedData(
            building_id="BLD#T_001",
            building_name="Test Building",
            records_extracted=3,
            model_used="test-model",
            duration_ms=500,
        )
        event = AIBuildingExtractedEvent(operation_id="test-op", data=data)
        n = await bus.publish(event)

        assert n == 1
        received = queue.get_nowait()
        assert received.data.building_id == "BLD#T_001"

    async def test_publish_without_subscriber_does_not_raise(self):
        """Publishing with no subscribers should not raise and return 0."""
        bus = PipelineEventBus()
        data = AIBuildingExtractedData(
            building_id="BLD#T_001",
            building_name="Test Building",
            records_extracted=3,
            model_used="test-model",
            duration_ms=500,
        )
        event = AIBuildingExtractedEvent(operation_id="orphan-op", data=data)
        n = await bus.publish(event)
        assert n == 0

    async def test_publish_only_routes_to_matching_operation(self):
        """Events are only routed to subscribers for the matching operation_id."""
        import asyncio

        bus = PipelineEventBus()

        queue1: asyncio.Queue = asyncio.Queue()
        queue2: asyncio.Queue = asyncio.Queue()
        bus._subscribers["op-1"] = [queue1]
        bus._subscribers["op-2"] = [queue2]

        data = AIBuildingExtractedData(
            building_id="BLD#T_001",
            building_name="Building",
            records_extracted=1,
            model_used="m",
            duration_ms=100,
        )
        n = await bus.publish(AIBuildingExtractedEvent(operation_id="op-1", data=data))

        assert n == 1
        assert queue1.qsize() == 1
        assert queue2.qsize() == 0


class TestExtractionStateHasOperationId:
    """Verify ExtractionState includes operation_id key."""

    def test_extraction_state_operation_id_key(self):
        import typing

        from open_notebook.graphs.acm_extraction import ExtractionState

        hints = typing.get_type_hints(ExtractionState)
        assert "operation_id" in hints, (
            "ExtractionState must include 'operation_id' key for E34-S1 streaming"
        )
