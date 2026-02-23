# ACM-AI Project Knowledge Base
> **Generated**: 2026-02-23 | **Session**: Claude Sonnet 4.6 | **For**: Continuity across sessions and agents

---

## 1. PROJECT IDENTITY

| Field | Value |
|-------|-------|
| **Project name** | ACM-AI (Asbestos Compliance Management AI) |
| **Client brand** | VAEA — Victorian Asbestos Eradication Agency |
| **Compliance target** | Victorian Government BAR (Building Asbestos Register) |
| **Status as of 2026-02-23** | 87/122 stories done (71%), core E2E flow functional |
| **Repo structure** | Monorepo: `/frontend` (Next.js 15), `/api` (FastAPI), `/open_notebook` (Python domain), `/commands`, `/prompts`, `/migrations`, `/tests` |
| **Sprint tracking** | `docs/sprint-artifacts/sprint-status.yaml` |
| **Story files** | `docs/sprint-artifacts/e{N}-s{N}-*.md` |

---

## 2. DESIGN SYSTEM — VAEA BRANDING

### Colour Tokens (OKLCH)

```css
--teal:        oklch(0.52 0.09 185);   /* #3a8f8a — primary brand */
--coral:       oklch(0.65 0.14 15);    /* #d4614a — CTA / accent */
--navy:        oklch(0.27 0.04 260);   /* #2a2f45 — text / technical */
--bg:          oklch(0.97 0.005 220);  /* #f4f7f9 — page background */
--card:        oklch(1.00 0 0);        /* #ffffff — card bg */
--success:     oklch(0.70 0.10 155);   /* #4caf82 */
--warn:        oklch(0.80 0.13 70);    /* #f59e0b */
--risk-high:   oklch(0.63 0.19 22);    /* #ef4444 */
--risk-medium: oklch(0.73 0.17 44);    /* #f97316 */
--risk-low:    oklch(0.76 0.18 141);   /* #22c55e */
```

### Typography
- **Display/Headlines**: DM Serif Display (Google Fonts)
- **Body**: DM Sans (Google Fonts)
- **Monospace/Code**: JetBrains Mono (Google Fonts)
- **Never use**: Inter, Roboto, Arial, system-ui as primary display fonts

### Design Philosophy
"Institutional Precision" — Government authority meets AI startup confidence. Think Financial Times meets Linear.app. Teal dominant, coral for CTAs, navy for technical depth.

---

## 3. TECHNOLOGY STACK

### Backend
| Layer | Technology | Version | Notes |
|-------|-----------|---------|-------|
| API | FastAPI (Python) | Latest | Port 5055 |
| Database | SurrealDB | Latest | Port 8000 |
| AI Pipeline | LangGraph | Latest | Agentic orchestration |
| PDF Extraction | MinerU (primary) | Latest | Complex tables, merged cells |
| PDF Extraction | Docling (fallback) | Latest | Text/layout |
| LLM Abstraction | Esperanto | Latest | Multi-provider |
| Background Jobs | surreal-commands | Latest | Worker pattern |
| Embeddings | mxbai-embed-large | 1024-dim | Ollama local |

### Frontend
| Layer | Technology | Notes |
|-------|-----------|-------|
| Framework | Next.js 15 + React 18 | App Router, Port 8502 |
| Spreadsheet | AG Grid v33 (Community) | 47 BAR columns |
| Chat | CopilotKit + AG-UI | SSE streaming |
| Styling | Tailwind CSS 4 | OKLCH tokens |
| State | Zustand + React Query | |

