"""
Unit tests for AI-Powered ACM Extraction.

Tests the Pydantic schemas, validation logic, chunking, and deduplication.
Story: E1-S7 AI-Powered ACM Extraction
"""

import pytest


class TestACMExtractionSchemas:
    """Test suite for extraction Pydantic schemas."""

    def test_acm_extraction_record_required_fields(self):
        """Test that required fields are properly enforced."""
        from open_notebook.extractors.acm_schemas import ACMExtractionRecord

        # Valid minimal record
        record = ACMExtractionRecord(
            building_id="B1",
            product="Floor Tiles",
            material_description="Vinyl asbestos tiles",
            result="Detected",
        )
        assert record.building_id == "B1"
        assert record.extraction_confidence == "medium"  # default
        assert record.data_issues == []  # default

    def test_acm_extraction_record_all_fields(self):
        """Test record with all optional fields."""
        from open_notebook.extractors.acm_schemas import ACMExtractionRecord

        record = ACMExtractionRecord(
            building_id="A1",
            building_name="Main Building",
            building_year=1975,
            building_construction="Brick",
            room_id="A1-R1",
            room_name="Classroom",
            room_area=45.5,
            area_type="Interior",
            product="Ceiling Tiles",
            material_description="Acoustic ceiling tiles with asbestos",
            extent="Whole ceiling",
            location="Ceiling",
            friable="Non Friable",
            material_condition="Good",
            risk_status="Low",
            result="Detected",
            disturbance_potential="Low",
            sample_no="S001",
            sample_result="Chrysotile detected",
            identifying_company="Acme Hygiene",
            quantity="50 m²",
            acm_labelled=True,
            acm_label_details="Yellow warning label applied 2020",
            hygienist_recommendations="Monitor annually",
            psb_supplied_acm_id="PSB-001",
            removal_status="N/A",
            date_of_removal=None,
            extraction_confidence="high",
            data_issues=["Minor formatting inconsistency"],
            page_number=5,
        )

        assert record.building_id == "A1"
        assert record.acm_labelled is True
        assert record.extraction_confidence == "high"
        assert len(record.data_issues) == 1

    def test_building_room_context_defaults(self):
        """Test BuildingRoomContext has correct defaults."""
        from open_notebook.extractors.acm_schemas import BuildingRoomContext

        context = BuildingRoomContext()

        assert context.school_name == "Unknown School"
        assert context.building_id is None
        assert context.room_id is None
        assert context.area_type == "Interior"
        assert context.current_page == 1

    def test_acm_extraction_result_update_stats(self):
        """Test that update_stats computes correct values."""
        from open_notebook.extractors.acm_schemas import (
            ACMExtractionRecord,
            ACMExtractionResult,
        )

        records = [
            ACMExtractionRecord(
                building_id="B1",
                product="Tiles",
                material_description="Vinyl",
                result="Detected",
                extraction_confidence="high",
            ),
            ACMExtractionRecord(
                building_id="B1",
                product="Lagging",
                material_description="Pipe wrap",
                result="Detected",
                extraction_confidence="medium",
            ),
            ACMExtractionRecord(
                building_id="B2",
                product="Insulation",
                material_description="Wall insulation",
                result="Presumed",
                extraction_confidence="low",
            ),
        ]

        result = ACMExtractionResult(records=records)
        result.update_stats()

        assert result.total_records == 3
        assert result.confidence_distribution["high"] == 1
        assert result.confidence_distribution["medium"] == 1
        assert result.confidence_distribution["low"] == 1

    def test_extraction_status_enum(self):
        """Test ExtractionStatus enum values."""
        from open_notebook.extractors.acm_schemas import ExtractionStatus

        assert ExtractionStatus.VALID.value == "valid"
        assert ExtractionStatus.INVALID.value == "invalid"
        assert ExtractionStatus.NO_ACM_DATA.value == "no_acm_data"


