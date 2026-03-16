# Glossary Builder

Instructions for building the `{{ glossary_table }}` section of a generated prompt. The glossary provides session-scoped term definitions so the executing Claude Code session has shared vocabulary without needing to re-read large docs.

---

## How to Select Terms

1. Identify the session's **domain(s)** from `domain_signals` in the `RequestClassification`
2. Pull the matching term sets from the sections below
3. Always include all **General domain** terms
4. Filter to terms that are **referenced in the user's original request** first
5. Fill remaining slots from the domain list in order until you reach **max 15 entries**
6. Format as a markdown table

---

## Pipeline Domain

**Activate when `domain_signals` contains:** `extraction`, `pipeline`, `graph`, `node`, `langgraph`, `surrealdb`, `provider`, `docling`, `mineru`, `building`, `item`

| Term | Definition | File Path (if applicable) |
|------|-----------|--------------------------|
| Building__c | Salesforce object representing a physical building in the SAMP asbestos register. The extraction pipeline produces one `BuildingRecord` per building. | `open_notebook/domain/acm.py` |
| Item__c | Salesforce object representing an individual ACM (asbestos-containing material) sample within a building. Maps to `ACMRecord` / `ACMExtractionRecord`. | `open_notebook/domain/acm.py` |
| ExtractionState | LangGraph `TypedDict` that carries all pipeline data between nodes: source metadata, docling tables, building cache, extracted records, validation flags. | `open_notebook/graphs/acm_extraction.py` |
| building_meta_cache | Dict keyed by building internal ID within `ExtractionState`, used to prevent redundant DB lookups across nodes. | `open_notebook/graphs/acm_extraction.py` |
| Pre-extraction stages | The STRUCTURE, PREFLIGHT, and ORCHESTRATOR pipeline stages that run before any LLM extraction — they gather metadata, validate the source, and plan the extraction strategy. | `open_notebook/graphs/acm_extraction.py` |
| Docling tables | Structured table objects produced by Docling's `DoclingDocument` parser. Each `TableItem` has row/cell data and bounding box coordinates. Used as primary extraction input. | `open_notebook/extractors/providers/docling_adapter.py` |
| SF picklist normalization | The process of mapping raw extracted text values to valid Salesforce picklist options using `SalesforcePicklistValidator`. Happens in the normalizer layer. | `open_notebook/extractors/normalizers/enums.py` |
| PipelineEventBus | Publish/subscribe bus that emits structured events (`extraction`, `ai`, `bulk`) to the SSE streaming endpoint during extraction runs. | `open_notebook/extractors/pipeline_event_bus.py` |
| SAMP | School Asbestos Management Plan — the source PDF document that the ACM pipeline processes. Contains asbestos survey results for one or more buildings. | — |
| ARA | Asbestos Register Assessment — the structured data output of a SAMP survey; what the pipeline extracts and stores. | — |
| Correction loop | The `correct_node` in the extraction graph that re-validates and re-extracts low-confidence records. Triggered when confidence score < threshold. | `open_notebook/graphs/acm_extraction.py` |
| PipelineLogger | Per-run logger that emits structured log events to both console and SurrealDB. Constructor: `(source_id, total_pages=0, command_id=None)`. | `open_notebook/extractors/pipeline_logger.py` |
| ExtractionProvider | Protocol class that all extraction adapters must implement. Methods: `extract_tables()`, `extract_text()`, `is_available()`. | `open_notebook/extractors/providers/base.py` |
| RawExtraction | Normalized domain object produced by an `ExtractionProvider` adapter. Carries tables, text blocks, and provider metadata. | `open_notebook/extractors/providers/base.py` |
| ConsensusEngine | Combines results from multiple providers using confidence-weighted voting. Part of the V3 consensus layer. | `open_notebook/extractors/consensus/engine.py` |

---

## Frontend Domain

**Activate when `domain_signals` contains:** `component`, `page`, `UI`, `React`, `css`, `frontend`, `grid`, `sidebar`, `hook`, `store`, `zustand`, `ag-grid`

