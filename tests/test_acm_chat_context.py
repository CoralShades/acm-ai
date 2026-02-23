"""
Tests for ACM context integration in source chat.

Stories:
- E4-S1: Add ACM Records to Chat Context
- E4-S3: ACM-Aware Chat Responses
- E4-S4: Support ACM-Specific Questions
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestFormatACMContext:
    """Test suite for format_acm_context function."""

    @pytest.mark.asyncio
    @patch("open_notebook.graphs.source_chat.ACMRecord")
    async def test_format_acm_context_with_records(self, mock_acm_record):
        """Test formatting ACM records as markdown table."""
        from open_notebook.graphs.source_chat import format_acm_context

        # Create mock ACM records
        mock_records = [
            MagicMock(
                building_name="Building A",
                building_id="B001",
                room_name="Room 101",
                product="Ceiling Tiles",
                material_description="Asbestos cement ceiling tiles in poor condition",
                risk_status="High",
                result="Detected",
            ),
            MagicMock(
                building_name="Building B",
                building_id="B002",
                room_name="Room 201",
                product="Floor Tiles",
                material_description="Vinyl asbestos floor tiles",
                risk_status="Low",
                result="Detected",
            ),
        ]
        mock_acm_record.get_by_source = AsyncMock(return_value=mock_records)

        result = await format_acm_context("source:123")

        # Verify function was called
        mock_acm_record.get_by_source.assert_called_once_with("source:123")

        # Verify markdown table structure
        assert "## ACM Register Data" in result
        assert "| Building | Room | Product | Material | Risk | Result |" in result
        assert "|----------|------|---------|----------|------|--------|" in result
        assert "Building A" in result
        assert "Room 101" in result
        assert "Ceiling Tiles" in result
        assert "High" in result
        assert "Detected" in result

    @pytest.mark.asyncio
    @patch("open_notebook.graphs.source_chat.ACMRecord")
    async def test_format_acm_context_empty_records(self, mock_acm_record):
        """Test formatting when no ACM records exist."""
        from open_notebook.graphs.source_chat import format_acm_context

        mock_acm_record.get_by_source = AsyncMock(return_value=[])

        result = await format_acm_context("source:123")

        assert result == ""

    @pytest.mark.asyncio
    @patch("open_notebook.graphs.source_chat.ACMRecord")
    async def test_format_acm_context_truncation(self, mock_acm_record):
        """Test that records are truncated when exceeding max_records."""
        from open_notebook.graphs.source_chat import format_acm_context

        # Create 60 mock records
        mock_records = [
            MagicMock(
                building_name=f"Building {i}",
                building_id=f"B{i:03d}",
                room_name=f"Room {i}",
                product="Ceiling Tiles",
                material_description="Test material description",
                risk_status="Medium",
                result="Detected",
            )
            for i in range(60)
        ]
        mock_acm_record.get_by_source = AsyncMock(return_value=mock_records)

        result = await format_acm_context("source:123", max_records=50)

        # Should have truncation indicator
        assert "50 of 60 records shown" in result
        # Should not have Building 59 (index 59 is the 60th record)
        assert "Building 59" not in result
        # Should have Building 49 (index 49 is the 50th record)
        assert "Building 49" in result

    @pytest.mark.asyncio
    @patch("open_notebook.graphs.source_chat.ACMRecord")
    async def test_format_acm_context_handles_missing_fields(self, mock_acm_record):
        """Test formatting handles records with missing optional fields."""
        from open_notebook.graphs.source_chat import format_acm_context

        mock_records = [
            MagicMock(
                building_name=None,
                building_id="B001",
                room_name=None,
                product="Ceiling Tiles",
                material_description="Short desc",
                risk_status=None,
                result="Detected",
            ),
        ]
        mock_acm_record.get_by_source = AsyncMock(return_value=mock_records)

        result = await format_acm_context("source:123")

        # Should use building_id as fallback for building_name
        assert "B001" in result
        # Should show dash for missing room
        assert "| - |" in result or "| -" in result

    @pytest.mark.asyncio
    @patch("open_notebook.graphs.source_chat.ACMRecord")
    async def test_format_acm_context_material_truncation(self, mock_acm_record):
        """Test that long material descriptions are truncated."""
        from open_notebook.graphs.source_chat import format_acm_context

        long_description = "A" * 100  # 100 character description
        mock_records = [
            MagicMock(
                building_name="Building A",
                building_id="B001",
                room_name="Room 101",
                product="Ceiling Tiles",
                material_description=long_description,
                risk_status="High",
                result="Detected",
            ),
        ]
        mock_acm_record.get_by_source = AsyncMock(return_value=mock_records)

        result = await format_acm_context("source:123")

        # Material description should be truncated
        assert "..." in result
        # Should not have full 100 A's
        assert "A" * 100 not in result


class TestSourceChatStateWithACM:
    """Test suite for SourceChatState with ACM context support."""

    def test_source_chat_state_includes_acm_context_flag(self):
        """Test that SourceChatState includes include_acm_context field."""
        from open_notebook.graphs.source_chat import SourceChatState

        # Create state with ACM context flag
        state: SourceChatState = {
            "messages": [],
            "source_id": "source:123",
            "source": None,
            "insights": None,
            "context": None,
            "model_override": None,
            "context_indicators": None,
            "include_acm_context": True,
        }

        assert state["include_acm_context"] is True


class TestFormatSourceContextWithACM:
    """Test suite for _format_source_context with ACM data."""

    def test_format_source_context_includes_acm_section(self):
        """Test that _format_source_context includes ACM section when provided."""
        from open_notebook.graphs.source_chat import _format_source_context

        context_data = {
            "sources": [{"id": "source:123", "title": "Test Source"}],
            "insights": [],
            "acm_context": "## ACM Register Data\n| Building | Room |\n|----------|------|\n| B1 | R1 |",
        }

        result = _format_source_context(context_data)

        assert "## ACM Register Data" in result
        assert "Building" in result
        assert "Room" in result


class TestSendMessageRequestWithACM:
    """Test suite for SendMessageRequest with ACM context field."""

    def test_send_message_request_has_acm_field(self):
        """Test that SendMessageRequest includes include_acm_context field."""
        from api.routers.source_chat import SendMessageRequest

        # Create request with ACM context enabled
        request = SendMessageRequest(message="Test message", include_acm_context=True)

        assert request.include_acm_context is True

    def test_send_message_request_acm_defaults_false(self):
        """Test that include_acm_context defaults to False."""
        from api.routers.source_chat import SendMessageRequest

        request = SendMessageRequest(message="Test message")

        assert request.include_acm_context is False


class TestACMPromptTemplate:
    """Test suite for ACM-aware prompt template (E4-S3)."""

    def test_acm_guidance_appears_when_acm_records_included(self):
        """Test that ACM guidance section appears when acm_records_included is set."""
        from ai_prompter import Prompter

        prompt_data = {
            "source": {"id": "source:123", "title": "Test SAMP Document"},
            "insights": [],
            "context": "Test source content",
            "context_indicators": {
                "sources": ["source:123"],
                "insights": [],
                "notes": [],
                "acm_records_included": ["source:123"],
            },
        }

        system_prompt = Prompter(prompt_template="source_chat").render(data=prompt_data)

        # Verify ACM-specific sections appear
        assert "ACM (ASBESTOS CONTAINING MATERIAL) GUIDANCE" in system_prompt
        assert "Risk Levels" in system_prompt
        assert "High Risk" in system_prompt
        assert "Material Types" in system_prompt
        assert "Friable" in system_prompt
        assert "ACM Citation Format" in system_prompt
        assert "[acm:" in system_prompt

    def test_acm_guidance_absent_when_no_acm_records(self):
        """Test that ACM guidance section is absent when acm_records_included is empty."""
        from ai_prompter import Prompter

        prompt_data = {
            "source": {"id": "source:123", "title": "Test Document"},
            "insights": [],
            "context": "Test source content",
            "context_indicators": {
                "sources": ["source:123"],
                "insights": [],
                "notes": [],
                "acm_records_included": [],  # Empty - no ACM data
            },
        }

        system_prompt = Prompter(prompt_template="source_chat").render(data=prompt_data)

        # Verify ACM-specific sections do NOT appear
        assert "ACM (ASBESTOS CONTAINING MATERIAL) GUIDANCE" not in system_prompt
        assert "Friable" not in system_prompt
        assert "Risk Levels" not in system_prompt

    def test_acm_guidance_absent_when_context_indicators_none(self):
        """Test that ACM guidance section is absent when context_indicators is None."""
        from ai_prompter import Prompter

        prompt_data = {
            "source": {"id": "source:123", "title": "Test Document"},
            "insights": [],
            "context": "Test source content",
            "context_indicators": None,
        }

        system_prompt = Prompter(prompt_template="source_chat").render(data=prompt_data)

        # Verify ACM-specific sections do NOT appear
        assert "ACM (ASBESTOS CONTAINING MATERIAL) GUIDANCE" not in system_prompt

    def test_acm_citation_format_in_instructions(self):
        """Test that ACM citation format is added to citing instructions."""
        from ai_prompter import Prompter

        prompt_data = {
            "source": {"id": "source:123", "title": "Test SAMP Document"},
            "insights": [],
            "context": "Test source content",
            "context_indicators": {
                "sources": ["source:123"],
                "insights": [],
                "notes": [],
                "acm_records_included": ["source:123"],
            },
        }

        system_prompt = Prompter(prompt_template="source_chat").render(data=prompt_data)

        # Verify ACM citation format appears in citing instructions
        assert "For ACM records: [acm:record_id]" in system_prompt

    def test_acm_example_appears_when_acm_records_included(self):
        """Test that ACM example section appears when ACM data is present."""
        from ai_prompter import Prompter

        prompt_data = {
            "source": {"id": "source:123", "title": "Test SAMP Document"},
            "insights": [],
            "context": "Test source content",
            "context_indicators": {
                "sources": ["source:123"],
                "insights": [],
                "notes": [],
                "acm_records_included": ["source:123"],
            },
        }

        system_prompt = Prompter(prompt_template="source_chat").render(data=prompt_data)

        # Verify ACM examples section appears with various question type examples
        assert "ACM EXAMPLES" in system_prompt
        assert "Location Query Example" in system_prompt

    def test_acm_capabilities_added_when_acm_records_included(self):
        """Test that ACM capabilities are listed when ACM data is present."""
        from ai_prompter import Prompter

        prompt_data = {
            "source": {"id": "source:123", "title": "Test SAMP Document"},
            "insights": [],
            "context": "Test source content",
            "context_indicators": {
                "sources": ["source:123"],
                "insights": [],
                "notes": [],
                "acm_records_included": ["source:123"],
            },
        }

        system_prompt = Prompter(prompt_template="source_chat").render(data=prompt_data)

        # Verify ACM capabilities appear
        assert "Expertise in Asbestos Containing Material" in system_prompt
        assert "ACM survey data" in system_prompt

    def test_acm_important_notes_added_when_acm_records_included(self):
        """Test that ACM-specific important notes appear when ACM data is present."""
        from ai_prompter import Prompter

        prompt_data = {
            "source": {"id": "source:123", "title": "Test SAMP Document"},
            "insights": [],
            "context": "Test source content",
            "context_indicators": {
                "sources": ["source:123"],
                "insights": [],
                "notes": [],
                "acm_records_included": ["source:123"],
            },
        }

        system_prompt = Prompter(prompt_template="source_chat").render(data=prompt_data)

        # Verify ACM-specific important notes
        assert "Prioritize safety" in system_prompt
        assert "Be precise with ACM citations" in system_prompt

    def test_acm_conversation_focus_items_added_when_acm_records_included(self):
        """Test that ACM conversation focus items appear when ACM data is present."""
        from ai_prompter import Prompter

        prompt_data = {
            "source": {"id": "source:123", "title": "Test SAMP Document"},
            "insights": [],
            "context": "Test source content",
            "context_indicators": {
                "sources": ["source:123"],
                "insights": [],
                "notes": [],
                "acm_records_included": ["source:123"],
            },
        }

        system_prompt = Prompter(prompt_template="source_chat").render(data=prompt_data)

        # Verify ACM conversation focus items
        assert "Understand ACM risk levels" in system_prompt
        assert "high-priority areas" in system_prompt


class TestQuestionPatternDetection:
    """Test suite for ACM question type detection (E4-S4)."""

    def test_detect_location_query(self):
        """Test detection of building/room location queries."""
        from api.utils.acm_context import detect_question_type

        assert detect_question_type("What's in Building A?") == "location_query"
        assert detect_question_type("Show me Room 101") == "location_query"
        assert detect_question_type("What is in the floor area?") == "location_query"
        assert detect_question_type("Items in Wing B") == "location_query"
        assert detect_question_type("What ACM is in the block?") == "location_query"

    def test_detect_risk_query(self):
        """Test detection of risk-related queries."""
        from api.utils.acm_context import detect_question_type

        assert detect_question_type("What are the high risk items?") == "risk_query"
        assert detect_question_type("Is this building safe?") == "risk_query"
        assert detect_question_type("Show me the hazardous materials") == "risk_query"
        assert detect_question_type("What's the danger level?") == "risk_query"
        assert detect_question_type("Medium risk items please") == "risk_query"

    def test_detect_terminology_query(self):
        """Test detection of terminology explanation queries."""
        from api.utils.acm_context import detect_question_type

        assert detect_question_type("What is friable asbestos?") == "terminology_query"
        assert detect_question_type("What does ACM mean?") == "terminology_query"
        assert detect_question_type("Define non-friable") == "terminology_query"
        assert (
            detect_question_type("Explain the SAMP documentation")
            == "terminology_query"
        )
        assert detect_question_type("What are ACMs?") == "terminology_query"

    def test_detect_action_query(self):
        """Test detection of action/compliance queries."""
        from api.utils.acm_context import detect_question_type

        assert detect_question_type("Do we need to remove anything?") == "action_query"
        assert detect_question_type("Should we remediate this?") == "action_query"
        assert detect_question_type("What action is required?") == "action_query"
        assert detect_question_type("Encapsulation recommendations?") == "action_query"
        assert detect_question_type("What needs to be done?") == "action_query"

    def test_detect_summary_query(self):
        """Test detection of summary/overview queries."""
        from api.utils.acm_context import detect_question_type

        assert detect_question_type("Give me an overview") == "summary_query"
        assert detect_question_type("How many items are there?") == "summary_query"
        assert detect_question_type("Total count of ACMs") == "summary_query"
        assert detect_question_type("List all the materials") == "summary_query"
        assert detect_question_type("Summary of findings") == "summary_query"

    def test_detect_general_query(self):
        """Test detection of general queries that don't match specific types."""
        from api.utils.acm_context import detect_question_type

        assert detect_question_type("Hello") == "general"
        assert detect_question_type("Thanks for the info") == "general"
        assert detect_question_type("Can you help me?") == "general"


