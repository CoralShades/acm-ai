"""Tests for the unified session message history endpoint.

Covers GET /{source_id}/unified-sessions/{session_id}/messages
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client after environment variables have been cleared by conftest."""
    from api.main import app

    return TestClient(app)


class TestGetSessionMessages:
    """Test suite for GET /unified-sessions/{session_id}/messages."""

    @patch("api.routers.unified_sessions.get_checkpointer")
    @patch("api.routers.unified_sessions.repo_query")
    def test_returns_messages_when_checkpoint_exists(
        self, mock_repo_query, mock_get_checkpointer, client
    ):
        """Should return serialized messages from the LangGraph checkpoint."""
        # Session found with a thread_id
        mock_repo_query.return_value = [{"thread_id": "thread-abc-123"}]

        # Stub checkpointer with a checkpoint containing two messages
        mock_checkpointer = MagicMock()
        fake_ai_message = MagicMock()
        fake_ai_message.type = "ai"
        fake_ai_message.content = "Hello, how can I help?"
        fake_ai_message.tool_calls = []
        fake_ai_message.additional_kwargs = {}

        fake_human_message = MagicMock()
        fake_human_message.type = "human"
        fake_human_message.content = "Summarise this document"
        fake_human_message.additional_kwargs = {}

        fake_checkpoint = {
            "channel_values": {
                "messages": [fake_human_message, fake_ai_message],
            }
        }
        fake_tuple = MagicMock()
        fake_tuple.checkpoint = fake_checkpoint
        mock_checkpointer.aget_tuple = AsyncMock(return_value=fake_tuple)
        mock_get_checkpointer.return_value = mock_checkpointer

        with patch(
            "api.routers.unified_sessions.messages_to_dict",
            return_value=[
                {"type": "human", "data": {"content": "Summarise this document"}},
                {"type": "ai", "data": {"content": "Hello, how can I help?"}},
            ],
        ):
            response = client.get(
                "/api/sources/source:abc/unified-sessions/chat_session:1/messages"
            )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["messages"]) == 2

        user_msg = data["messages"][0]
        assert user_msg["role"] == "user"
        assert user_msg["content"] == "Summarise this document"

        ai_msg = data["messages"][1]
        assert ai_msg["role"] == "assistant"
        assert ai_msg["content"] == "Hello, how can I help?"

    @patch("api.routers.unified_sessions.get_checkpointer")
    @patch("api.routers.unified_sessions.repo_query")
    def test_returns_empty_when_no_checkpoint(
        self, mock_repo_query, mock_get_checkpointer, client
    ):
        """Should return empty list when checkpointer has no data for the thread."""
        mock_repo_query.return_value = [{"thread_id": "thread-xyz"}]

        mock_checkpointer = MagicMock()
        mock_checkpointer.aget_tuple = AsyncMock(return_value=None)
        mock_get_checkpointer.return_value = mock_checkpointer

        response = client.get(
            "/api/sources/source:abc/unified-sessions/chat_session:2/messages"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["messages"] == []

    @patch("api.routers.unified_sessions.repo_query")
    def test_returns_empty_when_session_has_no_thread_id(
        self, mock_repo_query, client
    ):
        """Should return empty list when session exists but has no thread_id yet."""
        mock_repo_query.return_value = [{"thread_id": None}]

        response = client.get(
            "/api/sources/source:abc/unified-sessions/chat_session:3/messages"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["messages"] == []

    @patch("api.routers.unified_sessions.repo_query")
    def test_returns_404_when_session_not_found(self, mock_repo_query, client):
        """Should return 404 when the session record is not in SurrealDB."""
        mock_repo_query.return_value = []

        response = client.get(
            "/api/sources/source:abc/unified-sessions/chat_session:missing/messages"
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Session not found"

    @patch("api.routers.unified_sessions.get_checkpointer")
    @patch("api.routers.unified_sessions.repo_query")
    def test_graceful_degradation_on_checkpointer_error(
        self, mock_repo_query, mock_get_checkpointer, client
    ):
        """Should return empty list (not 500) if the checkpointer raises an error."""
        mock_repo_query.return_value = [{"thread_id": "thread-err"}]

        mock_checkpointer = MagicMock()
        mock_checkpointer.aget_tuple = AsyncMock(side_effect=RuntimeError("DB locked"))
        mock_get_checkpointer.return_value = mock_checkpointer

        response = client.get(
            "/api/sources/source:abc/unified-sessions/chat_session:4/messages"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["messages"] == []

    @patch("api.routers.unified_sessions.get_checkpointer")
    @patch("api.routers.unified_sessions.repo_query")
    def test_role_mapping_tool_message(
        self, mock_repo_query, mock_get_checkpointer, client
    ):
        """Should correctly map LangChain 'tool' type to role 'tool'."""
        mock_repo_query.return_value = [{"thread_id": "thread-tool"}]

        mock_checkpointer = MagicMock()
        fake_checkpoint = {"channel_values": {"messages": [MagicMock()]}}
        fake_tuple = MagicMock()
        fake_tuple.checkpoint = fake_checkpoint
        mock_checkpointer.aget_tuple = AsyncMock(return_value=fake_tuple)
        mock_get_checkpointer.return_value = mock_checkpointer

        with patch(
            "api.routers.unified_sessions.messages_to_dict",
            return_value=[
                {
                    "type": "tool",
                    "data": {
                        "content": '{"result": "ok"}',
                        "tool_call_id": "call-999",
                    },
                }
            ],
        ):
            response = client.get(
                "/api/sources/source:abc/unified-sessions/chat_session:5/messages"
            )

        assert response.status_code == 200
        msg = response.json()["messages"][0]
        assert msg["role"] == "tool"
        assert msg["tool_call_id"] == "call-999"
