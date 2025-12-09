# Tech-Spec: E1-S2 ACM Record Domain Model

**Created:** 2025-12-07
**Status:** Ready for Development
**Epic:** E1 - ACM Data Extraction Pipeline
**Story:** S2 - Create ACM Record Domain Model

---

## Overview

### Problem Statement

The ACM-AI feature needs a Python domain model to work with ACM (Asbestos Containing Material) records extracted from PDF documents. The database schema exists (E1-S1 complete), but there's no Python class to handle CRUD operations, validation, and business logic for ACM records.

### Solution

Create an `ACMRecord` class in `open_notebook/domain/acm.py` that:
- Extends `ObjectModel` from `base.py` (following existing patterns)
- Maps all fields from the `acm_record` SurrealDB table
- Provides CRUD operations (inherited from ObjectModel)
- Includes convenience methods for querying by source, building, room
- Validates required fields

### Scope

**In Scope:**
- `ACMRecord` Pydantic model class
- Field definitions matching database schema
- Class methods for filtered queries (by source_id, building_id, risk_status)
- Basic validation for required fields

**Out of Scope:**
- Extraction logic (E1-S3)
- API endpoints (E1-S4)
- Embedding/vectorization (not needed for ACM records)

---

## Context for Development

### Codebase Patterns

#### 1. Domain Model Pattern
Location: `open_notebook/domain/`

All domain models extend `ObjectModel` from `base.py`:
```python
from open_notebook.domain.base import ObjectModel

class MyModel(ObjectModel):
    table_name: ClassVar[str] = "my_table"
    # Fields here
```

#### 2. Field Types Pattern
From existing models:
```python
# Required field
name: str

# Optional field
title: Optional[str] = None

# List with default
topics: Optional[List[str]] = Field(default_factory=list)

# Nested model
asset: Optional[Asset] = None
```

#### 3. ClassVar Pattern
```python
from typing import ClassVar
table_name: ClassVar[str] = "source"
```

#### 4. Query Pattern
From `notebook.py`:
```python
@classmethod
async def get_by_source(cls, source_id: str) -> List["ACMRecord"]:
    result = await repo_query(
        "SELECT * FROM acm_record WHERE source_id = $source_id",
        {"source_id": ensure_record_id(source_id)}
    )
    return [cls(**record) for record in result]
```

### Files to Reference

| File | Purpose |
|------|---------|
| `open_notebook/domain/base.py` | ObjectModel base class with CRUD |
| `open_notebook/domain/notebook.py` | Examples: Source, Note, Notebook classes |
| `migrations/10.surrealql` | ACM record database schema |
| `open_notebook/database/repository.py` | repo_query, ensure_record_id utilities |

### Database Schema (from E1-S1)

```surrealql
DEFINE TABLE acm_record SCHEMAFULL;

-- Foreign key
DEFINE FIELD source_id TYPE record<source>;

-- School
DEFINE FIELD school_name TYPE string;
DEFINE FIELD school_code TYPE option<string>;

-- Building
DEFINE FIELD building_id TYPE string;
DEFINE FIELD building_name TYPE option<string>;
DEFINE FIELD building_year TYPE option<int>;
DEFINE FIELD building_construction TYPE option<string>;

-- Room
DEFINE FIELD room_id TYPE option<string>;
DEFINE FIELD room_name TYPE option<string>;
DEFINE FIELD room_area TYPE option<float>;
DEFINE FIELD area_type TYPE option<string>;

-- ACM Item
DEFINE FIELD product TYPE string;
DEFINE FIELD material_description TYPE string;
DEFINE FIELD extent TYPE option<string>;
DEFINE FIELD location TYPE option<string>;
DEFINE FIELD friable TYPE option<string>;
DEFINE FIELD material_condition TYPE option<string>;
DEFINE FIELD risk_status TYPE option<string>;
DEFINE FIELD result TYPE string;

-- Citation
DEFINE FIELD page_number TYPE option<int>;
DEFINE FIELD extraction_confidence TYPE option<float>;

-- Timestamps
DEFINE FIELD created DEFAULT time::now();
DEFINE FIELD updated DEFAULT time::now();
```

---

## Implementation Plan

### Tasks

- [ ] **Task 1: Create `open_notebook/domain/acm.py`**
  - Define `ACMRecord` class extending `ObjectModel`
  - Add `table_name: ClassVar[str] = "acm_record"`
  - Define all fields with proper types

- [ ] **Task 2: Add field validators**
  - Validate `source_id` is not empty
  - Validate `school_name` is not empty
  - Validate `building_id` is not empty
  - Validate `product` is not empty
  - Validate `result` is not empty

