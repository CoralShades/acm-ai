"use client";

import { useState, useEffect, useRef } from "react";
import { cn } from "@/lib/cn";
import { MermaidDiagram } from "@/components/architecture/MermaidDiagram";

// ---------------------------------------------------------------------------
// Sidebar nav structure
// ---------------------------------------------------------------------------

interface NavItem {
  id: string;
  label: string;
  href: string;
  indent?: boolean;
}

interface NavGroup {
  heading: string;
  items: NavItem[];
}

const NAV_GROUPS: NavGroup[] = [
  {
    heading: "OVERVIEW",
    items: [
      { id: "executive-summary", label: "Executive Summary", href: "#executive-summary" },
      { id: "system-context", label: "System Context", href: "#system-context" },
    ],
  },
  {
    heading: "ARCHITECTURE",
    items: [
      { id: "e2e-flow", label: "End-to-End Data Flow", href: "#e2e-flow" },
      { id: "infrastructure", label: "Infrastructure & Deployment", href: "#infrastructure" },
      { id: "pipeline", label: "LangGraph Pipeline", href: "#pipeline" },
    ],
  },
  {
    heading: "PIPELINE DEEP DIVE",
    items: [
      { id: "phase1", label: "Phase 1: Source Processing", href: "#phase1", indent: true },
      { id: "phase2", label: "Phase 2: Pre-Extraction Intel", href: "#phase2", indent: true },
      { id: "phase3", label: "Phase 3: Orchestration", href: "#phase3", indent: true },
      { id: "phase4", label: "Phase 4: AI Extraction", href: "#phase4", indent: true },
      { id: "phase5", label: "Phase 5: Post-Extraction", href: "#phase5", indent: true },
      { id: "phase6", label: "Phase 6: Storage & Export", href: "#phase6", indent: true },
    ],
  },
  {
    heading: "AI & MODELS",
    items: [
      { id: "ai-models", label: "AI Model Decision Tree", href: "#ai-models" },
      { id: "structured-output", label: "Structured Output & Fallbacks", href: "#structured-output" },
    ],
  },
  {
    heading: "DATA & FRONTEND",
    items: [
      { id: "data-model", label: "Data Model & Schema", href: "#data-model" },
      { id: "frontend", label: "Frontend Architecture", href: "#frontend" },
    ],
  },
  {
    heading: "QUALITY",
    items: [
      { id: "accuracy-journey", label: "Accuracy Journey", href: "#accuracy-journey" },
      { id: "design-principles", label: "Design Principles", href: "#design-principles" },
    ],
  },
];

const ALL_SECTION_IDS = NAV_GROUPS.flatMap((g) => g.items.map((i) => i.id));

// ---------------------------------------------------------------------------
// Mermaid chart definitions
// ---------------------------------------------------------------------------

const CHART_SYSTEM_CONTEXT = `graph TB
  subgraph Users["Users"]
    CO["Compliance Officer<br/><i>Uploads PDFs, reviews data,<br/>exports BAR spreadsheets</i>"]
    ADMIN["System Administrator<br/><i>Configures models, manages<br/>extraction settings</i>"]
    DIR["Agency Director<br/><i>Views dashboards,<br/>compliance status</i>"]
  end
  subgraph External["External Systems"]
    PDF["Consultant PDFs<br/><i>Prensa, Greencap, Generic<br/>Asbestos Risk Assessments</i>"]
    BAR["BAR Templates<br/><i>Victorian Government<br/>Building Asbestos Register</i>"]
  end
  subgraph ACMAI["ACM-AI Platform"]
    direction TB
    FE["Next.js Frontend<br/><i>AG Grid, CopilotKit Chat</i>"]
    API["FastAPI Backend<br/><i>REST API, SSE Streaming</i>"]
    PIPE["Extraction Pipeline<br/><i>LangGraph, Multi-Agent AI</i>"]
    DB["SurrealDB<br/><i>Documents, Records, Graph</i>"]
  end
  subgraph AIProviders["AI Providers"]
    OR["OpenRouter<br/><i>Claude Sonnet 4, GPT-4o,<br/>Gemini 2.0 Flash</i>"]
    OL["Ollama Local<br/><i>Qwen 2.5:7b<br/>Embeddings</i>"]
  end
  CO --> FE
  ADMIN --> FE
  DIR --> FE
  PDF --> ACMAI
  FE --> API
  API --> PIPE
  PIPE --> DB
  PIPE --> OR
  PIPE --> OL
  ACMAI --> BAR
  style ACMAI fill:#f0f9f8,stroke:#3a8f8a,stroke-width:2px
  style Users fill:#f4f4f7,stroke:#2a2f45,stroke-width:1px
  style External fill:#fdf4f2,stroke:#d4614a,stroke-width:1px
  style AIProviders fill:#fce7f3,stroke:#be185d,stroke-width:1px`;

const CHART_E2E_FLOW = `flowchart TB
  subgraph UPLOAD["USER UPLOAD"]
    U1["Compliance Officer uploads PDF via browser"]
    U2["Upload Wizard captures site metadata"]
  end
  subgraph SOURCE["SOURCE PROCESSING -- Parallel Hybrid Extraction"]
    direction LR
    S1["PyMuPDF -- Full reading-order text<br/>Page markers: --- Page N ---<br/>Covers ALL pages"]
    S2["Docling Direct API -- TableFormer ACCURATE<br/>Row-major DataFrames<br/>Structured table data"]
  end
  subgraph CMD["COMMAND QUEUE"]
    C1["SurrealDB command table -- Worker polls and claims job"]
  end
  subgraph PREEX["PRE-EXTRACTION INTELLIGENCE -- Stage -1"]
    P1["TOC and Structure<br/>Document type, section hierarchy"]
    P2["Building Inventory<br/>Per-building page ranges"]
    P3["Page Tagging<br/>Section taxonomy 0-7"]
    P4["Metadata<br/>Consultant, date, site name"]
  end
  subgraph ORCH["UNIFIED ORCHESTRATOR -- Stage 0.5"]
    O1["Plan Extraction<br/>Assign per-building strategy"]
    O2["Context Assembly<br/>Building content + Docling tables"]
    O3["Parallel Execution<br/>asyncio.gather semaphore 3"]
  end
  subgraph EXTRACT["AI EXTRACTION -- Stage 1"]
    E1["Prompt Template<br/>building_extraction.jinja"]
    E2["Claude Sonnet 4<br/>via OpenRouter"]
    E3["JSON Parse + Validate<br/>Pydantic ACMExtractionResult"]
  end
  subgraph POSTEX["POST-EXTRACTION -- Stages 2-2.5"]
    V1["Validation<br/>Required fields check"]
    V2["LLM Correction<br/>Max 3 retries"]
    V3["Re-chunk Retry<br/>Structural failures"]
    V4["Deduplication<br/>room + product + location key"]
    V5["No-Access Recovery<br/>Regex fallback scanner"]
  end
  subgraph STORE["STORAGE AND ENRICHMENT -- Stage 3"]
    ST1["Save to SurrealDB<br/>acm_record table"]
    ST2["Enriched Embeddings<br/>Hierarchical context vectors"]
    ST3["Knowledge Graph<br/>School to Building to Room to ACM"]
  end
  subgraph OUTPUT["USER REVIEW AND EXPORT"]
    EX1["AG Grid Spreadsheet<br/>Interactive review"]
    EX2["AI Chat<br/>CopilotKit + ACM context"]
    EX3["BAR Excel Export<br/>47-column template"]
  end
  UPLOAD --> SOURCE
  SOURCE --> CMD
  CMD --> PREEX
  P1 --> P2
  P2 --> P3
  P1 --> P4
  PREEX --> ORCH
  O1 --> O2
  O2 --> O3
  ORCH --> EXTRACT
  E1 --> E2
  E2 --> E3
  EXTRACT --> POSTEX
  V1 --> |"field errors"| V2
  V1 --> |"structural errors"| V3
  V2 --> V4
  V3 --> V4
  V4 --> V5
  POSTEX --> STORE
  ST1 --> ST2
  ST1 --> ST3
  STORE --> OUTPUT
  style UPLOAD fill:#f3e8ff,stroke:#7e22ce,stroke-width:2px
  style SOURCE fill:#e0f2fe,stroke:#0369a1,stroke-width:2px
  style CMD fill:#f1f3f5,stroke:#868e96,stroke-width:1px
  style PREEX fill:#fef3c7,stroke:#a16207,stroke-width:2px
  style ORCH fill:#fce7f3,stroke:#be185d,stroke-width:2px
  style EXTRACT fill:#fce7f3,stroke:#be185d,stroke-width:2px
  style POSTEX fill:#dcfce7,stroke:#15803d,stroke-width:2px
  style STORE fill:#fef3c7,stroke:#a16207,stroke-width:2px
  style OUTPUT fill:#f0f9f8,stroke:#3a8f8a,stroke-width:2px`;

const CHART_INFRA = `graph TB
  subgraph Cloud["CLOUD"]
    subgraph Vercel["Vercel"]
      FE["Next.js Frontend<br/>Port 8502"]
    end
    subgraph OpenRouterAPI["OpenRouter API"]
      OR_API["Multi-provider routing<br/>Anthropic to Google to OpenAI"]
    end
  end
  subgraph CF["Cloudflare Tunnel"]
    TUN["Encrypted tunnel<br/>Vercel to Local Backend"]
  end
  subgraph Local["LOCAL WORKSTATION"]
    subgraph Python["Python Runtime"]
      API["FastAPI Backend<br/>Port 5055"]
      WORKER["Background Worker<br/>Command polling"]
      PIPE["LangGraph Pipeline"]
    end
    subgraph GPU["NVIDIA RTX 4090"]
      DOCLING["Docling + TableFormer<br/>CUDA-accelerated"]
    end
    subgraph Docker["Docker Containers"]
      SURREAL["SurrealDB v2<br/>Port 8000"]
      OLLAMA["Ollama<br/>Port 11434"]
    end
  end
  FE --> |"HTTPS"| TUN
  TUN --> |"HTTP"| API
  API --> WORKER
  WORKER --> PIPE
  PIPE --> DOCLING
  PIPE --> OR_API
  PIPE --> OLLAMA
  API --> SURREAL
  WORKER --> SURREAL
  style Cloud fill:#e0f2fe,stroke:#0369a1,stroke-width:1px
  style CF fill:#fef3c7,stroke:#a16207,stroke-width:1px
  style Local fill:#f0f9f8,stroke:#3a8f8a,stroke-width:2px
  style Python fill:#dcfce7,stroke:#15803d,stroke-width:1px
  style GPU fill:#fce7f3,stroke:#be185d,stroke-width:1px
  style Docker fill:#f3e8ff,stroke:#7e22ce,stroke-width:1px`;

