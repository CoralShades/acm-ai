import { useState, useEffect, useRef } from "react";
import {
  Upload, FileText, Database, Table, MessageSquare, Download,
  CheckCircle, AlertTriangle, TrendingUp, Building, Search,
  ChevronRight, ChevronDown, Zap, Shield, BarChart3, Eye,
  ArrowRight, Play, Loader, Settings, Users, Award
} from "lucide-react";
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from "recharts";

const T = { teal: "#3a8f8a", coral: "#d4614a", navy: "#2a2f45", bg: "#f4f7f9", card: "#ffffff", success: "#4caf82", warn: "#f59e0b", rHigh: "#ef4444", rMed: "#f97316", rLow: "#22c55e" };

const StatCard = ({ icon: Icon, label, value, color }) => (
  <div className="rounded-xl p-5 shadow-sm border border-gray-100" style={{ background: T.card }}>
    <div className="flex items-center gap-3 mb-2">
      <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ background: color + "18" }}><Icon size={20} style={{ color }} /></div>
      <span className="text-sm font-medium" style={{ color: T.navy + "99" }}>{label}</span>
    </div>
    <div className="text-3xl font-bold tracking-tight" style={{ color: T.navy }}>{value}</div>
  </div>
);

const Badge = ({ children, color = T.success }) => (
  <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold" style={{ background: color + "18", color }}>{children}</span>
);

const sections = [
  { id: "overview", icon: Building, label: "Overview" },
  { id: "pipeline", icon: Zap, label: "Pipeline" },
  { id: "spreadsheet", icon: Table, label: "Spreadsheet" },
  { id: "chat", icon: MessageSquare, label: "Chat" },
  { id: "export", icon: Download, label: "Export" },
  { id: "progress", icon: TrendingUp, label: "Progress" },
  { id: "architecture", icon: Settings, label: "Architecture" },
  { id: "stakeholders", icon: Users, label: "Stakeholders" },
];

const pipelineStages = [
  { id: -1, name: "PRE-ANALYSIS", icon: Search, color: T.navy, desc: "TOC extraction, building inventory compilation, page-level section tagging, document metadata enhancement", tools: "LangGraph agentic orchestrator" },
  { id: 0, name: "PREFLIGHT", icon: FileText, color: T.teal, desc: "PDF classifier detects digital vs scanned. Parser router selects MinerU or Docling based on content type.", tools: "PDF Classifier → Parser Router" },
  { id: 0.5, name: "ORCHESTRATION", icon: Zap, color: T.coral, desc: "Agentic orchestrator routes each page section to optimal extraction tool. MinerU for complex tables, Docling for text/layout.", tools: "MinerU (primary) | Docling (fallback)" },
  { id: 1, name: "EXTRACT", icon: Database, color: T.teal, desc: "Raw table extraction preserving bounding boxes, page numbers, merged cells, and multi-page stitching.", tools: "MineruTableExtractor | Docling | Generic Configurable Parser" },
  { id: 2, name: "INTERPRET", icon: BarChart3, color: T.navy, desc: "AI maps raw extracted cells to 47 BAR field schema. Wording normalisation, enum validation, product classification (T1–T8).", tools: "LLM + register_row.schema.json + register_enums.json" },
  { id: 2.5, name: "VALIDATE", icon: Shield, color: T.coral, desc: "Validates enum fields against BAR controlled vocabulary. Up to 3 LLM correction attempts for invalid values.", tools: "ValidationIssue → CorrectionStats → LLM re-extraction" },
  { id: 3, name: "SAVE & INDEX", icon: CheckCircle, color: T.success, desc: "Deduplication with SHA-256 composite keys. Contextual embeddings for vector search. Persisted to SurrealDB.", tools: "SurrealDB | Vector embeddings | Parent Document Retrieval" },
];

const logLines = [
  "[Stage -1] Extracting TOC... found 3 sections, 5 buildings",
  "[Stage  0] PDF classified as: digital (non-scanned)",
  "[Stage 0.5] Routing pages 1-4 → MinerU (complex tables detected)",
  "[Stage 0.5] Routing pages 5-6 → Docling (text-heavy layout)",
  "[Stage  1] Extracted 3 tables, 47 rows, 12 merged cells stitched",
  "[Stage  2] Mapped 47 fields. Classification: 31 non-friable, 16 friable",
  "[Stage 2.5] Validation: 3 enum errors corrected via RAG loop (attempt 1/3)",
  "[Stage  3] Saved 44 ACM records to SurrealDB. Embeddings indexed.",
  "✅ Extraction complete in 18.3s — 44 records, 96% confidence",
];

const gridRows = [
  { dept: "DJCS", agency: "VicPol", site: "Rathdowne St HQ", bcode: "B001", btype: "Police Station", level: "Level 1", room: "Corridor", io: "Internal", product: "Cement Sheet", friable: "No", cond: "Good", risk: "Low", result: "Not Detected", rec: "Monitor", page: 12, table: 3, row: 7 },
  { dept: "DJCS", agency: "VicPol", site: "Rathdowne St HQ", bcode: "B001", btype: "Police Station", level: "Level 2", room: "Server Room", io: "Internal", product: "Vinyl Floor Tiles", friable: "No", cond: "Fair", risk: "Medium", result: "Positive", rec: "Encapsulate", page: 12, table: 3, row: 9 },
  { dept: "DHHS", agency: "Health VIC", site: "Royal Melbourne", bcode: "B003", btype: "Hospital", level: "Roof", room: "Plant Room", io: "External", product: "Pipe Lagging", friable: "YES", cond: "Poor", risk: "High", result: "Friable Positive", rec: "Remove Immediately", page: 24, table: 5, row: 2 },
  { dept: "DET", agency: "Schools VIC", site: "Northcote High", bcode: "B012", btype: "School", level: "Ground", room: "Science Lab", io: "Internal", product: "Ceiling Tiles", friable: "No", cond: "Fair", risk: "Medium", result: "Suspected", rec: "Sample & Monitor", page: 31, table: 7, row: 4 },
  { dept: "DHHS", agency: "Health VIC", site: "Royal Melbourne", bcode: "B003", btype: "Hospital", level: "Basement", room: "Mechanical", io: "Internal", product: "Boiler Insulation", friable: "YES", cond: "Deteriorating", risk: "High", result: "Friable Positive", rec: "Remove Immediately", page: 25, table: 5, row: 8 },
  { dept: "DET", agency: "Schools VIC", site: "Northcote High", bcode: "B012", btype: "School", level: "Level 1", room: "Staff Room", io: "Internal", product: "Vinyl Floor Tiles", friable: "No", cond: "Good", risk: "Low", result: "Not Detected", rec: "Monitor", page: 32, table: 7, row: 11 },
];