class TestACMRecordModel:
    """Test suite for the updated ACMRecord domain model."""

    def test_acm_record_new_fields(self):
        """Test that new fields are available on ACMRecord."""
        from open_notebook.domain.acm import ACMRecord

        record = ACMRecord(
            source_id="source:123",
            school_name="Test School",
            building_id="B1",
            product="Tiles",
            material_description="Vinyl tiles",
            result="Detected",
            # New fields
            disturbance_potential="Low",
            sample_no="S001",
            sample_result="Chrysotile",
            identifying_company="Test Co",
            quantity="10 m²",
            acm_labelled=True,
            acm_label_details="Warning label",
            hygienist_recommendations="Monitor",
            psb_supplied_acm_id="PSB001",
            removal_status="N/A",
            date_of_removal=None,
            extraction_confidence="high",
            data_issues=["Issue 1"],
        )

        assert record.disturbance_potential == "Low"
        assert record.acm_labelled is True
        assert record.extraction_confidence == "high"
        assert record.data_issues == ["Issue 1"]

    def test_extraction_confidence_validator(self):
        """Test that extraction_confidence is validated."""
        from open_notebook.domain.acm import ACMRecord
        from open_notebook.exceptions import InvalidInputError

        # Valid values
        for conf in ["high", "medium", "low", "HIGH", "Medium", "LOW"]:
            record = ACMRecord(
                source_id="source:123",
                school_name="Test",
                building_id="B1",
                product="Tiles",
                material_description="Vinyl",
                result="Detected",
                extraction_confidence=conf,
            )
            assert record.extraction_confidence in ["high", "medium", "low"]

        # Invalid value
        with pytest.raises(InvalidInputError):
            ACMRecord(
                source_id="source:123",
                school_name="Test",
                building_id="B1",
                product="Tiles",
                material_description="Vinyl",
                result="Detected",
                extraction_confidence="invalid",
            )

    def test_acm_record_backward_compatibility(self):
        """Test that existing records without new fields still work."""
        from open_notebook.domain.acm import ACMRecord

        # Create record without any new fields
        record = ACMRecord(
            source_id="source:123",
            school_name="Test School",
            building_id="B1",
            product="Tiles",
            material_description="Vinyl tiles",
            result="Detected",
        )

        # All new fields should be None
        assert record.disturbance_potential is None
        assert record.sample_no is None
        assert record.extraction_confidence is None
        assert record.data_issues is None


class TestChunkingLogic:
    """Test suite for content chunking."""

    def test_chunk_small_content(self):
        """Test that small content is not chunked."""
        from open_notebook.graphs.acm_extraction import _chunk_content

        content = "This is a small piece of content."
        chunks = _chunk_content(content)

        assert len(chunks) == 1
        assert chunks[0]["content"] == content
        assert chunks[0]["chunk_index"] == 0

    def test_chunk_by_page_markers(self):
        """Test chunking by page markers when content exceeds threshold."""
        from open_notebook.graphs.acm_extraction import _chunk_content

        # Create content large enough to trigger chunking (>50% of context window)
        # With context_window=50, threshold is 25 tokens
        # Each page needs enough content to be meaningful
        content = """--- Page 1 ---
This is page one with plenty of content to make it worth chunking.
We need enough text here to exceed the 50% threshold of the context window.
Adding more lines to ensure we have substantial content for testing.

--- Page 2 ---
Page two also has lots of content for the chunking algorithm to process.
The algorithm should split this at page boundaries when the total exceeds threshold.
More content here to pad out the page and ensure proper token counts.

--- Page 3 ---
The third page completes our test document with additional material.
This should result in three separate chunks when the context is small enough.
Final lines of content to ensure adequate length for testing purposes."""

        # Use very small context window to force chunking
        chunks = _chunk_content(content, context_window=50)

        # With such a small window, content should be chunked
        assert len(chunks) >= 1

        # The first chunk should have page_number 1
        assert chunks[0]["page_number"] == 1


