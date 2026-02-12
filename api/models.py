from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


# Notebook models
class NotebookCreate(BaseModel):
    name: str = Field(..., description="Name of the notebook")
    description: str = Field(default="", description="Description of the notebook")


class NotebookUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Name of the notebook")
    description: Optional[str] = Field(None, description="Description of the notebook")
    archived: Optional[bool] = Field(
        None, description="Whether the notebook is archived"
    )


class NotebookResponse(BaseModel):
    id: str
    name: str
    description: str
    archived: bool
    created: str
    updated: str
    source_count: int
    note_count: int


# Search models
class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    type: Literal["text", "vector"] = Field("text", description="Search type")
    limit: int = Field(100, description="Maximum number of results", le=1000)
    search_sources: bool = Field(True, description="Include sources in search")
    search_notes: bool = Field(True, description="Include notes in search")
    minimum_score: float = Field(
        0.2, description="Minimum score for vector search", ge=0, le=1
    )


class SearchResponse(BaseModel):
    results: List[Dict[str, Any]] = Field(..., description="Search results")
    total_count: int = Field(..., description="Total number of results")
    search_type: str = Field(..., description="Type of search performed")


class AskRequest(BaseModel):
    question: str = Field(..., description="Question to ask the knowledge base")
    strategy_model: str = Field(..., description="Model ID for query strategy")
    answer_model: str = Field(..., description="Model ID for individual answers")
    final_answer_model: str = Field(..., description="Model ID for final answer")


class AskResponse(BaseModel):
    answer: str = Field(..., description="Final answer from the knowledge base")
    question: str = Field(..., description="Original question")


# Models API models
class ModelCreate(BaseModel):
    name: str = Field(..., description="Model name (e.g., gpt-5-mini, claude, gemini)")
    provider: str = Field(
        ..., description="Provider name (e.g., openai, anthropic, gemini)"
    )
    type: str = Field(
        ...,
        description="Model type (language, embedding, text_to_speech, speech_to_text)",
    )


class ModelResponse(BaseModel):
    id: str
    name: str
    provider: str
    type: str
    created: str
    updated: str


class DefaultModelsResponse(BaseModel):
    default_chat_model: Optional[str] = None
    default_transformation_model: Optional[str] = None
    large_context_model: Optional[str] = None
    default_text_to_speech_model: Optional[str] = None
    default_speech_to_text_model: Optional[str] = None
    default_embedding_model: Optional[str] = None
    default_tools_model: Optional[str] = None
    default_extraction_model: Optional[str] = None  # ACM extraction model


class ProviderAvailabilityResponse(BaseModel):
    available: List[str] = Field(..., description="List of available providers")
    unavailable: List[str] = Field(..., description="List of unavailable providers")
    supported_types: Dict[str, List[str]] = Field(
        ..., description="Provider to supported model types mapping"
    )


# Transformations API models
class TransformationCreate(BaseModel):
    name: str = Field(..., description="Transformation name")
    title: str = Field(..., description="Display title for the transformation")
    description: str = Field(
        ..., description="Description of what this transformation does"
    )
    prompt: str = Field(..., description="The transformation prompt")
    apply_default: bool = Field(
        False, description="Whether to apply this transformation by default"
    )


class TransformationUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Transformation name")
    title: Optional[str] = Field(
        None, description="Display title for the transformation"
    )
    description: Optional[str] = Field(
        None, description="Description of what this transformation does"
    )
    prompt: Optional[str] = Field(None, description="The transformation prompt")
    apply_default: Optional[bool] = Field(
        None, description="Whether to apply this transformation by default"
    )


class TransformationResponse(BaseModel):
    id: str
    name: str
    title: str
    description: str
    prompt: str
    apply_default: bool
    created: str
    updated: str


class TransformationExecuteRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    transformation_id: str = Field(
        ..., description="ID of the transformation to execute"
    )
    input_text: str = Field(..., description="Text to transform")
    model_id: str = Field(..., description="Model ID to use for the transformation")


class TransformationExecuteResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    output: str = Field(..., description="Transformed text")
    transformation_id: str = Field(..., description="ID of the transformation used")
    model_id: str = Field(..., description="Model ID used")


# Default Prompt API models
class DefaultPromptResponse(BaseModel):
    transformation_instructions: str = Field(
        ..., description="Default transformation instructions"
    )


class DefaultPromptUpdate(BaseModel):
    transformation_instructions: str = Field(
        ..., description="Default transformation instructions"
    )


# Notes API models
class NoteCreate(BaseModel):
    title: Optional[str] = Field(None, description="Note title")
    content: str = Field(..., description="Note content")
    note_type: Optional[str] = Field("human", description="Type of note (human, ai)")
    notebook_id: Optional[str] = Field(
        None, description="Notebook ID to add the note to"
    )


class NoteUpdate(BaseModel):
    title: Optional[str] = Field(None, description="Note title")
    content: Optional[str] = Field(None, description="Note content")
    note_type: Optional[str] = Field(None, description="Type of note (human, ai)")


class NoteResponse(BaseModel):
    id: str
    title: Optional[str]
    content: Optional[str]
    note_type: Optional[str]
    created: str
    updated: str


# Embedding API models
class EmbedRequest(BaseModel):
    item_id: str = Field(..., description="ID of the item to embed")
    item_type: str = Field(..., description="Type of item (source, note)")
    async_processing: bool = Field(
        False, description="Process asynchronously in background"
    )


class EmbedResponse(BaseModel):
    success: bool = Field(..., description="Whether embedding was successful")
    message: str = Field(..., description="Result message")
    item_id: str = Field(..., description="ID of the item that was embedded")
    item_type: str = Field(..., description="Type of item that was embedded")
    command_id: Optional[str] = Field(
        None, description="Command ID for async processing"
    )


# Rebuild request/response models
class RebuildRequest(BaseModel):
    mode: Literal["existing", "all"] = Field(
        ...,
        description="Rebuild mode: 'existing' only re-embeds items with embeddings, 'all' embeds everything",
    )
    include_sources: bool = Field(True, description="Include sources in rebuild")
    include_notes: bool = Field(True, description="Include notes in rebuild")
    include_insights: bool = Field(True, description="Include insights in rebuild")


class RebuildResponse(BaseModel):
    command_id: str = Field(..., description="Command ID to track progress")
    total_items: int = Field(..., description="Estimated number of items to process")
    message: str = Field(..., description="Status message")


class RebuildProgress(BaseModel):
    processed: int = Field(..., description="Number of items processed")
    total: int = Field(..., description="Total items to process")
    percentage: float = Field(..., description="Progress percentage")


class RebuildStats(BaseModel):
    sources: int = Field(0, description="Sources processed")
    notes: int = Field(0, description="Notes processed")
    insights: int = Field(0, description="Insights processed")
    failed: int = Field(0, description="Failed items")


class RebuildStatusResponse(BaseModel):
    command_id: str = Field(..., description="Command ID")
    status: str = Field(..., description="Status: queued, running, completed, failed")
    progress: Optional[RebuildProgress] = None
    stats: Optional[RebuildStats] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None


# Settings API models
class SettingsResponse(BaseModel):
    default_content_processing_engine_doc: Optional[str] = None
    default_content_processing_engine_url: Optional[str] = None
    default_embedding_option: Optional[str] = None
    auto_delete_files: Optional[str] = None
    youtube_preferred_languages: Optional[List[str]] = None


class SettingsUpdate(BaseModel):
    default_content_processing_engine_doc: Optional[str] = None
    default_content_processing_engine_url: Optional[str] = None
    default_embedding_option: Optional[str] = None
    auto_delete_files: Optional[str] = None
    youtube_preferred_languages: Optional[List[str]] = None


# Sources API models
class AssetModel(BaseModel):
    file_path: Optional[str] = None
    url: Optional[str] = None


