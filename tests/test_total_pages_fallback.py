"""Tests for _extract_total_pages page count extraction (F3)."""

from open_notebook.extractors.document_structure import _extract_total_pages


def test_extract_total_pages_with_markers():
    content = "--- Page 1 ---\nfoo\n--- Page 5 ---\nbar\n--- Page 10 ---\nbaz"
    assert _extract_total_pages(content) == 10


def test_extract_total_pages_no_markers():
    content = "Some text without any page markers at all"
    assert _extract_total_pages(content) == 0


def test_extract_total_pages_html_markers():
    content = "<!-- Page 1 -->\nfoo\n<!-- Page 3 -->\nbar"
    assert _extract_total_pages(content) == 3


def test_extract_total_pages_empty_string():
    assert _extract_total_pages("") == 0
