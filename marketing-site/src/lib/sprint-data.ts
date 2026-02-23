export const velocityData = [
  { sprint: "S1", done: 4, target: 8 },
  { sprint: "S2", done: 7, target: 8 },
  { sprint: "S3", done: 9, target: 8 },
  { sprint: "S4", done: 10, target: 10 },
  { sprint: "S5", done: 8, target: 10 },
  { sprint: "S6", done: 11, target: 10 },
  { sprint: "S7", done: 12, target: 10 },
  { sprint: "S8", done: 10, target: 10 },
  { sprint: "S9", done: 11, target: 10 },
  { sprint: "S10", done: 14, target: 10 },
  { sprint: "S11", done: 11, target: 10 },
  { sprint: "S12", done: 5, target: 10 },
];

export const projectStats = {
  storiesDelivered: 121,
  totalStories: 131,
  epicsComplete: 19,
  totalEpics: 20,
  commits: 318,
  completionRate: 100,
  changeProposals: 5,
  extractionAccuracy: 87,
  barColumns: 47,
  featureComplete: "23 Feb 2026",
};

export const barColumns = [
  "Department", "Agency", "Sub Agency", "Site Name", "Building Name",
  "Building Type", "Building Address", "Suburb", "Postcode", "Owned or Leased",
  "Building Unique ID", "Frequency of Use", "Public Access?", "Date of Inspection",
  "Est. Year Built", "Est. Building Size (m\u00B2)", "Number of Levels",
  "Construction Type", "Roof Type", "Internal / External", "Level",
  "Room or Area", "Location in Room", "Specific Item / ACM Name",
  "Friability of Material", "ACM Product Group", "ACM Product Type",
  "NATA Sample Number", "Sample Result", "Identifying Hygiene Company",
  "Condition", "Disturbance Potential", "Quantity", "Labelled",
  "Label Details", "Hygienist Recommendations", "Additional Comments",
  "PSB Supplied ACM ID", "Assumed Removed?", "Date of Removal",
  "Quantity Removed", "Removal Notification No.", "EPA Waste Transport Cert No.",
  "Removal Comments", "Photo Reference Number",
];

export const techStack = [
  { layer: "Frontend", tech: "Next.js 15 + React", purpose: "Web UI + AG Grid spreadsheet" },
  { layer: "Backend", tech: "FastAPI (Python)", purpose: "REST API + SSE streaming" },
  { layer: "Database", tech: "SurrealDB", purpose: "Document + vector + graph store" },
  { layer: "AI Pipeline", tech: "LangGraph", purpose: "Agentic workflow orchestration" },
  { layer: "Extraction", tech: "MinerU + Docling", purpose: "PDF table extraction (ML-based)" },
  { layer: "AI/LLM", tech: "Esperanto", purpose: "Multi-provider: OpenAI, Anthropic, Ollama" },
  { layer: "Grid", tech: "AG Grid v35", purpose: "Enterprise spreadsheet component" },
  { layer: "Chat", tech: "CopilotKit + AG-UI", purpose: "SSE agent streaming protocol" },
  { layer: "Export", tech: "openpyxl", purpose: "BAR Excel generation" },
];

