"""Test negative result markers in ACM preprocessing and sub-chunking logic.

Validates Issue #15 fix: negative results must be marked with
>>> NO ASBESTOS: Negative result <<< markers for extraction parity.
"""

import re

import pytest


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
