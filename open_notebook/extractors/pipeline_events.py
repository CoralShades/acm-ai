"""Pydantic models for pipeline observability events.

These models serve as the source of truth for event schemas.
They are used by PipelineLogger for structured terminal logging
and will support future SSE streaming (AG-UI Pipeline Spec Section 11.5).

Story: E1-S21 Extraction Pipeline Observability & Structured Logging
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class StageId(str, Enum):
    """Pipeline stage identifiers matching AG-UI spec Stage Map."""

    STRUCTURE = "STRUCTURE"
    PREFLIGHT = "PREFLIGHT"
    ORCHESTRATOR = "ORCHESTRATOR"
    DOCLING_EXTRACTION = "DOCLING_EXTRACTION"
    EXTRACT = "EXTRACT"
    VALIDATE = "VALIDATE"
    CORRECT = "CORRECT"
    NO_ACCESS_RECOVERY = "NO_ACCESS_RECOVERY"
    STORE = "STORE"


class StageStatus(str, Enum):
    """Status of a pipeline stage."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"
    SKIPPED = "skipped"


class PipelineRunStatus(str, Enum):
    """Overall pipeline run status."""

    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


# Stage metadata constants
STAGE_METADATA: Dict[StageId, Dict[str, str]] = {
    StageId.STRUCTURE: {
        "name": "Document Structure Analysis",
        "description": "Extract metadata, document structure, building inventory, and page tags",
        "log_prefix": "STRUCTURE",
    },
    StageId.PREFLIGHT: {
        "name": "Preflight",
        "description": "Content preparation, chunking, and context assembly",
        "log_prefix": "PREFLIGHT",
    },
    StageId.ORCHESTRATOR: {
        "name": "Agentic Orchestrator",
        "description": "Plan extraction strategy per building section",
        "log_prefix": "ORCHESTRATOR",
    },
    StageId.DOCLING_EXTRACTION: {
        "name": "Docling Table Extraction",
        "description": "Extracting structured tables via Docling Direct Python API",
        "log_prefix": "DOCLING",
    },
    StageId.EXTRACT: {
        "name": "Extract",
        "description": "LLM extraction of ACM records from content chunks",
        "log_prefix": "EXTRACT",
    },
    StageId.VALIDATE: {
        "name": "Validate",
        "description": "Schema validation and business rule checks",
        "log_prefix": "VALIDATE",
    },
    StageId.CORRECT: {
        "name": "Corrective Validation",
        "description": "Auto-correction and LLM re-extraction for failed records",
        "log_prefix": "CORRECT",
    },
    StageId.NO_ACCESS_RECOVERY: {
        "name": "No-Access Record Recovery",
        "description": "Scanning for No Access/Not Sampled records missed by LLM extraction",
        "log_prefix": "RECOVERY",
    },
    StageId.STORE: {
        "name": "Enrich & Store",
        "description": "Save records, create parent sections, generate embeddings",
        "log_prefix": "STORE",
    },
}


class StageError(BaseModel):
    """Error information for a failed stage."""

    message: str
    code: str = "STAGE_ERROR"
    records_affected: int = 0


class StageState(BaseModel):
    """State of a single pipeline stage."""

    id: StageId
    status: StageStatus = StageStatus.PENDING
    entered_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    progress: float = 0.0
    message: Optional[str] = None
    record_count: Optional[int] = None
    metrics: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[StageError] = None


class PipelineRunState(BaseModel):
    """Full state of a pipeline run. Built incrementally by PipelineLogger."""

    run_id: str = ""
    source_id: str = ""
    status: PipelineRunStatus = PipelineRunStatus.IDLE
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_duration_ms: Optional[int] = None
    stages: Dict[str, StageState] = Field(default_factory=dict)

    # Summary metrics (populated at pipeline end)
    total_pages: int = 0
    total_chunks: int = 0
    total_buildings: int = 0
    total_records: int = 0
    records_rejected: int = 0
    records_unidentified: int = 0
    confidence_distribution: Dict[str, int] = Field(default_factory=dict)
    models_used: List[str] = Field(default_factory=list)
    strategy_distribution: Dict[str, int] = Field(default_factory=dict)

    def get_stage(self, stage_id: StageId) -> StageState:
        """Get or create a stage state."""
        key = stage_id.value
        if key not in self.stages:
            self.stages[key] = StageState(id=stage_id)
        return self.stages[key]


# --- SSE Event Models (for future streaming, used now for structured data) ---


class PipelineStartedEvent(BaseModel):
    """Emitted when the pipeline begins."""

    run_id: str
    source_id: str
    started_at: str
    total_pages: int = 0


class StageEnteredEvent(BaseModel):
    """Emitted when a pipeline stage begins."""

    run_id: str
    stage_id: StageId
    stage_name: str
    entered_at: str
    message: str = ""


class StageProgressEvent(BaseModel):
    """Emitted during a stage to report progress."""

    run_id: str
    stage_id: StageId
    progress: float
    message: str
    records_so_far: Optional[int] = None


class StageCompletedEvent(BaseModel):
    """Emitted when a stage completes successfully."""

    run_id: str
    stage_id: StageId
    completed_at: str
    duration_ms: int
    records_extracted: Optional[int] = None
    summary: str = ""


class StageFailedEvent(BaseModel):
    """Emitted when a stage fails."""

    run_id: str
    stage_id: StageId
    failed_at: str
    duration_ms: int
    error: str
    error_code: str = "STAGE_ERROR"
    records_affected: int = 0


class PipelineCompletedEvent(BaseModel):
    """Emitted when the pipeline completes."""

    run_id: str
    source_id: str
    completed_at: str
    total_duration_ms: int
    total_records: int
    records_rejected: int
    confidence_distribution: Dict[str, int] = Field(default_factory=dict)


def now_iso() -> str:
    """Return current UTC time as ISO string (for SSE event models)."""
    return datetime.now(timezone.utc).isoformat()


def now_utc() -> datetime:
    """Return current UTC datetime (for state models with datetime fields)."""
    return datetime.now(timezone.utc)