const CHART_COMMAND_QUEUE = `sequenceDiagram
  participant User as Compliance Officer
  participant FE as Next.js Frontend
  participant API as FastAPI
  participant DB as SurrealDB
  participant Worker as Background Worker
  participant Pipeline as LangGraph Pipeline
  User->>FE: Upload PDF
  FE->>API: POST /api/sources (file)
  API->>DB: INSERT INTO command pending
  API-->>FE: 202 Accepted (source_id)
  loop Poll every 2s
    Worker->>DB: SELECT pending commands
    DB-->>Worker: command record
  end
  Worker->>DB: UPDATE command SET status=running
  Worker->>Pipeline: process_source_command(source)
  Note over Pipeline: PyMuPDF + Docling extraction
  Pipeline-->>Worker: source.full_text + acm_table_sections
  Worker->>DB: UPDATE source SET full_text
  Worker->>DB: UPDATE command SET completed
  User->>FE: Click Extract ACM
  FE->>API: POST /api/acm/extract (source_id)
  API->>DB: INSERT INTO command acm_extract pending
  Worker->>DB: SELECT pending commands
  Worker->>Pipeline: extract_acm_from_source(source)
  Note over Pipeline: Full 7-stage LangGraph pipeline
  Pipeline-->>Worker: ACMExtractionOutput (records)
  Worker->>DB: INSERT INTO acm_record records
  Worker->>DB: UPDATE command completed
  FE->>API: GET /api/acm/records?source_id=xxx
  API-->>FE: ACM records (JSON)
  FE-->>User: AG Grid spreadsheet view`;

const CHART_PIPELINE_STATE = `stateDiagram-v2
  [*] --> extract_metadata
  state "Stage -1: Pre-Extraction Intelligence" as PreEx {
    extract_metadata --> extract_structure : TOC and document type
    extract_structure --> compile_inventory : Building identification
    compile_inventory --> tag_page_sections : Section taxonomy
  }
  tag_page_sections --> orchestrate_extraction
  state "Stage 0.5: Orchestrator" as Orch {
    orchestrate_extraction --> plan_strategy : Analyse buildings
    plan_strategy --> execute_buildings : Per-building plans
  }
  execute_buildings --> validate_records
  state "Stage 2: Validation and Correction" as PostEx {
    validate_records --> check_result
    check_result --> correct_records : Field errors
    check_result --> rechunk_retry : Structural errors
    check_result --> deduplicate_records : All valid
    correct_records --> validate_records
    rechunk_retry --> validate_records
  }
  deduplicate_records --> recover_no_access
  state "Stage 3: Enrich and Store" as Store {
    recover_no_access --> save_records
    save_records --> generate_embeddings
    generate_embeddings --> update_graph
  }
  update_graph --> [*]`;

const CHART_PHASE1 = `flowchart LR
  PDF["PDF File"]
  subgraph PyMuPDF["Engine 1: PyMuPDF"]
    PM1["Extract full text reading order"]
    PM2["Insert page markers --- Page N ---"]
    PM3["Store as source.full_text"]
  end
  subgraph Docling["Engine 2: Docling Direct API"]
    DL1["DocumentConverter TableFormer ACCURATE"]
    DL2["export_to_dataframe Row-major DataFrames"]
    DL3["Normalize split sample numbers and strip Asbestos prefix"]
    DL4["Store as acm_table_section rows"]
  end
  PDF --> PM1
  PM1 --> PM2
  PM2 --> PM3
  PDF --> DL1
  DL1 --> DL2
  DL2 --> DL3
  DL3 --> DL4
  PM3 --> NEXT["Ready for ACM extraction"]
  DL4 --> NEXT
  style PyMuPDF fill:#e0f2fe,stroke:#0369a1,stroke-width:2px
  style Docling fill:#f3e8ff,stroke:#7e22ce,stroke-width:2px`;

const CHART_PHASE2 = `flowchart TB
  FT["source.full_text"]
  subgraph S16["E1-S16: Structure and TOC"]
    S16A["Detect document type SAMP ARA Division 5"]
    S16B["Extract section hierarchy 0-7 taxonomy"]
    S16C["Find register start page"]
    S16D["Identify building IDs"]
  end
  subgraph S17["E1-S17: Building Inventory"]
    S17A["Map buildings to page ranges"]
    S17B["Classify complexity simple or complex"]
    S17C["Create ProcessingGroups"]
  end
  subgraph S18["E1-S18: Page Tagging"]
    S18A["Tag each page with section ID 0=Cover 4=Register 7=Appendix"]
    S18B["Batch processing 5 pages per LLM call"]
  end
  subgraph S19["E1-S19: Metadata"]
    S19A["Extract consultant name"]
    S19B["Extract report date and site name"]
  end
  FT --> S16
  S16 --> S17
  S17 --> S18
  S16 --> S19
  S18 --> ORCH["Orchestrator Stage 0.5"]
  S19 --> ORCH
  style S16 fill:#fef3c7,stroke:#a16207,stroke-width:1px
  style S17 fill:#fef3c7,stroke:#a16207,stroke-width:1px
  style S18 fill:#fef3c7,stroke:#a16207,stroke-width:1px
  style S19 fill:#fef3c7,stroke:#a16207,stroke-width:1px`;

const CHART_PHASE3 = `flowchart TB
  INPUT["Building Inventory + Page Tags + Document Structure"]
  INPUT --> PLAN["plan_extraction -- Iterate over buildings"]
  PLAN --> CHECK{"Does building have register pages? section_id = 4"}
  CHECK --> |"No register pages"| SKIP["SKIP -- Methodology, conclusions, appendices"]
  CHECK --> |"Has register pages"| COMPLEX{"Building complexity?"}
  COMPLEX --> |"simple"| REGEX["REGEX_ONLY -- Minimal records result=Not Detected"]
  COMPLEX --> |"complex or unknown"| LLM["FULL_LLM -- Claude Sonnet 4 per-building prompt"]
  LLM --> ASSEMBLE["Context Assembly"]
  subgraph ASSEMBLE_DETAIL["Context Assembly per Building"]
    A1["1. Extract building content from full_text using page markers"]
    A2["2. Fetch Docling DataFrames for building page range"]
    A3["3. Append markdown tables to context if DataFrames exist"]
    A4["4. Add structured table extraction prompt instructions"]
    A5["5. Include building metadata name code page range"]
  end
  ASSEMBLE --> ASSEMBLE_DETAIL
  ASSEMBLE_DETAIL --> DISPATCH["Parallel Dispatch asyncio.gather semaphore=3"]
  DISPATCH --> MERGE["merge_building_results -- Combine all records and stats"]
  style SKIP fill:#f1f3f5,stroke:#868e96
  style REGEX fill:#dcfce7,stroke:#15803d
  style LLM fill:#fce7f3,stroke:#be185d
  style ASSEMBLE_DETAIL fill:#e0f2fe,stroke:#0369a1`;

const CHART_PHASE5 = `flowchart TB
  RAW["Raw AI Output"]
  RAW --> V1["Validation -- Pydantic schema check<br/>Required: product, result, room<br/>Enum: friable, risk_status"]
  V1 --> |"Valid records"| V4
  V1 --> |"Field errors"| V2["LLM Correction<br/>Same content + error feedback<br/>Claude Sonnet 4 retry -- Max 3 attempts"]
  V1 --> |"Structural errors"| V3["Re-chunk Retry<br/>Different chunk boundaries"]
  V2 --> V1S["Re-validate"]
  V3 --> V1S
  V1S --> |"Pass"| V4
  V1S --> |"Fail"| V2
  V4["Deduplication<br/>Key: room + product + location<br/>31 raw to 30 after dedup"]
  V4 --> V5["No-Access Recovery<br/>Regex scan full_text for missed entries<br/>30 to 32 (2 recovered)"]
  V5 --> FINAL["Final Record Set<br/>31 unique ground-truth matches"]
  style V1 fill:#dcfce7,stroke:#15803d
  style V2 fill:#fce7f3,stroke:#be185d
  style V3 fill:#fef3c7,stroke:#a16207
  style V4 fill:#e0f2fe,stroke:#0369a1
  style V5 fill:#f3e8ff,stroke:#7e22ce
  style FINAL fill:#f0f9f8,stroke:#3a8f8a,stroke-width:2px`;

const CHART_AI_MODELS = `flowchart TB
  subgraph PreEx["Pre-Extraction Stages"]
    PE1["Document Structure<br/>Building Inventory<br/>Page Tagging<br/>Metadata"]
  end
  subgraph Extract["Extraction Stage"]
    EX1["Per-building ACM record extraction"]
  end
  subgraph Correct["Correction Stage"]
    CO1["Field-level correction<br/>Missing value recovery"]
  end
  subgraph Embed["Embedding Stage"]
    EM1["Vector embedding generation"]
  end
  subgraph Classify["Classification Stage"]
    CL1["ACM Product Group and Type taxonomy"]
  end
  PE1 --> |"Claude Sonnet 4 via OpenRouter"| OR1["OpenRouter<br/>1. Anthropic<br/>2. Google<br/>3. OpenAI"]
  EX1 --> |"Claude Sonnet 4 via OpenRouter"| OR1
  CO1 --> |"Claude Sonnet 4 via OpenRouter"| OR1
  EM1 --> |"Qwen 2.5:7b"| OL["Ollama Local<br/>GPU-accelerated<br/>1024-dim embeddings"]
  CL1 --> |"Regex primary LLM fallback"| HYBRID["Hybrid<br/>Pattern matching first<br/>LLM only if ambiguous"]
  style PreEx fill:#fef3c7,stroke:#a16207,stroke-width:1px
  style Extract fill:#fce7f3,stroke:#be185d,stroke-width:2px
  style Correct fill:#dcfce7,stroke:#15803d,stroke-width:1px
  style Embed fill:#e0f2fe,stroke:#0369a1,stroke-width:1px
  style Classify fill:#f3e8ff,stroke:#7e22ce,stroke-width:1px`;