class SourceCreate(BaseModel):
    # Backward compatibility: support old single notebook_id
    notebook_id: Optional[str] = Field(
        None, description="Notebook ID to add the source to (deprecated, use notebooks)"
    )
    # New multi-notebook support
    notebooks: Optional[List[str]] = Field(
        None, description="List of notebook IDs to add the source to"
    )
    # Required fields
    type: str = Field(..., description="Source type: link, upload, or text")
    url: Optional[str] = Field(None, description="URL for link type")
    file_path: Optional[str] = Field(None, description="File path for upload type")
    content: Optional[str] = Field(None, description="Text content for text type")
    title: Optional[str] = Field(None, description="Source title")
    transformations: Optional[List[str]] = Field(
        default_factory=list, description="Transformation IDs to apply"
    )
    embed: bool = Field(False, description="Whether to embed content for vector search")
    delete_source: bool = Field(
        False, description="Whether to delete uploaded file after processing"
    )
    # New async processing support
    async_processing: bool = Field(
        False, description="Whether to process source asynchronously"
    )

    @model_validator(mode="after")
    def validate_notebook_fields(self):
        # Ensure only one of notebook_id or notebooks is provided
        if self.notebook_id is not None and self.notebooks is not None:
            raise ValueError(
                "Cannot specify both 'notebook_id' and 'notebooks'. Use 'notebooks' for multi-notebook support."
            )

        # Convert single notebook_id to notebooks array for internal processing
        if self.notebook_id is not None:
            self.notebooks = [self.notebook_id]
            # Keep notebook_id for backward compatibility in response

        # Set empty array if no notebooks specified (allow sources without notebooks)
        if self.notebooks is None:
            self.notebooks = []

        return self


class SourceUpdate(BaseModel):
    title: Optional[str] = Field(None, description="Source title")
    topics: Optional[List[str]] = Field(None, description="Source topics")


class SourceResponse(BaseModel):
    id: str
    title: Optional[str]
    topics: Optional[List[str]]
    asset: Optional[AssetModel]
    full_text: Optional[str]
    embedded: bool
    embedded_chunks: int
    file_available: Optional[bool] = None
    created: str
    updated: str
    # New fields for async processing
    command_id: Optional[str] = None
    status: Optional[str] = None
    processing_info: Optional[Dict] = None
    # Notebook associations
    notebooks: Optional[List[str]] = None


class SourceListResponse(BaseModel):
    id: str
    title: Optional[str]
    topics: Optional[List[str]]
    asset: Optional[AssetModel]
    embedded: bool  # Boolean flag indicating if source has embeddings
    embedded_chunks: int  # Number of embedded chunks
    insights_count: int
    created: str
    updated: str
    file_available: Optional[bool] = None
    # Status fields for async processing
    command_id: Optional[str] = None
    status: Optional[str] = None
    processing_info: Optional[Dict[str, Any]] = None


# Context API models
class ContextConfig(BaseModel):
    sources: Dict[str, str] = Field(
        default_factory=dict, description="Source inclusion config {source_id: level}"
    )
    notes: Dict[str, str] = Field(
        default_factory=dict, description="Note inclusion config {note_id: level}"
    )


class ContextRequest(BaseModel):
    notebook_id: str = Field(..., description="Notebook ID to get context for")
    context_config: Optional[ContextConfig] = Field(
        None, description="Context configuration"
    )


class ContextResponse(BaseModel):
    notebook_id: str
    sources: List[Dict[str, Any]] = Field(..., description="Source context data")
    notes: List[Dict[str, Any]] = Field(..., description="Note context data")
    total_tokens: Optional[int] = Field(None, description="Estimated token count")


# Insights API models
class SourceInsightResponse(BaseModel):
    id: str
    source_id: str
    insight_type: str
    content: str
    created: str
    updated: str


class SaveAsNoteRequest(BaseModel):
    notebook_id: Optional[str] = Field(None, description="Notebook ID to add note to")


class CreateSourceInsightRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    transformation_id: str = Field(..., description="ID of transformation to apply")
    model_id: Optional[str] = Field(
        None, description="Model ID (uses default if not provided)"
    )


# Source status response
class SourceStatusResponse(BaseModel):
    status: Optional[str] = Field(None, description="Processing status")
    message: str = Field(..., description="Descriptive message about the status")
    processing_info: Optional[Dict[str, Any]] = Field(
        None, description="Detailed processing information"
    )
    command_id: Optional[str] = Field(None, description="Command ID if available")


# Error response
class ErrorResponse(BaseModel):
    error: str
    message: str


# ACM API Models
class ACMRecordResponse(BaseModel):
    """Single ACM record response."""

    id: str
    source_id: str
    school_name: str
    school_code: Optional[str] = None
    building_id: str
    building_name: Optional[str] = None
    building_year: Optional[int] = None
    building_construction: Optional[str] = None
    room_id: Optional[str] = None
    room_name: Optional[str] = None
    room_area: Optional[float] = None
    area_type: Optional[str] = None
    product: str
    material_description: str
    extent: Optional[str] = None
    location: Optional[str] = None
    friable: Optional[str] = None
    material_condition: Optional[str] = None
    risk_status: Optional[str] = None
    result: str
    page_number: Optional[int] = None
    extraction_confidence: Optional[str] = None  # "high", "medium", "low"
    # Classification fields (E1-S9 - Victorian BAR taxonomy)
    acm_product_group: Optional[str] = None
    acm_product_type: Optional[str] = None
    classification_confidence: Optional[float] = None
    classification_method: Optional[str] = None
    classification_override: Optional[bool] = None
    created: Optional[str] = None
    updated: Optional[str] = None


class ACMRecordListResponse(BaseModel):
    """Paginated list of ACM records."""

    records: List[ACMRecordResponse]
    total: int
    page: int
    pages: int
    limit: int


class ACMExtractRequest(BaseModel):
    """Request to trigger ACM extraction."""

    source_id: str = Field(..., description="Source ID to extract ACM data from")
    force: bool = Field(default=False, description="Delete existing records before re-extraction")


class ACMExtractResponse(BaseModel):
    """Response from extraction trigger."""

    command_id: str = Field(..., description="Command ID to track progress")
    status: str = Field(default="submitted", description="Initial status")
    message: str = Field(default="ACM extraction started")


class ACMStatsResponse(BaseModel):
    """ACM statistics summary."""

    total_records: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    building_count: int
    room_count: int
    source_id: Optional[str] = None


class ACMRecordCreateRequest(BaseModel):
    """Request to create a new ACM record."""

    source_id: str = Field(..., description="Source document ID")
    school_name: str = Field(..., min_length=1, description="School name")
    school_code: Optional[str] = Field(None, description="School code")
    building_id: str = Field(..., min_length=1, description="Building ID")
    building_name: Optional[str] = Field(None, description="Building name")
    building_year: Optional[int] = Field(None, description="Building year")
    building_construction: Optional[str] = Field(None, description="Construction type")
    room_id: Optional[str] = Field(None, description="Room ID")
    room_name: Optional[str] = Field(None, description="Room name")
    room_area: Optional[float] = Field(None, description="Room area in m²")
    area_type: Optional[str] = Field(
        None, description="Area type: Interior/Exterior/Grounds"
    )
    product: str = Field(..., min_length=1, description="ACM product name")
    material_description: str = Field(
        ..., min_length=1, description="Material description"
    )
    extent: Optional[str] = Field(None, description="Extent of ACM")
    location: Optional[str] = Field(None, description="Location within room")
    friable: Optional[str] = Field(None, description="Friable/Non Friable")
    material_condition: Optional[str] = Field(None, description="Material condition")
    risk_status: Optional[str] = Field(None, description="Risk status: Low/Medium/High")
    result: str = Field(..., min_length=1, description="Test result")
    page_number: Optional[int] = Field(None, description="Source page number")


