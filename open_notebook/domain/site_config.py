"""
Site Configuration Domain Model

Stores non-extractable metadata required for Victorian BAR exports.
Each source document can have one site configuration containing
organizational and building classification data.

Story: E1-S8 Site Configuration Data Entry
"""

from enum import Enum
from typing import ClassVar, List, Optional

from loguru import logger
from pydantic import Field

from open_notebook.database.repository import ensure_record_id, repo_query
from open_notebook.domain.base import ObjectModel
from open_notebook.exceptions import DatabaseOperationError


class Department(str, Enum):
    """
    Victorian Government departments.

    Note: These enums are defined for reference/documentation purposes.
    Fields are typed as Optional[str] rather than enum types because:
    1. BAR validation is intentionally non-blocking per AC5
    2. Users may need to enter custom values not in predefined list
    3. Frontend provides dropdown options from matching constants
    """

    DJCS = "DJCS"  # Department of Justice and Community Safety
    DHHS = "DHHS"  # Department of Health and Human Services
    DET = "DET"  # Department of Education and Training
    DOT = "DOT"  # Department of Transport
    DJPR = "DJPR"  # Department of Jobs, Precincts and Regions
    OTHER = "Other"


class BuildingType(str, Enum):
    """Building type classifications."""

    POLICE_STATION = "Police Station"
    HOSPITAL = "Hospital"
    SCHOOL = "School"
    OFFICE = "Office"
    RESIDENTIAL = "Residential"
    INDUSTRIAL = "Industrial"
    OTHER = "Other"


class Ownership(str, Enum):
    """Building ownership status."""

    OWNED = "Owned"
    LEASED = "Leased"


class FrequencyOfUse(str, Enum):
    """How frequently the building is used (BAR exact wording)."""

    EVERY_DAY = "Every day"
    EVERY_DAY_INTERMITTENT = "Every day with intermittent breaks"
    EVERY_3_5_DAYS = "Once every 3-5 days"
    EVERY_2_3_WEEKS = "Every 2-3 weeks"
    EVERY_2_3_MONTHS = "Once every 2-3 months"
    ANNUALLY_OR_LESS = "Annually or less frequently"


class PublicAccess(str, Enum):
    """Whether the building has public access."""

    YES = "YES"
    NO = "NO"


class SiteConfig(ObjectModel):
    """
    Site configuration for Victorian BAR compliance.

    Stores metadata that cannot be extracted from consultant PDFs
    but is required for BAR exports.
    """

    table_name: ClassVar[str] = "site_config"

    # Foreign key to source document
    source_id: str = Field(description="Reference to source document")

    # Victorian Government organizational fields
    department: Optional[str] = Field(
        default=None,
        description="Victorian Government department (DJCS, DHHS, DET, DOT, DJPR, Other)",
    )
    agency: Optional[str] = Field(
        default=None,
        description="Agency within department (e.g., Victoria Police, District Health)",
    )

    # Building classification fields
    building_type: Optional[str] = Field(
        default=None,
        description="Type of building (Police Station, Hospital, School, etc.)",
    )
    owned_or_leased: Optional[str] = Field(
        default=None, description="Ownership status (Owned or Leased)"
    )
    frequency_of_use: Optional[str] = Field(
        default=None, description="How frequently the building is used"
    )
    public_access: Optional[str] = Field(
        default=None, description="Whether public has access (YES or NO)"
    )
    building_unique_id: Optional[str] = Field(
        default=None, description="Unique identifier for the building"
    )

    @classmethod
    async def get_by_source(cls, source_id: str) -> Optional["SiteConfig"]:
        """
        Get site configuration for a specific source document.

        Args:
            source_id: The source document ID

        Returns:
            SiteConfig if found, None otherwise
        """
        try:
            query = (
                f"SELECT * FROM {cls.table_name} WHERE source_id = $source_id LIMIT 1;"
            )
            result = await repo_query(query, {"source_id": ensure_record_id(source_id)})

            if result and len(result) > 0:
                return cls(**result[0])
            return None

        except Exception as e:
            logger.error(f"Error fetching site config for source {source_id}: {e}")
            raise DatabaseOperationError(f"Failed to fetch site config: {e}")

    @classmethod
    async def get_templates(cls, limit: int = 20) -> List[dict]:
        """
        Get distinct site configurations to use as templates.

        Groups by department/agency combination and returns the most
        recently updated config for each group.

        Returns:
            List of template configurations with source info
        """
        try:
            query = """
                SELECT
                    source_id,
                    source.title as source_title,
                    department,
                    agency,
                    building_type,
                    owned_or_leased,
                    frequency_of_use,
                    public_access,
                    updated
                FROM site_config
                WHERE department != NONE OR agency != NONE
                ORDER BY updated DESC
                LIMIT $limit;
            """
            result = await repo_query(query, {"limit": limit})
            return result if result else []

        except Exception as e:
            logger.error(f"Error fetching site config templates: {e}")
            raise DatabaseOperationError(f"Failed to fetch templates: {e}")

    @classmethod
    async def get_agencies(cls, department: Optional[str] = None) -> List[str]:
        """
        Get distinct agency values for autocomplete.

        Args:
            department: Optional department filter

        Returns:
            List of unique agency names
        """
        try:
            if department:
                query = """
                    SELECT DISTINCT agency
                    FROM site_config
                    WHERE agency != NONE AND department = $department
                    ORDER BY agency;
                """
                result = await repo_query(query, {"department": department})
            else:
                query = """
                    SELECT DISTINCT agency
                    FROM site_config
                    WHERE agency != NONE
                    ORDER BY agency;
                """
                result = await repo_query(query)

            return [r["agency"] for r in result if r.get("agency")]

        except Exception as e:
            logger.error(f"Error fetching agencies: {e}")
            return []

    @classmethod
    async def upsert(cls, source_id: str, **kwargs) -> "SiteConfig":
        """
        Create or update site configuration for a source.

        Args:
            source_id: The source document ID
            **kwargs: Configuration fields to set

        Returns:
            The created or updated SiteConfig
        """
        try:
            existing = await cls.get_by_source(source_id)

            if existing:
                # Update existing config
                for key, value in kwargs.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
                await existing.save()
                return existing
            else:
                # Create new config
                config = cls(source_id=source_id, **kwargs)
                await config.save()
                return config

        except Exception as e:
            logger.error(f"Error upserting site config for {source_id}: {e}")
            raise DatabaseOperationError(f"Failed to save site config: {e}")

    def _prepare_save_data(self) -> dict:
        """Override to ensure source_id is proper record format (TYPE record<source>)."""
        data = super()._prepare_save_data()
        if data.get("source_id"):
            data["source_id"] = ensure_record_id(data["source_id"])
        return data

    def get_missing_bar_fields(self) -> List[str]:
        """
        Get list of BAR-required fields that are not filled.

        Returns:
            List of field names that are missing
        """
        required_fields = [
            ("department", self.department),
            ("agency", self.agency),
            ("building_type", self.building_type),
            ("owned_or_leased", self.owned_or_leased),
            ("frequency_of_use", self.frequency_of_use),
            ("public_access", self.public_access),
        ]

        return [name for name, value in required_fields if not value]

    def is_bar_complete(self) -> bool:
        """Check if all BAR-required fields are filled."""
        return len(self.get_missing_bar_fields()) == 0