const epicData = [
  { epic: "E1 Pipeline", stories: 31, title: "ACM Data Extraction Pipeline", highlight: "7-stage agentic pipeline with MinerU + Docling" },
  { epic: "E2 AG Grid", stories: 12, title: "AG Grid Spreadsheet Integration", highlight: "47-column BAR schema with risk colour-coding" },
  { epic: "E3 Citations", stories: 4, title: "Cell Citations & PDF Viewer", highlight: "Click any cell → see PDF source page" },
  { epic: "E4 Chat", stories: 4, title: "Chat with ACM Context", highlight: "LangGraph supervisor with ACM query tools" },
  { epic: "E5 Export", stories: 4, title: "Export Functionality", highlight: "BAR-compliant Excel with template management" },
  { epic: "E6 Brand", stories: 4, title: "Rebranding to ACM-AI", highlight: "VAEA government identity system" },
  { epic: "E7 Upload", stories: 7, title: "Upload Wizard", highlight: "Drag-drop PDF with extraction trigger" },
  { epic: "E9 Library", stories: 3, title: "Document Library Management", highlight: "Bulk operations and processing dashboard" },
  { epic: "E10 Nav", stories: 1, title: "ACM-AI UI Simplification", highlight: "Streamlined ACM-focused navigation" },
  { epic: "E11 Search", stories: 2, title: "Search & Retrieval Enhancement", highlight: "Hybrid search + parent document retrieval" },
  { epic: "E12 Settings", stories: 4, title: "Extraction Settings & Configuration", highlight: "Config-driven field schema, model selection" },
  { epic: "E13 Graph", stories: 3, title: "Knowledge Graph Visualization", highlight: "React Flow entity relationship explorer" },
  { epic: "E14 UX", stories: 11, title: "UX & Enterprise Readiness", highlight: "WCAG 2.1 AA, VAEA tokens, skeletons" },
  { epic: "E15 Monitor", stories: 2, title: "Extraction Monitor & Logging", highlight: "Real-time SSE pipeline progress UI" },
  { epic: "E16 UX+", stories: 3, title: "UX Enhancement Sprint", highlight: "Dashboard home, record detail panel" },
  { epic: "E17 Live AI", stories: 6, title: "Live Extraction Intelligence", highlight: "AG-UI + A2A agent card + reasoning display" },
];

const velocityData = [
  { sprint: "S1", done: 4, target: 8 }, { sprint: "S2", done: 7, target: 8 }, { sprint: "S3", done: 9, target: 8 },
  { sprint: "S4", done: 10, target: 10 }, { sprint: "S5", done: 8, target: 10 }, { sprint: "S6", done: 11, target: 10 },
  { sprint: "S7", done: 12, target: 10 }, { sprint: "S8", done: 10, target: 10 }, { sprint: "S9", done: 11, target: 10 },
  { sprint: "S10", done: 14, target: 10 }, { sprint: "S11", done: 11, target: 10 }, { sprint: "S12", done: 5, target: 10 },
];

const barColumns = [
  "Department","Agency","Sub Agency","Site Name","Building Name","Building Type","Building Address","Suburb","Postcode","Owned or Leased",
  "Building Unique ID","Frequency of Use","Public Access?","Date of Inspection","Est. Year Built","Est. Building Size (m²)","Number of Levels",
  "Construction Type","Roof Type","Internal / External","Level","Room or Area","Location in Room","Specific Item / ACM Name",
  "Friability of Material","ACM Product Group","ACM Product Type","NATA Sample Number","Sample Result","Identifying Hygiene Company",
  "Condition","Disturbance Potential","Quantity","Labelled","Label Details","Hygienist Recommendations","Additional Comments",
  "PSB Supplied ACM ID","Assumed Removed?","Date of Removal","Quantity Removed","Removal Notification No.","EPA Waste Transport Cert No.",
  "Removal Comments","Photo Reference Number"
];

const techStack = [
  ["Frontend", "Next.js 15 + React", "Web UI + AG Grid spreadsheet"],
  ["Backend", "FastAPI (Python)", "REST API + SSE streaming"],
  ["Database", "SurrealDB", "Document + vector + graph store"],
  ["AI Pipeline", "LangGraph", "Agentic workflow orchestration"],
  ["Extraction", "MinerU + Docling", "PDF table extraction (ML-based)"],
  ["AI/LLM", "Esperanto", "Multi-provider: OpenAI, Anthropic, Ollama"],
  ["Grid", "AG Grid v33", "Enterprise spreadsheet component"],
  ["Chat", "CopilotKit + AG-UI", "SSE agent streaming protocol"],
  ["Export", "openpyxl", "BAR Excel generation"],
];

