export interface Epic {
  id: string;
  code: string;
  title: string;
  stories: number;
  status: "done" | "in-progress" | "planned";
  highlight: string;
  category: "extraction" | "ui" | "data" | "ai" | "infra" | "ux";
}

export const epics: Epic[] = [
  { id: "E1", code: "E1 Pipeline", title: "ACM Data Extraction Pipeline", stories: 31, status: "done", highlight: "7-stage agentic pipeline with MinerU + Docling", category: "extraction" },
  { id: "E2", code: "E2 AG Grid", title: "AG Grid Spreadsheet Integration", stories: 12, status: "done", highlight: "47-column BAR schema with risk colour-coding", category: "ui" },
  { id: "E3", code: "E3 Citations", title: "Cell Citations & PDF Viewer", stories: 4, status: "done", highlight: "Click any cell \u2192 see PDF source page", category: "data" },
  { id: "E4", code: "E4 Chat", title: "Chat with ACM Context", stories: 4, status: "done", highlight: "LangGraph supervisor with ACM query tools", category: "ai" },
  { id: "E5", code: "E5 Export", title: "Export Functionality", stories: 4, status: "done", highlight: "BAR-compliant Excel with template management", category: "data" },
  { id: "E6", code: "E6 Brand", title: "Rebranding to ACM-AI", stories: 4, status: "done", highlight: "VAEA government identity system", category: "ux" },
  { id: "E7", code: "E7 Upload", title: "Upload Wizard", stories: 7, status: "done", highlight: "Drag-drop PDF with extraction trigger", category: "ui" },
  { id: "E9", code: "E9 Library", title: "Document Library Management", stories: 3, status: "done", highlight: "Bulk operations and processing dashboard", category: "ui" },
  { id: "E10", code: "E10 Nav", title: "ACM-AI UI Simplification", stories: 1, status: "done", highlight: "Streamlined ACM-focused navigation", category: "ux" },
  { id: "E11", code: "E11 Search", title: "Search & Retrieval Enhancement", stories: 2, status: "done", highlight: "Hybrid search + parent document retrieval", category: "ai" },
  { id: "E12", code: "E12 Settings", title: "Extraction Settings & Configuration", stories: 4, status: "done", highlight: "Config-driven field schema, model selection", category: "infra" },
  { id: "E13", code: "E13 Graph", title: "Knowledge Graph Visualization", stories: 3, status: "done", highlight: "React Flow entity relationship explorer", category: "data" },
  { id: "E14", code: "E14 UX", title: "UX & Enterprise Readiness", stories: 11, status: "done", highlight: "WCAG 2.1 AA, VAEA tokens, skeletons", category: "ux" },
  { id: "E15", code: "E15 Monitor", title: "Extraction Monitor & Logging", stories: 2, status: "done", highlight: "Real-time SSE pipeline progress UI", category: "infra" },
  { id: "E16", code: "E16 UX+", title: "UX Enhancement Sprint", stories: 3, status: "done", highlight: "Dashboard home, record detail panel", category: "ux" },
  { id: "E17", code: "E17 Live AI", title: "Live Extraction Intelligence", stories: 6, status: "done", highlight: "AG-UI + A2A agent card + reasoning display", category: "ai" },
];

export const futureEpics = [
  { id: "E18", title: "Extraction Quality & Edge Cases", status: "planned" as const, description: "Handling edge cases in complex PDFs, improving accuracy to 98%+" },
  { id: "E19", title: "Marketing Site & Documentation", status: "in-progress" as const, description: "Public-facing marketing site, executive demo, and documentation hub" },
  { id: "E20", title: "Knowledge Graph Intelligence", status: "planned" as const, description: "Cross-document entity resolution, relationship inference, portfolio analytics" },
];

export const audienceData: Record<string, { headline: string; cards: string[]; callout: string }> = {
  Director: {
    headline: "Risk Mitigation + Operational Efficiency",
    cards: [
      "Hours saved per document: 8\u201312 hours of manual data entry eliminated",
      "Accuracy: 90%+ extraction accuracy vs error-prone manual entry",
      "Compliance: 100% BAR field coverage \u2014 no submission gaps",
      "Traceability: Every data point linked back to source PDF page",
    ],
    callout: "Reduces liability exposure from incomplete asbestos registers",
  },
  CTO: {
    headline: "Enterprise-Grade Architecture",
    cards: [
      "Stack: FastAPI + SurrealDB + LangGraph + Next.js 15",
      "AI: Multi-provider LLM (OpenAI, Anthropic, Ollama) via Esperanto",
      "Extraction: MinerU (ML-based) + Docling \u2014 handles merged cells, multi-page tables",
      "Protocol: AG-UI + CopilotKit for real-time SSE agent streaming",
      "Schema: Config-driven (JSON), no code changes for new BAR fields",
    ],
    callout: "All processing is local-first \u2014 zero external API calls for document extraction",
  },
  CEO: {
    headline: "Strategic Compliance Platform",
    cards: [
      "Market: Victorian Government mandatory BAR submissions",
      "Delivery: 92% of 122 stories completed, feature complete",
      "Velocity: 281 commits across autonomous development sprints",
      "Scale: Multi-document, multi-site portfolio support",
    ],
    callout: "ACM-AI positions VAEA as the leading compliance intelligence platform for the Victorian public sector",
  },
  Client: {
    headline: "What This Means For You",
    cards: [
      "Upload your PDF asbestos register \u2014 drag and drop, any format",
      "Configure site details (Department, Agency, Building Type) once",
      "Wait ~18 seconds \u2014 AI extracts all tables automatically",
      "Review your data in the interactive spreadsheet \u2014 sort, filter, search",
      "Ask questions in plain English: 'What's high risk in Building B?'",
      "Click to see exactly which PDF page each data row came from",
      "Export BAR-compliant Excel \u2014 ready for government submission",
    ],
    callout: "No training needed. No manual data entry. No compliance gaps.",
  },
};