class ParentContextResponse(BaseModel):
    """Parent table section context for search results (E11-S1)."""

    id: str
    building_name: Optional[str] = None
    page_start: int
    page_end: int
    table_type: Optional[str] = None
    raw_text: Optional[str] = None


class ACMSearchResultResponse(BaseModel):
    """Single ACM search result with similarity score."""

    id: str
    source_id: str
    school_name: str
    building_id: str
    building_name: Optional[str] = None
    room_id: Optional[str] = None
    room_name: Optional[str] = None
    product: str
    material_description: str
    extent: Optional[str] = None
    location: Optional[str] = None
    material_condition: Optional[str] = None
    risk_status: Optional[str] = None
    result: str
    score: float = Field(..., description="Semantic similarity score (0-1)")
    parent_context: Optional[ParentContextResponse] = Field(
        None, description="Parent table section context (when include_parent=true)"
    )


class ACMSearchResponse(BaseModel):
    """Semantic search results response."""

    query: str
    results: List[ACMSearchResultResponse]
    total: int


class ACMRecordUpdateRequest(BaseModel):
    """Request to update an ACM record. All fields optional for partial updates."""

    school_name: Optional[str] = Field(None, min_length=1, description="School name")
    school_code: Optional[str] = Field(None, description="School code")
    building_id: Optional[str] = Field(None, min_length=1, description="Building ID")
    building_name: Optional[str] = Field(None, description="Building name")
    building_year: Optional[int] = Field(None, description="Building year")
    building_construction: Optional[str] = Field(None, description="Construction type")
    room_id: Optional[str] = Field(None, description="Room ID")
    room_name: Optional[str] = Field(None, description="Room name")
    room_area: Optional[float] = Field(None, description="Room area in m²")
    area_type: Optional[str] = Field(
        None, description="Area type: Interior/Exterior/Grounds"
    )
    product: Optional[str] = Field(None, min_length=1, description="ACM product name")
    material_description: Optional[str] = Field(
        None, min_length=1, description="Material description"
    )
    extent: Optional[str] = Field(None, description="Extent of ACM")
    location: Optional[str] = Field(None, description="Location within room")
    friable: Optional[str] = Field(None, description="Friable/Non Friable")
    material_condition: Optional[str] = Field(None, description="Material condition")
    risk_status: Optional[str] = Field(None, description="Risk status: Low/Medium/High")
    result: Optional[str] = Field(None, min_length=1, description="Test result")
    page_number: Optional[int] = Field(None, description="Source page number")

    # Classification fields (E1-S9 - Victorian BAR taxonomy)
    acm_product_group: Optional[str] = Field(
        None, description="BAR taxonomy product group"
    )
    acm_product_type: Optional[str] = Field(
        None, description="BAR taxonomy product type"
    )
    classification_override: Optional[bool] = Field(
        None,
        description="Mark as manual override (set to True when user corrects classification)",
    )


# Site Configuration Models (E1-S8 - Victorian BAR Compliance)
class SiteConfigRequest(BaseModel):
    """Request to create or update site configuration."""

    source_id: str = Field(..., description="Source document ID")
    department: Optional[str] = Field(
        None, description="Victorian Government department"
    )
    agency: Optional[str] = Field(None, description="Agency within department")
    building_type: Optional[str] = Field(None, description="Type of building")
    owned_or_leased: Optional[str] = Field(None, description="Ownership status")
    frequency_of_use: Optional[str] = Field(
        None, description="How frequently building is used"
    )
    public_access: Optional[str] = Field(
        None, description="Whether public has access (YES/NO)"
    )
    building_unique_id: Optional[str] = Field(
        None, description="Unique building identifier"
    )