class TestACMContextFormatting:
    """Test suite for ACM context formatting by question type (E4-S4)."""

    def test_format_risk_summary(self):
        """Test formatting ACM records for risk queries."""
        from api.utils.acm_context import format_acm_context_for_question

        # Use MagicMock to create ACM record-like objects
        records = [
            MagicMock(
                building_id="B001",
                building_name="Building A",
                room_id="R101",
                room_name="Room 101",
                product="Pipe Lagging",
                risk_status="High",
            ),
            MagicMock(
                building_id="B002",
                building_name="Building B",
                room_id="R201",
                room_name="Room 201",
                product="Floor Tiles",
                risk_status="Low",
            ),
            MagicMock(
                building_id="B001",
                building_name="Building A",
                room_id="R102",
                room_name="Room 102",
                product="Ceiling Tiles",
                risk_status="Medium",
            ),
        ]

        result = format_acm_context_for_question(records, "risk_query")

        assert "## ACM Risk Summary" in result
        assert "High Risk (1 item)" in result
        assert "Medium Risk (1 item)" in result
        assert "Low Risk (1 item)" in result
        assert "Pipe Lagging" in result

    def test_format_by_location(self):
        """Test formatting ACM records for location queries."""
        from api.utils.acm_context import format_acm_context_for_question

        records = [
            MagicMock(
                building_id="B001",
                building_name="Building A",
                room_id="R101",
                room_name="Room 101",
                product="Pipe Lagging",
                risk_status="High",
            ),
            MagicMock(
                building_id="B001",
                building_name="Building A",
                room_id="R102",
                room_name="Room 102",
                product="Floor Tiles",
                risk_status="Low",
            ),
            MagicMock(
                building_id="B002",
                building_name="Building B",
                room_id="R201",
                room_name="Room 201",
                product="Ceiling Tiles",
                risk_status="Medium",
            ),
        ]

        result = format_acm_context_for_question(records, "location_query")

        assert "## ACM by Location" in result
        assert "### Building A" in result
        assert "### Building B" in result
        assert "| Room | Product | Risk |" in result
        assert "Room 101" in result
        assert "Pipe Lagging" in result

    def test_format_summary(self):
        """Test formatting ACM records for summary queries."""
        from api.utils.acm_context import format_acm_context_for_question

        records = [
            MagicMock(
                building_id="B001",
                building_name="Building A",
                room_id=None,
                room_name=None,
                product="Pipe Lagging",
                risk_status="High",
            ),
            MagicMock(
                building_id="B002",
                building_name="Building B",
                room_id=None,
                room_name=None,
                product="Floor Tiles",
                risk_status="Low",
            ),
        ]

        result = format_acm_context_for_question(records, "summary_query")

        assert "## ACM Summary Overview" in result
        assert "**Total Records:** 2" in result
        assert "### By Risk Level" in result
        assert "### By Building" in result

    def test_format_as_table_for_general(self):
        """Test formatting ACM records as table for general queries."""
        from api.utils.acm_context import format_acm_context_for_question

        records = [
            MagicMock(
                building_id="B001",
                building_name="Building A",
                room_id="R101",
                room_name="Room 101",
                product="Pipe Lagging",
                material_description="Test material",
                risk_status="High",
                result="Detected",
            ),
        ]

        result = format_acm_context_for_question(records, "general")

        assert "## ACM Register Data" in result
        assert "| Building | Room | Product | Material | Risk | Result |" in result
        assert "Building A" in result
        assert "Room 101" in result

    def test_format_empty_records(self):
        """Test formatting with no records."""
        from api.utils.acm_context import format_acm_context_for_question

        result = format_acm_context_for_question([], "risk_query")
        assert result == ""


