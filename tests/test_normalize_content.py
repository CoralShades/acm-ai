"""Tests for Docling content normalization (E21-S4)."""

from open_notebook.extractors.normalizers.content import (
    normalize_docling_text,
    reconstruct_markdown_table_rows,
)


class TestNormalizeContent:
    """Unit tests for normalize_docling_text."""

    def test_normalize_content_fixes_split_values(self):
        """Split values should be re-joined for extraction prompts."""
        raw_text = (
            "Sample No: Same as\n"
            "34511-039001\n"
            "Hazard: Asbestos\n"
            "Assumed\n"
            "positive\n"
            "Result: Assumed\n"
            "positive\n"
            "Access: No\n"
            "access\n"
            "Status: N/A\n"
            "(negative)"
        )

        normalized = normalize_docling_text(raw_text)

        assert "Same as 34511-039001" in normalized
        assert "Asbestos Assumed positive" in normalized
        assert "Assumed positive" in normalized
        assert "No access" in normalized
        assert "N/A (negative)" in normalized

    def test_normalize_content_collapses_split_sample_number(self):
        """Multi-line sample numbers should be collapsed into one token."""
        raw_text = "34511\n-\n039\n-\n001"

        normalized = normalize_docling_text(raw_text)

        assert "34511-039-001" in normalized

    def test_normalize_content_collapses_sample_suffix_break(self):
        """Sample numbers split after suffix dash should be normalized."""
        raw_text = "Sample: 34511-039-\n001"

        normalized = normalize_docling_text(raw_text)

        assert "34511-039-001" in normalized

    def test_normalize_content_joins_split_room_names(self):
        """Known room-name line breaks should be normalized."""
        raw_text = "Front Desk\nArea\nMain\nFoyer\nSwitch\nRoom"

        normalized = normalize_docling_text(raw_text)

        assert "Front Desk Area" in normalized
        assert "Main Foyer" in normalized
        assert "Switch Room" in normalized

    def test_reconstruct_markdown_table_rows_merges_split_pairs(self):
        """Adjacent split markdown rows should be reconstructed into one row."""
        raw_text = (
            "| Room | Product | Result |\n"
            "| --- | --- | --- |\n"
            "| Front Desk | Filing cabinet | Assumed |\n"
            "| Area | Top panel | Positive |"
        )

        reconstructed = reconstruct_markdown_table_rows(raw_text)

        assert (
            "| Front Desk Area | Filing cabinet Top panel | Assumed Positive |"
            in reconstructed
        )

    def test_normalize_content_keeps_clean_text_unchanged(self):
        """Already clean text should be returned as-is."""
        raw_text = "Same as 34511-039001\nAssumed positive\nNo access\nN/A (negative)"

        assert normalize_docling_text(raw_text) == raw_text