const CHART_STRUCTURED_OUTPUT = `flowchart TB
  CALL["LLM Call -- model.ainvoke(messages)"]
  CALL --> |"Raw text response"| PARSE["parse_json_response<br/>Brace-depth JSON extractor"]
  PARSE --> UNWRAP["_unwrap_completion_state<br/>Handle OpenRouter envelope"]
  UNWRAP --> NORMALIZE["_normalize_extraction_json<br/>Fix null data_issues, coerce types"]
  NORMALIZE --> VALIDATE["Pydantic model_validate<br/>ACMExtractionResult -- 40+ field validation"]
  VALIDATE --> |"Success"| RECORDS["Validated Records"]
  VALIDATE --> |"ValidationError"| FALLBACK["Heuristic Fallback per stage"]
  style PARSE fill:#e0f2fe,stroke:#0369a1
  style UNWRAP fill:#fce7f3,stroke:#be185d
  style NORMALIZE fill:#fef3c7,stroke:#a16207
  style VALIDATE fill:#dcfce7,stroke:#15803d
  style RECORDS fill:#f0f9f8,stroke:#3a8f8a,stroke-width:2px`;

const CHART_DATA_MODEL = `erDiagram
  source ||--o{ acm_record : "extracted_from"
  source ||--o{ acm_table_section : "has_tables"
  source ||--o| site_config : "configured_with"
  school ||--o{ building : "school_has_building"
  building ||--o{ room : "building_has_room"
  room ||--o{ acm_record : "room_has_acm"
  source {
    string id PK
    string title
    string full_text
    string file_path
    datetime created
  }
  acm_record {
    string id PK
    string source_id FK
    string building_id
    string building_name
    string room_id
    string room_name
    string product
    string result
    string friable
    string risk_status
    string nata_sample_number
    int page_number
    float embedding
  }
  acm_table_section {
    string id PK
    string source_id FK
    int page_start
    string raw_text
    string raw_html
    string table_type
  }
  site_config {
    string id PK
    string source_id FK
    string department
    string agency
    string building_type
  }
  school {
    string school_code PK
    string school_name
  }
  building {
    string building_code PK
    string building_name
    string school_code FK
  }
  room {
    string room_code PK
    string room_name
    string building_code FK
  }`;

const CHART_FRONTEND = `flowchart TB
  subgraph Pages["Next.js Pages"]
    DASH["Dashboard /"]
    JOBS["Jobs List /jobs"]
    JOB["Job Detail /jobs/[id]"]
    EXTRACT["Extraction Monitor /jobs/[id]/extract"]
    ACM["ACM Register /acm"]
    SETTINGS["Settings /settings"]
  end
  subgraph Components["Key Components"]
    GRID["ACMGrid AG Grid"]
    CHAT["CopilotChat CopilotKit"]
    PDF["PDFViewer react-pdf"]
    GRAPH["KnowledgeGraph React Flow"]
    MONITOR["ExtractionMonitor SSE Stream"]
  end
  subgraph API["FastAPI Backend"]
    REST["REST API /api/acm and /api/sources"]
    SSE["SSE Endpoints /api/extraction/events and /api/supervisor/stream"]
  end
  JOB --> GRID
  JOB --> CHAT
  JOB --> PDF
  JOB --> GRAPH
  EXTRACT --> MONITOR
  GRID --> REST
  CHAT --> SSE
  MONITOR --> SSE
  style Pages fill:#f0f9f8,stroke:#3a8f8a
  style Components fill:#e0f2fe,stroke:#0369a1
  style API fill:#fef3c7,stroke:#a16207`;


// ---------------------------------------------------------------------------
// Reusable components
// ---------------------------------------------------------------------------

function SectionHeader({ id, number, title, subtitle }: { id: string; number: string; title: string; subtitle?: string }) {
  return (
    <div className="mb-8">
      <p className="font-[family-name:var(--font-jetbrains-mono)] text-xs font-semibold uppercase tracking-widest text-vaea-teal-500 mb-1">
        {number}
      </p>
      <h2
        id={id}
        className="font-[family-name:var(--font-dm-serif)] text-3xl sm:text-4xl text-foreground scroll-mt-24 mb-3"
      >
        {title}
      </h2>
      {subtitle && (
        <p className="text-base text-muted-foreground leading-relaxed max-w-3xl">{subtitle}</p>
      )}
    </div>
  );
}

function Card({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={cn("bg-white border border-border rounded-xl p-6 shadow-sm", className)}>
      {children}
    </div>
  );
}

function CalloutTeal({ children }: { children: React.ReactNode }) {
  return (
    <div className="border-l-4 border-vaea-teal-500 bg-[#f0f9f8] rounded-r-lg px-6 py-4">
      {children}
    </div>
  );
}

function CalloutCoral({ children }: { children: React.ReactNode }) {
  return (
    <div className="border-l-4 border-vaea-coral bg-[#fdf4f2] rounded-r-lg px-6 py-4">
      {children}
    </div>
  );
}

function CalloutNavy({ children }: { children: React.ReactNode }) {
  return (
    <div className="border-l-4 border-vaea-navy bg-[#f4f4f7] rounded-r-lg px-6 py-4">
      {children}
    </div>
  );
}

function DiagramContainer({ title, caption, children }: { title: string; caption?: string; children: React.ReactNode }) {
  return (
    <div className="bg-white border border-border rounded-2xl p-8 shadow-md overflow-x-auto">
      <p className="font-[family-name:var(--font-jetbrains-mono)] text-xs font-semibold uppercase tracking-widest text-vaea-teal-700 mb-1">
        {title}
      </p>
      {caption && <p className="text-sm text-muted-foreground mb-6">{caption}</p>}
      {children}
    </div>
  );
}