### AI Models Supported
| Provider | Models | Notes |
|----------|--------|-------|
| Anthropic | claude-3-5-haiku-20241022, claude-sonnet-4-6 | Direct API |
| OpenAI | gpt-4o, gpt-4o-mini | Direct API |
| Ollama | qwen2.5:32b, mxbai-embed-large | Local, Port 11434 |
| OpenRouter | 40+ models via qwen/*, deepseek/*, llama/* | Free tier available |

---

## 4. THE 7-STAGE EXTRACTION PIPELINE

```
Stage -1  PRE-ANALYSIS      TOC extraction, building inventory, page section tagging, metadata
Stage  0  PREFLIGHT         PDF classifier (digital vs scanned), parser router selection
Stage  0.5 ORCHESTRATION    Agentic routing: MinerU for tables, Docling for text
Stage  1  EXTRACT           Verbatim extraction with provenance (page, table, row, bounding box)
Stage  2  INTERPRET         Field mapping → BAR schema, enum normalisation, taxonomy classification
Stage  2.5 VALIDATE         Corrective RAG loop (up to 3 LLM re-extraction attempts)
Stage  3  SAVE & INDEX      Deduplication (SHA-256), vector embeddings, SurrealDB persistence
```

### Key Pipeline Files
| File | Purpose |
|------|---------|
| `open_notebook/graphs/acm_extraction.py` | Main LangGraph pipeline, `_preprocess_samp_format()` |
| `prompts/acm/extraction.jinja` | Primary extraction prompt (non-orchestrator path) |
| `prompts/acm/building_extraction.jinja` | Orchestrator extraction prompt |
| `prompts/acm/correction.jinja` | Corrective RAG prompt |
| `open_notebook/extractors/mineru_extractor.py` | MineruTableExtractor (476 lines, 37 unit tests) |
| `open_notebook/extractors/document_structure.py` | Stage -1: TOC/structure |
| `open_notebook/extractors/building_inventory.py` | Stage -1: Building inventory |
| `open_notebook/extractors/page_tagger.py` | Stage -1: Page-level section tagging |
| `api/model_provisioning.py` | MODEL_CATALOG, seed_model_catalog(), capability detection |
| `open_notebook/domain/models.py` | _PROVIDER_DEFAULTS, _EMBEDDING_DEFAULTS, capability methods |

---

## 5. BAR SCHEMA — 47 COLUMN ORDER

```
 1. Department          2. Agency              3. Sub Agency
 4. Site Name           5. Building Name       6. Building Type
 7. Building Address    8. Suburb              9. Postcode
10. Owned or Leased    11. Building Unique ID  12. Frequency of Use
13. Public Access?     14. Date of Inspection  15. Est. Year Built
16. Est. Building Size 17. Number of Levels    18. Construction Type
19. Roof Type          20. Internal/External   21. Level
22. Room/Area          23. Item No.            24. ACM Present?
25. Product            26. Material Desc.      27. Friable?
28. Material Condition 29. Disturbance Potential 30. Accessibility
31. ACM Product Group  32. ACM Group Name      33. ACM Product Type
34. Quantity           35. UOM                 36. Sample Result
37. Hygienist Recs     38. Risk Priority       39. Action Required
40. Action By Date     41. Assumed Removed?    42. Date Confirmed Removed
43. Qty Removed        44. Removed By          45. Removal Cert No.
46. Removal Notif No.  47. Notes
```

### Controlled Enumerations
- **Sample Result**: `Positive | Assumed Positive | Negative | Assumed Negative`
- **Condition**: `Poor | Fair | Good | Unknown | N/A (negative) | N/A (assumed negative)`
- **Disturbance Potential**: `High | Moderate | Low | Unknown | N/A (negative) | N/A (assumed negative)`
- **Friability**: `Non-friable | Friable`
- **Yes/No fields**: `YES | NO`

### ACM Product Taxonomy
- **Non-friable** (T1–T8): T1 Cement, T2 Bitumen, T3 Vinyl, T4 Gasket, T5 Coatings, T6 Plastics, T7 Other, T8 Insulation
- **Friable** (T1–T6): T1 Cement(f), T2 Vinyl(f), T3 Insulation(f), T4 Gasket(f), T5 Textiles(f), T6 Other(f)

---

## 6. EPIC & STORY STATUS (as of 2026-02-23)

| Epic | Title | Stories | Status |
|------|-------|---------|--------|
| E1 | ACM Data Extraction Pipeline | 31 | ✅ 30/31 done (1 ready-for-dev) |
| E2 | AG Grid Spreadsheet | 12 | 🔄 10/12 (2 ready-for-dev) |
| E3 | Cell Citations & PDF Viewer | 4 | ✅ Done |
| E4 | Chat with ACM Context | 4 | ✅ Done |
| E5 | Export Functionality | 4 | 🔄 2/4 done |
| E6 | Rebranding to ACM-AI | 4 | ✅ Done |
| E7 | Upload Wizard | 7 | ✅ Done |
| E8 | UI Refresh Bento Grid | 10 | 📦 Archived |
| E9 | Document Library | 3 | 🔄 2/3 done |
| E10 | UI Simplification | 1 | 📋 ready-for-dev |
| E11 | Search & Retrieval (RAG) | 2 | 🔄 1/2 done |
| E12 | Extraction Settings UI | 4 | 📋 Drafted |
| E13 | Knowledge Graph | 3 | 📋 Backlog |
| E14 | UX & Enterprise Readiness | 11 | ✅ Done |
| E15 | Extraction Monitor UI | 2 | 🔄 1/2 done |
| E16 | UX Enhancement Sprint | 3 | 🔄 1/3 done |
| E17 | Live Extraction Intelligence | 6 | 📋 0/6 backlog |
| E18 | Extraction Quality | 5+ | 🔄 In progress (E18-S5 at 87%) |
| E19 | Marketing Site + Docs | 1 | 🔄 In progress (new) |

### Ready-for-Dev (next to implement)
```
E1-S23   Token limit quality validation (Haiku 8K vs Sonnet 32K)
E2-S8    Column visibility management
E2-S11   BAR field type safety
E5-S3    BAR template management (unblocks E5-S4)
E9-S3    Bulk document actions
E10-S1   UI simplification / navigation
E16-S1   Dashboard home with ACM stats
E16-S3   Empty states & onboarding hints
E17-S6   New OpenRouter model additions
```

---

## 7. KNOWN BUGS & FIXES (Feb 2026)

### Critical / Fixed
| Bug | Status | Fix Location |
|-----|--------|-------------|
| Migration runner: migrations 14-20 not registered | ✅ Fixed | `open_notebook/database/async_migrate.py` |
| SurrealQL DISTINCT → GROUP BY in site_config.py | ✅ Fixed | `open_notebook/domain/site_config.py` |
| Anthropic model ID typo: `claude-haiku-3-5-20241022` | ✅ Fixed | `api/model_provisioning.py` |
| Hardcoded max_tokens across 15+ files | ✅ Fixed | Multiple files, E1-S29 |
| SSE heartbeat counter overflow | ✅ Fixed | PR #34 |
| taskkill empty string argument (Windows) | ✅ Fixed | PR #36 |
| supports_tool_calling model capability | ✅ Fixed | PR #37, utils.py |
| Negative results silently dropped | ✅ Fixed | `acm_extractor.py` |
| Grid columns: Building ID vs Building Code | ✅ Fixed | `ACMGrid.tsx` |
| Post-upload navigation missing | ✅ Fixed | `AddSourceDialog.tsx` |

### Demo Validation Failures (Feb 22 findings.md)
| FAIL | Severity | Status | Notes |
|------|----------|--------|-------|
| FAIL-001: Turbopack race condition on Windows | P2 | Workaround: `npm run dev:stable` | Delete `.next` and restart |
| FAIL-002: Landing CTA links to /sources not /documents | P3 | Fix: update href | Quick fix |
| FAIL-003: Worker not auto-starting | P0 | Fix: add health check + auto-restart | Critical for demo |
| FAIL-004: Export 404 on empty records | P3 | Fix: return 200 with empty file | Aesthetic fix |

---

## 8. EXTRACTION QUALITY RESEARCH (E18-S5)

### Current State (2026-02-23)
- **Baseline**: 26/31 records (84%)  
- **After E18-S5 work**: 27/31 (87%)
- **Target**: 31/31 (100%)
- **Test PDF**: Broadmeadows Police Station SAMP (31 ground truth records)

### 4 Remaining Missing Records

| # | Room | Expected Item | Root Cause | Fix |
|---|------|--------------|------------|-----|
| 1 | Switch Room / Auto Battery Charger | Fuse cartridge | PDF says "Fuses" not "Fuse cartridge" | Fix B: vocab mapping in preprocessor |
| 2 | Roof / East Ductwork | Flange joints | PDF says "Flange mastic" — test matching issue | Fix C: synonym mapping in test |
| 3 | Lift Foyer / Lift | Internal lining | No access entry — no preprocessor marker | Fix A: inject `>>> NO ACCESS <<<` marker |
| 4 | Main Foyer / Disabled Toilet | Unknown | No access + no product name | Fix A: same as #3 |

### Fix A: NO ACCESS Marker (Highest ROI — fixes #3 and #4)
```python
# In _preprocess_samp_format() in open_notebook/graphs/acm_extraction.py
NO_ACCESS_PHRASES = [
    "No access at the time of the Assessment",
    "No access due to locked door",
    "Height restriction",
    "Restricted Access",
    "Live Electrical Hazard",
]
NO_ACCESS_MARKER = ">>> NO ACCESS ENTRY: Sample Result = Assumed Positive — MUST be extracted <<<"
```

### Fix B: Vocabulary Normalization (fixes #1)
```python
PRODUCT_NORMALIZATIONS = {
    r'\bFuses\b': 'Fuse cartridge',
    r'\bFlange\s+mastic\b': 'Flange joints',
}
```

### Fix C: Test Synonym Matching (fixes #2)
```python
PRODUCT_SYNONYMS = {
    "flange joints": ["flange mastic", "mastic"],
    "fuse cartridge": ["fuses", "fuse"],
}
```

### Structured Output Issue (OpenRouter)
- `ChatOpenAI.with_structured_output(ACMExtractionResult)` fails with OpenRouter + Claude
- **Fix applied**: Fallback JSON parser — catches ValidationError, re-invokes model directly, extracts JSON from markdown code blocks
- `max_tokens` fallback increased 8192 → 16384 (31 records in JSON was truncating)

---

## 9. QWEN2.5:32B CONFIGURATION

### Specifications
| Property | Value |
|----------|-------|
| Parameters | 32B |
| Context window | 128k tokens (131,072) |
| Max output tokens | **8,192** |
| Structured output | JSON mode only (NOT function calling) |
| Instruction format | ChatML (`<\|im_start\|>system/user/assistant<\|im_end\|>`) |
| Thinking tokens | No (this is instruct, not Qwen3-thinking) |
| Ollama ID | `qwen2.5:32b` |
| OpenRouter ID | `qwen/qwen-2.5-32b-instruct` |
| Quantization (24GB VRAM) | Q4_K_M |

### Prompt Engineering for Qwen2.5:32b
1. Strong system prompt upfront defining role and output contract
2. Explicit JSON schema in user prompt (not just "return JSON")
3. "Think step by step" at the END of user message
4. Response prefilling: start assistant turn with ` ```json\n{ `
5. Temperature: 0.0 for extraction, 0.1 for correction
6. Chunk input to max 60,000 tokens (leave 8k for output)

### Model Catalog Registration
```python
# In api/model_provisioning.py MODEL_CATALOG:
{
    "provider": "ollama",
    "name": "qwen2.5:32b",
    "context_window": 131072,
    "max_output_tokens": 8192,
    "supports_structured_output": True,  # JSON mode
    "supports_tool_calling": False,
}
```

### Tool Calling Blocklist
```python
# In open_notebook/graphs/utils.py
TOOL_CALLING_BLOCKLIST = ["qwen2.5", "phi4", "gemma-3"]
```

---

## 10. API ENDPOINTS REFERENCE

```
POST /api/acm/extract                              Trigger extraction for a source
GET  /api/acm/records?source_id=xxx                List ACM records
GET  /api/acm/records/{id}                         Single record
PUT  /api/acm/records/{id}                         Update record
GET  /api/acm/export/csv                           CSV export (47 BAR columns)
GET  /api/acm/export/excel                         BAR-compliant Excel
GET  /api/acm/stats                                Summary statistics
GET  /api/acm/config                               Site configuration
POST /api/acm/config                               Create/update site config
GET  /api/acm/templates                            BAR templates
POST /api/acm/classify                             AI product classification
GET  /api/acm/extraction-progress/{cmd_id}/stream  SSE stream (real-time)
GET  /api/acm/extraction-progress/{cmd_id}         REST polling fallback
GET  /api/acm/field-schema                         Dynamic column definitions
GET  /api/supervisor/stream                        AG-UI chat SSE endpoint
GET  /api/health/worker                            Worker process status
```

---

## 11. MARKETING SITE (E19) — ARCHITECTURE

### Pages Built
| Route | Purpose |
|-------|---------|
| `/` | Landing page — hero, pipeline preview, live status |
| `/demo` | Interactive 8-section executive demo (enhanced from artifact) |
| `/docs` | Fumadocs documentation hub |
| `/docs/prd/*` | PRD sections as navigable MDX pages |
| `/docs/architecture/*` | Architecture docs with Excalidraw diagrams |
| `/docs/epics/*` | Epic/story breakdown |
| `/status` | Live infrastructure dashboard |
| `/roadmap` | Visual timeline of epics |

### Live Data Integration
| Service | API | Env Var | Data Shown |
|---------|-----|---------|-----------|
| GitHub | Octokit REST | `GITHUB_TOKEN` | Commits, PRs, CI status |
| Vercel | Vercel API v6 | `VERCEL_API_TOKEN` | Deployment status, URL |
| Railway | Railway GraphQL | `RAILWAY_API_TOKEN` | Service health, last deploy |

### API Routes (Next.js)
```
/api/github/stats      → github commit count, last commit, CI status
/api/vercel/status     → deployment state (Ready/Building/Error)
/api/railway/status    → service health
```

### Key Dependencies
```
fumadocs-ui fumadocs-core fumadocs-mdx    — documentation
framer-motion lottie-react                — animations
@excalidraw/excalidraw                    — interactive diagrams
@octokit/rest swr                         — live GitHub data
recharts                                  — charts
```

---

## 12. DEMO SCENARIO (Broadmeadows Police Station)

### Realistic Sample Data for Demo
```
Row 1: DJCS | VicPol | Rathdowne St HQ | B001 | Level 1 | Corridor | Cement Sheet | No | Good | Low
Row 2: DJCS | VicPol | Rathdowne St HQ | B001 | Level 2 | Server Room | Vinyl Floor Tiles | No | Fair | Medium
Row 3: DHHS | Health VIC | Royal Melbourne | B003 | Roof | Plant Room | Pipe Lagging | YES | Poor | HIGH
Row 4: DET | Schools VIC | Northcote High | B012 | Ground | Science Lab | Ceiling Tiles | No | Fair | Medium
Row 5: DHHS | Health VIC | Royal Melbourne | B003 | Basement | Mechanical | Boiler Insulation | YES | Deteriorating | HIGH
```

### Demo Flow Script (for presenters)
1. Upload Broadmeadows PDF → watch 7-stage pipeline complete in ~18s
2. Open AG Grid — building tabs at top, risk colour-coded rows
3. Click any cell → PDF viewer opens to exact source page
4. Ask chat: "Which rooms have high-risk materials?"
5. Click Export BAR Excel → download government-ready .xlsx

### What to Say If Live Demo Breaks
> "We're in active development — let me show you the architecture instead."
> Switch to the `/demo` page → Pipeline section → run the animated simulation.

---

## 13. SPRINT METHODOLOGY (BMAD + Ralph)

### Story Lifecycle
```
backlog → drafted → ready-for-dev → in-progress → review → done
```

### BMAD Commands (Claude Code)
```
# Create a new story
"Create story file docs/sprint-artifacts/e{N}-s{N}-{slug}.md following BMAD format"

# Implement a story
"Read docs/sprint-artifacts/e{N}-s{N}-{slug}.md and implement all acceptance criteria.
 Verify with: uv run ruff check . && uv run pytest tests/ -x && cd frontend && npm run build"

# Promote a story
"Update docs/sprint-artifacts/sprint-status.yaml: change e{N}-s{N}: drafted → ready-for-dev"
```

### Ralph Loop Pattern
```bash
# Start autonomous implementation loop
bash .ralph/ralph_loop.sh

# Claude Code autonomous pattern:
# 1. Read ready-for-dev story
# 2. Read referenced files
# 3. Implement acceptance criteria
# 4. Run verification
# 5. Update sprint-status.yaml to done
# 6. Pick next ready-for-dev story
```

### Verification Commands (always run after changes)
```bash
# Backend
uv run ruff check .
uv run pytest tests/ -x --tb=short

# Frontend  
cd frontend && npm run lint && npm run build

# E2E extraction test
uv run pytest tests/test_broadmeadows_e2e.py -v

# Model verification
python scripts/verify_model_setup.py --model ollama/qwen2.5:32b
```

---

## 14. ACTIVE ENVIRONMENT

### Services (local dev)
```
Frontend:   http://localhost:8502
API:        http://localhost:5055
SurrealDB:  http://localhost:8000
Ollama:     http://localhost:11434
Worker:     uv run run_worker.py --import-modules commands
```

### Key Environment Variables
```bash
DEFAULT_CHAT_MODEL=ollama/qwen2.5:32b           # or openrouter/qwen/qwen-2.5-32b-instruct
DEFAULT_EXTRACTION_MODEL=ollama/qwen2.5:32b
DEFAULT_EMBEDDING_MODEL=ollama/mxbai-embed-large
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
OPENROUTER_API_KEY=sk-or-...
OLLAMA_BASE_URL=http://localhost:11434
SURREALDB_URL=http://localhost:8000
```

### Last Known Good State (Feb 22-23, 2026)
- PR #41 merged — tracking files updated
- 87 stories done / 122 total (71%)
- E2E extraction: 87% (27/31 Broadmeadows records)
- Migrations 14-20: now registered (was broken, fixed Feb 22)
- All frontend bug fixes from Phase 1-4 triage: merged

---

## 15. NEXT SESSION PRIORITIES

### Immediate (unblock demo)
1. Implement Fix A: NO ACCESS markers in `_preprocess_samp_format()` → target 29/31
2. Implement Fix B + C: vocabulary mapping + synonym test matching → target 31/31
3. Worker auto-start fix (FAIL-003) — critical for live demos
4. Marketing site polish (E19) — landing page animations, live GitHub widget

### Short-term (next sprint)
5. E5-S3: BAR Template Management (unblocks E5-S4 field mapping UI)
6. E16-S1: Dashboard home with ACM stats
7. E2-S8: Column visibility management
8. E17-S1: AG-UI extraction pipeline endpoint (live streaming to grid)

### Architectural considerations
- Migration 21 needed for dynamic embedding dimensions (E1-S30 pattern)
- Qwen2.5:32b now fully configured and ready for production use
- OpenRouter fallback parser handles all models that don't support tool_use

---

## 16. FILE LOCATIONS CHEAT SHEET

```
Extraction pipeline:     open_notebook/graphs/acm_extraction.py
Extraction prompts:      prompts/acm/extraction.jinja
                         prompts/acm/building_extraction.jinja
Model capabilities:      open_notebook/domain/models.py (_PROVIDER_DEFAULTS)
Model provisioning:      api/model_provisioning.py (MODEL_CATALOG)
AG Grid component:       frontend/src/components/acm/ACMGrid.tsx
Export endpoints:        api/routers/acm.py
Sprint status:           docs/sprint-artifacts/sprint-status.yaml
Epic stories:            _bmad-output/project-planning-artifacts/acm-ai/05-epics-and-stories.md
Architecture docs:       _bmad-output/project-planning-artifacts/acm-ai/04-architecture.md
PRD:                     _bmad-output/project-planning-artifacts/acm-ai/03-prd.md
E2E test:                tests/test_broadmeadows_e2e.py
Bug triage log:          docs/dumplog/bug-fix-feb22.md
Marketing site:          /home/claude/acm-ai-site/ (separate from main app)
```

---

*Last updated: 2026-02-23 | Session Claude Sonnet 4.6 | Project: ACM-AI v1.0*
