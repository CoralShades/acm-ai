"""
Tests for V3 Data Migration Script (E30-S5).

Covers all acceptance criteria:
- AC1: Migration extracts building-level fields from acm_record into building_record
- AC2: Groups by building_id, one building_record per unique building
- AC3: building_record_id FK populated on acm_records
- AC4: Legacy building_id preserved
- AC5: "Good" -> "Stable" vocabulary migration
- AC6: Rollback script
- AC7: Dry-run mode
- AC8: Broadmeadows and Alexander benchmark scenarios
- AC9: Idempotent re-run

All tests mock the DB layer; no live database is required.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from scripts.v3_data_migration import (
    _extract_building_fields,
    _find_existing_building,
    _group_records_by_building,
    migrate_all,
    migrate_source,
    migrate_vocabulary,
    verify_schema,
)
from scripts.v3_data_migration_rollback import rollback_all, rollback_source

# ---------------------------------------------------------------------------
# Helper factories
# ---------------------------------------------------------------------------


def _make_acm_raw(
    *,
    source_id: str = "source:src001",
    building_id: str = "B01",
    building_name: str = "Main Building",
    building_year: int | None = 1970,
    building_construction: str | None = "Brick",
    building_address: str | None = "1 School St",
    suburb: str | None = "Broadmeadows",
    postcode: str | None = "3047",
    building_type: str | None = "Permanent",
    material_condition: str | None = "Good",
    building_record_id: str | None = None,
    record_id: str = "acm_record:rec001",
) -> dict:
    """Return a raw acm_record dict as returned by repo_query."""
    return {
        "id": record_id,
        "source_id": source_id,
        "building_id": building_id,
        "building_name": building_name,
        "building_year": building_year,
        "building_construction": building_construction,
        "building_address": building_address,
        "suburb": suburb,
        "postcode": postcode,
        "building_type": building_type,
        "material_condition": material_condition,
        "building_record_id": building_record_id,
        "product": "Ceiling Tiles",
        "material_description": "Asbestos ceiling tiles",
        "result": "Detected",
        "room_id": "R01",
        "room_name": "Room 1",
    }


def _make_building_raw(
    *,
    record_id: str = "building_record:bld001",
    source_id: str = "source:src001",
    building_code: str = "B01",
    internal_id: str = "BLD#MAINBUIL_001",
) -> dict:
    """Return a minimal raw building_record dict."""
    return {
        "id": record_id,
        "source_id": source_id,
        "building_code": building_code,
        "internal_id": internal_id,
        "building_name": "Main Building",
    }


# ---------------------------------------------------------------------------
# AC2: Grouping by building_id
# ---------------------------------------------------------------------------


class TestGroupRecordsByBuilding:
    """Unit tests for the _group_records_by_building helper."""

    def test_single_building_single_record(self):
        """One record in one group."""
        records = [_make_acm_raw(building_id="B01")]
        groups = _group_records_by_building(records)
        assert len(groups) == 1
        key = ("source:src001", "B01")
        assert key in groups
        assert len(groups[key]) == 1

    def test_two_buildings_five_records(self):
        """AC2: Five records with 2 distinct building_ids produce 2 groups."""
        records = [
            _make_acm_raw(building_id="B01", record_id="acm_record:r1"),
            _make_acm_raw(building_id="B01", record_id="acm_record:r2"),
            _make_acm_raw(building_id="B01", record_id="acm_record:r3"),
            _make_acm_raw(building_id="B02", record_id="acm_record:r4"),
            _make_acm_raw(building_id="B02", record_id="acm_record:r5"),
        ]
        groups = _group_records_by_building(records)
        assert len(groups) == 2
        assert len(groups[("source:src001", "B01")]) == 3
        assert len(groups[("source:src001", "B02")]) == 2

    def test_different_sources_separate_groups(self):
        """Records from different sources are grouped independently."""
        records = [
            _make_acm_raw(
                source_id="source:s1", building_id="B01", record_id="acm_record:r1"
            ),
            _make_acm_raw(
                source_id="source:s2", building_id="B01", record_id="acm_record:r2"
            ),
        ]
        groups = _group_records_by_building(records)
        assert len(groups) == 2
        assert ("source:s1", "B01") in groups
        assert ("source:s2", "B01") in groups

    def test_empty_records_returns_empty(self):
        """Empty input returns empty dict."""
        assert _group_records_by_building([]) == {}

    def test_broadmeadows_31_records_one_building(self):
        """AC8: 31 Broadmeadows records all sharing building_id produce 1 group."""
        records = [
            _make_acm_raw(
                building_id="BLK-A",
                source_id="source:broadmeadows",
                record_id=f"acm_record:r{i}",
            )
            for i in range(31)
        ]
        groups = _group_records_by_building(records)
        assert len(groups) == 1
        assert len(groups[("source:broadmeadows", "BLK-A")]) == 31

    def test_alexander_43_records_five_buildings(self):
        """AC8: 43 Alexander records across 5 buildings produce 5 groups."""
        building_sizes = [9, 9, 9, 8, 8]  # sum = 43
        records = []
        for bld_idx, size in enumerate(building_sizes):
            for i in range(size):
                records.append(
                    _make_acm_raw(
                        building_id=f"BLK-{bld_idx}",
                        source_id="source:alexander",
                        record_id=f"acm_record:r{bld_idx}_{i}",
                    )
                )
        groups = _group_records_by_building(records)
        assert len(groups) == 5
        assert sum(len(v) for v in groups.values()) == 43


# ---------------------------------------------------------------------------
# AC1: Building field extraction
# ---------------------------------------------------------------------------


class TestExtractBuildingFields:
    """Unit tests for _extract_building_fields helper."""

    def test_direct_copy_fields(self):
        """AC1: building_name, construction, address, suburb, postcode, type copied."""
        rec = _make_acm_raw(
            building_name="Science Wing",
            building_construction="Steel Frame",
            building_address="42 Smith St",
            suburb="Kew",
            postcode="3101",
            building_type="Demountable",
        )
        fields = _extract_building_fields(rec)
        assert fields["building_name"] == "Science Wing"
        assert fields["building_construction"] == "Steel Frame"
        assert fields["building_address"] == "42 Smith St"
        assert fields["suburb"] == "Kew"
        assert fields["postcode"] == "3101"
        assert fields["building_type"] == "Demountable"

    def test_building_code_from_building_id(self):
        """building_code on BuildingRecord is populated from building_id on ACMRecord."""
        rec = _make_acm_raw(building_id="BLK-99")
        fields = _extract_building_fields(rec)
        assert fields["building_code"] == "BLK-99"

    def test_building_year_int_to_str_cast(self):
        """AC1: building_year int -> str conversion (SF picklist type)."""
        rec = _make_acm_raw(building_year=1975)
        fields = _extract_building_fields(rec)
        assert fields["building_year"] == "1975"
        assert isinstance(fields["building_year"], str)

    def test_building_year_none_stays_none(self):
        """building_year=None produces None (not 'None' string)."""
        rec = _make_acm_raw(building_year=None)
        fields = _extract_building_fields(rec)
        assert fields["building_year"] is None

    def test_source_id_included(self):
        """source_id is included in extracted fields."""
        rec = _make_acm_raw(source_id="source:mysrc")
        fields = _extract_building_fields(rec)
        assert fields["source_id"] == "source:mysrc"

    def test_none_fields_are_none(self):
        """Fields absent from the raw record produce None values."""
        rec = _make_acm_raw(
            building_name=None,
            building_construction=None,
            suburb=None,
        )
        fields = _extract_building_fields(rec)
        assert fields["building_name"] is None
        assert fields["building_construction"] is None
        assert fields["suburb"] is None


# ---------------------------------------------------------------------------
# AC5: Vocabulary migration
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestVocabularyMigration:
    """Tests for migrate_vocabulary function."""

    @patch("scripts.v3_data_migration.repo_query", new_callable=AsyncMock)
    async def test_good_to_stable(self, mock_query):
        """AC5: Records with 'Good' are counted and updated to 'Stable'."""
        # First call: count query returns 5 records
        # Second call: UPDATE call (no meaningful return needed)
        mock_query.side_effect = [
            [{"total": 5}],
            [],
        ]
        count = await migrate_vocabulary(dry_run=False)
        assert count == 5
        # Verify the UPDATE was called
        assert mock_query.call_count == 2
        update_call_sql = mock_query.call_args_list[1][0][0]
        assert "Stable" in update_call_sql
        assert "Good" in update_call_sql

    @patch("scripts.v3_data_migration.repo_query", new_callable=AsyncMock)
    async def test_no_good_values_returns_zero(self, mock_query):
        """Already-migrated DB (no 'Good' values) returns 0 without writing."""
        mock_query.return_value = [{"total": 0}]
        count = await migrate_vocabulary(dry_run=False)
        assert count == 0
        # Only the count query ran, no UPDATE
        assert mock_query.call_count == 1

    @patch("scripts.v3_data_migration.repo_query", new_callable=AsyncMock)
    async def test_dry_run_counts_but_no_update(self, mock_query):
        """AC7: dry_run=True returns count but does not call UPDATE."""
        mock_query.return_value = [{"total": 12}]
        count = await migrate_vocabulary(dry_run=True)
        assert count == 12
        # Only the count query, no UPDATE
        assert mock_query.call_count == 1

    @patch("scripts.v3_data_migration.repo_query", new_callable=AsyncMock)
    async def test_empty_count_result_treated_as_zero(self, mock_query):
        """Empty count result treated as zero (no records to update)."""
        mock_query.return_value = []
        count = await migrate_vocabulary(dry_run=False)
        assert count == 0


# ---------------------------------------------------------------------------
# AC3, AC9: migrate_source — FK linkage and idempotency
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestMigrateSource:
    """Tests for migrate_source function with mocked DB."""

    @patch("scripts.v3_data_migration.repo_query", new_callable=AsyncMock)
    @patch("scripts.v3_data_migration.BuildingRecord", autospec=True)
    async def test_creates_building_record_and_links_acm(self, mock_br_cls, mock_query):
        """AC3: One building_record created, building_record_id set on acm_records."""
        raw_records = [
            _make_acm_raw(record_id="acm_record:r1"),
            _make_acm_raw(record_id="acm_record:r2"),
        ]

        # Call sequence for migrate_source("source:src001"):
        # 1. SELECT * FROM acm_record ... (fetch records)
        # 2. SELECT id FROM building_record ... (idempotency check) -> none found
        # 3. UPDATE acm_record for r1
        # 4. UPDATE acm_record for r2
        mock_query.side_effect = [
            raw_records,  # fetch records
            [],  # idempotency check -> no existing building
            [],  # UPDATE r1
            [],  # UPDATE r2
        ]

        # Mock BuildingRecord.generate_internal_id and instance
        mock_br_cls.generate_internal_id = AsyncMock(return_value="BLD#SRC001__001")
        mock_building_instance = MagicMock()
        mock_building_instance.id = "building_record:bld001"
        mock_building_instance.save = AsyncMock()
        mock_br_cls.return_value = mock_building_instance

        summary = await migrate_source("source:src001")

        assert summary["buildings_created"] == 1
        assert summary["buildings_skipped"] == 0
        assert summary["records_linked"] == 2
        assert summary["records_already_linked"] == 0

    @patch("scripts.v3_data_migration.repo_query", new_callable=AsyncMock)
    @patch("scripts.v3_data_migration.BuildingRecord", autospec=True)
    async def test_idempotent_skips_existing_building(self, mock_br_cls, mock_query):
        """AC9: If building_record already exists, skip creation."""
        raw_records = [
            _make_acm_raw(record_id="acm_record:r1"),
        ]
        mock_query.side_effect = [
            raw_records,  # fetch records
            [{"id": "building_record:bld_existing"}],  # idempotency check -> found!
            [],  # UPDATE r1 (FK still set)
        ]

        summary = await migrate_source("source:src001")

        # Building should be skipped (already exists), but FK still gets set
        assert summary["buildings_created"] == 0
        assert summary["buildings_skipped"] == 1
        assert summary["records_linked"] == 1

    @patch("scripts.v3_data_migration.repo_query", new_callable=AsyncMock)
    @patch("scripts.v3_data_migration.BuildingRecord", autospec=True)
    async def test_idempotent_skips_already_linked_records(
        self, mock_br_cls, mock_query
    ):
        """AC9: acm_records that already have building_record_id are not re-updated."""
        # Record already has building_record_id set
        raw_records = [
            _make_acm_raw(
                record_id="acm_record:r1",
                building_record_id="building_record:bld_existing",
            ),
        ]
        mock_query.side_effect = [
            raw_records,  # fetch records
            [{"id": "building_record:bld_existing"}],  # idempotency check -> found
            # No UPDATE call should happen for already-linked records
        ]

        summary = await migrate_source("source:src001")

        # Record was already linked — counted as already_linked
        assert summary["records_already_linked"] == 1
        assert summary["records_linked"] == 0

    @patch("scripts.v3_data_migration.repo_query", new_callable=AsyncMock)
    @patch("scripts.v3_data_migration.BuildingRecord", autospec=True)
    async def test_dry_run_no_db_writes(self, mock_br_cls, mock_query):
        """AC7: dry_run=True does not write BuildingRecord or update FKs."""
        raw_records = [
            _make_acm_raw(record_id="acm_record:r1"),
            _make_acm_raw(record_id="acm_record:r2"),
        ]
        mock_query.side_effect = [
            raw_records,  # fetch records
            [],  # idempotency check -> not found
            # No further DB writes in dry-run
        ]

        summary = await migrate_source("source:src001", dry_run=True)

        # Should count what WOULD happen, but not write
        assert summary["buildings_created"] == 1
        assert summary["records_linked"] == 2
        # BuildingRecord.save should NOT have been called
        mock_br_cls.return_value.save.assert_not_called()
        # Only 2 repo_query calls (fetch + idempotency check), no UPDATE calls
        assert mock_query.call_count == 2

    @patch("scripts.v3_data_migration.repo_query", new_callable=AsyncMock)
    async def test_no_records_returns_empty_summary(self, mock_query):
        """migrate_source with no acm_records returns zero summary."""
        mock_query.return_value = []
        summary = await migrate_source("source:src_empty")
        assert summary["buildings_created"] == 0
        assert summary["records_linked"] == 0

    @patch("scripts.v3_data_migration.repo_query", new_callable=AsyncMock)
    @patch("scripts.v3_data_migration.BuildingRecord", autospec=True)
    async def test_two_buildings_two_building_records(self, mock_br_cls, mock_query):
        """AC2: 5 records across 2 buildings produce 2 BuildingRecords."""
        raw_records = [
            _make_acm_raw(building_id="B01", record_id="acm_record:r1"),
            _make_acm_raw(building_id="B01", record_id="acm_record:r2"),
            _make_acm_raw(building_id="B01", record_id="acm_record:r3"),
            _make_acm_raw(building_id="B02", record_id="acm_record:r4"),
            _make_acm_raw(building_id="B02", record_id="acm_record:r5"),
        ]

        # B01: check -> not found, B02: check -> not found
        # Then 5 UPDATE calls (one per record)
        mock_query.side_effect = [
            raw_records,  # fetch
            [],  # idempotency for B01
            [],  # UPDATE r1
            [],  # UPDATE r2
            [],  # UPDATE r3
            [],  # idempotency for B02
            [],  # UPDATE r4
            [],  # UPDATE r5
        ]

        internal_id_call = 0

        async def _gen_id(src_id):
            nonlocal internal_id_call
            internal_id_call += 1
            return f"BLD#SRC001__{internal_id_call:03d}"

        mock_br_cls.generate_internal_id = _gen_id

        mock_bld1 = MagicMock()
        mock_bld1.id = "building_record:bld001"
        mock_bld1.save = AsyncMock()
        mock_bld2 = MagicMock()
        mock_bld2.id = "building_record:bld002"
        mock_bld2.save = AsyncMock()
        mock_br_cls.side_effect = [mock_bld1, mock_bld2]

        summary = await migrate_source("source:src001")

        assert summary["buildings_created"] == 2
        assert summary["records_linked"] == 5


# ---------------------------------------------------------------------------
# AC8: Benchmark scenarios
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestBenchmarkScenarios:
    """AC8: Broadmeadows and Alexander benchmark scenarios."""

    @patch("scripts.v3_data_migration.repo_query", new_callable=AsyncMock)
    @patch("scripts.v3_data_migration.BuildingRecord", autospec=True)
    async def test_broadmeadows_31_records_one_building(self, mock_br_cls, mock_query):
        """AC8: 31 Broadmeadows records with 1 building_id -> 1 BuildingRecord created."""
        raw_records = [
            _make_acm_raw(
                source_id="source:broadmeadows",
                building_id="BLK-A",
                building_name="Broadmeadows Primary - Main Block",
                building_year=1968,
                suburb="Broadmeadows",
                postcode="3047",
                record_id=f"acm_record:r{i}",
            )
            for i in range(31)
        ]

        # idempotency check (not found) + 31 UPDATE calls
        mock_query.side_effect = [raw_records, []] + [[]] * 31

        mock_br_cls.generate_internal_id = AsyncMock(return_value="BLD#BROADMEA_001")
        mock_bld = MagicMock()
        mock_bld.id = "building_record:bld_broadmeadows"
        mock_bld.save = AsyncMock()
        mock_br_cls.return_value = mock_bld

        summary = await migrate_source("source:broadmeadows")

        assert summary["buildings_created"] == 1
        assert summary["records_linked"] == 31

    @patch("scripts.v3_data_migration.repo_query", new_callable=AsyncMock)
    @patch("scripts.v3_data_migration.BuildingRecord", autospec=True)
    async def test_alexander_43_records_five_buildings(self, mock_br_cls, mock_query):
        """AC8: 43 Alexander records across 5 buildings -> 5 BuildingRecords created."""
        building_sizes = [9, 9, 9, 8, 8]
        raw_records = []
        for bld_idx, size in enumerate(building_sizes):
            for rec_idx in range(size):
                raw_records.append(
                    _make_acm_raw(
                        source_id="source:alexander",
                        building_id=f"BLK-{bld_idx}",
                        building_name=f"Alexander PS - Block {bld_idx}",
                        record_id=f"acm_record:r{bld_idx}_{rec_idx}",
                    )
                )

        # 5 idempotency checks (all not found) + 43 UPDATE calls
        mock_query.side_effect = [raw_records] + [[]] * 5 + [[]] * 43

        call_count = 0

        async def _gen_id(src_id):
            nonlocal call_count
            call_count += 1
            return f"BLD#ALEXANDE_{call_count:03d}"

        mock_br_cls.generate_internal_id = _gen_id

        # Create 5 distinct mock building instances
        mock_buildings = []
        for i in range(5):
            b = MagicMock()
            b.id = f"building_record:bld_alex_{i:03d}"
            b.save = AsyncMock()
            mock_buildings.append(b)
        mock_br_cls.side_effect = mock_buildings

        summary = await migrate_source("source:alexander")

        assert summary["buildings_created"] == 5
        assert summary["records_linked"] == 43


# ---------------------------------------------------------------------------
# AC6: Rollback
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestRollback:
    """Tests for rollback functions."""

    @patch("scripts.v3_data_migration_rollback.repo_query", new_callable=AsyncMock)
    async def test_rollback_source_nulls_fks_and_deletes_buildings(self, mock_query):
        """AC6: rollback_source nulls FKs and deletes building_records for source."""
        # 1. UPDATE (null FKs) -> RETURN BEFORE gives 3 rows
        # 2. DELETE building_record -> RETURN BEFORE gives 1 row
        mock_query.side_effect = [
            [{"id": "acm_record:r1"}, {"id": "acm_record:r2"}, {"id": "acm_record:r3"}],
            [{"id": "building_record:bld001"}],
        ]

        summary = await rollback_source("source:src001")

        assert summary["fks_nulled"] == 3
        assert summary["buildings_deleted"] == 1
        assert summary["vocab_reverted"] == 0
        assert mock_query.call_count == 2

    @patch("scripts.v3_data_migration_rollback.repo_query", new_callable=AsyncMock)
    async def test_rollback_all_nulls_fks_and_deletes_all_buildings(self, mock_query):
        """AC6: rollback_all nulls all FKs and deletes all building_records."""
        mock_query.side_effect = [
            [{"id": "acm_record:r1"}, {"id": "acm_record:r2"}],  # null FKs
            [{"id": "building_record:bld001"}],  # delete buildings
        ]

        summary = await rollback_all()

        assert summary["fks_nulled"] == 2
        assert summary["buildings_deleted"] == 1
        assert summary["vocab_reverted"] == 0

    @patch("scripts.v3_data_migration_rollback.repo_query", new_callable=AsyncMock)
    async def test_rollback_with_revert_vocab(self, mock_query):
        """AC6: --revert-vocab reverts 'Stable' -> 'Good'."""
        mock_query.side_effect = [
            [],  # null FKs (0 records)
            [],  # delete buildings (0 records)
            [{"total": 7}],  # count Stable records
            [],  # UPDATE Stable -> Good
        ]

        summary = await rollback_all(revert_vocab=True)

        assert summary["vocab_reverted"] == 7

    @patch("scripts.v3_data_migration_rollback.repo_query", new_callable=AsyncMock)
    async def test_rollback_all_idempotent_when_already_clean(self, mock_query):
        """Rollback is safe on an already-clean DB (no FKs, no buildings)."""
        mock_query.side_effect = [
            [],  # null FKs -> none found
            [],  # delete buildings -> none found
        ]

        summary = await rollback_all()

        assert summary["fks_nulled"] == 0
        assert summary["buildings_deleted"] == 0


# ---------------------------------------------------------------------------
# AC9: Idempotent re-run via migrate_all
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestIdempotentRerun:
    """AC9: Verify migrate_all is safe to re-run."""

    @patch("scripts.v3_data_migration.verify_schema", new_callable=AsyncMock)
    @patch("scripts.v3_data_migration.migrate_vocabulary", new_callable=AsyncMock)
    @patch("scripts.v3_data_migration.migrate_source", new_callable=AsyncMock)
    @patch("scripts.v3_data_migration.repo_query", new_callable=AsyncMock)
    async def test_second_run_skips_all_buildings(
        self,
        mock_query,
        mock_migrate_source,
        mock_migrate_vocab,
        mock_verify,
    ):
        """Running migrate_all twice: second run skips all buildings (already created)."""
        mock_verify.return_value = True

        # Two distinct source_ids in the DB
        mock_query.return_value = [
            {"source_id": "source:s1"},
            {"source_id": "source:s2"},
        ]

        # Simulate second run: all buildings already existed
        mock_migrate_source.return_value = {
            "buildings_created": 0,
            "buildings_skipped": 3,
            "records_linked": 0,
            "records_already_linked": 10,
        }
        mock_migrate_vocab.return_value = 0  # no 'Good' values remain

        summary = await migrate_all()

        assert summary["buildings_created"] == 0
        assert summary["buildings_skipped"] == 6  # 3 per source * 2 sources
        assert summary["vocab_updated"] == 0
        assert summary["sources_processed"] == 2


# ---------------------------------------------------------------------------
# Schema verification
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestVerifySchema:
    """Tests for verify_schema helper."""

    @patch("scripts.v3_data_migration.repo_query", new_callable=AsyncMock)
    async def test_returns_true_when_table_exists(self, mock_query):
        """verify_schema returns True when building_record table is accessible."""
        mock_query.return_value = []  # Empty result is fine — table exists
        result = await verify_schema()
        assert result is True

    @patch("scripts.v3_data_migration.repo_query", new_callable=AsyncMock)
    async def test_returns_false_when_query_raises(self, mock_query):
        """verify_schema returns False when query raises (table missing)."""
        mock_query.side_effect = Exception("Table 'building_record' does not exist")
        result = await verify_schema()
        assert result is False


# ---------------------------------------------------------------------------
# _find_existing_building
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestFindExistingBuilding:
    """Tests for _find_existing_building idempotency helper."""

    @patch("scripts.v3_data_migration.repo_query", new_callable=AsyncMock)
    async def test_returns_id_when_found(self, mock_query):
        """Returns record ID string when existing building found."""
        mock_query.return_value = [{"id": "building_record:bld001"}]
        result = await _find_existing_building("source:src001", "B01")
        assert result == "building_record:bld001"

    @patch("scripts.v3_data_migration.repo_query", new_callable=AsyncMock)
    async def test_returns_none_when_not_found(self, mock_query):
        """Returns None when no existing building found."""
        mock_query.return_value = []
        result = await _find_existing_building("source:src001", "B01")
        assert result is None
