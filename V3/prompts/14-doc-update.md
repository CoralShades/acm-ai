# 14: Tech Writer Documentation Update

> **BMAD Command:** (agent-based — no direct command)
> **Agent:** Paige — 📚 Technical Writer
> **Load:** `/bmad-agent-bmm-tech-writer`, then use code `WD` (Write Document)
> **Depends On:** Stories completed (run after each epic or batch of stories)
> **Output:** Updated docs in `docs/` directory
> **Run in:** Fresh context window

---

## Pre-Read Documents

- `docs/index.md` — Documentation index
- `docs/development/architecture.md` — Development architecture doc
- `docs/development/api-reference.md` — API reference
- `_bmad-output/project-planning-artifacts/acm-ai/04-architecture.md` — V3 architecture (source of truth)
- Completed story tech specs (for implementation details)
- `CLAUDE.md` — Project instructions (may need updating)

---

## Prompt

```text
/bmad-agent-bmm-tech-writer

WD — Update ACM-AI documentation for V3 implementation

### Context
V3 stories have been implemented. The project documentation needs updating to reflect the new architecture, features, and workflows.

### Documents to Update

#### 1. docs/development/architecture.md
Update to reflect V3 architecture:
- Multi-provider extraction pipeline (Docling + second provider + consensus layer)
- Building__c + Item__c data model (separate tables, master-detail FK)
- Provider adapter interface
- Provenance tracking data model
- SSE streaming architecture
- AI batching strategy

#### 2. docs/development/api-reference.md
Add new V3 endpoints:
- Building CRUD endpoints
- Raw extraction endpoints
- Provenance query endpoints
- Multi-provider extraction trigger
- SSE subscription endpoints
- SF Data Loader export endpoints

#### 3. CLAUDE.md
Update:
- Architecture section (add V3 data model overview)
- Essential Commands (any new commands)
- Database section (new tables: building_record, raw_extraction, extraction_provenance)
- Environment Variables (new provider config vars)

#### 4. docs/index.md
Add V3 documentation links.

#### 5. README.md (if user-facing changes warrant it)
Update features list and setup instructions for new providers.

### Documentation Standards
- Follow existing documentation patterns and formatting
- Include code examples for new API endpoints
- Include Mermaid diagrams where architecture has changed
- Reference SF field names consistently
- Keep documentation concise — link to architecture doc for deep details

### Constraints
- Only update documentation for IMPLEMENTED features (not planned/backlog)
- Do NOT add speculative documentation for future providers
- Reference actual file paths and actual API endpoints
- Verify code examples compile/work before including them
```

---

## Alternate Prompts for Specific Documentation Tasks

### Validate Existing Documentation
```text
/bmad-agent-bmm-tech-writer

VD — Validate docs/development/architecture.md

Review this document against the actual codebase. Flag any sections that:
- Reference outdated patterns (BAR field names, old API endpoints)
- Are missing V3 additions
- Have incorrect code examples
- Need Mermaid diagram updates
```

### Generate API Documentation
```text
/bmad-agent-bmm-tech-writer

WD — Generate API documentation for V3 endpoints

Scan `api/routers/acm.py` and any new router files. For each V3 endpoint, document:
- HTTP method + path
- Request body schema (Pydantic model)
- Response schema
- Authentication requirements
- Example curl commands
- SSE event types (for streaming endpoints)
```
