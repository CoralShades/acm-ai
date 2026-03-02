# P0: Extract HTML Documents to Markdown

> **Type:** Pre-step (manual — no BMAD command)
> **Purpose:** Convert V3 HTML documents to markdown summaries for downstream agent consumption
> **When:** Run FIRST, before any other prompt in this pack
> **Output:** `V3/output/` markdown files

---

## Prompt

```text
I have three HTML documents in my V3/ directory that need to be converted to markdown summaries for use by BMAD planning agents. Please process each one:

### Files to Convert

1. **V3/acm-ai-solution-architecture-v3.html** (55KB)
   - This is the client-required solution architecture for ACM-AI V3
   - Extract: system diagrams, component descriptions, data flows, integration points, technology choices, constraints
   - Save to: V3/output/solution-architecture-v3.md

2. **V3/heuristic-rules-reference.html** (60KB)
   - This contains extraction heuristic rules for the ACM pipeline
   - Extract: rule definitions, matching patterns, field mappings, decision logic, edge cases
   - Assess: Is this still relevant to V3 or has it been superseded by E29 changes?
   - Save to: V3/output/heuristic-rules-reference.md

3. **V3/bmad-architecture-audit.html** (62KB)
   - This is a BMAD architecture audit of the current system
   - Extract: findings, gaps, recommendations, current state assessment, change impact areas
   - Assess: How much of this overlaps with V3/output/e30-multi-agent-audit-unified.md?
   - Save to: V3/output/bmad-architecture-audit.md

### Requirements
- Preserve all technical content — tables, diagrams (convert to mermaid where possible), code blocks
- Add a "Relevance Assessment" section at the top of each output noting:
  - Whether the content is current, outdated, or partially relevant
  - Which V3 planning steps should reference this document
  - Key sections that downstream agents need most
- Keep markdown files under 2000 lines each — summarize verbose sections but preserve technical detail
- If any document contains Mermaid-compatible diagrams, preserve them as ```mermaid blocks

### Context
These markdown files will be referenced by BMAD agents running:
- Party Mode (multi-agent V3 planning)
- Create Architecture (V3 architecture document)
- Technical Research (extraction provider evaluation)
- Dev Story (implementation guidance)
```

---

## Verification

After running, confirm these files exist:
- [ ] `V3/output/solution-architecture-v3.md`
- [ ] `V3/output/heuristic-rules-reference.md`
- [ ] `V3/output/bmad-architecture-audit.md`

Each should have a "Relevance Assessment" header section.
