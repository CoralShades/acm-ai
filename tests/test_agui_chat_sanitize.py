"""Tests for AG-UI chat event sanitization — BUG-4 regression coverage.

Verifies that AIMessage objects from execute_write_node are correctly
sanitized before AG-UI EventEncoder serialization, preventing the SSE
stream crash identified in BUG-4.
"""

import json

import pytest
from ag_ui.core import EventType, MessagesSnapshotEvent, StateSnapshotEvent
from ag_ui.encoder import EventEncoder
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from api.routers.agui_chat import (
    _safe_encode,
    _sanitize_messages_snapshot,
    _sanitize_state_snapshot,
)


class TestSanitizeStateSnapshot:
    """_sanitize_state_snapshot must convert BaseMessage objects in snapshot."""

    def test_aimessage_in_snapshot_is_converted(self):
        """Core BUG-4 scenario: AIMessage from execute_write_node."""
        ai_msg = AIMessage(content="Write confirmed: updated friability.")
        event = StateSnapshotEvent(
            type=EventType.STATE_SNAPSHOT,
            snapshot={
                "messages": [ai_msg],
                "source_id": "source:abc123",
                "intent": "write",
            },
        )

        sanitized = _sanitize_state_snapshot(event)

        # snapshot should be a dict with no BaseMessage objects
        assert isinstance(sanitized.snapshot, dict)
        msgs = sanitized.snapshot["messages"]
        assert len(msgs) == 1
        assert isinstance(msgs[0], dict)
        assert msgs[0]["role"] == "assistant"
        assert "Write confirmed" in msgs[0]["content"]

    def test_mixed_messages_preserved(self):
        """Snapshot with HumanMessage + AIMessage both get converted."""
        human = HumanMessage(content="Update record")
        ai = AIMessage(content="Done")
        event = StateSnapshotEvent(
            type=EventType.STATE_SNAPSHOT,
            snapshot={"messages": [human, ai]},
        )

        sanitized = _sanitize_state_snapshot(event)
        msgs = sanitized.snapshot["messages"]
        assert len(msgs) == 2
        roles = {m["role"] for m in msgs}
        assert roles == {"user", "assistant"}

    def test_already_safe_snapshot_passthrough(self):
        """Snapshot with no BaseMessage objects passes through unchanged."""
        event = StateSnapshotEvent(
            type=EventType.STATE_SNAPSHOT,
            snapshot={"messages": [{"role": "assistant", "content": "hi"}]},
        )

        sanitized = _sanitize_state_snapshot(event)
        assert sanitized.snapshot["messages"] == [
            {"role": "assistant", "content": "hi"}
        ]

    def test_empty_messages_passthrough(self):
        """Snapshot with empty messages list passes through."""
        event = StateSnapshotEvent(
            type=EventType.STATE_SNAPSHOT,
            snapshot={"messages": [], "source_id": "source:x"},
        )

        sanitized = _sanitize_state_snapshot(event)
        assert sanitized.snapshot == {"messages": [], "source_id": "source:x"}

    def test_non_dict_snapshot_passthrough(self):
        """Non-dict snapshot passes through."""
        event = StateSnapshotEvent(
            type=EventType.STATE_SNAPSHOT,
            snapshot="raw-string",
        )

        sanitized = _sanitize_state_snapshot(event)
        assert sanitized.snapshot == "raw-string"

    def test_other_state_fields_made_json_safe(self):
        """Non-message fields in snapshot are also sanitized."""
        event = StateSnapshotEvent(
            type=EventType.STATE_SNAPSHOT,
            snapshot={
                "messages": [AIMessage(content="ok")],
                "source_id": "source:abc",
                "intent": None,
            },
        )

        sanitized = _sanitize_state_snapshot(event)
        assert sanitized.snapshot["source_id"] == "source:abc"


class TestSanitizeMessagesSnapshot:
    """_sanitize_messages_snapshot handles stray BaseMessage objects."""

    def test_basemessage_cannot_be_constructed_in_event(self):
        """Pydantic rejects BaseMessage at MessagesSnapshotEvent construction.

        This proves the crash happens INSIDE _handle_stream_events when
        langchain_messages_to_agui() fails — the generator-level try/except
        in the custom endpoint is the correct fix (not post-construction
        sanitization).
        """
        ai = AIMessage(content="Write confirmed")
        with pytest.raises(Exception):
            # Pydantic's discriminated union rejects BaseMessage objects
            MessagesSnapshotEvent(
                type=EventType.MESSAGES_SNAPSHOT,
                messages=[ai],
            )

    def test_clean_messages_passthrough(self):
        """Event with proper AGUI messages passes through."""
        from ag_ui.core import AssistantMessage

        agui_msg = AssistantMessage(
            id="test-id", role="assistant", content="hello"
        )
        event = MessagesSnapshotEvent(
            type=EventType.MESSAGES_SNAPSHOT,
            messages=[agui_msg],
        )

        sanitized = _sanitize_messages_snapshot(event)
        assert sanitized.messages == [agui_msg]

    def test_empty_messages_passthrough(self):
        event = MessagesSnapshotEvent(
            type=EventType.MESSAGES_SNAPSHOT,
            messages=[],
        )
        sanitized = _sanitize_messages_snapshot(event)
        assert sanitized.messages == []