// ─── OVERVIEW SECTION ───
const Overview = () => (
  <div className="space-y-8">
    <div className="text-center py-10 rounded-2xl relative overflow-hidden" style={{ background: `linear-gradient(135deg, ${T.navy} 0%, ${T.teal} 100%)` }}>
      <div className="absolute inset-0 opacity-10" style={{ backgroundImage: "radial-gradient(circle at 20% 50%, white 1px, transparent 1px)", backgroundSize: "30px 30px" }} />
      <div className="relative">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-semibold mb-4" style={{ background: "rgba(255,255,255,0.15)", color: "white" }}>
          <Shield size={14} /> VICTORIAN GOVERNMENT COMPLIANCE
        </div>
        <h1 className="text-4xl font-bold text-white mb-3 tracking-tight">ACM-AI</h1>
        <p className="text-lg text-white opacity-80 max-w-2xl mx-auto">Asbestos Compliance Intelligence — Transforming PDF Asbestos Registers into Victorian Government BAR-compliant data with AI</p>
      </div>
    </div>
    <div className="grid grid-cols-4 gap-4">
      <StatCard icon={CheckCircle} label="Stories Delivered" value="112" color={T.teal} />
      <StatCard icon={Award} label="Epics Complete" value="16" color={T.coral} />
      <StatCard icon={Database} label="Commits" value="281" color={T.navy} />
      <StatCard icon={TrendingUp} label="Completion Rate" value="92%" color={T.success} />
    </div>
    <div>
      <h2 className="text-xl font-bold mb-4" style={{ color: T.navy }}>What ACM-AI Does</h2>
      <div className="grid grid-cols-3 gap-5">
        {[
          { icon: Upload, title: "Upload PDF", desc: "AI extracts asbestos data from any register format — Prensa, Greencap, or custom." },
          { icon: Table, title: "Interactive Spreadsheet", desc: "View all 47 BAR columns in AG Grid with risk colour-coding, sorting, and filtering." },
          { icon: Download, title: "Export BAR Excel", desc: "One-click BAR-compliant Excel export — ready for Victorian Government submission." },
        ].map((c, i) => (
          <div key={i} className="rounded-xl p-6 border border-gray-100 shadow-sm" style={{ background: T.card }}>
            <div className="w-12 h-12 rounded-xl flex items-center justify-center mb-4" style={{ background: T.teal + "14" }}><c.icon size={24} style={{ color: T.teal }} /></div>
            <h3 className="font-bold mb-2" style={{ color: T.navy }}>{c.title}</h3>
            <p className="text-sm leading-relaxed" style={{ color: T.navy + "88" }}>{c.desc}</p>
          </div>
        ))}
      </div>
    </div>
    <div className="rounded-xl p-6 border-l-4" style={{ borderColor: T.teal, background: T.teal + "08" }}>
      <h3 className="font-bold mb-3" style={{ color: T.teal }}>Key Compliance Facts</h3>
      <div className="grid grid-cols-2 gap-2 text-sm" style={{ color: T.navy + "cc" }}>
        {["Targets Victorian Government BAR (Building Asbestos Register) format", "47-column schema matching the official VAEA template",
          "Department → Agency → Site → Building → Room → ACM Item hierarchy", "Supports Friable and Non-friable ACM taxonomy (T1–T8)",
          "Config-driven field schema — no code changes for new BAR fields", "Every data point traced back to source PDF page and cell"
        ].map((f, i) => <div key={i} className="flex items-start gap-2"><CheckCircle size={14} className="mt-0.5 shrink-0" style={{ color: T.teal }} />{f}</div>)}
      </div>
    </div>
  </div>
);

// ─── PIPELINE SECTION ───
const Pipeline = () => {
  const [running, setRunning] = useState(false);
  const [activeStage, setActiveStage] = useState(-2);
  const [logs, setLogs] = useState([]);

  const run = () => {
    setRunning(true); setActiveStage(-1); setLogs([]);
    pipelineStages.forEach((_, i) => {
      setTimeout(() => setActiveStage(i), i * 900);
      setTimeout(() => setLogs(prev => [...prev, logLines[i] || logLines[logLines.length - 1]]), i * 900 + 400);
    });
    setTimeout(() => { setLogs(prev => [...prev, logLines[7], logLines[8]]); setRunning(false); }, pipelineStages.length * 900 + 500);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div><h2 className="text-xl font-bold" style={{ color: T.navy }}>7-Stage Extraction Pipeline</h2><p className="text-sm mt-1" style={{ color: T.navy + "77" }}>From raw PDF to structured compliance data</p></div>
        <button onClick={run} disabled={running} className="flex items-center gap-2 px-5 py-2.5 rounded-lg text-white text-sm font-semibold transition-all" style={{ background: running ? T.navy + "66" : T.coral }}>
          {running ? <Loader size={16} className="animate-spin" /> : <Play size={16} />}{running ? "Processing..." : "Run Demo"}
        </button>
      </div>
      <div className="space-y-2">
        {pipelineStages.map((s, i) => {
          const active = i <= activeStage;
          const current = i === activeStage && running;
          return (
            <div key={i} className="flex items-start gap-3 p-3.5 rounded-xl border transition-all duration-500" style={{ borderColor: active ? s.color + "44" : "#e5e7eb", background: current ? s.color + "08" : active ? s.color + "04" : "white" }}>
              <div className="w-9 h-9 rounded-lg flex items-center justify-center shrink-0 transition-all" style={{ background: active ? s.color : "#e5e7eb" }}>
                <s.icon size={16} style={{ color: active ? "white" : "#999" }} />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono px-1.5 py-0.5 rounded" style={{ background: T.navy + "0c", color: T.navy + "88" }}>Stage {s.id}</span>
                  <span className="font-semibold text-sm" style={{ color: T.navy }}>{s.name}</span>
                  {current && <span className="w-2 h-2 rounded-full animate-pulse" style={{ background: s.color }} />}
                  {active && !current && <CheckCircle size={14} style={{ color: T.success }} />}
                </div>
                <p className="text-xs mt-1 leading-relaxed" style={{ color: T.navy + "77" }}>{s.desc}</p>
                <p className="text-xs mt-1 font-mono" style={{ color: s.color + "aa" }}>{s.tools}</p>
              </div>
            </div>
          );
        })}
      </div>
      <div>
        <h3 className="text-sm font-bold mb-3" style={{ color: T.navy }}>Data Flow</h3>
        <div className="flex items-center gap-1 overflow-x-auto pb-2">
          {["PDF Upload", "MinerU / Docling", "ACM Parser", "SurrealDB", "AG Grid", "BAR Export"].map((s, i) => (
            <div key={i} className="flex items-center gap-1 shrink-0">
              <div className="px-3 py-2 rounded-lg text-xs font-semibold text-white whitespace-nowrap" style={{ background: i % 2 === 0 ? T.teal : T.navy }}>{s}</div>
              {i < 5 && <ArrowRight size={14} style={{ color: T.coral }} />}
            </div>
          ))}
        </div>
      </div>
      {(logs.length > 0 || running) && (
        <div className="rounded-xl p-4 font-mono text-xs leading-relaxed overflow-auto max-h-48" style={{ background: "#0f1419", color: "#4ade80" }}>
          {logs.map((l, i) => <div key={i} className="py-0.5" style={{ color: l.startsWith("✅") ? "#4ade80" : l.includes("Validation") ? "#f59e0b" : "#8b949e" }}>{l}</div>)}
          {running && <span className="animate-pulse">▊</span>}
        </div>
      )}
    </div>
  );
};

