"""
Integration tests for ACM extraction with realistic Docling output.

Tests the extraction against sample markdown that mimics the structure
produced by Docling when processing ACM Register PDFs.
"""

import pytest

from open_notebook.extractors.acm_extractor import extract_acm_records


class TestSamplePDF1124:
    """Tests based on expected output from 1124_AsbestosRegister.pdf."""

    SAMPLE_MARKDOWN = """# Westview Primary School - Asbestos Register

--- Page 1 ---

## Building: B01A - Administration Block - 1965

### Area Type: Interior

#### Room: B01A-R001 - Principal Office - 42.5m²

| Product | Material Description | Extent | Location | Friable | Condition | Risk | Result |
|---------|---------------------|--------|----------|---------|-----------|------|--------|
| Floor Tiles | Vinyl asbestos floor tiles, 9x9 inch | 42m² | Throughout floor | Non Friable | Good | Low | Detected |
| Pipe Lagging | Chrysotile asbestos pipe insulation | 8m linear | Ceiling void | Friable | Fair | Medium | Detected |

#### Room: B01A-R002 - Reception Area - 28.0m²

| Product | Material Description | Extent | Location | Friable | Condition | Risk | Result |
|---------|---------------------|--------|----------|---------|-----------|------|--------|
| Ceiling Tiles | Acoustic ceiling tiles | 28m² | Suspended ceiling | Non Friable | Good | Low | Detected |

--- Page 2 ---

## Building: B02A - Science Block - 1972

### Area Type: Interior

#### Room: B02A-R001 - Lab 1 - 65.0m²

| Product | Material Description | Extent | Location | Friable | Condition | Risk | Result |
|---------|---------------------|--------|----------|---------|-----------|------|--------|
| Bench Tops | Compressed asbestos cement | 12m² | Lab benches | Non Friable | Fair | Low | Detected |
| Fume Hood Lining | Millboard asbestos lining | 4m² | Inside fume hood | Friable | Poor | High | Detected |

#### Room: B02A-R002 - Store Room - 15.0m²

| Product | Material Description | Extent | Location | Friable | Condition | Risk | Result |
|---------|---------------------|--------|----------|---------|-----------|------|--------|
| Floor Covering | Vinyl tiles | 15m² | Floor | Non Friable | Good | Low | No Asbestos Detected |
"""

    def test_extracts_correct_record_count(self):
        """Test that all 6 records are extracted."""
        result = extract_acm_records(self.SAMPLE_MARKDOWN, "source:1124")
        assert len(result) == 6

    def test_school_name_extraction(self):
        """Test school name is correctly extracted."""
        result = extract_acm_records(self.SAMPLE_MARKDOWN, "source:1124")
        assert all(r["school_name"] == "Westview Primary School" for r in result)

    def test_building_context_preservation(self):
        """Test building context is preserved across rooms."""
        result = extract_acm_records(self.SAMPLE_MARKDOWN, "source:1124")

        # First 3 records should be from B01A
        b01a_records = [r for r in result if r["building_id"] == "B01A"]
        assert len(b01a_records) == 3
        assert all(r["building_name"] == "Administration Block" for r in b01a_records)
        assert all(r["building_year"] == 1965 for r in b01a_records)

        # Last 3 records should be from B02A
        b02a_records = [r for r in result if r["building_id"] == "B02A"]
        assert len(b02a_records) == 3
        assert all(r["building_name"] == "Science Block" for r in b02a_records)
        assert all(r["building_year"] == 1972 for r in b02a_records)

    def test_room_context_preservation(self):
        """Test room context is preserved within building."""
        result = extract_acm_records(self.SAMPLE_MARKDOWN, "source:1124")

        # Check room B01A-R001 records
        r001_records = [r for r in result if r["room_id"] == "B01A-R001"]
        assert len(r001_records) == 2
        assert all(r["room_name"] == "Principal Office" for r in r001_records)
        assert all(r["room_area"] == 42.5 for r in r001_records)

    def test_page_numbers(self):
        """Test page numbers are correctly tracked."""
        result = extract_acm_records(self.SAMPLE_MARKDOWN, "source:1124")

        page1_records = [r for r in result if r["building_id"] == "B01A"]
        page2_records = [r for r in result if r["building_id"] == "B02A"]

        assert all(r["page_number"] == 1 for r in page1_records)
        assert all(r["page_number"] == 2 for r in page2_records)

    def test_no_asbestos_detected_normalization(self):
        """Test 'No Asbestos Detected' is normalized to 'Not Detected'."""
        result = extract_acm_records(self.SAMPLE_MARKDOWN, "source:1124")

        not_detected = [r for r in result if r["result"] == "Not Detected"]
        assert len(not_detected) == 1
        assert not_detected[0]["product"] == "Floor Covering"

    def test_risk_status_extraction(self):
        """Test risk status is extracted correctly."""
        result = extract_acm_records(self.SAMPLE_MARKDOWN, "source:1124")

        high_risk = [r for r in result if r["risk_status"] == "High"]
        assert len(high_risk) == 1
        assert high_risk[0]["product"] == "Fume Hood Lining"