class TestSafeEncode:
    """_safe_encode must never raise, even on non-serializable events."""

    def test_normal_event_encodes(self):
        """Normal event encodes to SSE format."""
        encoder = EventEncoder()
        event = StateSnapshotEvent(
            type=EventType.STATE_SNAPSHOT,
            snapshot={"messages": [], "source_id": "source:x"},
        )

        result = _safe_encode(encoder, event)
        assert result.startswith("data: ")
        assert result.endswith("\n\n")
        parsed = json.loads(result[len("data: ") : -2])
        assert parsed["type"] == "STATE_SNAPSHOT" or "snapshot" in parsed

    def test_sanitized_aimessage_event_encodes(self):
        """BUG-4 core test: sanitized StateSnapshotEvent with AIMessage encodes."""
        encoder = EventEncoder()
        ai_msg = AIMessage(content="Write confirmed: friability updated.")
        event = StateSnapshotEvent(
            type=EventType.STATE_SNAPSHOT,
            snapshot={
                "messages": [ai_msg],
                "source_id": "source:abc",
            },
        )

        # Sanitize first (as the endpoint does)
        event = _sanitize_state_snapshot(event)

        # This must not raise
        result = _safe_encode(encoder, event)
        assert "data: " in result

    def test_unsanitized_aimessage_fallback(self):
        """Unsanitized AIMessage in snapshot triggers fallback encoding."""
        encoder = EventEncoder()
        ai_msg = AIMessage(content="Write confirmed")
        event = StateSnapshotEvent(
            type=EventType.STATE_SNAPSHOT,
            snapshot={"messages": [ai_msg]},
        )

        # Skip sanitization — _safe_encode must still not crash
        result = _safe_encode(encoder, event)
        assert result.startswith("data: ")
        assert result.endswith("\n\n")


class TestFullEncodePipeline:
    """End-to-end: create event → sanitize → encode → valid SSE."""

    def test_execute_write_node_output_full_pipeline(self):
        """Simulates the exact BUG-4 flow: execute_write_node → snapshot → encode."""
        encoder = EventEncoder()

        # Simulate execute_write_node output
        write_result = "Write confirmed: updated friability to 'Non-friable' on record acm_record:abc123"
        ai_msg = AIMessage(content=write_result)

        # Simulate the StateSnapshotEvent emitted by the adapter
        event = StateSnapshotEvent(
            type=EventType.STATE_SNAPSHOT,
            snapshot={
                "messages": [
                    HumanMessage(content="Approved. Execute operation #op123"),
                    ai_msg,
                ],
                "source_id": "source:test",
                "intent": "write",
            },
        )

        # Sanitize (as the custom endpoint does)
        event = _sanitize_state_snapshot(event)

        # Encode (must not raise)
        sse_str = _safe_encode(encoder, event)
        assert sse_str.startswith("data: ")

        # Parse the JSON payload
        payload = json.loads(sse_str[len("data: ") : -2])
        snapshot = payload.get("snapshot", {})
        msgs = snapshot.get("messages", [])

        # Verify both messages were converted
        assert len(msgs) == 2
        assert msgs[0]["role"] == "user"
        assert msgs[1]["role"] == "assistant"
        assert "Write confirmed" in msgs[1]["content"]

    def test_tool_message_in_snapshot(self):
        """ToolMessage objects in snapshot are also handled."""
        encoder = EventEncoder()
        tool_msg = ToolMessage(
            content="Query returned 5 rows",
            tool_call_id="call_123",
        )
        event = StateSnapshotEvent(
            type=EventType.STATE_SNAPSHOT,
            snapshot={"messages": [tool_msg]},
        )

        event = _sanitize_state_snapshot(event)
        sse_str = _safe_encode(encoder, event)
        payload = json.loads(sse_str[len("data: ") : -2])
        msgs = payload.get("snapshot", {}).get("messages", [])
        assert len(msgs) == 1
        assert msgs[0]["role"] == "tool"
