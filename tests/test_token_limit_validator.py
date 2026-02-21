"""Tests for TokenLimitValidator (E1-S23)."""

from open_notebook.extractors.token_limit_validator import TokenLimitValidator


class TestTokenLimitValidator:
    def setup_method(self):
        self.validator = TokenLimitValidator(
            model_id="test-model",
            context_window=128000,
            safety_margin=0.8,
        )

    def test_estimate_tokens(self):
        # 3 chars per token for table data
        content = "a" * 3000
        assert self.validator.estimate_tokens(content) == 1000

    def test_needs_chunking_small_content(self):
        content = "Small table content"
        assert not self.validator.needs_chunking(content)

    def test_needs_chunking_large_content(self):
        # 128000 * 0.8 = 102400 safe tokens, minus 4000 overhead = 98400
        # At 3 chars/token, need 98400 * 3 = 295200 chars to exceed
        content = "x" * 300000
        assert self.validator.needs_chunking(content)

    def test_check_response_truncation_normal(self):
        assert not self.validator.check_response_truncation('{"records": []}')
        assert not self.validator.check_response_truncation("[1, 2, 3]")

    def test_check_response_truncation_truncated(self):
        assert self.validator.check_response_truncation('{"records": [')
        assert self.validator.check_response_truncation("")

    def test_assess_extraction_no_issues(self):
        result = self.validator.assess_extraction(
            content="Small content",
            chunks_used=1,
            records_extracted=5,
        )
        assert result["token_limit_exceeded"] is False
        assert result["chunk_count"] == 1
        assert result["warnings"] == []

    def test_assess_extraction_large_input(self):
        large_content = "x" * 400000  # Way over budget
        result = self.validator.assess_extraction(
            content=large_content,
            chunks_used=4,
            records_extracted=20,
        )
        assert result["token_limit_exceeded"] is True
        assert result["chunk_count"] == 4
        assert len(result["warnings"]) > 0

    def test_assess_extraction_truncated_response(self):
        result = self.validator.assess_extraction(
            content="Some content",
            chunks_used=1,
            records_extracted=0,
            response_text='{"records": [',
        )
        assert result["token_limit_exceeded"] is True

    def test_small_context_window(self):
        small_validator = TokenLimitValidator(
            model_id="haiku",
            context_window=8000,
            safety_margin=0.8,
        )
        # 8000 * 0.8 = 6400 safe tokens, minus 4000 overhead = 2400
        # At 3 chars/token = 7200 chars to exceed
        content = "x" * 8000
        assert small_validator.needs_chunking(content)
