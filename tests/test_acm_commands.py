"""
Unit tests for ACM extraction commands.

Tests the background command for ACM extraction.
"""

import pytest

from commands.acm_commands import ACMExtractionInput, ACMExtractionOutput


class TestACMExtractionInput:
    """Test suite for ACMExtractionInput model."""

    def test_input_requires_source_id(self):
        """Test that source_id is required."""
        input_data = ACMExtractionInput(source_id="source:123")
        assert input_data.source_id == "source:123"

    def test_input_inherits_from_command_input(self):
        """Test that input inherits from CommandInput."""
        from surreal_commands import CommandInput

        assert issubclass(ACMExtractionInput, CommandInput)


class TestACMExtractionOutput:
    """Test suite for ACMExtractionOutput model."""

    def test_output_default_values(self):
        """Test output has correct default values."""
        output = ACMExtractionOutput(
            success=True,
            source_id="source:123",
        )
        assert output.success is True
        assert output.source_id == "source:123"
        assert output.records_created == 0
        assert output.records_deleted == 0
        assert output.processing_time == 0.0
        assert output.error_message is None

    def test_output_with_all_fields(self):
        """Test output with all fields populated."""
        output = ACMExtractionOutput(
            success=True,
            source_id="source:123",
            records_created=15,
            records_deleted=5,
            processing_time=2.5,
            error_message=None,
        )
        assert output.records_created == 15
        assert output.records_deleted == 5
        assert output.processing_time == 2.5

    def test_output_failure_with_error(self):
        """Test output for failed extraction."""
        output = ACMExtractionOutput(
            success=False,
            source_id="source:123",
            error_message="Source not found",
        )
        assert output.success is False
        assert output.error_message == "Source not found"

    def test_output_inherits_from_command_output(self):
        """Test that output inherits from CommandOutput."""
        from surreal_commands import CommandOutput

        assert issubclass(ACMExtractionOutput, CommandOutput)


class TestCommandRegistration:
    """Test suite for command registration."""

    def test_acm_extract_command_exists(self):
        """Test that acm_extract command function exists."""
        from commands.acm_commands import acm_extract_command

        assert callable(acm_extract_command)

    def test_command_is_async(self):
        """Test that command is async."""
        import asyncio

        from commands.acm_commands import acm_extract_command

        assert asyncio.iscoroutinefunction(acm_extract_command)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
