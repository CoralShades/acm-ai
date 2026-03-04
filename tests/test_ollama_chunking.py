"""Tests for Ollama token-budget content chunking (E32-S8).

Verifies that _ollama_split_by_budget and _split_content_by_char_budget
correctly split large building content into budget-sized chunks instead
of silently hard-truncating, which would drop ACM records.
"""

from unittest.mock import patch

import pytest

from open_notebook.graphs.utils import (
    _ollama_split_by_budget,
    _split_content_by_char_budget,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_openai_model(num_ctx: int = 8192):
    """Create a real ChatOpenAI-like instance — no 'ollama' in MRO."""

    class ChatOpenAI:
        pass

    inst = ChatOpenAI()
    inst.num_ctx = num_ctx
    inst.model_kwargs = {}
    return inst


def _make_ollama_model(num_ctx: int = 8192):
    """Create a real ChatOllama-like instance — 'ollama' in MRO class name."""

    class ChatOllama:
        pass

    inst = ChatOllama()
    inst.num_ctx = num_ctx
    inst.model_kwargs = {}
    return inst


# ---------------------------------------------------------------------------
# _split_content_by_char_budget
# ---------------------------------------------------------------------------


def test_split_no_boundaries_within_budget():
    content = "Small content with no room headers"
    chunks = _split_content_by_char_budget(content, max_chars=1000)
    assert chunks == [content]


def test_split_no_boundaries_over_budget():
    content = "A" * 200
    with patch("open_notebook.graphs.utils.logger") as mock_log:
        chunks = _split_content_by_char_budget(content, max_chars=100)
    assert len(chunks) == 1
    assert len(chunks[0]) == 100
    mock_log.warning.assert_called_once()


def test_split_two_rooms_each_fits_separately():
    room1 = "B001-R0001 Room One\n" + "x" * 50
    room2 = "B001-R0002 Room Two\n" + "y" * 50
    content = room1 + room2
    # max_chars forces one room per chunk
    chunks = _split_content_by_char_budget(content, max_chars=80)
    assert len(chunks) == 2
    assert "B001-R0001" in chunks[0]
    assert "B001-R0002" in chunks[1]


def test_split_two_rooms_fit_in_one_chunk():
    room1 = "B001-R0001 Room One\n" + "x" * 30
    room2 = "B001-R0002 Room Two\n" + "y" * 30
    content = room1 + room2
    chunks = _split_content_by_char_budget(content, max_chars=5000)
    assert len(chunks) == 1
    assert chunks[0] == content


def test_split_oversized_single_room_truncated_with_warning():
    # One room that alone exceeds the budget
    big_room = "B001-R0001 Big Room\n" + "z" * 500
    content = big_room
    with patch("open_notebook.graphs.utils.logger") as mock_log:
        chunks = _split_content_by_char_budget(content, max_chars=100)
    assert len(chunks) == 1
    assert len(chunks[0]) == 100
    mock_log.warning.assert_called()


def test_split_ara_format_items():
    # ARA pattern requires \n before item number (except at start of string)
    item1 = "1. Office corridor\n" + "a" * 50
    item2 = "\n2. Boiler room\n" + "b" * 50  # \n before "2." triggers the ARA pattern
    content = item1 + item2  # ~134 chars, budget of 80 forces a split
    chunks = _split_content_by_char_budget(content, max_chars=80)
    assert len(chunks) == 2
    assert "1." in chunks[0]
    assert "2." in chunks[1]


def test_split_preamble_included_in_first_chunk():
    preamble = "Building header information\n"
    room1 = "B001-R0001 Room One\n" + "x" * 20
    room2 = "B001-R0002 Room Two\n" + "y" * 20
    content = preamble + room1 + room2
    # Budget large enough for preamble + room1 but not all three together
    chunks = _split_content_by_char_budget(
        content, max_chars=len(preamble) + len(room1) + 5
    )
    assert chunks[0].startswith(preamble)
    assert "B001-R0001" in chunks[0]


# ---------------------------------------------------------------------------
# _ollama_split_by_budget
# ---------------------------------------------------------------------------


def test_non_ollama_model_returns_unchanged():
    model = _make_openai_model()
    content = "A" * 10000
    result = _ollama_split_by_budget(content, model)
    assert result == [content]


def test_ollama_content_within_budget_returns_single_chunk():
    model = _make_ollama_model(num_ctx=8192)
    # 8192 * 3.5 = 28672 max_chars; content is well within
    content = "B001-R0001 Room\n" + "x" * 100
    result = _ollama_split_by_budget(content, model)
    assert result == [content]


def test_ollama_content_split_across_two_budget_chunks():
    model = _make_ollama_model(num_ctx=100)  # 100 * 3.5 = 350 max_chars
    room1 = "B001-R0001 Room One\n" + "x" * 200  # ~220 chars
    room2 = "B001-R0002 Room Two\n" + "y" * 200  # ~220 chars
    content = room1 + room2  # ~440 chars > 350
    result = _ollama_split_by_budget(content, model)
    assert len(result) == 2
    assert "B001-R0001" in result[0]
    assert "B001-R0002" in result[1]


def test_num_ctx_controls_budget():
    """model.num_ctx=4096 → max_chars = 4096 * 3.5 = 14336."""
    model = _make_ollama_model(num_ctx=4096)
    # Content that fits within 14336 chars should be single chunk
    content = "B001-R0001 Room\n" + "x" * 100
    result = _ollama_split_by_budget(content, model)
    assert len(result) == 1


def test_env_override_takes_priority(monkeypatch):
    """OLLAMA_MAX_CONTENT_CHARS=200 overrides num_ctx."""
    monkeypatch.setenv("OLLAMA_MAX_CONTENT_CHARS", "200")
    model = _make_ollama_model(num_ctx=100000)  # huge num_ctx, should be ignored
    room1 = "B001-R0001 Room One\n" + "x" * 120  # ~140 chars
    room2 = "B001-R0002 Room Two\n" + "y" * 120  # ~140 chars
    content = room1 + room2  # ~280 chars > 200
    result = _ollama_split_by_budget(content, model)
    assert len(result) == 2


def test_env_override_small_fits_all(monkeypatch):
    """OLLAMA_MAX_CONTENT_CHARS=5000 — content within 5000 chars → single chunk."""
    monkeypatch.setenv("OLLAMA_MAX_CONTENT_CHARS", "5000")
    model = _make_ollama_model(num_ctx=10)  # tiny num_ctx, should be ignored
    content = "B001-R0001 Room\n" + "x" * 50
    result = _ollama_split_by_budget(content, model)
    assert len(result) == 1
    assert result[0] == content