function BadgeTeal({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-block px-2.5 py-0.5 rounded-full text-xs font-semibold bg-[#f0f9f8] text-vaea-teal-700 border border-vaea-teal-500/20">
      {children}
    </span>
  );
}

function BadgeCoral({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-block px-2.5 py-0.5 rounded-full text-xs font-semibold bg-[#fdf4f2] text-vaea-coral border border-vaea-coral/20">
      {children}
    </span>
  );
}

function BadgeNavy({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-block px-2.5 py-0.5 rounded-full text-xs font-semibold bg-[#f4f4f7] text-vaea-navy border border-vaea-navy/15">
      {children}
    </span>
  );
}

function StatBlock({ value, label }: { value: string; label: string }) {
  return (
    <div className="bg-white border border-border rounded-xl p-5 text-center">
      <p className="font-[family-name:var(--font-dm-serif)] text-3xl text-foreground">{value}</p>
      <p className="text-sm text-muted-foreground mt-1">{label}</p>
    </div>
  );
}


// ---------------------------------------------------------------------------
// Section 01 — Executive Summary
// ---------------------------------------------------------------------------

function Section01() {
  return (
    <section id="executive-summary" className="space-y-6 scroll-mt-24">
      <SectionHeader
        id="executive-summary"
        number="01"
        title="Executive Summary"
        subtitle="A non-technical overview of what ACM-AI does, why it exists, and how it transforms government compliance workflows."
      />

      <CalloutTeal>
        <p className="font-semibold text-vaea-teal-700 mb-1">The Problem</p>
        <p className="text-sm text-foreground leading-relaxed">
          Victorian Government agencies manage thousands of PDF asbestos assessment reports — one per school building, per
          consultant visit, per compliance cycle. Each report uses a slightly different table structure, font, and layout.
          Manually transcribing records into the Building Asbestos Register (BAR) spreadsheet costs compliance officers
          hours per document.
        </p>
      </CalloutTeal>

      <div className="border-l-4 border-vaea-teal-300 bg-[#f0f9f8] rounded-r-lg px-6 py-4">
        <p className="font-semibold text-vaea-teal-700 mb-1">The Solution</p>
        <p className="text-sm text-foreground leading-relaxed">
          ACM-AI automates this conversion using a hybrid approach: ML-based table extraction (Docling + TableFormer)
          combined with LLM interpretation (Claude Sonnet 4), achieving 100% accuracy on benchmark documents and
          processing a 20-page report in under 3 minutes.
        </p>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <StatBlock value="100%" label="Extraction Accuracy" />
        <StatBlock value="~3 min" label="Per Document" />
        <StatBlock value="2000+" label="Target Documents" />
        <StatBlock value="47" label="BAR Columns" />
      </div>

      <h3 className="font-semibold text-foreground text-xl mt-4">How It Works (In Brief)</h3>

      <div className="flex flex-wrap gap-2 items-center">
        {[
          { emoji: "📄", label: "PDF Upload" },
          { emoji: "🔍", label: "Table Extraction" },
          { emoji: "📋", label: "Document Analysis" },
          { emoji: "🤖", label: "AI Extraction" },
          { emoji: "✅", label: "Validation" },
          { emoji: "💾", label: "BAR Output" },
        ].map((step, i, arr) => (
          <div key={step.label} className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-vaea-teal-500/10 border border-vaea-teal-500/20 text-sm font-medium text-vaea-teal-700">
              <span>{step.emoji}</span>
              <span>{step.label}</span>
            </span>
            {i < arr.length - 1 && (
              <span className="text-muted-foreground text-sm">→</span>
            )}
          </div>
        ))}
      </div>

      <p className="text-sm text-muted-foreground leading-relaxed">
        Each PDF is processed through a 7-stage LangGraph pipeline. The system extracts building and room records,
        validates against the BAR schema, deduplicates, and persists to SurrealDB. Compliance officers review the
        results in an interactive AG Grid spreadsheet and export directly to BAR-format Excel.
      </p>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Section 02 — System Context
// ---------------------------------------------------------------------------

function Section02() {
  return (
    <section id="system-context" className="space-y-6 scroll-mt-24">
      <SectionHeader
        id="system-context"
        number="02"
        title="System Context"
        subtitle="Where ACM-AI fits within the Victorian Government compliance ecosystem and who interacts with it."
      />

      <DiagramContainer
        title="System Context Diagram"
        caption="ACM-AI's position in the VAEA compliance workflow"
      >
        <MermaidDiagram chart={CHART_SYSTEM_CONTEXT} />
      </DiagramContainer>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <h4 className="font-semibold text-foreground mb-2">Input Documents</h4>
          <p className="text-sm text-muted-foreground leading-relaxed">
            Asbestos Risk Assessment PDFs from consulting firms including Prensa, Greencap, and generic Victorian
            Government formats. Each uses different table layouts.
          </p>
        </Card>
        <Card>
          <h4 className="font-semibold text-foreground mb-2">Output Format</h4>
          <p className="text-sm text-muted-foreground leading-relaxed">
            Victorian Government BAR (Building Asbestos Register) spreadsheet — 47 mandatory columns per record,
            school and building hierarchy, NATA sampling data.
          </p>
        </Card>
        <Card>
          <h4 className="font-semibold text-foreground mb-2">Key Challenge</h4>
          <p className="text-sm text-muted-foreground leading-relaxed">
            No two consultant reports have the same table structure. The system must interpret intent, not just
            copy text — a task requiring AI reasoning, not simple parsing.
          </p>
        </Card>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Section 03 — End-to-End Data Flow
// ---------------------------------------------------------------------------

function Section03() {
  return (
    <section id="e2e-flow" className="space-y-6 scroll-mt-24">
      <SectionHeader
        id="e2e-flow"
        number="03"
        title="End-to-End Data Flow"
        subtitle="The complete journey of data from PDF upload to BAR-compliant export."
      />

      <DiagramContainer title="Complete Data Flow: PDF → BAR Spreadsheet">
        <MermaidDiagram chart={CHART_E2E_FLOW} />
      </DiagramContainer>

      <CalloutNavy>
        <p className="font-semibold text-vaea-navy mb-1">Unified Pipeline Principle</p>
        <p className="text-sm text-foreground leading-relaxed">
          Every PDF flows through the same orchestrated pipeline regardless of document format. The pre-extraction
          intelligence stage adapts the extraction strategy per-building, so the pipeline code stays clean while
          document complexity is handled dynamically at runtime.
        </p>
      </CalloutNavy>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Section 04 — Infrastructure & Deployment
// ---------------------------------------------------------------------------

function Section04() {
  return (
    <section id="infrastructure" className="space-y-6 scroll-mt-24">
      <SectionHeader
        id="infrastructure"
        number="04"
        title="Infrastructure & Deployment"
        subtitle="The physical and logical topology of all services."
      />

      <DiagramContainer title="Deployment Topology">
        <MermaidDiagram chart={CHART_INFRA} />
      </DiagramContainer>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <Card>
          <BadgeTeal>Vercel</BadgeTeal>
          <h4 className="font-semibold text-foreground mt-2 mb-1">Frontend</h4>
          <p className="text-sm text-muted-foreground">Next.js 15, React 19, AG Grid, CopilotKit. Deployed on Vercel edge network. Connects to local backend via Cloudflare Tunnel.</p>
        </Card>
        <Card>
          <BadgeTeal>FastAPI</BadgeTeal>
          <h4 className="font-semibold text-foreground mt-2 mb-1">Backend API</h4>
          <p className="text-sm text-muted-foreground">Python 3.11, FastAPI on port 5055. REST endpoints + SSE streaming. Runs on local workstation.</p>
        </Card>
        <Card>
          <BadgeTeal>Background</BadgeTeal>
          <h4 className="font-semibold text-foreground mt-2 mb-1">Worker Process</h4>
          <p className="text-sm text-muted-foreground">Polls SurrealDB command table every 2 seconds. Claims and executes extraction jobs asynchronously.</p>
        </Card>
        <Card>
          <BadgeNavy>SurrealDB</BadgeNavy>
          <h4 className="font-semibold text-foreground mt-2 mb-1">Database</h4>
          <p className="text-sm text-muted-foreground">SurrealDB v2 in Docker on port 8000. Graph + relational + vector storage in a single engine.</p>
        </Card>
        <Card>
          <BadgeCoral>RTX 4090</BadgeCoral>
          <h4 className="font-semibold text-foreground mt-2 mb-1">GPU Processing</h4>
          <p className="text-sm text-muted-foreground">NVIDIA RTX 4090 for CUDA-accelerated Docling TableFormer inference. Processes tables in seconds per page.</p>
        </Card>
        <Card>
          <BadgeCoral>OpenRouter</BadgeCoral>
          <h4 className="font-semibold text-foreground mt-2 mb-1">AI Routing</h4>
          <p className="text-sm text-muted-foreground">OpenRouter provides provider failover: Anthropic → Google → OpenAI. Ensures uptime even during provider outages.</p>
        </Card>
      </div>

      <h3 className="font-semibold text-foreground text-xl">Command Queue Architecture</h3>
      <p className="text-sm text-muted-foreground leading-relaxed">
        All long-running operations (PDF text extraction, ACM record extraction) are executed via an async command
        queue backed by SurrealDB. The frontend receives an immediate 202 Accepted response and polls for completion.
        This decoupling ensures the API stays responsive regardless of document size or AI provider latency.
      </p>

      <DiagramContainer title="Command Queue Flow">
        <MermaidDiagram chart={CHART_COMMAND_QUEUE} />
      </DiagramContainer>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Section 05 — LangGraph Pipeline State Machine
// ---------------------------------------------------------------------------

function Section05() {
  return (
    <section id="pipeline" className="space-y-6 scroll-mt-24">
      <SectionHeader
        id="pipeline"
        number="05"
        title="LangGraph Pipeline State Machine"
        subtitle="The extraction pipeline is modelled as a LangGraph state machine with conditional routing between stages."
      />

      <DiagramContainer title="Extraction Pipeline Graph">
        <MermaidDiagram chart={CHART_PIPELINE_STATE} />
      </DiagramContainer>

      <div className="overflow-x-auto">
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="bg-vaea-navy text-white text-left">
              <th className="px-4 py-3 font-semibold rounded-tl-lg">Stage</th>
              <th className="px-4 py-3 font-semibold">ID</th>
              <th className="px-4 py-3 font-semibold">Nodes</th>
              <th className="px-4 py-3 font-semibold">Purpose</th>
              <th className="px-4 py-3 font-semibold rounded-tr-lg">AI Used?</th>
            </tr>
          </thead>
          <tbody>
            {[
              { stage: "Pre-Analysis", id: "Stage -1", nodes: "4 nodes", purpose: "Document type, TOC, building inventory, page tagging, metadata", ai: "Yes — LLM" },
              { stage: "Orchestrator", id: "Stage 0.5", nodes: "3 nodes", purpose: "Plan strategy per-building, assemble context, dispatch parallel", ai: "No — Heuristic" },
              { stage: "Extract", id: "Stage 1", nodes: "1 node", purpose: "Per-building ACM record extraction via Jinja2 prompt + Claude", ai: "Yes — Claude Sonnet 4" },
              { stage: "Validate", id: "Stage 2", nodes: "2 nodes", purpose: "Pydantic schema check, route to correction or next stage", ai: "No — Pydantic" },
              { stage: "Correct", id: "Stage 2.1", nodes: "1 node", purpose: "LLM re-extraction with specific field error feedback, max 3 retries", ai: "Yes — Claude Sonnet 4" },
              { stage: "Dedup", id: "Stage 2.5", nodes: "1 node", purpose: "Deduplicate on room + product + location composite key", ai: "No — Heuristic" },
              { stage: "Recovery", id: "Stage 2.7", nodes: "1 node", purpose: "Regex scan for no-access and inaccessible room records", ai: "No — Regex" },
              { stage: "Store", id: "Stage 3", nodes: "3 nodes", purpose: "Persist to SurrealDB, generate embeddings, update knowledge graph", ai: "Yes — Embeddings" },
            ].map((row, i) => (
              <tr key={row.stage} className={i % 2 === 0 ? "bg-white" : "bg-muted/30"}>
                <td className="px-4 py-3 font-medium text-foreground">{row.stage}</td>
                <td className="px-4 py-3 font-[family-name:var(--font-jetbrains-mono)] text-xs text-vaea-teal-700">{row.id}</td>
                <td className="px-4 py-3 text-muted-foreground">{row.nodes}</td>
                <td className="px-4 py-3 text-muted-foreground">{row.purpose}</td>
                <td className="px-4 py-3">{row.ai.startsWith("Yes") ? <BadgeTeal>{row.ai}</BadgeTeal> : <BadgeNavy>{row.ai}</BadgeNavy>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}


// ---------------------------------------------------------------------------
// Section 06 — Phase 1: Source Processing
// ---------------------------------------------------------------------------

function Section06() {
  return (
    <section id="phase1" className="space-y-6 scroll-mt-24">
      <SectionHeader
        id="phase1"
        number="06"
        title="Phase 1: Source Processing"
        subtitle="How a raw PDF becomes structured text and table data ready for AI analysis."
      />

      <h3 className="font-semibold text-foreground text-xl">Why Two Extraction Engines?</h3>
      <p className="text-sm text-muted-foreground leading-relaxed">
        PDF documents contain two types of content that need different tools. PyMuPDF excels at preserving reading
        order across the full document, giving the AI the narrative context needed to understand which building a
        section belongs to. Docling with TableFormer excels at parsing complex merged-cell tables into clean
        DataFrames — the very tables containing ACM records. Using both in parallel gives the AI both the context
        and the structure.
      </p>

      <DiagramContainer title="Parallel Hybrid Extraction Architecture">
        <MermaidDiagram chart={CHART_PHASE1} />
      </DiagramContainer>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <h4 className="font-semibold text-foreground mb-2">PyMuPDF Output</h4>
          <ul className="space-y-1.5 text-sm text-muted-foreground">
            <li className="flex items-start gap-2"><span className="text-vaea-teal-500 mt-0.5">•</span>Full document text in reading order</li>
            <li className="flex items-start gap-2"><span className="text-vaea-teal-500 mt-0.5">•</span>Page boundary markers (--- Page N ---)</li>
            <li className="flex items-start gap-2"><span className="text-vaea-teal-500 mt-0.5">•</span>Stored as <code className="font-[family-name:var(--font-jetbrains-mono)] text-xs bg-muted px-1 rounded">source.full_text</code></li>
            <li className="flex items-start gap-2"><span className="text-vaea-teal-500 mt-0.5">•</span>Used for: section detection, building identification, metadata extraction</li>
          </ul>
        </Card>
        <Card>
          <h4 className="font-semibold text-foreground mb-2">Docling Output</h4>
          <ul className="space-y-1.5 text-sm text-muted-foreground">
            <li className="flex items-start gap-2"><span className="text-vaea-teal-500 mt-0.5">•</span>Row-major DataFrames per table per page</li>
            <li className="flex items-start gap-2"><span className="text-vaea-teal-500 mt-0.5">•</span>Handles merged cells (colspan/rowspan)</li>
            <li className="flex items-start gap-2"><span className="text-vaea-teal-500 mt-0.5">•</span>Stored as <code className="font-[family-name:var(--font-jetbrains-mono)] text-xs bg-muted px-1 rounded">acm_table_section</code> rows</li>
            <li className="flex items-start gap-2"><span className="text-vaea-teal-500 mt-0.5">•</span>Injected as markdown tables into AI extraction context</li>
          </ul>
        </Card>
      </div>

      <CalloutTeal>
        <p className="font-semibold text-vaea-teal-700 mb-1">Design Decision: Non-Blocking Docling</p>
        <p className="text-sm text-foreground leading-relaxed">
          Docling extraction runs concurrently with PyMuPDF extraction and does not block the ACM extraction pipeline.
          If Docling fails (e.g. no GPU available), the pipeline continues with PyMuPDF text only. The AI extraction
          quality degrades slightly but the pipeline never crashes — graceful degradation is a first-class requirement.
        </p>
      </CalloutTeal>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Section 07 — Phase 2: Pre-Extraction Intelligence
// ---------------------------------------------------------------------------

function Section07() {
  return (
    <section id="phase2" className="space-y-6 scroll-mt-24">
      <SectionHeader
        id="phase2"
        number="07"
        title="Phase 2: Pre-Extraction Intelligence"
        subtitle="Before a single ACM record is extracted, four parallel analysis stages build a complete document map."
      />

      <DiagramContainer title="Stage -1: Document Understanding Pipeline">
        <MermaidDiagram chart={CHART_PHASE2} />
      </DiagramContainer>

      <div className="overflow-x-auto">
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="bg-vaea-navy text-white text-left">
              <th className="px-4 py-3 font-semibold rounded-tl-lg">Stage</th>
              <th className="px-4 py-3 font-semibold">Input</th>
              <th className="px-4 py-3 font-semibold">Output</th>
              <th className="px-4 py-3 font-semibold">LLM Fallback</th>
              <th className="px-4 py-3 font-semibold rounded-tr-lg">Why It Matters</th>
            </tr>
          </thead>
          <tbody>
            {[
              {
                stage: "E1-S16 Structure & TOC",
                input: "full_text",
                output: "doc_type, section_hierarchy, register_start_page",
                fallback: "Regex header scan",
                why: "Determines which pages contain the ACM register vs. methodology",
              },
              {
                stage: "E1-S17 Building Inventory",
                input: "structure output",
                output: "BuildingInventory: per-building page ranges + complexity",
                fallback: "Single-building assumption",
                why: "Enables parallel per-building extraction with correct page scoping",
              },
              {
                stage: "E1-S18 Page Tagging",
                input: "full_text pages",
                output: "page_sections: {page: section_id} for all pages",
                fallback: "Default section 4 (register) for all pages",
                why: "Filters out non-register content (appendices, methodology) from extraction context",
              },
              {
                stage: "E1-S19 Metadata",
                input: "full_text",
                output: "consultant, report_date, site_name, school_code",
                fallback: "Empty strings, manual entry",
                why: "Populates BAR header fields without manual entry by the compliance officer",
              },
            ].map((row, i) => (
              <tr key={row.stage} className={i % 2 === 0 ? "bg-white" : "bg-muted/30"}>
                <td className="px-4 py-3 font-medium text-foreground text-xs font-[family-name:var(--font-jetbrains-mono)]">{row.stage}</td>
                <td className="px-4 py-3 text-muted-foreground">{row.input}</td>
                <td className="px-4 py-3 text-muted-foreground">{row.output}</td>
                <td className="px-4 py-3 text-muted-foreground">{row.fallback}</td>
                <td className="px-4 py-3 text-muted-foreground">{row.why}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <CalloutCoral>
        <p className="font-semibold text-vaea-coral mb-1">Key Insight: Heuristic Fallbacks Are Production-Ready</p>
        <p className="text-sm text-foreground leading-relaxed">
          Every AI-powered pre-extraction stage has a heuristic fallback that activates if the LLM call fails or
          returns malformed output. This means the pipeline continues extracting even during AI provider outages.
          The output quality may decrease but zero records are lost — compliance officers always get data to review.
        </p>
      </CalloutCoral>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Section 08 — Phase 3: Unified Orchestration
// ---------------------------------------------------------------------------

function Section08() {
  return (
    <section id="phase3" className="space-y-6 scroll-mt-24">
      <SectionHeader
        id="phase3"
        number="08"
        title="Phase 3: Unified Orchestration"
        subtitle="The orchestrator translates the document map into a parallel extraction plan, dispatching per-building AI calls with rich context."
      />

      <DiagramContainer title="Orchestrator Decision Logic">
        <MermaidDiagram chart={CHART_PHASE3} />
      </DiagramContainer>

      <h3 className="font-semibold text-foreground text-xl">Context Injection: What the AI Actually Sees</h3>
      <p className="text-sm text-muted-foreground leading-relaxed mb-4">
        For each building, the orchestrator assembles a rich context block injected into the extraction prompt.
        This ensures the AI has everything it needs in a single call — no multi-turn conversation required.
      </p>
      <div className="bg-vaea-navy rounded-xl p-6 overflow-x-auto">
        <pre className="font-[family-name:var(--font-jetbrains-mono)] text-xs text-vaea-teal-300 leading-relaxed whitespace-pre-wrap">
{`# Building: BLOCK A (BLK-A) — Pages 12-28

## Source: Full Text (PyMuPDF reading-order)
--- Page 12 ---
BLOCK A — ASBESTOS RISK ASSESSMENT
Site: Northcote Primary School
...
Room A-101 — Principal's Office
Friable material identified above ceiling tiles...

--- Page 13 ---
TABLE: ACM REGISTER — BLOCK A
[table content follows...]

## Source: Structured Tables (Docling TableFormer)
| Room | Location | Product | Condition | Result | NATA Sample |
|------|----------|---------|-----------|--------|-------------|
| A-101 | Above ceiling tiles | Amosite AIB | Fair | Positive | NS-2024-001 |
...`}
        </pre>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Section 09 — Phase 4: AI Extraction
// ---------------------------------------------------------------------------

function Section09() {
  return (
    <section id="phase4" className="space-y-6 scroll-mt-24">
      <SectionHeader
        id="phase4"
        number="09"
        title="Phase 4: AI Extraction"
        subtitle="Claude Sonnet 4 interprets building context and outputs structured BAR-compliant records."
      />

      <h3 className="font-semibold text-foreground text-xl mb-4">The AI&apos;s Job: Interpretation, Not Just Extraction</h3>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {[
          { title: "Record Identification", desc: "Distinguish ACM records from methodology text, commentary, and inspection notes. Each unique room+material combination is one record." },
          { title: "Building Context", desc: "Resolve building name ambiguities across pages. 'Block A' in the text may be 'BLOCK-A' in the table header — the AI reconciles these." },
          { title: "Sample Interpretation", desc: "Parse NATA sample numbers like 'NS-2024-001/A' into base number and sub-sample. Handle ranges ('NS-001 to NS-005') correctly." },
          { title: "BAR Field Mapping", desc: "Map consultant-specific field names to BAR columns. 'Condition' → risk_status, 'ACM Type' → product, 'Location Detail' → specific_location." },
          { title: "Product Classification", desc: "Classify ACM into product groups (AIB, Sprayed, Vinyl, Rope) and types (Amosite, Chrysotile, etc.) from free-text descriptions." },
          { title: "Risk Assessment", desc: "Interpret condition ratings (Poor/Fair/Good) and accessibility (Accessible/Inaccessible/No Access) into BAR-standard enum values." },
        ].map((item) => (
          <Card key={item.title}>
            <h4 className="font-semibold text-foreground mb-2">{item.title}</h4>
            <p className="text-sm text-muted-foreground leading-relaxed">{item.desc}</p>
          </Card>
        ))}
      </div>

      <h3 className="font-semibold text-foreground text-xl mt-2">Output Schema: ACMExtractionRecord (40+ Fields)</h3>

      <div className="overflow-x-auto">
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="bg-vaea-navy text-white text-left">
              <th className="px-4 py-3 font-semibold rounded-tl-lg">Category</th>
              <th className="px-4 py-3 font-semibold">Fields</th>
              <th className="px-4 py-3 font-semibold rounded-tr-lg">BAR Columns</th>
            </tr>
          </thead>
          <tbody>
            {[
              { cat: "Location", fields: "building_id, building_name, room_id, room_name, floor_level, specific_location", cols: "Cols A–F" },
              { cat: "Material", fields: "product, product_group, product_type, description, quantity, unit", cols: "Cols G–L" },
              { cat: "ACM Classification", fields: "friable (enum), asbestos_type, chrysotile_pct, amosite_pct", cols: "Cols M–P" },
              { cat: "Sampling", fields: "nata_sample_number, nata_sub_sample, sample_date, laboratory, nata_cert_no", cols: "Cols Q–U" },
              { cat: "Assessment", fields: "condition, accessibility, risk_status (enum), priority, result (enum)", cols: "Cols V–Z" },
              { cat: "Tracking", fields: "action_required, action_date, work_order, completion_date, inspector", cols: "Cols AA–AE" },
              { cat: "Metadata", fields: "page_number, source_id, building_code, school_code, extraction_confidence", cols: "Internal" },
            ].map((row, i) => (
              <tr key={row.cat} className={i % 2 === 0 ? "bg-white" : "bg-muted/30"}>
                <td className="px-4 py-3 font-medium text-foreground">{row.cat}</td>
                <td className="px-4 py-3 text-muted-foreground font-[family-name:var(--font-jetbrains-mono)] text-xs">{row.fields}</td>
                <td className="px-4 py-3"><BadgeTeal>{row.cols}</BadgeTeal></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}


// ---------------------------------------------------------------------------
// Section 10 — Phase 5: Post-Extraction Quality
// ---------------------------------------------------------------------------

function Section10() {
  return (
    <section id="phase5" className="space-y-6 scroll-mt-24">
      <SectionHeader
        id="phase5"
        number="10"
        title="Phase 5: Post-Extraction Quality"
        subtitle="Three automated quality stages transform raw AI output into verified, deduplicated, ground-truth-matching records."
      />

      <DiagramContainer title="Post-Extraction Quality Pipeline">
        <MermaidDiagram chart={CHART_PHASE5} />
      </DiagramContainer>

      <h3 className="font-semibold text-foreground text-xl">The Three Fixes That Achieved 100%</h3>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white border border-border rounded-xl overflow-hidden shadow-sm">
          <div className="h-1 bg-vaea-teal-500" />
          <div className="p-6">
            <BadgeTeal>Fix 1</BadgeTeal>
            <h4 className="font-semibold text-foreground mt-2 mb-2">Dedup Key Design</h4>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Changed deduplication key from record ID to composite <code className="font-[family-name:var(--font-jetbrains-mono)] text-xs bg-muted px-1 rounded">room + product + location</code>.
              This collapsed 31 raw records with duplicates to 30 clean unique records matching ground truth.
            </p>
          </div>
        </div>

        <div className="bg-white border border-border rounded-xl overflow-hidden shadow-sm">
          <div className="h-1 bg-vaea-coral" />
          <div className="p-6">
            <BadgeCoral>Fix 2</BadgeCoral>
            <h4 className="font-semibold text-foreground mt-2 mb-2">Prompt Engineering</h4>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Explicit instructions to distinguish between &ldquo;Not Detected&rdquo; (tested, no ACM found) and
              &ldquo;No Access&rdquo; (cannot sample). Eliminated the main source of false positives in early benchmarks.
            </p>
          </div>
        </div>

        <div className="bg-white border border-border rounded-xl overflow-hidden shadow-sm">
          <div className="h-1 bg-vaea-navy" />
          <div className="p-6">
            <BadgeNavy>Fix 3</BadgeNavy>
            <h4 className="font-semibold text-foreground mt-2 mb-2">Regex Recovery</h4>
            <p className="text-sm text-muted-foreground leading-relaxed">
              A regex post-processor scans <code className="font-[family-name:var(--font-jetbrains-mono)] text-xs bg-muted px-1 rounded">full_text</code> for patterns matching
              &ldquo;no access&rdquo; and &ldquo;inaccessible&rdquo; rooms missed by the LLM. Recovered 2 additional
              records taking accuracy from 29/31 to 31/31.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Section 11 — Phase 6: Storage & Export
// ---------------------------------------------------------------------------

function Section11() {
  return (
    <section id="phase6" className="space-y-6 scroll-mt-24">
      <SectionHeader
        id="phase6"
        number="11"
        title="Phase 6: Storage & Export"
        subtitle="Validated records are persisted, enriched with semantic embeddings, and made queryable via graph relationships."
      />

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <BadgeTeal>SurrealDB</BadgeTeal>
          <h4 className="font-semibold text-foreground mt-2 mb-1">SurrealDB Persistence</h4>
          <p className="text-sm text-muted-foreground leading-relaxed">
            Records stored in <code className="font-[family-name:var(--font-jetbrains-mono)] text-xs bg-muted px-1 rounded">acm_record</code> table with full BAR schema. SurrealDB&apos;s multi-model
            engine stores relational, graph, and vector data in one place.
          </p>
        </Card>
        <Card>
          <BadgeTeal>Ollama</BadgeTeal>
          <h4 className="font-semibold text-foreground mt-2 mb-1">Vector Embeddings</h4>
          <p className="text-sm text-muted-foreground leading-relaxed">
            Each record gets a 1024-dimensional embedding from Qwen 2.5:7b via local Ollama. Context includes
            building + room + product + location for rich semantic search.
          </p>
        </Card>
        <Card>
          <BadgeNavy>Graph</BadgeNavy>
          <h4 className="font-semibold text-foreground mt-2 mb-1">Knowledge Graph</h4>
          <p className="text-sm text-muted-foreground leading-relaxed">
            SurrealDB graph edges model: School → Building → Room → ACM Record. Enables graph traversal queries:
            &ldquo;all ACM in Block A&rdquo; or &ldquo;all high-risk rooms at this school.&rdquo;
          </p>
        </Card>
        <Card>
          <BadgeCoral>Export</BadgeCoral>
          <h4 className="font-semibold text-foreground mt-2 mb-1">BAR Excel Export</h4>
          <p className="text-sm text-muted-foreground leading-relaxed">
            One-click export maps all 47 BAR columns to the Victorian Government template. Headers, column widths,
            and formatting preserved for immediate submission.
          </p>
        </Card>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Section 12 — AI Model Decision Tree
// ---------------------------------------------------------------------------

function Section12() {
  return (
    <section id="ai-models" className="space-y-6 scroll-mt-24">
      <SectionHeader
        id="ai-models"
        number="12"
        title="AI Model Decision Tree"
        subtitle="Each pipeline stage uses the right AI tool for the job — from frontier LLMs to local embedding models."
      />

      <DiagramContainer title="AI Model Usage by Pipeline Stage">
        <MermaidDiagram chart={CHART_AI_MODELS} />
      </DiagramContainer>

      <div className="overflow-x-auto">
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="bg-vaea-navy text-white text-left">
              <th className="px-4 py-3 font-semibold rounded-tl-lg">Stage</th>
              <th className="px-4 py-3 font-semibold">Model</th>
              <th className="px-4 py-3 font-semibold">Provider</th>
              <th className="px-4 py-3 font-semibold">Why This Model</th>
              <th className="px-4 py-3 font-semibold rounded-tr-lg">Fallback</th>
            </tr>
          </thead>
          <tbody>
            {[
              { stage: "Pre-Extraction", model: "claude-sonnet-4", provider: "OpenRouter → Anthropic", why: "Strong instruction following for structured JSON output from document analysis", fallback: "Regex heuristics" },
              { stage: "ACM Extraction", model: "claude-sonnet-4", provider: "OpenRouter → Anthropic", why: "Best benchmark accuracy on BAR field mapping vs. GPT-4o and Gemini", fallback: "GPT-4o via OpenRouter" },
              { stage: "Correction", model: "claude-sonnet-4", provider: "OpenRouter → Anthropic", why: "Consistent with extraction model — same context window, same token costs", fallback: "Accept partial record" },
              { stage: "Embeddings", model: "qwen2.5:7b", provider: "Ollama (local)", why: "GPU-accelerated local inference, zero API cost, 1024-dim for rich similarity", fallback: "OpenAI text-embedding-3-small" },
              { stage: "Classification", model: "Regex + LLM", provider: "Hybrid", why: "Pattern matching for known ACM types, LLM only for ambiguous cases to save cost", fallback: "Manual review flag" },
            ].map((row, i) => (
              <tr key={row.stage} className={i % 2 === 0 ? "bg-white" : "bg-muted/30"}>
                <td className="px-4 py-3 font-medium text-foreground">{row.stage}</td>
                <td className="px-4 py-3 font-[family-name:var(--font-jetbrains-mono)] text-xs text-vaea-teal-700">{row.model}</td>
                <td className="px-4 py-3 text-muted-foreground">{row.provider}</td>
                <td className="px-4 py-3 text-muted-foreground">{row.why}</td>
                <td className="px-4 py-3 text-muted-foreground">{row.fallback}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Section 13 — Structured Output & Fallback Chain
// ---------------------------------------------------------------------------

function Section13() {
  return (
    <section id="structured-output" className="space-y-6 scroll-mt-24">
      <SectionHeader
        id="structured-output"
        number="13"
        title="Structured Output & Fallback Chain"
        subtitle="Every LLM response passes through a 4-stage normalisation pipeline before Pydantic validation."
      />

      <DiagramContainer title="LLM Response Processing Chain">
        <MermaidDiagram chart={CHART_STRUCTURED_OUTPUT} />
      </DiagramContainer>

      <CalloutCoral>
        <p className="font-semibold text-vaea-coral mb-1">Known Issue: completionState Envelope</p>
        <p className="text-sm text-foreground leading-relaxed">
          OpenRouter + Claude Sonnet 4 occasionally wraps responses in a <code className="font-[family-name:var(--font-jetbrains-mono)] text-xs bg-muted px-1 rounded">completionState</code> envelope
          instead of returning raw JSON. The <code className="font-[family-name:var(--font-jetbrains-mono)] text-xs bg-muted px-1 rounded">_unwrap_completion_state</code> function detects and unwraps
          this envelope before JSON parsing. Without this fix, approximately 15% of extraction calls would fail with
          a parse error on otherwise valid responses.
        </p>
      </CalloutCoral>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <h4 className="font-semibold text-foreground mb-2">Brace-Depth JSON Extraction</h4>
          <p className="text-sm text-muted-foreground leading-relaxed">
            The <code className="font-[family-name:var(--font-jetbrains-mono)] text-xs bg-muted px-1 rounded">parse_json_response</code> function walks character-by-character tracking
            brace depth to extract the JSON object even when the LLM includes preamble text like &ldquo;Here is the
            JSON:&rdquo; before the actual JSON payload.
          </p>
        </Card>
        <Card>
          <h4 className="font-semibold text-foreground mb-2">Type Coercion in Normalisation</h4>
          <p className="text-sm text-muted-foreground leading-relaxed">
            <code className="font-[family-name:var(--font-jetbrains-mono)] text-xs bg-muted px-1 rounded">_normalize_extraction_json</code> converts nulls in arrays to empty strings,
            coerces integer page numbers from floats, and strips Asbestos Containing Material (ACM) prefixes from
            product names — all common LLM output patterns that would otherwise fail Pydantic validation.
          </p>
        </Card>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Section 14 — Data Model & Schema
// ---------------------------------------------------------------------------

function Section14() {
  return (
    <section id="data-model" className="space-y-6 scroll-mt-24">
      <SectionHeader
        id="data-model"
        number="14"
        title="Data Model & Schema"
        subtitle="SurrealDB multi-model schema supporting relational queries, graph traversal, and vector search."
      />

      <DiagramContainer title="Database Entity Relationship">
        <MermaidDiagram chart={CHART_DATA_MODEL} />
      </DiagramContainer>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <CalloutTeal>
          <p className="font-semibold text-vaea-teal-700 mb-1">Graph Layer</p>
          <p className="text-sm text-foreground leading-relaxed">
            SurrealDB&apos;s graph edges model the hierarchy: <code className="font-[family-name:var(--font-jetbrains-mono)] text-xs bg-muted px-1 rounded">school → building → room → acm_record</code>.
            This enables traversal queries like <code className="font-[family-name:var(--font-jetbrains-mono)] text-xs bg-muted px-1 rounded">SELECT -&gt;building-&gt;room-&gt;acm_record FROM school</code>
            that would require multiple JOINs in a relational database.
          </p>
        </CalloutTeal>
        <CalloutNavy>
          <p className="font-semibold text-vaea-navy mb-1">Vector Layer</p>
          <p className="text-sm text-foreground leading-relaxed">
            The <code className="font-[family-name:var(--font-jetbrains-mono)] text-xs bg-muted px-1 rounded">embedding</code> field on <code className="font-[family-name:var(--font-jetbrains-mono)] text-xs bg-muted px-1 rounded">acm_record</code> stores 1024-dimensional
            vectors enabling semantic search: &ldquo;find all ACM records similar to this one&rdquo; or
            &ldquo;which rooms have friable material in poor condition.&rdquo;
          </p>
        </CalloutNavy>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Section 15 — Frontend Architecture
// ---------------------------------------------------------------------------

function Section15() {
  return (
    <section id="frontend" className="space-y-6 scroll-mt-24">
      <SectionHeader
        id="frontend"
        number="15"
        title="Frontend Architecture"
        subtitle="A Next.js 15 application built for compliance officers — not developers."
      />

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <BadgeTeal>AG Grid</BadgeTeal>
          <h4 className="font-semibold text-foreground mt-2 mb-1">AG Grid Spreadsheet</h4>
          <p className="text-sm text-muted-foreground leading-relaxed">
            Enterprise AG Grid with inline editing, column pinning, and cell citations linking back to source PDF
            pages. Compliance officers can review and correct extracted data directly in the grid.
          </p>
        </Card>
        <Card>
          <BadgeTeal>CopilotKit</BadgeTeal>
          <h4 className="font-semibold text-foreground mt-2 mb-1">CopilotKit AI Chat</h4>
          <p className="text-sm text-muted-foreground leading-relaxed">
            CopilotKit-powered chat sidebar with full ACM record context. Ask questions like &ldquo;which buildings
            have friable ACM?&rdquo; or &ldquo;summarise the risk profile for Block A.&rdquo;
          </p>
        </Card>
        <Card>
          <BadgeNavy>SSE</BadgeNavy>
          <h4 className="font-semibold text-foreground mt-2 mb-1">Live Extraction Monitor</h4>
          <p className="text-sm text-muted-foreground leading-relaxed">
            Server-Sent Events stream real-time pipeline progress. Each stage emits events as records are extracted,
            validated, and stored — compliance officers see progress in real time.
          </p>
        </Card>
        <Card>
          <BadgeCoral>React Flow</BadgeCoral>
          <h4 className="font-semibold text-foreground mt-2 mb-1">Knowledge Graph</h4>
          <p className="text-sm text-muted-foreground leading-relaxed">
            React Flow visualisation of the School → Building → Room → ACM hierarchy. Click any node to filter the
            AG Grid to that scope. Zoom out to see the full school campus.
          </p>
        </Card>
      </div>

      <DiagramContainer title="Frontend Component Architecture">
        <MermaidDiagram chart={CHART_FRONTEND} />
      </DiagramContainer>
    </section>
  );
}


// ---------------------------------------------------------------------------
// Section 16 — Accuracy Journey
// ---------------------------------------------------------------------------

interface AccuracyMilestone {
  date: string;
  id: string;
  label: string;
  score: string;
  pct: number;
  variant: "red" | "amber" | "green";
  isMilestone?: boolean;
}

const ACCURACY_MILESTONES: AccuracyMilestone[] = [
  { date: "2026-02-10", id: "E1-S7", label: "E1-S7 Baseline", score: "8/31 (26%)", pct: 26, variant: "red" },
  { date: "2026-02-22", id: "E18", label: "E18 Demo", score: "26/31 (84%)", pct: 84, variant: "amber" },
  { date: "2026-02-23", id: "E18-S5", label: "E18-S5 Prompt Fix", score: "28/31 (90%)", pct: 90, variant: "amber" },
  { date: "2026-02-26", id: "E20-S6", label: "E20-S6 Regression", score: "17/31 (55%)", pct: 55, variant: "red" },
  { date: "2026-02-27", id: "E25", label: "E25 Research Spike", score: "29/31 (93.5%)", pct: 93.5, variant: "amber" },
  { date: "2026-02-28", id: "E26-S6", label: "E26-S6 Final", score: "31/31 (100%) ⭐", pct: 100, variant: "green", isMilestone: true },
];

function AccuracyBadge({ variant, children }: { variant: "red" | "amber" | "green"; children: React.ReactNode }) {
  const cls = {
    red: "bg-red-100 text-red-700 border border-red-200",
    amber: "bg-amber-100 text-amber-700 border border-amber-200",
    green: "bg-green-100 text-green-700 border border-green-200",
  }[variant];
  return (
    <span className={cn("inline-block px-2 py-0.5 rounded-full text-xs font-semibold", cls)}>
      {children}
    </span>
  );
}

function Section16() {
  return (
    <section id="accuracy-journey" className="space-y-6 scroll-mt-24">
      <SectionHeader
        id="accuracy-journey"
        number="16"
        title="Accuracy Journey"
        subtitle="From 26% to 100% in 18 days — a log of every benchmark run and the fix that followed each regression."
      />

      <div className="relative">
        {/* Gradient vertical line */}
        <div
          className="absolute left-5 top-0 bottom-0 w-0.5"
          style={{ background: "linear-gradient(to bottom, #01A09C, #EB787A)" }}
        />

        <div className="space-y-6 pl-14">
          {ACCURACY_MILESTONES.map((m) => (
            <div key={m.id} className="relative">
              {/* Timeline dot */}
              <div
                className={cn(
                  "absolute -left-9 top-1 flex h-5 w-5 items-center justify-center rounded-full border-2",
                  m.isMilestone
                    ? "border-vaea-coral bg-vaea-coral"
                    : m.variant === "green"
                    ? "border-green-500 bg-green-100"
                    : m.variant === "red"
                    ? "border-red-400 bg-red-100"
                    : "border-amber-400 bg-amber-100"
                )}
              >
                {m.isMilestone ? (
                  <span className="text-white text-[8px]">★</span>
                ) : (
                  <span
                    className={cn(
                      "h-2 w-2 rounded-full",
                      m.variant === "green" ? "bg-green-500" : m.variant === "red" ? "bg-red-400" : "bg-amber-400"
                    )}
                  />
                )}
              </div>

              <div className={cn("bg-white border border-border rounded-xl p-5 shadow-sm", m.isMilestone && "border-vaea-coral/40 ring-1 ring-vaea-coral/20")}>
                <div className="flex items-start justify-between gap-3 flex-wrap">
                  <div>
                    <p className="font-[family-name:var(--font-jetbrains-mono)] text-xs font-semibold text-muted-foreground">{m.date}</p>
                    <p className="font-semibold text-foreground mt-0.5">{m.label}</p>
                  </div>
                  <AccuracyBadge variant={m.variant}>{m.score}</AccuracyBadge>
                </div>

                {/* Progress bar */}
                <div className="mt-3 h-2 w-full bg-muted rounded-full overflow-hidden">
                  <div
                    className={cn(
                      "h-full rounded-full transition-all",
                      m.variant === "green" ? "bg-green-500" : m.variant === "red" ? "bg-red-400" : "bg-amber-400"
                    )}
                    style={{ width: `${m.pct}%` }}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <CalloutTeal>
        <p className="font-semibold text-vaea-teal-700 mb-1">Key Lesson</p>
        <p className="text-sm text-foreground leading-relaxed">
          Model switching alone does not solve extraction problems. The regressions in this journey were caused by
          prompt ambiguity and missing deduplication logic — not by model capability. The most impactful fixes were
          engineering changes: a composite dedup key, explicit result enum instructions, and a regex recovery scanner.
          The model stayed constant throughout.
        </p>
      </CalloutTeal>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Section 17 — Design Principles
// ---------------------------------------------------------------------------

function Section17() {
  const principles = [
    {
      accent: "border-vaea-teal-500",
      title: "Unified Pipeline",
      desc: "Every document flows through the same 7-stage LangGraph pipeline. Format differences are handled by per-building strategy decisions inside the pipeline, not by separate code paths. One pipeline to maintain, one pipeline to test.",
    },
    {
      accent: "border-vaea-coral",
      title: "Hybrid Extraction",
      desc: "ML table extraction (Docling) provides structure. LLM (Claude) provides interpretation. Neither alone is sufficient. Together they handle the full range of real-world PDF quality — from clean digital exports to scanned documents with OCR artifacts.",
    },
    {
      accent: "border-vaea-navy",
      title: "AI Interprets, Rules Validate",
      desc: "AI extracts and interprets. Pydantic validates. Regex recovers. This separation of concerns means each tool does what it does best. The AI is not burdened with schema enforcement, and the validator is not burdened with interpretation.",
    },
    {
      accent: "border-vaea-teal-500",
      title: "Graceful Degradation",
      desc: "Every stage has a fallback. Docling fails? Continue with PyMuPDF. LLM correction fails? Accept the partial record. Embeddings fail? Skip and continue. The compliance officer always gets output — even if some fields need manual review.",
    },
    {
      accent: "border-vaea-coral",
      title: "Measure Before Fixing",
      desc: "No pipeline change is made without a benchmark run before and after. The accuracy journey table documents every regression and fix. This discipline prevented the team from introducing changes that felt right but reduced accuracy.",
    },
    {
      accent: "border-vaea-navy",
      title: "Design for the Officer",
      desc: "The compliance officer never sees the pipeline. They see: upload → wait → review in grid → export. Every technical complexity is hidden behind a simple, familiar spreadsheet interface that requires no AI literacy to use.",
    },
  ];

  return (
    <section id="design-principles" className="space-y-6 scroll-mt-24">
      <SectionHeader
        id="design-principles"
        number="17"
        title="Design Principles"
        subtitle="Six principles that guided every technical decision in ACM-AI."
      />

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {principles.map((p) => (
          <div key={p.title} className={cn("bg-white border border-border rounded-xl p-6 shadow-sm border-l-4", p.accent)}>
            <h4 className="font-semibold text-foreground mb-2">{p.title}</h4>
            <p className="text-sm text-muted-foreground leading-relaxed">{p.desc}</p>
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className="mt-12 rounded-2xl border border-border bg-card p-8 text-center">
        <p className="text-sm text-muted-foreground mb-4">
          ACM-AI Solution Architecture v2.0 — Victorian Asbestos Eradication Agency
        </p>
        <div className="flex items-center justify-center gap-3 flex-wrap">
          {[
            { label: "Teal 500", bg: "bg-vaea-teal-500" },
            { label: "Teal 300", bg: "bg-vaea-teal-300" },
            { label: "Teal 700", bg: "bg-vaea-teal-700" },
            { label: "Coral", bg: "bg-vaea-coral" },
            { label: "Navy", bg: "bg-vaea-navy" },
            { label: "Navy Light", bg: "bg-vaea-navy-light" },
          ].map((swatch) => (
            <div key={swatch.label} className="flex items-center gap-1.5">
              <span className={cn("w-4 h-4 rounded-sm inline-block", swatch.bg)} />
              <span className="text-xs text-muted-foreground">{swatch.label}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}


// ---------------------------------------------------------------------------
// Sidebar component
// ---------------------------------------------------------------------------

interface SidebarProps {
  activeSection: string;
  onNavigate: (id: string) => void;
}

function ArchSidebar({ activeSection, onNavigate }: SidebarProps) {
  return (
    <aside
      className="hidden lg:flex flex-col fixed top-16 left-0 z-40 w-[260px] border-r border-white/10 bg-vaea-navy overflow-y-auto"
      style={{ height: "calc(100vh - 4rem)" }}
      aria-label="Architecture page navigation"
    >
      {/* Brand section */}
      <div className="px-5 pt-5 pb-4 border-b border-white/10 shrink-0">
        <p className="font-[family-name:var(--font-dm-serif)] text-xl text-vaea-teal-300">ACM-AI</p>
        <p className="text-xs text-white/40 mt-0.5">Solution Architecture v2.0</p>
      </div>

      {/* Nav groups */}
      <nav className="flex-1 py-3 px-3 space-y-4">
        {NAV_GROUPS.map((group) => (
          <div key={group.heading}>
            <p className="font-[family-name:var(--font-jetbrains-mono)] text-[10px] font-semibold uppercase tracking-widest text-white/30 px-2 mb-1">
              {group.heading}
            </p>
            <div className="space-y-0.5">
              {group.items.map((item) => {
                const isActive = activeSection === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => onNavigate(item.id)}
                    className={cn(
                      "w-full text-left text-sm rounded-lg px-3 py-1.5 transition-colors duration-150",
                      item.indent && "pl-5",
                      isActive
                        ? "border-l-2 border-vaea-teal-300 bg-white/5 text-white"
                        : "text-white/50 hover:text-white/80 hover:bg-white/5"
                    )}
                  >
                    {item.label}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* Bottom version */}
      <div className="px-5 py-3 border-t border-white/10 shrink-0">
        <p className="font-[family-name:var(--font-jetbrains-mono)] text-[10px] text-white/30">March 2026 — v2.0</p>
      </div>
    </aside>
  );
}

// ---------------------------------------------------------------------------
// Mobile sidebar drawer
// ---------------------------------------------------------------------------

interface MobileSidebarProps {
  isOpen: boolean;
  onClose: () => void;
  activeSection: string;
  onNavigate: (id: string) => void;
}

function MobileDrawer({ isOpen, onClose, activeSection, onNavigate }: MobileSidebarProps) {
  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/40 z-40 lg:hidden"
        onClick={onClose}
        aria-hidden="true"
      />
      {/* Drawer */}
      <div
        className="fixed top-16 left-0 bottom-0 w-72 bg-vaea-navy z-50 lg:hidden overflow-y-auto border-r border-white/10"
        role="dialog"
        aria-label="Architecture navigation"
      >
        <div className="px-5 pt-5 pb-4 border-b border-white/10 flex items-center justify-between">
          <div>
            <p className="font-[family-name:var(--font-dm-serif)] text-xl text-vaea-teal-300">ACM-AI</p>
            <p className="text-xs text-white/40 mt-0.5">Solution Architecture v2.0</p>
          </div>
          <button
            onClick={onClose}
            className="text-white/40 hover:text-white/80 transition-colors"
            aria-label="Close navigation"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </button>
        </div>

        <nav className="py-3 px-3 space-y-4">
          {NAV_GROUPS.map((group) => (
            <div key={group.heading}>
              <p className="font-[family-name:var(--font-jetbrains-mono)] text-[10px] font-semibold uppercase tracking-widest text-white/30 px-2 mb-1">
                {group.heading}
              </p>
              <div className="space-y-0.5">
                {group.items.map((item) => {
                  const isActive = activeSection === item.id;
                  return (
                    <button
                      key={item.id}
                      onClick={() => { onNavigate(item.id); onClose(); }}
                      className={cn(
                        "w-full text-left text-sm rounded-lg px-3 py-1.5 transition-colors duration-150",
                        item.indent && "pl-5",
                        isActive
                          ? "border-l-2 border-vaea-teal-300 bg-white/5 text-white"
                          : "text-white/50 hover:text-white/80 hover:bg-white/5"
                      )}
                    >
                      {item.label}
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>
      </div>
    </>
  );
}

// ---------------------------------------------------------------------------
// Hero section
// ---------------------------------------------------------------------------

function Hero() {
  return (
    <div
      className="relative py-16 px-8 overflow-hidden"
      style={{
        background: "linear-gradient(135deg, #1e2235 0%, #2a2f45 50%, #2d706c 100%)",
      }}
    >
      {/* Grid overlay */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          backgroundImage:
            "linear-gradient(rgba(154,217,217,0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(154,217,217,0.05) 1px, transparent 1px)",
          backgroundSize: "60px 60px",
        }}
      />

      <div className="relative max-w-4xl">
        {/* Badge */}
        <span className="inline-block px-3 py-1 rounded-full text-xs font-semibold bg-white/10 text-vaea-teal-300 border border-white/10 mb-4">
          Victorian Asbestos Eradication Agency
        </span>

        {/* Title */}
        <h1 className="font-[family-name:var(--font-dm-serif)] text-4xl sm:text-5xl lg:text-6xl text-white leading-tight">
          ACM-AI{" "}
          <span className="text-vaea-teal-300">Solution Architecture</span>
        </h1>

        {/* Subtitle */}
        <p className="mt-4 text-white/70 text-lg leading-relaxed max-w-2xl">
          The complete technical design of the AI-powered asbestos compliance platform. From PDF upload to
          BAR-compliant export — every stage, every decision, every trade-off documented.
        </p>

        {/* Meta stats row */}
        <div className="mt-8 flex flex-wrap gap-4">
          {[
            { label: "Extraction Accuracy", value: "31/31 100%" },
            { label: "Pipeline Stages", value: "7" },
            { label: "BAR Schema Fields", value: "47" },
            { label: "Document Formats", value: "Prensa, Greencap, Generic" },
            { label: "Version", value: "March 2026" },
          ].map((stat) => (
            <div key={stat.label} className="bg-white/8 border border-white/10 rounded-lg px-4 py-2.5">
              <p className="font-[family-name:var(--font-jetbrains-mono)] text-xs text-white/40">{stat.label}</p>
              <p className="font-semibold text-white text-sm mt-0.5">{stat.value}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page — root component
// ---------------------------------------------------------------------------

export default function ArchitecturePage() {
  const [activeSection, setActiveSection] = useState("executive-summary");
  const [mobileOpen, setMobileOpen] = useState(false);
  const observerRef = useRef<IntersectionObserver | null>(null);

  useEffect(() => {
    observerRef.current = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setActiveSection(entry.target.id);
          }
        });
      },
      { rootMargin: "-30% 0px -60% 0px", threshold: 0 }
    );

    ALL_SECTION_IDS.forEach((id) => {
      const el = document.getElementById(id);
      if (el) observerRef.current?.observe(el);
    });

    return () => observerRef.current?.disconnect();
  }, []);

  function scrollToSection(id: string) {
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Desktop sidebar */}
      <ArchSidebar activeSection={activeSection} onNavigate={scrollToSection} />

      {/* Mobile drawer */}
      <MobileDrawer
        isOpen={mobileOpen}
        onClose={() => setMobileOpen(false)}
        activeSection={activeSection}
        onNavigate={scrollToSection}
      />

      {/* Main content area */}
      <div className="lg:ml-[260px]">
        {/* Mobile hamburger bar */}
        <div className="lg:hidden sticky top-16 z-30 flex items-center gap-3 px-4 py-3 bg-background/95 backdrop-blur-sm border-b border-border">
          <button
            onClick={() => setMobileOpen(true)}
            className="flex items-center gap-2 text-sm font-medium text-foreground hover:text-vaea-teal-700 transition-colors"
            aria-label="Open navigation"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <path d="M3 12h18M3 6h18M3 18h18" />
            </svg>
            Navigate
          </button>
          <span className="text-muted-foreground text-sm">—</span>
          <span className="text-sm font-semibold text-vaea-teal-700 capitalize">
            {NAV_GROUPS.flatMap((g) => g.items).find((i) => i.id === activeSection)?.label ?? "Architecture"}
          </span>
        </div>

        {/* Hero */}
        <Hero />

        {/* Sections */}
        <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 py-16 space-y-24">
          <Section01 />
          <Section02 />
          <Section03 />
          <Section04 />
          <Section05 />
          <Section06 />
          <Section07 />
          <Section08 />
          <Section09 />
          <Section10 />
          <Section11 />
          <Section12 />
          <Section13 />
          <Section14 />
          <Section15 />
          <Section16 />
          <Section17 />
        </div>
      </div>
    </div>
  );
}