class TestSamplePDF3980:
    """Tests based on expected output from 3980_AsbestosRegister.pdf."""

    SAMPLE_MARKDOWN = """# Riverside High School - ACM Register

--- Page 1 ---

## Building: A01 - Main Building - 1958 - Brick

### Area Type: Interior

#### Room: A01-R101 - Classroom 1 - 55.0m²

| Product | Material Description | Extent | Location | Friable | Condition | Risk | Result |
|---------|---------------------|--------|----------|---------|-----------|------|--------|
| Wall Panels | Asbestos cement sheeting | 40m² | Internal walls | Non Friable | Good | Low | Detected |
| Door Seals | Asbestos rope gaskets | 5m | Around door frames | Friable | Fair | Medium | Detected |

### Area Type: Exterior

#### Room: A01-E001 - External Eaves

| Product | Material Description | Extent | Location | Friable | Condition | Risk | Result |
|---------|---------------------|--------|----------|---------|-----------|------|--------|
| Eave Lining | Fibrous cement sheets | 85m² | Under eaves | Non Friable | Poor | Medium | Detected |

--- Page 2 ---

## Building: B01 - Gymnasium - 1975

### Area Type: Interior

#### Room: B01-R001 - Main Hall - 450.0m²

| Product | Material Description | Extent | Location | Friable | Condition | Risk | Result |
|---------|---------------------|--------|----------|---------|-----------|------|--------|
| Roof Insulation | Sprayed asbestos insulation | 450m² | Above ceiling | Friable | Poor | High | Detected |
"""

    def test_extracts_all_records(self):
        """Test all 4 records are extracted."""
        result = extract_acm_records(self.SAMPLE_MARKDOWN, "source:3980")
        assert len(result) == 4

    def test_building_construction_type(self):
        """Test building construction type is captured."""
        result = extract_acm_records(self.SAMPLE_MARKDOWN, "source:3980")

        a01_records = [r for r in result if r["building_id"] == "A01"]
        assert all(r["building_construction"] == "Brick" for r in a01_records)

    def test_area_type_changes(self):
        """Test area type changes are tracked."""
        result = extract_acm_records(self.SAMPLE_MARKDOWN, "source:3980")

        interior = [r for r in result if r["area_type"] == "Interior"]
        exterior = [r for r in result if r["area_type"] == "Exterior"]

        assert len(interior) == 3
        assert len(exterior) == 1

    def test_large_room_area(self):
        """Test large room areas are correctly parsed."""
        result = extract_acm_records(self.SAMPLE_MARKDOWN, "source:3980")

        gym = [r for r in result if r["room_id"] == "B01-R001"]
        assert len(gym) == 1
        assert gym[0]["room_area"] == 450.0