export const pipelineStages = [
  {
    id: -1,
    name: "PRE-ANALYSIS",
    desc: "TOC extraction, building inventory compilation, page-level section tagging, document metadata enhancement",
    tools: "LangGraph agentic orchestrator",
  },
  {
    id: 0,
    name: "PREFLIGHT",
    desc: "PDF classifier detects digital vs scanned. Parser router selects MinerU or Docling based on content type.",
    tools: "PDF Classifier \u2192 Parser Router",
  },
  {
    id: 0.5,
    name: "ORCHESTRATION",
    desc: "Agentic orchestrator routes each page section to optimal extraction tool. MinerU for complex tables, Docling for text/layout.",
    tools: "MinerU (primary) | Docling (fallback)",
  },
  {
    id: 1,
    name: "EXTRACT",
    desc: "Raw table extraction preserving bounding boxes, page numbers, merged cells, and multi-page stitching.",
    tools: "MineruTableExtractor | Docling | Generic Configurable Parser",
  },
  {
    id: 2,
    name: "INTERPRET",
    desc: "AI maps raw extracted cells to 47 BAR field schema. Wording normalisation, enum validation, product classification (T1\u2013T8).",
    tools: "LLM + register_row.schema.json + register_enums.json",
  },
  {
    id: 2.5,
    name: "VALIDATE",
    desc: "Validates enum fields against BAR controlled vocabulary. Up to 3 LLM correction attempts for invalid values.",
    tools: "ValidationIssue \u2192 CorrectionStats \u2192 LLM re-extraction",
  },
  {
    id: 3,
    name: "SAVE & INDEX",
    desc: "Deduplication with SHA-256 composite keys. Contextual embeddings for vector search. Persisted to SurrealDB.",
    tools: "SurrealDB | Vector embeddings | Parent Document Retrieval",
  },
];

export const logLines = [
  "[Stage -1] Extracting TOC... found 3 sections, 5 buildings",
  "[Stage  0] PDF classified as: digital (non-scanned)",
  "[Stage 0.5] Routing pages 1-4 \u2192 MinerU (complex tables detected)",
  "[Stage 0.5] Routing pages 5-6 \u2192 Docling (text-heavy layout)",
  "[Stage  1] Extracted 3 tables, 47 rows, 12 merged cells stitched",
  "[Stage  2] Mapped 47 fields. Classification: 31 non-friable, 16 friable",
  "[Stage 2.5] Validation: 3 enum errors corrected via RAG loop (attempt 1/3)",
  "[Stage  3] Saved 44 ACM records to SurrealDB. Embeddings indexed.",
  "\u2705 Extraction complete in 18.3s \u2014 44 records, 96% confidence",
];

export const gridRows = [
  { dept: "DJCS", agency: "VicPol", site: "Rathdowne St HQ", bcode: "B001", btype: "Police Station", level: "Level 1", room: "Corridor", io: "Internal", product: "Cement Sheet", friable: "No", cond: "Good", risk: "Low", result: "Not Detected", rec: "Monitor", page: 12, table: 3, row: 7 },
  { dept: "DJCS", agency: "VicPol", site: "Rathdowne St HQ", bcode: "B001", btype: "Police Station", level: "Level 2", room: "Server Room", io: "Internal", product: "Vinyl Floor Tiles", friable: "No", cond: "Fair", risk: "Medium", result: "Positive", rec: "Encapsulate", page: 12, table: 3, row: 9 },
  { dept: "DHHS", agency: "Health VIC", site: "Royal Melbourne", bcode: "B003", btype: "Hospital", level: "Roof", room: "Plant Room", io: "External", product: "Pipe Lagging", friable: "YES", cond: "Poor", risk: "High", result: "Friable Positive", rec: "Remove Immediately", page: 24, table: 5, row: 2 },
  { dept: "DET", agency: "Schools VIC", site: "Northcote High", bcode: "B012", btype: "School", level: "Ground", room: "Science Lab", io: "Internal", product: "Ceiling Tiles", friable: "No", cond: "Fair", risk: "Medium", result: "Suspected", rec: "Sample & Monitor", page: 31, table: 7, row: 4 },
  { dept: "DHHS", agency: "Health VIC", site: "Royal Melbourne", bcode: "B003", btype: "Hospital", level: "Basement", room: "Mechanical", io: "Internal", product: "Boiler Insulation", friable: "YES", cond: "Deteriorating", risk: "High", result: "Friable Positive", rec: "Remove Immediately", page: 25, table: 5, row: 8 },
  { dept: "DET", agency: "Schools VIC", site: "Northcote High", bcode: "B012", btype: "School", level: "Level 1", room: "Staff Room", io: "Internal", product: "Vinyl Floor Tiles", friable: "No", cond: "Good", risk: "Low", result: "Not Detected", rec: "Monitor", page: 32, table: 7, row: 11 },
];
