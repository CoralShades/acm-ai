"""Tests for room ID generation (MCS11).

Verifies that _assign_room_ids assigns sequential R001, R002, ...
codes per-building, resets across buildings, and handles None room_name.
"""

from unittest.mock import MagicMock

import pytest

from open_notebook.graphs.acm_extraction import _assign_room_ids


def _make_record(room_name=None, room_id=None):
    """Create a mock ACMExtractionRecord with room_name and room_id attrs."""
    rec = MagicMock()
    rec.room_name = room_name
    rec.room_id = room_id
    return rec


class TestAssignRoomIds:
    """MCS11: Room ID generation tests."""

    def test_sequential_room_ids(self):
        records = [
            _make_record(room_name="Bedroom 1"),
            _make_record(room_name="Bedroom 2"),
            _make_record(room_name="Kitchen"),
        ]
        _assign_room_ids(records)
        assert records[0].room_id == "R001"
        assert records[1].room_id == "R002"
        assert records[2].room_id == "R003"

    def test_same_room_name_gets_same_id(self):
        records = [
            _make_record(room_name="Office"),
            _make_record(room_name="Hallway"),
            _make_record(room_name="Office"),  # repeat
            _make_record(room_name="Hallway"),  # repeat
        ]
        _assign_room_ids(records)
        assert records[0].room_id == "R001"
        assert records[1].room_id == "R002"
        assert records[2].room_id == "R001"  # same as first Office
        assert records[3].room_id == "R002"  # same as first Hallway

    def test_none_room_name_gets_none_id(self):
        records = [
            _make_record(room_name="Office"),
            _make_record(room_name=None),
            _make_record(room_name="Lab"),
        ]
        _assign_room_ids(records)
        assert records[0].room_id == "R001"
        assert records[1].room_id is None  # unchanged from default
        assert records[2].room_id == "R002"

    def test_empty_room_name_gets_none_id(self):
        records = [
            _make_record(room_name=""),
            _make_record(room_name="Office"),
        ]
        _assign_room_ids(records)
        # Empty string is falsy, so no room_id assigned
        assert records[0].room_id is None
        assert records[1].room_id == "R001"

    def test_per_building_scope_reset(self):
        """Room codes reset when called separately per building."""
        building_a_records = [
            _make_record(room_name="Room A1"),
            _make_record(room_name="Room A2"),
        ]
        building_b_records = [
            _make_record(room_name="Room B1"),
            _make_record(room_name="Room B2"),
            _make_record(room_name="Room B3"),
        ]
        _assign_room_ids(building_a_records)
        _assign_room_ids(building_b_records)

        # Building A: R001, R002
        assert building_a_records[0].room_id == "R001"
        assert building_a_records[1].room_id == "R002"
        # Building B: R001, R002, R003 (reset!)
        assert building_b_records[0].room_id == "R001"
        assert building_b_records[1].room_id == "R002"
        assert building_b_records[2].room_id == "R003"

    def test_empty_records_list(self):
        records = []
        _assign_room_ids(records)  # should not raise
        assert records == []

    def test_all_none_room_names(self):
        records = [
            _make_record(room_name=None),
            _make_record(room_name=None),
        ]
        _assign_room_ids(records)
        assert records[0].room_id is None
        assert records[1].room_id is None