class TestSamplePDF4601:
    """Tests based on expected output from 4601_AsbestosRegister.pdf."""

    SAMPLE_MARKDOWN = """# Oakwood College - SAMP Register

--- Page 1 ---

## Building: C10 - Technology Wing - 1985

### Area Type: Interior

#### Room: C10-R200 - Workshop - 120.0m²

| Product | Material Description | Extent | Location | Friable | Condition | Risk | Result |
|---------|---------------------|--------|----------|---------|-----------|------|--------|
| Brake Pads | Demonstration brake components | 10 items | Storage cabinet | Non Friable | Good | Low | Detected |

#### Room: C10-R201 - Computer Lab - 80.0m²

| Product | Material Description | Extent | Location | Friable | Condition | Risk | Result |
|---------|---------------------|--------|----------|---------|-----------|------|--------|
| Raised Floor Tiles | Vinyl composite tiles | 80m² | Under floor system | Non Friable | Good | Low | No Asbestos Detected |
| Cable Ducting | Asbestos cement ducting | 25m | Below floor | Non Friable | Fair | Low | Detected |

--- Page 2 ---

## Building: C10 - Technology Wing - 1985

### Area Type: Grounds

#### Room: C10-EXT - External Plant Room

| Product | Material Description | Extent | Location | Friable | Condition | Risk | Result |
|---------|---------------------|--------|----------|---------|-----------|------|--------|
| Boiler Insulation | Calcium silicate blocks | 5m² | Around boiler | Non Friable | Fair | Medium | Detected |
| Flue Pipe | Asbestos cement flue | 8m | External stack | Non Friable | Good | Low | Detected |
"""

    def test_extracts_all_records(self):
        """Test all 5 records are extracted."""
        result = extract_acm_records(self.SAMPLE_MARKDOWN, "source:4601")
        assert len(result) == 5

    def test_grounds_area_type(self):
        """Test Grounds area type is captured."""
        result = extract_acm_records(self.SAMPLE_MARKDOWN, "source:4601")

        grounds = [r for r in result if r["area_type"] == "Grounds"]
        assert len(grounds) == 2

    def test_same_building_different_pages(self):
        """Test same building across different pages maintains context."""
        result = extract_acm_records(self.SAMPLE_MARKDOWN, "source:4601")

        c10_records = [r for r in result if r["building_id"] == "C10"]
        assert len(c10_records) == 5
        assert all(r["building_name"] == "Technology Wing" for r in c10_records)
        assert all(r["building_year"] == 1985 for r in c10_records)

    def test_multiple_not_detected(self):
        """Test extraction handles multiple tables correctly."""
        result = extract_acm_records(self.SAMPLE_MARKDOWN, "source:4601")

        not_detected = [r for r in result if r["result"] == "Not Detected"]
        assert len(not_detected) == 1


class TestAccuracyMetrics:
    """Test accuracy requirements from AC7."""

    def test_field_accuracy_sample1(self):
        """Test >90% field accuracy on sample 1 - validates actual field values."""
        markdown = TestSamplePDF1124.SAMPLE_MARKDOWN
        result = extract_acm_records(markdown, "source:1124")

        # Validate specific records with expected values
        expected_records = [
            {
                "school_name": "Westview Primary School",
                "building_id": "B01A",
                "building_name": "Administration Block",
                "building_year": 1965,
                "room_id": "B01A-R001",
                "room_name": "Principal Office",
                "room_area": 42.5,
                "product": "Floor Tiles",
                "material_description": "Vinyl asbestos floor tiles, 9x9 inch",
                "result": "Detected",
            },
            {
                "school_name": "Westview Primary School",
                "building_id": "B01A",
                "room_id": "B01A-R001",
                "product": "Pipe Lagging",
                "material_description": "Chrysotile asbestos pipe insulation",
                "friable": "Friable",
                "material_condition": "Fair",
                "risk_status": "Medium",
                "result": "Detected",
            },
            {
                "building_id": "B02A",
                "building_name": "Science Block",
                "building_year": 1972,
                "room_id": "B02A-R001",
                "room_name": "Lab 1",
                "product": "Bench Tops",
            },
        ]

        correct = 0
        total = 0

        for expected in expected_records:
            # Find matching record
            for record in result:
                match = all(
                    record.get(k) == v for k, v in expected.items()
                )
                if match:
                    correct += len(expected)
                    break
            total += len(expected)

        accuracy = correct / total if total > 0 else 0
        assert accuracy > 0.9, f"Accuracy {accuracy:.2%} is below 90% threshold"

    def test_all_required_fields_present(self):
        """Test all required fields are present in extracted records."""
        markdown = TestSamplePDF1124.SAMPLE_MARKDOWN
        result = extract_acm_records(markdown, "source:1124")

        required_fields = ["source_id", "school_name", "building_id", "product", "result"]

        for record in result:
            for field in required_fields:
                assert field in record, f"Missing required field: {field}"
                if field != "source_id":  # source_id can be empty string
                    assert record[field], f"Empty required field: {field}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