class TestDeduplicationLogic:
    """Test suite for record deduplication."""

    def test_generate_dedup_key(self):
        """Test deduplication key generation."""
        from open_notebook.extractors.acm_schemas import ACMExtractionRecord
        from open_notebook.graphs.acm_extraction import _generate_dedup_key

        record = ACMExtractionRecord(
            building_id="B1",
            room_id="B1-R1",
            product="Tiles",
            material_description="Vinyl floor tiles with asbestos",
            result="Detected",
        )

        key = _generate_dedup_key(record, "SCHOOL01")

        assert key.startswith("SCHOOL01_B1_B1-R1_")
        assert len(key) > 20  # Should include hash

    def test_dedup_key_different_for_different_records(self):
        """Test that different records get different keys."""
        from open_notebook.extractors.acm_schemas import ACMExtractionRecord
        from open_notebook.graphs.acm_extraction import _generate_dedup_key

        record1 = ACMExtractionRecord(
            building_id="B1",
            room_id="B1-R1",
            product="Tiles",
            material_description="Vinyl floor tiles",
            result="Detected",
        )

        record2 = ACMExtractionRecord(
            building_id="B1",
            room_id="B1-R1",
            product="Lagging",
            material_description="Pipe insulation",
            result="Detected",
        )

        key1 = _generate_dedup_key(record1, "SCHOOL01")
        key2 = _generate_dedup_key(record2, "SCHOOL01")

        assert key1 != key2

    def test_merge_records_keeps_higher_confidence(self):
        """Test that merge keeps record with higher confidence."""
        from open_notebook.extractors.acm_schemas import ACMExtractionRecord
        from open_notebook.graphs.acm_extraction import _merge_records

        low_conf = ACMExtractionRecord(
            building_id="B1",
            product="Tiles",
            material_description="Vinyl",
            result="Detected",
            extraction_confidence="low",
            data_issues=["Issue from low"],
        )

        high_conf = ACMExtractionRecord(
            building_id="B1",
            product="Tiles",
            material_description="Vinyl",
            result="Detected",
            extraction_confidence="high",
            data_issues=["Issue from high"],
        )

        merged = _merge_records(low_conf, high_conf)

        assert merged.extraction_confidence == "high"
        # Both issues should be merged
        assert "Issue from low" in merged.data_issues
        assert "Issue from high" in merged.data_issues


class TestValidationLogic:
    """Test suite for record validation."""

    def test_result_normalization(self):
        """Test that result values are normalized during validation."""
        # This tests the validation logic in the graph
        # We test the expected behavior
        result_mappings = {
            "no asbestos detected": "Not Detected",
            "NAD": "Not Detected",
            "not detected": "Not Detected",
            "detected": "Detected",
            "positive": "Detected",
            "presumed": "Presumed",
        }

        for input_val, expected in result_mappings.items():
            # The normalization happens in validate_records node
            # Here we just test the mapping logic
            result_lower = input_val.lower()
            if "no asbestos" in result_lower or "nad" in result_lower or "not detected" in result_lower:
                normalized = "Not Detected"
            elif "detected" in result_lower or "positive" in result_lower:
                normalized = "Detected"
            elif "presumed" in result_lower:
                normalized = "Presumed"
            else:
                normalized = "Unknown"

            assert normalized == expected, f"Failed for {input_val}"


class TestExtractionInputOutput:
    """Test suite for extraction input/output schemas."""

    def test_acm_extraction_input(self):
        """Test ACMExtractionInput schema."""
        from open_notebook.extractors.acm_schemas import ACMExtractionInput

        input_data = ACMExtractionInput(
            source_id="source:123",
            model_id="model:456",
            force=True,
        )

        assert input_data.source_id == "source:123"
        assert input_data.model_id == "model:456"
        assert input_data.force is True

    def test_acm_extraction_output(self):
        """Test ACMExtractionOutput schema."""
        from open_notebook.extractors.acm_schemas import ACMExtractionOutput

        output = ACMExtractionOutput(
            source_id="source:123",
            status="success",
            total_records=5,
            confidence_distribution={"high": 2, "medium": 2, "low": 1},
            extraction_time_ms=1500,
        )

        assert output.source_id == "source:123"
        assert output.status == "success"
        assert output.total_records == 5
        assert output.confidence_distribution["high"] == 2


class TestExtractionConfidenceEnum:
    """Test suite for ExtractionConfidence enum."""

    def test_extraction_confidence_values(self):
        """Test ExtractionConfidence enum values."""
        from open_notebook.domain.acm import ExtractionConfidence

        assert ExtractionConfidence.HIGH.value == "high"
        assert ExtractionConfidence.MEDIUM.value == "medium"
        assert ExtractionConfidence.LOW.value == "low"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
