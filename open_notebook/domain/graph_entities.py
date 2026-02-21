"""Knowledge Graph Entity Models

Entity and relation models for the ACM knowledge graph:
school -> building -> room -> acm_record

Story: E13-S1 Knowledge Graph Schema
"""

from typing import ClassVar, Optional

from open_notebook.domain.base import ObjectModel


class School(ObjectModel):
    """School entity in the knowledge graph."""

    table_name: ClassVar[str] = "school"

    school_code: str
    name: Optional[str] = None
    address: Optional[str] = None
    region: Optional[str] = None


class Building(ObjectModel):
    """Building entity in the knowledge graph."""

    table_name: ClassVar[str] = "building"

    school_code: str
    building_code: str
    building_name: Optional[str] = None
    year_built: Optional[str] = None


class Room(ObjectModel):
    """Room entity in the knowledge graph."""

    table_name: ClassVar[str] = "room"

    school_code: str
    building_code: str
    room_code: str
    room_name: Optional[str] = None
    floor_level: Optional[str] = None