| Term | Definition | File Path (if applicable) |
|------|-----------|--------------------------|
| AG Grid | Enterprise React data grid used for the `ItemGrid` and `BuildingGrid` views. Supports row grouping, column pinning, virtual scrolling, and dynamic columns from the SF schema API. | `frontend/src/components/acm/ItemGrid.tsx` |
| CopilotKit | Real-time AI copilot framework providing the `useCopilotReadable` / `useCopilotAction` hooks. Used to expose extraction state and trigger actions from the chat interface. | `frontend/src/components/` |
| AG-UI Protocol | Event protocol (from CopilotKit) that streams agent actions to the frontend via the `/api/agui/extraction/{id}/stream` endpoint. | `frontend/src/lib/hooks/useV3SSE.ts` |
| Zustand store | Client-side state management. Stores: `buildingStore` (selected building, filter state), `streamingStore` (SSE pipeline events), `notebookStore` (current notebook). | `frontend/src/lib/stores/` |
| shadcn/ui | Component library providing base UI primitives (Button, Card, Dialog, etc.) following Radix UI + Tailwind CSS patterns. | `frontend/src/components/ui/` |
| ExtractionProgressPanel | The real-time extraction progress panel that subscribes to `PipelineEventBus` events via the SSE hook and renders stage-by-stage progress. | `frontend/src/components/acm/` |
| BuildingSidebar | Left-panel component on the source detail page (`/source/[id]`) listing all buildings for a source. Clicking a building filters the ItemGrid. | `frontend/src/components/acm/BuildingSidebar.tsx` |
| ItemGrid | AG Grid component showing all `ACMRecord` items for the selected building. Columns are dynamically generated from `GET /api/acm/field-schema`. | `frontend/src/components/acm/ItemGrid.tsx` |
| useBuildings | React Query hook wrapping `GET /api/acm/buildings?source_id=X`. Returns `BuildingRecord[]` with `record_count`. | `frontend/src/lib/hooks/useBuildings.ts` |
| useACMItems | React Query hook wrapping `GET /api/acm/items?building_id=X`. Returns `ACMRecord[]` for the selected building. | `frontend/src/lib/hooks/useACMItems.ts` |
| React Query | Data-fetching and server-state cache library. All API calls go through `useQuery`/`useMutation` hooks. Cache keys follow `['resource', id]` pattern. | `frontend/src/lib/hooks/` |
| SFFieldSchemaConfig | TypeScript type representing the full Salesforce field schema config returned by `GET /api/acm/field-schema`. Used to dynamically generate AG Grid column defs. | `frontend/src/lib/types/sf-schema.ts` |
| ProvenanceViewer | PDF page viewer component that highlights the source table region for a selected ACM record using bounding box data. Wrapped in `next/dynamic` to avoid SSR issues with pdfjs. | `frontend/src/components/acm/ProvenanceViewer.tsx` |

---

## General Domain

**Always include these terms** (they apply to all sessions regardless of domain):

| Term | Definition | File Path (if applicable) |
|------|-----------|--------------------------|
| Skill | A markdown instruction set for Claude Code that activates specialized behavior. Loaded via `/skill-name` in a session. Lives in `.claude/skills/` or `.agents/skills/`. | `.claude/skills/` |
| Slash command | A project-defined command invocable as `/command-name` in Claude Code. Lives in `.claude/commands/` as `.md` files. Different from skills — commands are shorter, more procedural. | `.claude/commands/` |
| Subagent | A Claude Code session spawned via the `Task` tool. Used for parallel independent work. Model guidance: `sonnet` for complex tasks, `haiku` for simple/focused tasks in teams. | — |
| Context7 MCP | Model Context Protocol server that fetches live library documentation. Invoked with `resolve-library-id` + `query-docs`. Required for any work touching specific library APIs. | — |
| Plan mode | When `plan_mode=true`, the session starts by reading/writing a `task_plan.md` file instead of directly implementing. Used for complex tasks to prevent scope creep. | `docs/sprint-artifacts/` |

---

## Selection Rules

1. **Max 15 entries total** across all domains
2. **Priority order**: terms mentioned in the user's request > terms from the request's domain > general terms
3. **Always include** all 5 General domain terms unless the total would exceed 15
4. **Skip terms** that reference files the session will not interact with
5. **Add file path** only when the term has a direct 1:1 mapping to a source file
6. **Trim definitions** to 1–2 sentences max; full docs are in the referenced files

---

## Example Output

For a pipeline session with 8 total entries:

```markdown
| Term | Definition |
|------|-----------|
| Building__c | Salesforce object for a physical building. The extraction pipeline produces one `BuildingRecord` per building. |
| Item__c | Salesforce object for an individual ACM sample. Maps to `ACMExtractionRecord` in `open_notebook/domain/acm.py`. |
| ExtractionState | LangGraph TypedDict carrying all data between pipeline nodes. |
| Docling tables | Structured table objects from Docling's `DoclingDocument` parser; primary extraction input. |
| PipelineEventBus | Pub/sub bus emitting events to the SSE endpoint during extraction runs. |
| Skill | Markdown instruction set for Claude Code activated via `/skill-name`. |
| Subagent | Claude Code session spawned via Task tool for parallel work. |
| Plan mode | Session starts by reading/writing `task_plan.md` to prevent scope creep. |
```