- [ ] **Task 3: Add class methods for filtered queries**
  - `get_by_source(source_id)` - Get all records for a source
  - `get_by_building(building_id)` - Get all records in a building
  - `get_by_risk_status(risk_status)` - Get all records with risk level
  - `get_summary_by_source(source_id)` - Get counts/summary stats

- [ ] **Task 4: Add `get_source()` instance method**
  - Fetch the related Source object
  - Follow pattern from SourceInsight.get_source()

- [ ] **Task 5: Write unit tests**
  - Test model instantiation
  - Test field validation
  - Test query methods (with mocked database)

### Acceptance Criteria

- [ ] **AC1**: ACMRecord class exists and inherits from ObjectModel
  - Given: The file `open_notebook/domain/acm.py` exists
  - When: ACMRecord is imported
  - Then: It is a subclass of ObjectModel

- [ ] **AC2**: All database fields have corresponding model fields
  - Given: ACMRecord class definition
  - When: Fields are compared to database schema
  - Then: All 23 fields are present with correct types

- [ ] **AC3**: CRUD operations work (inherited from ObjectModel)
  - Given: An ACMRecord instance
  - When: save(), get(), delete() are called
  - Then: Records are persisted/retrieved/deleted correctly

- [ ] **AC4**: Query methods filter correctly
  - Given: Multiple ACM records in database
  - When: `get_by_source("source:123")` is called
  - Then: Only records with that source_id are returned

- [ ] **AC5**: Required field validation works
  - Given: ACMRecord instantiated with missing required field
  - When: Validation runs
  - Then: ValidationError is raised

---

## Code Specification

### File: `open_notebook/domain/acm.py`

