"""
Create test source with ACM data for manual testing.

Usage:
    uv run python scripts/create_test_acm_data.py

This will create:
1. A test source (simulating an uploaded SAMP document)
2. 6 ACM records linked to that source
"""

import asyncio
from open_notebook.domain.notebook import Source
from open_notebook.domain.acm import ACMRecord


async def create_test_data():
    print("Creating test source...")

    # Create a test source
    source = Source(
        title="Test SAMP Document - Administration & Science Buildings",
        source_type="document",
        full_text="""
        School Asbestos Management Plan (SAMP)
        Survey Date: 2024-01-15

        This document contains the asbestos register for Administration Block
        and Science Wing buildings. Multiple ACM materials have been identified
        including floor tiles, pipe lagging, ceiling tiles, and eaves lining.

        Building A1 - Administration Block (1965)
        Building B1 - Science Wing (1972)
        """,
    )
    await source.save()
    source_id = source.id
    print(f"  Created source: {source_id}")

    # Test ACM records from fixture
    school_name = "Test Primary School"

    test_records = [
        {
            "school_name": school_name,
            "building_id": "A1",
            "building_name": "Administration Block",
            "building_year": 1965,
            "room_id": "A1-R001",
            "room_name": "Main Office",
            "product": "Floor Tiles",
            "material_description": "Vinyl asbestos tiles, 9x9 inch, grey/white mottled",
            "extent": "45m²",
            "location": "Floor",
            "friable": "Non Friable",
            "material_condition": "Good",
            "risk_status": "Low",
            "result": "Detected",
            "page_number": 1
        },
        {
            "school_name": school_name,
            "building_id": "A1",
            "building_name": "Administration Block",
            "room_id": "A1-R001",
            "room_name": "Main Office",
            "product": "Pipe Lagging",
            "material_description": "Cement-bound pipe insulation on heating pipes",
            "extent": "Sections",
            "location": "Under floor",
            "friable": "Non Friable",
            "material_condition": "Fair",
            "risk_status": "Medium",
            "result": "Detected",
            "page_number": 1
        },
        {
            "school_name": school_name,
            "building_id": "A1",
            "building_name": "Administration Block",
            "room_id": "A1-R002",
            "room_name": "Reception",
            "product": "Ceiling Tiles",
            "material_description": "Acoustic ceiling tiles, 2x4 ft",
            "extent": "30m²",
            "location": "Ceiling",
            "friable": "Non Friable",
            "material_condition": "Good",
            "risk_status": "Low",
            "result": "Not Detected",
            "page_number": 1
        },
        {
            "school_name": school_name,
            "building_id": "B1",
            "building_name": "Science Wing",
            "building_year": 1972,
            "room_id": "B1-R001",
            "room_name": "Chemistry Lab",
            "product": "Fume Hood Lining",
            "material_description": "Cement sheet fume hood panels",
            "extent": "3 units",
            "location": "Bench tops",
            "friable": "Non Friable",
            "material_condition": "Fair",
            "risk_status": "Medium",
            "result": "Detected",
            "page_number": 2
        },
        {
            "school_name": school_name,
            "building_id": "B1",
            "building_name": "Science Wing",
            "room_id": "B1-R001",
            "room_name": "Chemistry Lab",
            "product": "Bench Tops",
            "material_description": "Cement sheet laboratory bench surfaces",
            "extent": "12m²",
            "location": "Benches",
            "friable": "Non Friable",
            "material_condition": "Good",
            "risk_status": "Low",
            "result": "Presumed",
            "page_number": 2
        },
        {
            "school_name": school_name,
            "building_id": "B1",
            "building_name": "Science Wing",
            "room_id": "B1-EXT",
            "room_name": "External Walls",
            "product": "Eaves Lining",
            "material_description": "Fibro cement eaves soffit lining - DETERIORATING",
            "extent": "50m linear",
            "location": "Eaves",
            "friable": "Friable",  # This one is friable!
            "material_condition": "Poor",
            "risk_status": "High",
            "result": "Detected",
            "page_number": 2
        }
    ]

    print(f"Creating {len(test_records)} ACM records...")

    for i, record_data in enumerate(test_records, 1):
        record = ACMRecord(
            source_id=source_id,
            **record_data
        )
        await record.save()
        risk = record_data.get('risk_status', 'Unknown')
        print(f"  [{i}/{len(test_records)}] {record_data['building_name']} - {record_data['room_name']}: {record_data['product']} ({risk} risk)")

    print()
    print("=" * 60)
    print("TEST DATA CREATED SUCCESSFULLY!")
    print("=" * 60)
    print()
    print(f"Source ID: {source_id}")
    print(f"Source Title: {source.title}")
    print(f"ACM Records: {len(test_records)}")
    print()
    print("Risk Summary:")
    print("  - High Risk: 1 (Eaves Lining - deteriorating friable material)")
    print("  - Medium Risk: 2 (Pipe Lagging, Fume Hood)")
    print("  - Low Risk: 3 (Floor Tiles, Ceiling Tiles, Bench Tops)")
    print()
    print("TO TEST:")
    print(f"  1. Open http://localhost:8502/sources")
    print(f"  2. Click on 'Test SAMP Document - Administration & Science Buildings'")
    print(f"  3. Enable the 'ACM Data' toggle in the chat panel")
    print(f"  4. Ask: 'What are the high-risk areas?'")
    print()


if __name__ == "__main__":
    asyncio.run(create_test_data())
