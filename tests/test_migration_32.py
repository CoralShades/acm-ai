"""Unit tests for Migration 32 — review_status field on Source.

These are pure unit tests that do not connect to a live database.
They verify:
  - Source domain model accepts review_status field
  - Default value is None for new Python objects
  - review_status is included in SourceResponse serialization
  - SourceUpdate can set review_status
  - SourceListResponse includes review_status
"""

import pytest
from pydantic import ValidationError

from api.models import SourceListResponse, SourceResponse, SourceUpdate
from open_notebook.domain.notebook import Source

# ---------------------------------------------------------------------------
# Source domain model tests
# ---------------------------------------------------------------------------


class TestSourceReviewStatus:
    """Tests for review_status field on the Source domain model."""

    def test_source_accepts_review_status(self):
        """Source model can be instantiated with review_status."""
        source = Source(review_status="pending_review")
        assert source.review_status == "pending_review"

    def test_source_review_status_defaults_to_none(self):
        """review_status defaults to None when not provided."""
        source = Source()
        assert source.review_status is None

    def test_source_review_status_all_valid_values(self):
        """Each allowed status value is accepted without error."""
        allowed_values = [
            "extracting",
            "pending_review",
            "building_review",
            "acm_review",
            "published",
        ]
        for value in allowed_values:
            source = Source(review_status=value)
            assert source.review_status == value

    def test_source_review_status_can_be_none(self):
        """review_status accepts None explicitly."""
        source = Source(review_status=None)
        assert source.review_status is None

    def test_source_serializes_review_status(self):
        """model_dump includes review_status."""
        source = Source(review_status="acm_review")
        data = source.model_dump()
        assert "review_status" in data
        assert data["review_status"] == "acm_review"

    def test_source_serializes_none_review_status(self):
        """model_dump includes review_status as None when not set."""
        source = Source()
        data = source.model_dump()
        assert "review_status" in data
        assert data["review_status"] is None


# ---------------------------------------------------------------------------
# SourceUpdate API model tests
# ---------------------------------------------------------------------------


class TestSourceUpdateReviewStatus:
    """Tests for review_status field on the SourceUpdate API model."""

    def test_source_update_accepts_review_status(self):
        """SourceUpdate can be constructed with review_status."""
        update = SourceUpdate(review_status="building_review")
        assert update.review_status == "building_review"

    def test_source_update_review_status_defaults_to_none(self):
        """review_status is None by default on SourceUpdate."""
        update = SourceUpdate()
        assert update.review_status is None

    def test_source_update_review_status_none_explicit(self):
        """SourceUpdate accepts None for review_status."""
        update = SourceUpdate(review_status=None)
        assert update.review_status is None

    def test_source_update_partial_update_no_review_status(self):
        """SourceUpdate with only title leaves review_status as None."""
        update = SourceUpdate(title="New Title")
        assert update.review_status is None
        assert update.title == "New Title"

    def test_source_update_all_fields(self):
        """SourceUpdate accepts all three fields simultaneously."""
        update = SourceUpdate(
            title="My Source",
            topics=["asbestos", "samp"],
            review_status="published",
        )
        assert update.title == "My Source"
        assert update.topics == ["asbestos", "samp"]
        assert update.review_status == "published"


# ---------------------------------------------------------------------------
# SourceResponse API model tests
# ---------------------------------------------------------------------------


class TestSourceResponseReviewStatus:
    """Tests for review_status field on the SourceResponse API model."""

    def _make_response(self, review_status=None) -> SourceResponse:
        """Helper: build a minimal valid SourceResponse."""
        return SourceResponse(
            id="source:abc123",
            title="Test Source",
            topics=[],
            asset=None,
            full_text=None,
            embedded=False,
            embedded_chunks=0,
            created="2026-01-01T00:00:00",
            updated="2026-01-01T00:00:00",
            review_status=review_status,
        )

    def test_source_response_includes_review_status(self):
        """SourceResponse serializes review_status correctly."""
        response = self._make_response(review_status="pending_review")
        data = response.model_dump()
        assert "review_status" in data
        assert data["review_status"] == "pending_review"

    def test_source_response_review_status_defaults_to_none(self):
        """review_status is None when not passed to SourceResponse."""
        response = self._make_response()
        assert response.review_status is None

    def test_source_response_review_status_none_in_serialization(self):
        """review_status key is present even when None."""
        response = self._make_response()
        data = response.model_dump()
        assert "review_status" in data
        assert data["review_status"] is None


# ---------------------------------------------------------------------------
# SourceListResponse API model tests
# ---------------------------------------------------------------------------


class TestSourceListResponseReviewStatus:
    """Tests for review_status field on the SourceListResponse API model."""

    def _make_list_response(self, review_status=None) -> SourceListResponse:
        """Helper: build a minimal valid SourceListResponse."""
        return SourceListResponse(
            id="source:xyz789",
            title="List Source",
            topics=[],
            asset=None,
            embedded=True,
            embedded_chunks=5,
            insights_count=2,
            created="2026-01-01T00:00:00",
            updated="2026-01-01T00:00:00",
            review_status=review_status,
        )

    def test_source_list_response_includes_review_status(self):
        """SourceListResponse serializes review_status correctly."""
        response = self._make_list_response(review_status="acm_review")
        data = response.model_dump()
        assert "review_status" in data
        assert data["review_status"] == "acm_review"

    def test_source_list_response_review_status_defaults_to_none(self):
        """review_status is None by default on SourceListResponse."""
        response = self._make_list_response()
        assert response.review_status is None