```python
"""
ACM (Asbestos Containing Material) Record Domain Model

Represents structured data extracted from ACM Register PDF documents.
Each record links to a source document and captures the hierarchical
structure: School > Building > Room > ACM Item.
"""

from datetime import datetime
from typing import ClassVar, List, Optional

from loguru import logger
from pydantic import Field, field_validator

from open_notebook.database.repository import ensure_record_id, repo_query
from open_notebook.domain.base import ObjectModel
from open_notebook.exceptions import DatabaseOperationError, InvalidInputError


class ACMRecord(ObjectModel):
    """
    Domain model for ACM (Asbestos Containing Material) records.

    Represents a single ACM item extracted from a SAMP (Site Asbestos
    Management Plan) or ACM Register document.
    """

    table_name: ClassVar[str] = "acm_record"

    # Foreign key to source document
    source_id: str  # Will be record<source> in DB

    # School identification
    school_name: str
    school_code: Optional[str] = None

    # Building hierarchy
    building_id: str
    building_name: Optional[str] = None
    building_year: Optional[int] = None
    building_construction: Optional[str] = None

    # Room hierarchy
    room_id: Optional[str] = None
    room_name: Optional[str] = None
    room_area: Optional[float] = None
    area_type: Optional[str] = None  # "Interior", "Exterior", "Grounds"

    # ACM item data
    product: str
    material_description: str
    extent: Optional[str] = None
    location: Optional[str] = None
    friable: Optional[str] = None  # "Friable", "Non Friable"
    material_condition: Optional[str] = None
    risk_status: Optional[str] = None  # "Low", "Medium", "High"
    result: str  # "Detected", "Not Detected", etc.

    # Citation support
    page_number: Optional[int] = None
    extraction_confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)

    # Validators for required fields
    @field_validator("source_id", mode="before")
    @classmethod
    def validate_source_id(cls, v):
        if not v:
            raise InvalidInputError("source_id is required")
        # Ensure proper record format
        if isinstance(v, str) and not v.startswith("source:"):
            return f"source:{v}"
        return str(v)

    @field_validator("school_name")
    @classmethod
    def validate_school_name(cls, v):
        if not v or not v.strip():
            raise InvalidInputError("school_name cannot be empty")
        return v.strip()

    @field_validator("building_id")
    @classmethod
    def validate_building_id(cls, v):
        if not v or not v.strip():
            raise InvalidInputError("building_id cannot be empty")
        return v.strip()

    @field_validator("product")
    @classmethod
    def validate_product(cls, v):
        if not v or not v.strip():
            raise InvalidInputError("product cannot be empty")
        return v.strip()

    @field_validator("result")
    @classmethod
    def validate_result(cls, v):
        if not v or not v.strip():
            raise InvalidInputError("result cannot be empty")
        return v.strip()

    # Class methods for filtered queries
    @classmethod
    async def get_by_source(cls, source_id: str) -> List["ACMRecord"]:
        """Get all ACM records for a specific source document."""
        if not source_id:
            raise InvalidInputError("source_id is required")
        try:
            result = await repo_query(
                "SELECT * FROM acm_record WHERE source_id = $source_id ORDER BY building_id, room_id",
                {"source_id": ensure_record_id(source_id)}
            )
            return [cls(**record) for record in result]
        except Exception as e:
            logger.error(f"Error fetching ACM records for source {source_id}: {e}")
            raise DatabaseOperationError(e)

    @classmethod
    async def get_by_building(cls, building_id: str, source_id: Optional[str] = None) -> List["ACMRecord"]:
        """Get all ACM records for a specific building."""
        if not building_id:
            raise InvalidInputError("building_id is required")
        try:
            if source_id:
                result = await repo_query(
                    "SELECT * FROM acm_record WHERE building_id = $building_id AND source_id = $source_id ORDER BY room_id",
                    {"building_id": building_id, "source_id": ensure_record_id(source_id)}
                )
            else:
                result = await repo_query(
                    "SELECT * FROM acm_record WHERE building_id = $building_id ORDER BY room_id",
                    {"building_id": building_id}
                )
            return [cls(**record) for record in result]
        except Exception as e:
            logger.error(f"Error fetching ACM records for building {building_id}: {e}")
            raise DatabaseOperationError(e)

    @classmethod
    async def get_by_risk_status(cls, risk_status: str, source_id: Optional[str] = None) -> List["ACMRecord"]:
        """Get all ACM records with a specific risk status."""
        if not risk_status:
            raise InvalidInputError("risk_status is required")
        try:
            if source_id:
                result = await repo_query(
                    "SELECT * FROM acm_record WHERE risk_status = $risk_status AND source_id = $source_id",
                    {"risk_status": risk_status, "source_id": ensure_record_id(source_id)}
                )
            else:
                result = await repo_query(
                    "SELECT * FROM acm_record WHERE risk_status = $risk_status",
                    {"risk_status": risk_status}
                )
            return [cls(**record) for record in result]
        except Exception as e:
            logger.error(f"Error fetching ACM records with risk status {risk_status}: {e}")
            raise DatabaseOperationError(e)

    @classmethod
    async def get_summary_by_source(cls, source_id: str) -> dict:
        """Get summary statistics for ACM records in a source."""
        if not source_id:
            raise InvalidInputError("source_id is required")
        try:
            result = await repo_query(
                """
                SELECT
                    count() as total_records,
                    count(risk_status = 'High' OR NULL) as high_risk_count,
                    count(risk_status = 'Medium' OR NULL) as medium_risk_count,
                    count(risk_status = 'Low' OR NULL) as low_risk_count,
                    array::distinct(building_id) as buildings,
                    array::distinct(room_id) as rooms
                FROM acm_record
                WHERE source_id = $source_id
                GROUP ALL
                """,
                {"source_id": ensure_record_id(source_id)}
            )
            if result:
                summary = result[0]
                return {
                    "total_records": summary.get("total_records", 0),
                    "high_risk_count": summary.get("high_risk_count", 0),
                    "medium_risk_count": summary.get("medium_risk_count", 0),
                    "low_risk_count": summary.get("low_risk_count", 0),
                    "building_count": len(summary.get("buildings", [])),
                    "room_count": len([r for r in summary.get("rooms", []) if r]),
                }
            return {
                "total_records": 0,
                "high_risk_count": 0,
                "medium_risk_count": 0,
                "low_risk_count": 0,
                "building_count": 0,
                "room_count": 0,
            }
        except Exception as e:
            logger.error(f"Error getting ACM summary for source {source_id}: {e}")
            raise DatabaseOperationError(e)

    @classmethod
    async def delete_by_source(cls, source_id: str) -> int:
        """Delete all ACM records for a source. Returns count of deleted records."""
        if not source_id:
            raise InvalidInputError("source_id is required")
        try:
            result = await repo_query(
                "DELETE acm_record WHERE source_id = $source_id RETURN BEFORE",
                {"source_id": ensure_record_id(source_id)}
            )
            return len(result) if result else 0
        except Exception as e:
            logger.error(f"Error deleting ACM records for source {source_id}: {e}")
            raise DatabaseOperationError(e)

    # Instance methods
    async def get_source(self) -> "Source":
        """Get the source document this record was extracted from."""
        from open_notebook.domain.notebook import Source
        return await Source.get(self.source_id)

    def _prepare_save_data(self) -> dict:
        """Override to ensure source_id is proper record format."""
        data = super()._prepare_save_data()
        if data.get("source_id"):
            data["source_id"] = ensure_record_id(data["source_id"])
        return data
```

