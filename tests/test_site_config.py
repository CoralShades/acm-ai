"""
Tests for Site Configuration Domain Model and API Endpoints.

Story: E1-S8 Site Configuration Data Entry
"""

import pytest
from unittest.mock import AsyncMock, patch

from open_notebook.domain.site_config import SiteConfig


class TestSiteConfigModel:
    """Tests for SiteConfig domain model."""

    def test_get_missing_bar_fields_all_empty(self):
        """Test that all fields are reported as missing when none are set."""
        config = SiteConfig(source_id="source:test")

        missing = config.get_missing_bar_fields()

        assert len(missing) == 6
        assert "department" in missing
        assert "agency" in missing
        assert "building_type" in missing
        assert "owned_or_leased" in missing
        assert "frequency_of_use" in missing
        assert "public_access" in missing

    def test_get_missing_bar_fields_partial(self):
        """Test that only unfilled fields are reported as missing."""
        config = SiteConfig(
            source_id="source:test",
            department="DJCS",
            agency="Victoria Police",
        )

        missing = config.get_missing_bar_fields()

        assert len(missing) == 4
        assert "department" not in missing
        assert "agency" not in missing
        assert "building_type" in missing

    def test_get_missing_bar_fields_all_filled(self):
        """Test that no fields are missing when all are filled."""
        config = SiteConfig(
            source_id="source:test",
            department="DJCS",
            agency="Victoria Police",
            building_type="Police Station",
            owned_or_leased="Owned",
            frequency_of_use="Every day",
            public_access="YES",
        )

        missing = config.get_missing_bar_fields()

        assert len(missing) == 0

    def test_is_bar_complete_false_when_missing(self):
        """Test is_bar_complete returns False when fields are missing."""
        config = SiteConfig(source_id="source:test")

        assert config.is_bar_complete() is False

    def test_is_bar_complete_true_when_all_filled(self):
        """Test is_bar_complete returns True when all fields are filled."""
        config = SiteConfig(
            source_id="source:test",
            department="DJCS",
            agency="Victoria Police",
            building_type="Police Station",
            owned_or_leased="Owned",
            frequency_of_use="Every day",
            public_access="YES",
        )

        assert config.is_bar_complete() is True

    def test_building_unique_id_not_required_for_bar_complete(self):
        """Test that building_unique_id is optional for BAR completeness."""
        config = SiteConfig(
            source_id="source:test",
            department="DJCS",
            agency="Victoria Police",
            building_type="Police Station",
            owned_or_leased="Owned",
            frequency_of_use="Every day",
            public_access="YES",
            # building_unique_id intentionally not set
        )

        assert config.is_bar_complete() is True
        assert "building_unique_id" not in config.get_missing_bar_fields()


class TestSiteConfigGetBySource:
    """Tests for SiteConfig.get_by_source method."""

    @pytest.mark.asyncio
    async def test_get_by_source_found(self):
        """Test retrieving existing config by source ID."""
        mock_result = [{
            "id": "site_config:123",
            "source_id": "source:test",
            "department": "DJCS",
            "agency": "Victoria Police",
        }]

        with patch("open_notebook.domain.site_config.repo_query", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = mock_result

            config = await SiteConfig.get_by_source("source:test")

            assert config is not None
            assert config.department == "DJCS"
            assert config.agency == "Victoria Police"

    @pytest.mark.asyncio
    async def test_get_by_source_not_found(self):
        """Test retrieving non-existent config returns None."""
        with patch("open_notebook.domain.site_config.repo_query", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = []

            config = await SiteConfig.get_by_source("source:nonexistent")

            assert config is None


class TestSiteConfigUpsert:
    """Tests for SiteConfig.upsert method."""

    @pytest.mark.asyncio
    async def test_upsert_creates_new_config(self):
        """Test upsert creates new config when none exists."""
        with patch.object(SiteConfig, "get_by_source", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None

            with patch.object(SiteConfig, "save", new_callable=AsyncMock) as mock_save:
                mock_save.return_value = None

                config = await SiteConfig.upsert(
                    source_id="source:new",
                    department="DJCS",
                )

                assert config.source_id == "source:new"
                assert config.department == "DJCS"
                mock_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_upsert_updates_existing_config(self):
        """Test upsert updates existing config."""
        existing = SiteConfig(
            source_id="source:existing",
            department="DJCS",
        )

        with patch.object(SiteConfig, "get_by_source", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = existing

            with patch.object(SiteConfig, "save", new_callable=AsyncMock) as mock_save:
                mock_save.return_value = None

                config = await SiteConfig.upsert(
                    source_id="source:existing",
                    agency="Victoria Police",
                )

                assert config.department == "DJCS"  # Preserved
                assert config.agency == "Victoria Police"  # Updated
                mock_save.assert_called_once()