class TestACMQuestionExamples:
    """Test suite for ACM question examples in prompt (E4-S4)."""

    def test_prompt_includes_common_question_types(self):
        """Test that the prompt includes common ACM question types."""
        from ai_prompter import Prompter

        prompt_data = {
            "source": {"id": "source:123", "title": "Test SAMP Document"},
            "insights": [],
            "context": "Test source content",
            "context_indicators": {
                "sources": ["source:123"],
                "insights": [],
                "notes": [],
                "acm_records_included": ["source:123"],
            },
        }

        system_prompt = Prompter(prompt_template="source_chat").render(data=prompt_data)

        # Verify common question type sections appear
        assert "Building/Room Location Queries" in system_prompt
        assert "Risk Summary Queries" in system_prompt
        assert "Terminology Queries" in system_prompt
        assert "Action/Compliance Queries" in system_prompt
        assert "Summary/Overview Queries" in system_prompt

    def test_prompt_includes_location_query_example(self):
        """Test that prompt includes location query example with table."""
        from ai_prompter import Prompter

        prompt_data = {
            "source": {"id": "source:123", "title": "Test SAMP"},
            "insights": [],
            "context": "Test content",
            "context_indicators": {
                "sources": ["source:123"],
                "insights": [],
                "notes": [],
                "acm_records_included": ["source:123"],
            },
        }

        system_prompt = Prompter(prompt_template="source_chat").render(data=prompt_data)

        # Verify location query example
        assert "Location Query Example" in system_prompt
        assert "What's in Building A1?" in system_prompt

    def test_prompt_includes_safety_query_example(self):
        """Test that prompt includes safety query example with recommendations."""
        from ai_prompter import Prompter

        prompt_data = {
            "source": {"id": "source:123", "title": "Test SAMP"},
            "insights": [],
            "context": "Test content",
            "context_indicators": {
                "sources": ["source:123"],
                "insights": [],
                "notes": [],
                "acm_records_included": ["source:123"],
            },
        }

        system_prompt = Prompter(prompt_template="source_chat").render(data=prompt_data)

        # Verify safety query example
        assert "Safety Query Example" in system_prompt
        assert "Is the school safe?" in system_prompt
        assert "licensed asbestos professional" in system_prompt

    def test_prompt_includes_terminology_query_example(self):
        """Test that prompt includes terminology query example."""
        from ai_prompter import Prompter

        prompt_data = {
            "source": {"id": "source:123", "title": "Test SAMP"},
            "insights": [],
            "context": "Test content",
            "context_indicators": {
                "sources": ["source:123"],
                "insights": [],
                "notes": [],
                "acm_records_included": ["source:123"],
            },
        }

        system_prompt = Prompter(prompt_template="source_chat").render(data=prompt_data)

        # Verify terminology query example
        assert "Terminology Query Example" in system_prompt
        assert "friable" in system_prompt.lower()

    def test_prompt_includes_action_query_example(self):
        """Test that prompt includes action query example with professional recommendation."""
        from ai_prompter import Prompter

        prompt_data = {
            "source": {"id": "source:123", "title": "Test SAMP"},
            "insights": [],
            "context": "Test content",
            "context_indicators": {
                "sources": ["source:123"],
                "insights": [],
                "notes": [],
                "acm_records_included": ["source:123"],
            },
        }

        system_prompt = Prompter(prompt_template="source_chat").render(data=prompt_data)

        # Verify action query example
        assert "Action Query Example" in system_prompt
        assert "licensed asbestos assessor" in system_prompt

    def test_prompt_recommends_professional_assessment(self):
        """Test that prompt recommends professional assessment for safety decisions."""
        from ai_prompter import Prompter

        prompt_data = {
            "source": {"id": "source:123", "title": "Test SAMP"},
            "insights": [],
            "context": "Test content",
            "context_indicators": {
                "sources": ["source:123"],
                "insights": [],
                "notes": [],
                "acm_records_included": ["source:123"],
            },
        }

        system_prompt = Prompter(prompt_template="source_chat").render(data=prompt_data)

        # Verify professional assessment recommendation appears
        assert "recommend consulting a licensed asbestos assessor" in system_prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
