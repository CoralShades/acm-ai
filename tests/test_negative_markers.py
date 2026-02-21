"""Test negative result markers in ACM preprocessing and sub-chunking logic.

Validates Issue #15 fix: negative results must be marked with
>>> NO ASBESTOS: Negative result <<< markers for extraction parity.
"""

import re

import pytest


class TestNegativeMarkerPreprocessing:
    """Test _preprocess_acm_content adds negative markers."""

    @pytest.fixture
    def preprocess(self):
        from open_notebook.graphs.acm_extraction import _preprocess_acm_content

        return _preprocess_acm_content

    def test_no_asbestos_gets_marker(self, preprocess):
        content = (
            "B009 - R0012 - Male Locker Room - 12.30 m2\n"
            "Floor Coverings\nVinyl Tiles\n10m2\nThroughout\nNo Asbestos\n"
        )
        processed, meta = preprocess(content)
        assert ">>> NO ASBESTOS: Negative result <<<" in processed

    def test_not_detected_gets_marker(self, preprocess):
        content = (
            "B009 - R0015 - Kitchen - 8.50 m2\n"
            "Wall Linings\nFibre Cement\n5m2\nThroughout\nNot Detected\n"
        )
        processed, meta = preprocess(content)
        assert ">>> NO ASBESTOS: Negative result <<<" in processed

    def test_newline_split_no_asbestos(self, preprocess):
        content = (
            "B009 - R0020 - Corridor - 5.00 m2\n"
            "Floor Coverings\nVinyl\nNo Asbestos\nDetected\n"
        )
        processed, meta = preprocess(content)
        assert ">>> NO ASBESTOS: Negative result <<<" in processed

    def test_acm_marker_still_works(self, preprocess):
        content = (
            "B009 - R0005 - General Storeroom - 1.45 m2\n"
            "Floor Coverings\nVinyl Tiles\n2m2\nAsbestos-containing material\n"
        )
        processed, meta = preprocess(content)
        assert ">>> ACM DETECTED: Asbestos-containing material <<<" in processed

    def test_both_markers_in_same_content(self, preprocess):
        content = (
            "B009 - R0005 - Storeroom - 1.45 m2\n"
            "Floor Coverings\nVinyl Tiles\nAsbestos-containing material\n\n"
            "B009 - R0012 - Locker Room - 12.30 m2\n"
            "Floor Coverings\nVinyl Tiles\nNo Asbestos\n"
        )
        processed, meta = preprocess(content)
        assert ">>> ACM DETECTED:" in processed
        assert ">>> NO ASBESTOS:" in processed

    def test_no_double_negative_markers(self, preprocess):
        content = "No Asbestos No Asbestos\n"
        processed, meta = preprocess(content)
        # Should not have double markers adjacent
        assert ">>> NO ASBESTOS: Negative result <<< >>> NO ASBESTOS:" not in processed


class TestSubChunking:
    """Test room-count-based sub-chunking in orchestrator."""

    @pytest.fixture
    def split_fn(self):
        from open_notebook.extractors.orchestrator import _split_building_by_rooms

        return _split_building_by_rooms

    def test_small_building_no_split(self, split_fn):
        content = "\n".join(
            f"B009 - R{str(i).zfill(4)} - Room {i} - {i}.0 m2\nFloor\nVinyl\nNo Asbestos\n"
            for i in range(5)
        )
        chunks = split_fn(content, max_rooms=12)
        assert len(chunks) == 1

    def test_large_building_splits(self, split_fn):
        content = "\n".join(
            f"B009 - R{str(i).zfill(4)} - Room {i} - {i}.0 m2\nFloor\nVinyl\nNo Asbestos\n"
            for i in range(25)
        )
        chunks = split_fn(content, max_rooms=12)
        assert len(chunks) >= 2

    def test_split_preserves_all_rooms(self, split_fn):
        rooms = 20
        content = "\n".join(
            f"B009 - R{str(i).zfill(4)} - Room {i} - {i}.0 m2\nFloor\nVinyl\nNo Asbestos\n"
            for i in range(rooms)
        )
        chunks = split_fn(content, max_rooms=12)
        # Count total rooms across all chunks
        room_pattern = re.compile(r"B\d{3}\s*-\s*R\d{4,5}")
        total_rooms = sum(len(room_pattern.findall(c)) for c in chunks)
        assert total_rooms == rooms


class TestCompletenessCheck:
    """Test extraction completeness diagnostic."""

    def test_room_pattern_counting(self):
        """Verify the room counting regex matches expected patterns."""
        room_pattern = re.compile(r"B\d{3}\s*-\s*R\d{4,5}")
        content = (
            "B009 - R0005 - General Storeroom\n"
            "B009 - R0012 - Male Locker Room\n"
            "B009 - R0015 - Kitchen\n"
            "B010 - R0001 - Main Hall\n"
        )
        matches = set(room_pattern.findall(content))
        assert len(matches) == 4