class SiteConfigResponse(BaseModel):
    """Site configuration response."""

    id: Optional[str] = None
    source_id: str
    department: Optional[str] = None
    agency: Optional[str] = None
    building_type: Optional[str] = None
    owned_or_leased: Optional[str] = None
    frequency_of_use: Optional[str] = None
    public_access: Optional[str] = None
    building_unique_id: Optional[str] = None
    missing_fields: List[str] = Field(
        default_factory=list, description="BAR fields not yet filled"
    )
    is_bar_complete: bool = Field(
        default=False, description="Whether all BAR fields are filled"
    )
    created: Optional[str] = None
    updated: Optional[str] = None


class SiteConfigTemplateResponse(BaseModel):
    """Site configuration template for reuse."""

    source_id: str
    source_title: Optional[str] = None
    department: Optional[str] = None
    agency: Optional[str] = None
    building_type: Optional[str] = None
    owned_or_leased: Optional[str] = None
    frequency_of_use: Optional[str] = None
    public_access: Optional[str] = None


class ApplyTemplateRequest(BaseModel):
    """Request to apply a template configuration."""

    source_id: str = Field(..., description="Target source document ID")
    template_source_id: str = Field(..., description="Source ID to copy config from")


class AgencyListResponse(BaseModel):
    """List of agencies for autocomplete."""

    agencies: List[str]


# =============================================================================
# ACM Product Classification Models (E1-S9 - Victorian BAR Taxonomy)
# =============================================================================


class ClassifyRequest(BaseModel):
    """Request to classify an ACM item into taxonomy."""

    item_description: str = Field(..., min_length=1, description="ACM item description")
    friability: Optional[Literal["Friable", "Non-friable"]] = Field(
        None, description="Friability status (optional, defaults to Non-friable)"
    )
    product: Optional[str] = Field(
        None, description="Optional product field to improve classification"
    )
    use_llm_fallback: bool = Field(
        True, description="Use LLM for classification if pattern matching fails"
    )


class ClassifyResponse(BaseModel):
    """Response from classification request."""

    product_group: Optional[str] = Field(
        None, description="BAR taxonomy product group (e.g., 'T3 Vinyl products')"
    )
    product_type: Optional[str] = Field(
        None, description="BAR taxonomy product type (e.g., 'Vinyl Tiles')"
    )
    confidence: float = Field(
        ..., description="Classification confidence score (0.0-1.0)"
    )
    method: Literal["pattern", "llm", "none"] = Field(
        ..., description="Classification method used"
    )


class BatchClassifyRequest(BaseModel):
    """Request to classify all ACM records for a source."""

    source_id: str = Field(..., description="Source document ID")
    use_llm_fallback: bool = Field(
        True, description="Use LLM for classification if pattern matching fails"
    )
    skip_classified: bool = Field(
        True, description="Skip records that already have classification"
    )


class BatchClassifyResponse(BaseModel):
    """Response from batch classification request."""

    total: int = Field(..., description="Total records processed")
    classified: int = Field(..., description="Records successfully classified")
    skipped: int = Field(
        ..., description="Records skipped (already classified or no match)"
    )
    errors: int = Field(..., description="Records that failed classification")
    results: List[Dict[str, Any]] = Field(
        default_factory=list, description="Individual classification results"
    )


class NormalizeRequest(BaseModel):
    """Request to normalize a consultant recommendation."""

    recommendation: str = Field(
        ..., min_length=1, description="Raw consultant recommendation text"
    )


class NormalizeResponse(BaseModel):
    """Response from recommendation normalization."""

    raw_text: str = Field(..., description="Original input text")
    normalized_action: Optional[str] = Field(
        None,
        description="Canonical action (e.g., 'maintain_in_situ', 'review_required')",
    )
    confidence: float = Field(
        ..., description="Normalization confidence score (0.0-1.0)"
    )
    method: Literal["pattern", "config", "none"] = Field(
        ..., description="Normalization method used"
    )