// ─── SPREADSHEET SECTION ───
const Spreadsheet = () => {
  const [clicked, setClicked] = useState(null);
  const [preset, setPreset] = useState("essential");
  const riskStyle = (r) => r === "High" ? { borderLeft: `3px solid ${T.rHigh}`, background: T.rHigh + "0a" } : r === "Medium" ? { borderLeft: `3px solid ${T.rMed}`, background: T.rMed + "0a" } : { borderLeft: `3px solid ${T.rLow}`, background: T.rLow + "0a" };
  const riskBadge = (r) => <span className="px-2 py-0.5 rounded text-xs font-bold" style={{ color: r === "High" ? T.rHigh : r === "Medium" ? T.rMed : T.rLow, background: (r === "High" ? T.rHigh : r === "Medium" ? T.rMed : T.rLow) + "18" }}>{r}</span>;

  return (
    <div className="space-y-4">
      <div><h2 className="text-xl font-bold" style={{ color: T.navy }}>AG Grid — Victorian BAR Spreadsheet</h2><p className="text-sm mt-1" style={{ color: T.navy + "77" }}>47-column interactive register with risk colour-coding</p></div>
      <div className="flex items-center gap-2 p-2 rounded-lg border border-gray-200" style={{ background: "#f8fafc" }}>
        <div className="flex items-center gap-1 px-3 py-1.5 rounded border border-gray-200 bg-white text-xs flex-1"><Search size={12} className="text-gray-400" /><span className="text-gray-400">Search records...</span></div>
        <div className="px-3 py-1.5 rounded border border-gray-200 bg-white text-xs" style={{ color: T.navy }}>Filter: All Buildings ▼</div>
        <div className="px-3 py-1.5 rounded border border-gray-200 bg-white text-xs" style={{ color: T.navy }}>Columns ▼</div>
        <button className="px-3 py-1.5 rounded text-xs text-white font-semibold" style={{ background: T.teal }}>Export CSV</button>
        <button className="px-3 py-1.5 rounded text-xs text-white font-semibold" style={{ background: T.coral }}>Export BAR Excel</button>
      </div>
      <div className="relative flex gap-0">
        <div className={`overflow-x-auto rounded-xl border border-gray-200 transition-all ${clicked !== null ? "flex-1" : "w-full"}`}>
          <table className="w-full text-xs">
            <thead>
              <tr style={{ background: T.navy + "08" }}>
                <th colSpan={3} className="px-2 py-1.5 text-left font-bold border-b border-r" style={{ color: T.teal, borderColor: "#e5e7eb" }}>Organisation</th>
                <th colSpan={3} className="px-2 py-1.5 text-left font-bold border-b border-r" style={{ color: T.teal, borderColor: "#e5e7eb" }}>Building</th>
                <th colSpan={3} className="px-2 py-1.5 text-left font-bold border-b border-r" style={{ color: T.teal, borderColor: "#e5e7eb" }}>Location</th>
                <th colSpan={3} className="px-2 py-1.5 text-left font-bold border-b border-r" style={{ color: T.teal, borderColor: "#e5e7eb" }}>ACM Item</th>
                <th colSpan={3} className="px-2 py-1.5 text-left font-bold border-b" style={{ color: T.coral, borderColor: "#e5e7eb" }}>Assessment</th>
              </tr>
              <tr style={{ background: "#fafbfc" }}>
                {["Dept", "Agency", "Site", "Building", "Code", "Type", "Level", "Room", "I/E", "Product", "Friable?", "Condition", "Risk", "Result", "Rec."].map((h, i) => (
                  <th key={i} className="px-2 py-1.5 text-left font-semibold border-b whitespace-nowrap" style={{ color: T.navy + "aa", fontSize: "10px", borderColor: "#e5e7eb" }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {gridRows.map((r, i) => (
                <tr key={i} onClick={() => setClicked(i === clicked ? null : i)} className="cursor-pointer transition-colors hover:bg-gray-50" style={riskStyle(r.risk)}>
                  {[r.dept, r.agency, r.site, r.btype, r.bcode, r.btype, r.level, r.room, r.io, r.product, r.friable, r.cond].map((v, j) => (
                    <td key={j} className="px-2 py-2 border-b whitespace-nowrap" style={{ borderColor: "#f0f0f0", color: T.navy, fontWeight: r.risk === "High" && j >= 9 ? 600 : 400 }}>{v}</td>
                  ))}
                  <td className="px-2 py-2 border-b" style={{ borderColor: "#f0f0f0" }}>{riskBadge(r.risk)}</td>
                  <td className="px-2 py-2 border-b whitespace-nowrap" style={{ borderColor: "#f0f0f0", color: T.navy }}>{r.result}</td>
                  <td className="px-2 py-2 border-b whitespace-nowrap" style={{ borderColor: "#f0f0f0", color: T.navy }}>{r.rec}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {clicked !== null && (
          <div className="w-72 shrink-0 ml-3 rounded-xl border border-gray-200 p-4 space-y-3 shadow-lg" style={{ background: T.card }}>
            <div className="flex items-center justify-between">
              <h4 className="font-bold text-sm" style={{ color: T.navy }}>Citation</h4>
              <button onClick={() => setClicked(null)} className="text-gray-400 text-xs">✕</button>
            </div>
            <div className="space-y-2 text-xs" style={{ color: T.navy + "cc" }}>
              <div className="flex items-center gap-2"><FileText size={13} style={{ color: T.teal }} /> <span className="font-semibold">Source:</span> {gridRows[clicked].site}_ACM_Register.pdf</div>
              <div className="flex items-center gap-2"><Eye size={13} style={{ color: T.teal }} /> <span className="font-semibold">Location:</span> Page {gridRows[clicked].page}, Table {gridRows[clicked].table}, Row {gridRows[clicked].row}</div>
              <div className="font-mono text-xs px-2 py-1 rounded" style={{ background: T.teal + "0c", color: T.teal }}>acm:acm_record:{Math.random().toString(36).substr(2,6)}:risk_status</div>
              <div className="rounded-lg h-24 flex items-center justify-center border" style={{ background: "#f8f8f8" }}>
                <div className="w-16 h-20 rounded border-2 relative" style={{ borderColor: "#ddd", background: "white" }}>
                  <div className="absolute w-10 h-2 rounded top-3 left-1" style={{ background: T.warn + "44", border: `1px solid ${T.warn}` }} />
                  <div className="text-center text-gray-300 mt-6" style={{ fontSize: "6px" }}>PDF Preview</div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
      <div className="flex items-center gap-2">
        {["Essential View", "Full BAR View", "Assessment Focus", "Removal Tracking"].map(p => (
          <button key={p} onClick={() => setPreset(p)} className="px-3 py-1.5 rounded-lg text-xs font-semibold transition-all border" style={{ background: preset === p ? T.teal : "white", color: preset === p ? "white" : T.navy, borderColor: preset === p ? T.teal : "#e5e7eb" }}>{p}</button>
        ))}
      </div>
    </div>
  );
};

// ─── CHAT SECTION ───
const Chat = () => {
  const [typing, setTyping] = useState(true);
  useEffect(() => { const t = setTimeout(() => setTyping(false), 2500); return () => clearTimeout(t); }, []);

  return (
    <div className="space-y-4">
      <div><h2 className="text-xl font-bold" style={{ color: T.navy }}>Smart Chat — AI-Powered ACM Queries</h2><p className="text-sm mt-1" style={{ color: T.navy + "77" }}>Natural language queries against structured register data</p></div>
      <div className="rounded-xl border border-gray-200 overflow-hidden" style={{ background: T.card }}>
        <div className="px-4 py-2.5 flex items-center justify-between border-b" style={{ background: T.navy + "06" }}>
          <span className="text-sm font-semibold" style={{ color: T.navy }}>Smart Chat</span>
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold" style={{ background: T.teal + "18", color: T.teal }}><Table size={11} /> ACM Data ON</span>
        </div>
        <div className="p-4 space-y-4 max-h-96 overflow-y-auto" style={{ background: "#fafbfc" }}>
          <div className="flex justify-end"><div className="px-4 py-2.5 rounded-2xl rounded-tr-md text-sm max-w-md" style={{ background: T.teal, color: "white" }}>Show me all high-risk asbestos items in Building B003</div></div>
          <div className="flex justify-start"><div className="px-4 py-3 rounded-2xl rounded-tl-md text-sm max-w-lg border" style={{ background: "white", color: T.navy }}>
            <p className="font-semibold mb-2">I found 3 high-risk ACM items in Building B003 (Royal Melbourne Hospital):</p>
            {[
              { item: "Pipe Lagging", room: "Plant Room (Roof)", cond: "Poor | Friable | Positive", ref: "a1b2", rec: "Remove Immediately" },
              { item: "Ceiling Tiles", room: "Ward 4B", cond: "Damaged | Non-friable | Suspected", ref: "c3d4", rec: "Priority Assessment" },
              { item: "Boiler Insulation", room: "Basement Mechanical", cond: "Deteriorating | Friable | Positive", ref: "e5f6", rec: "Remove Immediately" },
            ].map((it, i) => (
              <div key={i} className="mb-2 pl-3 border-l-2" style={{ borderColor: T.rHigh }}>
                <p className="font-semibold text-xs">{i + 1}. {it.item} — {it.room}</p>
                <p className="text-xs mt-0.5" style={{ color: T.navy + "88" }}>{it.cond}</p>
                <p className="text-xs font-mono mt-0.5" style={{ color: T.teal }}>[acm:acm_record:{it.ref}:risk_status] → <span style={{ color: T.rHigh, fontWeight: 700 }}>HIGH RISK</span></p>
              </div>
            ))}
            <div className="flex items-center gap-1 mt-2 px-2 py-1 rounded text-xs font-semibold" style={{ background: T.rHigh + "0c", color: T.rHigh }}><AlertTriangle size={12} /> Immediate attention required. All 3 items exceed acceptable risk threshold.</div>
          </div></div>
          <div className="flex justify-end"><div className="px-4 py-2.5 rounded-2xl rounded-tr-md text-sm max-w-md" style={{ background: T.teal, color: "white" }}>What does "friable" mean and why is it more dangerous?</div></div>
          <div className="flex justify-start"><div className="px-4 py-3 rounded-2xl rounded-tl-md text-sm max-w-lg border" style={{ background: "white", color: T.navy }}>
            <p className="mb-2"><strong>Friable</strong> ACM can be crumbled by hand pressure, releasing fibres into the air. This makes it significantly more hazardous than non-friable ACM, which has fibres bound in a matrix.</p>
            <p className="text-xs mb-1" style={{ color: T.navy + "88" }}>Under the Victorian BAR taxonomy:</p>
            <p className="text-xs" style={{ color: T.navy + "88" }}>• Friable uses codes T1–T6 (e.g. T3 = Friable Insulation)</p>
            <p className="text-xs" style={{ color: T.navy + "88" }}>• Non-friable uses T1–T8 (e.g. T1 = Cement, T3 = Vinyl)</p>
            <p className="text-xs mt-2 font-semibold" style={{ color: T.coral }}>Friable items require specialist licensed removal contractors.</p>
            {typing && <span className="inline-block w-2 h-4 ml-1 animate-pulse" style={{ background: T.teal }} />}
          </div></div>
        </div>
      </div>
      <div className="rounded-xl p-4 border border-gray-200" style={{ background: T.card }}>
        <h4 className="text-xs font-bold mb-2" style={{ color: T.navy }}>HOW IT WORKS</h4>
        <div className="flex items-center gap-1 text-xs flex-wrap">
          {["User Message", "Supervisor Agent (LangGraph ReAct)", "ACM Tools (if toggle ON)", "SurrealDB query", "Citation generation", "SSE streamed response"].map((s, i) => (
            <div key={i} className="flex items-center gap-1"><span className="px-2 py-1 rounded" style={{ background: i === 1 ? T.coral + "14" : T.teal + "0c", color: T.navy, fontWeight: 500 }}>{s}</span>{i < 5 && <ArrowRight size={10} style={{ color: T.coral }} />}</div>
          ))}
        </div>
        <div className="flex gap-2 mt-3">
          {["🔍 query_by_building", "⚠️ query_by_risk", "🏢 building_search", "✅ compliance_check"].map(t => (
            <span key={t} className="px-2.5 py-1 rounded-full text-xs font-semibold" style={{ background: T.teal + "10", color: T.teal }}>{t}</span>
          ))}
        </div>
      </div>
    </div>
  );
};

// ─── EXPORT SECTION ───
const Export = () => (
  <div className="space-y-6">
    <div><h2 className="text-xl font-bold" style={{ color: T.navy }}>BAR-Compliant Export</h2><p className="text-sm mt-1" style={{ color: T.navy + "77" }}>Victorian Government submission-ready in one click</p></div>
    <div className="grid grid-cols-2 gap-5">
      <div className="rounded-xl p-6 border-2 space-y-3" style={{ borderColor: T.teal + "44", background: T.card }}>
        <div className="flex items-center gap-3"><FileText size={24} style={{ color: T.teal }} /><h3 className="font-bold" style={{ color: T.navy }}>CSV Export</h3></div>
        <div className="space-y-1.5 text-sm" style={{ color: T.navy + "aa" }}>
          {["All 47 BAR columns included", "Column order matches BAR specification", "UTF-8 encoded", "Filter by building before export", "Named: [SiteName]_ACM_[Date].csv"].map(f => <div key={f} className="flex items-center gap-2"><CheckCircle size={12} style={{ color: T.teal }} />{f}</div>)}
        </div>
        <button className="w-full py-2.5 rounded-lg text-white font-semibold text-sm" style={{ background: T.teal }}>⬇ Download CSV</button>
      </div>
      <div className="rounded-xl p-6 border-2 space-y-3" style={{ borderColor: T.coral + "44", background: T.card }}>
        <div className="flex items-center gap-3"><Table size={24} style={{ color: T.coral }} /><h3 className="font-bold" style={{ color: T.navy }}>BAR Excel (.xlsx)</h3></div>
        <div className="space-y-1.5 text-sm" style={{ color: T.navy + "aa" }}>
          {["Exact BAR column headers from VAEA template", "Column order matches official BAR spec (47 columns)", "Risk status cells colour-coded", "Header row frozen, columns auto-sized", "Data validation dropdowns for enum fields", "Optional reference sheets (Building Types, Product Types)", "Template versioning — upload new template without code changes"].map(f => <div key={f} className="flex items-center gap-2"><CheckCircle size={12} style={{ color: T.coral }} />{f}</div>)}
        </div>
        <button className="w-full py-2.5 rounded-lg text-white font-semibold text-sm" style={{ background: T.coral }}>⬇ Export BAR Excel</button>
      </div>
    </div>
    <div>
      <h3 className="text-sm font-bold mb-2" style={{ color: T.navy }}>The 45 BAR Columns</h3>
      <div className="grid grid-cols-3 gap-x-4 text-xs max-h-52 overflow-y-auto rounded-xl p-4 border" style={{ background: "#fafbfc", color: T.navy + "bb" }}>
        {barColumns.map((c, i) => <div key={i} className="py-0.5"><span className="font-mono mr-1.5" style={{ color: T.teal }}>{i + 1}.</span>{c}</div>)}
      </div>
    </div>
    <div className="rounded-xl p-4 border-l-4" style={{ borderColor: T.coral, background: T.coral + "06" }}>
      <p className="text-sm" style={{ color: T.navy }}><strong>Site Configuration:</strong> Non-extractable fields (Department, Agency, Building Type, etc.) are configured via the Site Config form before export — ensuring 100% BAR field coverage.</p>
    </div>
  </div>
);

// ─── PROGRESS SECTION ───
const Progress = () => (
  <div className="space-y-6">
    <div><h2 className="text-xl font-bold" style={{ color: T.navy }}>Project Delivery Dashboard</h2><p className="text-sm mt-1" style={{ color: T.navy + "77" }}>ACM-AI v1.0 — Feature Complete as of 22 Feb 2026</p></div>
    <div className="grid grid-cols-4 gap-4">
      <StatCard icon={CheckCircle} label="Stories Done" value="112 / 122" color={T.teal} />
      <StatCard icon={Award} label="Epics Complete" value="16 / 17" color={T.coral} />
      <StatCard icon={Database} label="Commits" value="281" color={T.navy} />
      <StatCard icon={Shield} label="Change Proposals" value="5 Navigated" color={T.success} />
    </div>
    <div className="rounded-xl border p-4" style={{ background: T.card }}>
      <h3 className="text-sm font-bold mb-3" style={{ color: T.navy }}>Stories per Epic</h3>
      <ResponsiveContainer width="100%" height={250}>
        <BarChart data={epicData} margin={{ bottom: 60 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis dataKey="epic" angle={-40} textAnchor="end" fontSize={10} tick={{ fill: T.navy + "88" }} />
          <YAxis fontSize={10} tick={{ fill: T.navy + "88" }} />
          <Tooltip contentStyle={{ borderRadius: 8, border: "1px solid #eee", fontSize: 12 }} />
          <Bar dataKey="stories" fill={T.teal} radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
    <div className="rounded-xl border overflow-hidden" style={{ background: T.card }}>
      <table className="w-full text-xs">
        <thead><tr style={{ background: T.navy + "08" }}><th className="px-3 py-2 text-left font-bold" style={{ color: T.navy }}>Epic</th><th className="px-3 py-2 text-left font-bold" style={{ color: T.navy }}>Title</th><th className="px-3 py-2 text-center font-bold" style={{ color: T.navy }}>Stories</th><th className="px-3 py-2 text-center font-bold" style={{ color: T.navy }}>Status</th><th className="px-3 py-2 text-left font-bold" style={{ color: T.navy }}>Key Achievement</th></tr></thead>
        <tbody>
          {epicData.map((e, i) => (
            <tr key={i} className="border-t" style={{ borderColor: "#f0f0f0" }}>
              <td className="px-3 py-2 font-mono font-semibold" style={{ color: T.teal }}>{e.epic.split(" ")[0]}</td>
              <td className="px-3 py-2" style={{ color: T.navy }}>{e.title}</td>
              <td className="px-3 py-2 text-center font-bold" style={{ color: T.navy }}>{e.stories}</td>
              <td className="px-3 py-2 text-center">{e.epic.includes("E8") ? <Badge color={T.navy}>📦 ARCHIVED</Badge> : <Badge color={T.success}>✅ DONE</Badge>}</td>
              <td className="px-3 py-2 text-xs" style={{ color: T.navy + "88" }}>{e.highlight}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
    <div className="rounded-xl border p-4" style={{ background: T.card }}>
      <h3 className="text-sm font-bold mb-3" style={{ color: T.navy }}>Sprint Velocity</h3>
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={velocityData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis dataKey="sprint" fontSize={10} tick={{ fill: T.navy + "88" }} />
          <YAxis fontSize={10} tick={{ fill: T.navy + "88" }} />
          <Tooltip contentStyle={{ borderRadius: 8, border: "1px solid #eee", fontSize: 12 }} />
          <Legend />
          <Line type="monotone" dataKey="done" stroke={T.teal} strokeWidth={2.5} name="Completed" dot={{ fill: T.teal }} />
          <Line type="monotone" dataKey="target" stroke={T.coral} strokeWidth={1.5} strokeDasharray="6 3" name="Target" dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  </div>
);

// ─── ARCHITECTURE SECTION ───
const ArchBox = ({ label, sub, color = T.teal, w = "auto" }) => (
  <div className="px-3 py-2 rounded-lg text-center border" style={{ background: color + "10", borderColor: color + "33", minWidth: w }}>
    <div className="text-xs font-bold" style={{ color }}>{label}</div>
    {sub && <div className="text-xs mt-0.5" style={{ color: T.navy + "77" }}>{sub}</div>}
  </div>
);

const Architecture = () => (
  <div className="space-y-6">
    <div><h2 className="text-xl font-bold" style={{ color: T.navy }}>Technical Architecture</h2><p className="text-sm mt-1" style={{ color: T.navy + "77" }}>FastAPI + SurrealDB + LangGraph + Next.js</p></div>
    <div className="rounded-xl border p-5 space-y-3" style={{ background: T.card }}>
      <h3 className="text-sm font-bold" style={{ color: T.navy }}>System Architecture</h3>
      <div className="flex flex-col items-center gap-2">
        <ArchBox label="Browser Client" sub=":8502" color={T.navy} w="200px" />
        <ArrowRight size={14} className="rotate-90" style={{ color: T.coral }} />
        <ArchBox label="Next.js Frontend" sub="/api/* proxy" color={T.teal} w="200px" />
        <ArrowRight size={14} className="rotate-90" style={{ color: T.coral }} />
        <ArchBox label="FastAPI Backend" sub="REST + SSE :5055" color={T.coral} w="200px" />
        <ArrowRight size={14} className="rotate-90" style={{ color: T.coral }} />
        <div className="flex gap-3">
          <ArchBox label="SurrealDB" sub="Doc + Vector + Graph :8000" color={T.teal} />
          <ArchBox label="Background Worker" sub="surreal-commands" color={T.navy} />
          <ArchBox label="MinerU / Docling" sub="PDF extraction" color={T.coral} />
        </div>
      </div>
    </div>
    <div className="rounded-xl border p-5 space-y-3" style={{ background: T.card }}>
      <h3 className="text-sm font-bold" style={{ color: T.navy }}>Chat Architecture</h3>
      <div className="flex items-center gap-1 flex-wrap text-xs">
        {[
          ["User", T.navy], ["CopilotKit (AG-UI)", T.teal], ["SSE /api/agui/chat", T.coral],
          ["LangGraph Supervisor", T.navy], ["ACM Tools / Search Tools", T.teal], ["SurrealDB", T.coral], ["Streamed Response", T.success]
        ].map(([l, c], i) => (
          <div key={i} className="flex items-center gap-1"><span className="px-2 py-1 rounded font-semibold" style={{ background: c + "14", color: c }}>{l}</span>{i < 6 && <ArrowRight size={10} style={{ color: T.coral }} />}</div>
        ))}
      </div>
    </div>
    <div className="rounded-xl border p-5 space-y-3" style={{ background: T.card }}>
      <h3 className="text-sm font-bold" style={{ color: T.navy }}>Data Model</h3>
      <div className="flex gap-2 flex-wrap">
        {["source", "acm_record", "acm_table_section", "site_config", "bar_template", "field_schema", "school", "building", "room"].map(t => (
          <div key={t} className="px-3 py-2 rounded-lg border text-xs font-mono font-semibold" style={{ borderColor: T.teal + "44", color: T.teal, background: T.teal + "06" }}>{t}</div>
        ))}
      </div>
      <div className="text-xs" style={{ color: T.navy + "77" }}>Graph relations: school→building→room→acm_record→source (SurrealDB RELATE)</div>
    </div>
    <div className="rounded-xl border overflow-hidden" style={{ background: T.card }}>
      <table className="w-full text-xs">
        <thead><tr style={{ background: T.navy + "08" }}><th className="px-3 py-2 text-left font-bold" style={{ color: T.navy }}>Layer</th><th className="px-3 py-2 text-left font-bold" style={{ color: T.navy }}>Technology</th><th className="px-3 py-2 text-left font-bold" style={{ color: T.navy }}>Purpose</th></tr></thead>
        <tbody>{techStack.map(([l, t, p], i) => (
          <tr key={i} className="border-t" style={{ borderColor: "#f0f0f0" }}>
            <td className="px-3 py-2 font-semibold" style={{ color: T.teal }}>{l}</td>
            <td className="px-3 py-2 font-mono" style={{ color: T.navy }}>{t}</td>
            <td className="px-3 py-2" style={{ color: T.navy + "88" }}>{p}</td>
          </tr>
        ))}</tbody>
      </table>
    </div>
  </div>
);

// ─── STAKEHOLDERS SECTION ───
const audienceData = {
  Director: {
    headline: "Risk Mitigation + Operational Efficiency",
    cards: [
      "Hours saved per document: 8–12 hours of manual data entry eliminated",
      "Accuracy: 90%+ extraction accuracy vs error-prone manual entry",
      "Compliance: 100% BAR field coverage — no submission gaps",
      "Traceability: Every data point linked back to source PDF page",
    ],
    callout: "Reduces liability exposure from incomplete asbestos registers",
  },
  CTO: {
    headline: "Enterprise-Grade Architecture",
    cards: [
      "Stack: FastAPI + SurrealDB + LangGraph + Next.js 15",
      "AI: Multi-provider LLM (OpenAI, Anthropic, Ollama) via Esperanto",
      "Extraction: MinerU (ML-based) + Docling — handles merged cells, multi-page tables",
      "Protocol: AG-UI + CopilotKit for real-time SSE agent streaming",
      "Schema: Config-driven (JSON), no code changes for new BAR fields",
    ],
    callout: "All processing is local-first — zero external API calls for document extraction",
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
      "📤 Upload your PDF asbestos register — drag and drop, any format",
      "⚙️ Configure site details (Department, Agency, Building Type) once",
      "⏱️ Wait ~18 seconds — AI extracts all tables automatically",
      "📊 Review your data in the interactive spreadsheet — sort, filter, search",
      "💬 Ask questions in plain English: 'What's high risk in Building B?'",
      "📄 Click to see exactly which PDF page each data row came from",
      "📤 Export BAR-compliant Excel — ready for government submission",
    ],
    callout: "No training needed. No manual data entry. No compliance gaps.",
  },
};

const Stakeholders = () => {
  const [tab, setTab] = useState("Director");
  const d = audienceData[tab];
  return (
    <div className="space-y-5">
      <div><h2 className="text-xl font-bold" style={{ color: T.navy }}>Value by Audience</h2></div>
      <div className="flex gap-1 p-1 rounded-xl" style={{ background: T.navy + "08" }}>
        {Object.keys(audienceData).map(k => (
          <button key={k} onClick={() => setTab(k)} className="flex-1 py-2 rounded-lg text-sm font-semibold transition-all" style={{ background: tab === k ? T.teal : "transparent", color: tab === k ? "white" : T.navy + "88" }}>{k}</button>
        ))}
      </div>
      <div className="rounded-xl p-6 border" style={{ background: T.card }}>
        <h3 className="text-lg font-bold mb-4" style={{ color: T.navy }}>{d.headline}</h3>
        <div className="space-y-2">
          {d.cards.map((c, i) => (
            <div key={i} className="flex items-start gap-3 p-3 rounded-lg" style={{ background: T.teal + "06" }}>
              <CheckCircle size={16} className="mt-0.5 shrink-0" style={{ color: T.teal }} />
              <span className="text-sm" style={{ color: T.navy }}>{c}</span>
            </div>
          ))}
        </div>
        <div className="mt-4 p-4 rounded-xl border-l-4" style={{ borderColor: T.coral, background: T.coral + "06" }}>
          <p className="text-sm font-semibold" style={{ color: T.coral }}>{d.callout}</p>
        </div>
      </div>
    </div>
  );
};

// ─── MAIN APP ───
export default function ACMAIDemo() {
  const [active, setActive] = useState("overview");
  const content = { overview: <Overview />, pipeline: <Pipeline />, spreadsheet: <Spreadsheet />, chat: <Chat />, export: <Export />, progress: <Progress />, architecture: <Architecture />, stakeholders: <Stakeholders /> };

  return (
    <div className="flex h-screen" style={{ background: T.bg, fontFamily: "'Segoe UI', system-ui, -apple-system, sans-serif" }}>
      <aside className="w-56 shrink-0 border-r flex flex-col" style={{ background: T.navy }}>
        <div className="p-4 border-b" style={{ borderColor: "rgba(255,255,255,0.08)" }}>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: T.teal }}><Shield size={16} className="text-white" /></div>
            <div><div className="text-sm font-bold text-white tracking-tight">ACM-AI</div><div className="text-xs" style={{ color: "rgba(255,255,255,0.45)" }}>v1.0 • VAEA</div></div>
          </div>
        </div>
        <nav className="flex-1 p-2 space-y-0.5">
          {sections.map(s => (
            <button key={s.id} onClick={() => setActive(s.id)} className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-all text-left" style={{ background: active === s.id ? T.teal + "22" : "transparent", color: active === s.id ? "white" : "rgba(255,255,255,0.55)" }}>
              <s.icon size={16} style={{ color: active === s.id ? T.teal : "rgba(255,255,255,0.35)" }} />
              <span className="font-medium">{s.label}</span>
            </button>
          ))}
        </nav>
        <div className="p-3 border-t" style={{ borderColor: "rgba(255,255,255,0.08)" }}>
          <div className="px-3 py-2 rounded-lg text-xs text-center" style={{ background: T.success + "18", color: T.success }}>
            <span className="font-bold">Feature Complete</span><br />22 Feb 2026
          </div>
        </div>
      </aside>
      <main className="flex-1 overflow-y-auto p-6">
        <div className="max-w-5xl mx-auto">{content[active]}</div>
      </main>
    </div>
  );
}