### File: `tests/test_acm_domain.py`

```python
"""Unit tests for ACMRecord domain model."""

import pytest
from pydantic import ValidationError

from open_notebook.domain.acm import ACMRecord
from open_notebook.exceptions import InvalidInputError


class TestACMRecordValidation:
    """Test field validation."""

    def test_valid_record(self):
        """Test creating a valid ACM record."""
        record = ACMRecord(
            source_id="source:123",
            school_name="Test School",
            building_id="B1",
            product="Floor Tiles",
            material_description="Vinyl asbestos tiles",
            result="Detected"
        )
        assert record.school_name == "Test School"
        assert record.source_id == "source:123"

    def test_source_id_normalization(self):
        """Test that source_id without prefix gets normalized."""
        record = ACMRecord(
            source_id="123",  # Without prefix
            school_name="Test School",
            building_id="B1",
            product="Tiles",
            material_description="Vinyl tiles",
            result="Detected"
        )
        assert record.source_id == "source:123"

    def test_missing_required_field_school_name(self):
        """Test that missing school_name raises error."""
        with pytest.raises((ValidationError, InvalidInputError)):
            ACMRecord(
                source_id="source:123",
                school_name="",  # Empty
                building_id="B1",
                product="Tiles",
                material_description="Vinyl tiles",
                result="Detected"
            )

    def test_missing_required_field_building_id(self):
        """Test that missing building_id raises error."""
        with pytest.raises((ValidationError, InvalidInputError)):
            ACMRecord(
                source_id="source:123",
                school_name="Test School",
                building_id="",  # Empty
                product="Tiles",
                material_description="Vinyl tiles",
                result="Detected"
            )

    def test_optional_fields(self):
        """Test that optional fields default to None."""
        record = ACMRecord(
            source_id="source:123",
            school_name="Test School",
            building_id="B1",
            product="Tiles",
            material_description="Vinyl tiles",
            result="Detected"
        )
        assert record.room_id is None
        assert record.risk_status is None
        assert record.page_number is None

    def test_confidence_range(self):
        """Test extraction_confidence must be 0-1."""
        record = ACMRecord(
            source_id="source:123",
            school_name="Test School",
            building_id="B1",
            product="Tiles",
            material_description="Vinyl tiles",
            result="Detected",
            extraction_confidence=0.95
        )
        assert record.extraction_confidence == 0.95

        with pytest.raises(ValidationError):
            ACMRecord(
                source_id="source:123",
                school_name="Test School",
                building_id="B1",
                product="Tiles",
                material_description="Vinyl tiles",
                result="Detected",
                extraction_confidence=1.5  # Out of range
            )


class TestACMRecordTableName:
    """Test table name configuration."""

    def test_table_name(self):
        """Test that table_name is set correctly."""
        assert ACMRecord.table_name == "acm_record"
```

---

## Additional Context

### Dependencies

| Dependency | Type | Notes |
|------------|------|-------|
| E1-S1 (ACM Data Model) | Story | Must be complete (migration applied) |
| ObjectModel | Code | Base class in `domain/base.py` |
| repo_query | Code | Database query utility |
| ensure_record_id | Code | ID normalization utility |

### Testing Strategy

1. **Unit Tests** (`tests/test_acm_domain.py`):
   - Field validation
   - Type checking
   - Model instantiation

2. **Integration Tests** (manual or later story):
   - Create, read, update, delete operations
   - Query methods with real database
   - Source relationship

### Notes

1. **No Embedding Needed**: Unlike Note/Source, ACM records don't need vector embeddings since they're structured data queried via filters/SQL rather than semantic search.

2. **source_id Handling**: The `source_id` field stores a SurrealDB record reference (`record<source>`). The validator ensures consistent formatting.

3. **Bulk Operations**: The `delete_by_source` method enables cleanup when a source is re-processed or deleted.

4. **Summary Statistics**: The `get_summary_by_source` method provides quick risk analysis for dashboards.

---

## Next Stories After This

| Story | Description | Depends On |
|-------|-------------|------------|
| E1-S3 | Implement ACM Extraction Transformation | This story |
| E1-S4 | Create ACM API Endpoints | This story |

---

*Tech-Spec generated by create-tech-spec workflow*