class TaxonomyGroupResponse(BaseModel):
    """Response for taxonomy product group."""

    pc_code: str = Field(..., description="Product code (e.g., 'T1', 'T2')")
    product_group_header: str = Field(..., description="Full product group name")
    product_types: List[str] = Field(
        ..., description="Available product types in this group"
    )


class TaxonomyResponse(BaseModel):
    """Response for full taxonomy listing."""

    friability: str = Field(
        ..., description="Taxonomy type: 'Friable' or 'Non-friable'"
    )
    groups: List[TaxonomyGroupResponse] = Field(
        ..., description="Product groups in taxonomy"
    )


# =============================================================================
# Field Schema Config Models (E1-S11 - Generic Configurable Parser)
# =============================================================================


class FieldDefResponse(BaseModel):
    """Single BAR field definition."""

    internal_name: str = Field(..., description="Snake_case field name")
    display_name: str = Field(..., description="BAR column header display name")
    excel_column: str = Field(..., description="Excel column letter")
    col_index: int = Field(..., description="1-based position in BAR spreadsheet")
    field_type: str = Field(..., description="Field type: string, number, date, enum")
    required: bool = Field(..., description="Whether field is required by BAR")
    active: bool = Field(True, description="Whether field is active for extraction")
    enum_name: Optional[str] = Field(None, description="Key into enums dict")
    group: Optional[str] = Field(None, description="UI grouping category")


class BusinessRuleResponse(BaseModel):
    """BAR business rule."""

    rule_id: str = Field(..., description="Rule identifier")
    description: str = Field(..., description="Human-readable description")
    enabled: bool = Field(True, description="Whether rule is active")


class FieldSchemaConfigResponse(BaseModel):
    """Full field schema configuration response."""

    fields: List[FieldDefResponse] = Field(
        ..., description="All 47 BAR field definitions"
    )
    enums: Dict[str, List[str]] = Field(..., description="Enum picklist definitions")
    business_rules: List[BusinessRuleResponse] = Field(
        ..., description="BAR business rules"
    )
    version: str = Field(..., description="Schema version")
    source_template: Optional[str] = Field(None, description="Source BAR template name")


class FieldSchemaConfigUpdateRequest(BaseModel):
    """Request to update field schema configuration."""

    fields: List[FieldDefResponse] = Field(..., description="Updated field definitions")
    enums: Dict[str, List[str]] = Field(..., description="Enum picklist definitions")
    business_rules: List[BusinessRuleResponse] = Field(
        ..., description="BAR business rules"
    )
    version: str = Field(..., description="Schema version")
    source_template: Optional[str] = Field(None, description="Source BAR template name")

    @model_validator(mode="after")
    def validate_field_config(self):
        # Check internal_name uniqueness
        names = [f.internal_name for f in self.fields]
        if len(names) != len(set(names)):
            raise ValueError("Field internal_name values must be unique")
        # Check field_type values
        allowed_types = {"string", "number", "date", "enum"}
        for f in self.fields:
            if f.field_type not in allowed_types:
                raise ValueError(
                    f"Invalid field_type '{f.field_type}' for field '{f.internal_name}'"
                )
        return self


class ReEmbedRequest(BaseModel):
    """Request to re-embed ACM records with contextual enrichment (E1-S14)."""

    source_id: Optional[str] = Field(None, description="Optional source ID filter")
    force: bool = Field(
        False, description="Re-embed all records even if already embedded"
    )


class ReEmbedResponse(BaseModel):
    """Response from re-embedding request."""

    success: bool = Field(
        ..., description="Whether re-embedding completed successfully"
    )
    records_processed: int = Field(..., description="Number of records processed")
    message: str = Field(..., description="Status message")


class BackfillParentsRequest(BaseModel):
    """Request to backfill parent_table_id for existing records (E11-S1)."""

    source_id: Optional[str] = Field(None, description="Optional source ID filter")


class BackfillParentsResponse(BaseModel):
    """Response from backfill parents operation."""

    records_updated: int = Field(..., description="Number of records linked to parents")
    message: str = Field(..., description="Status message")
