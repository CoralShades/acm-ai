# Task Plan: Create ACM-AI Specialized Agent Teams

## Goal
Create ~20+ specialized Claude Code agents in `~/.claude/agents/` that are globally available, ACM-AI specialized, and designed to work as agent teams across 4 compositions: sprint execution, research & design, pipeline development, and browser/E2E testing.

## Decisions
- **Scope:** All three categories (ACM domain + BMad methodology + Pipeline)
- **Specificity:** ACM-AI specialized
- **Model:** Sonnet for all agents
- **Location:** `~/.claude/agents/` (global)
- **Team patterns:** Sprint execution, Research & design, Pipeline dev, Browser/E2E testing

## Phase 1: BMad Methodology Agents (7 agents) — `in_progress`
Mirror the full BMad team roles as autonomous teammates:

| Agent | BMad Role | Key Responsibilities |
|-------|-----------|---------------------|
| `bmad-pm` | Product Manager | PRD management, requirements, change proposals, stakeholder alignment |
| `bmad-sm` | Scrum Master | Sprint planning, status tracking, story creation, backlog management |
| `bmad-dev` | Developer | Story implementation, TDD, code delivery |
| `bmad-architect` | Architect | Architecture docs, tech decisions, system design |
| `bmad-qa` | QA/TEA | Test design, test review, acceptance testing, regression |
| `bmad-tech-writer` | Tech Writer | Documentation, tech specs, API docs |
| `bmad-analyst` | Analyst | Research, domain analysis, gap identification |

## Phase 2: ACM Domain Agents (5 agents) — `pending`
ACM-AI specialized domain experts:

| Agent | Domain | Key Responsibilities |
|-------|--------|---------------------|
| `acm-extraction-pre` | Pre-extraction | TOC extraction, building inventory, page tagging, document structure |
| `acm-extraction-core` | Core extraction | ACM table extraction, metadata extraction, parser framework |
| `acm-extraction-post` | Post-extraction | Corrective validation, contextual enrichment, embedding, BAR compliance |
| `acm-schema-expert` | Schema/DB | SurrealDB migrations, BAR schema, graph entities, data model |
| `acm-rag-strategist` | RAG/Search | Agentic RAG, hybrid search, parent-doc retrieval, reranking |

## Phase 3: Browser/E2E Testing Agent (2 agents) — `pending`
Full-stack testing via MCP tools:

| Agent | Focus | Key Responsibilities |
|-------|-------|---------------------|
| `acm-e2e-tester` | E2E workflows | Upload PDF → extraction → grid verification → export via Playwright/browser |
| `acm-ui-tester` | UI verification | Page navigation, form testing, component rendering, accessibility |

## Phase 4: Team Lead Agents (2 agents) — `pending`
Specialized coordination agents:

| Agent | Role | Key Responsibilities |
|-------|------|---------------------|
| `acm-sprint-lead` | Sprint team lead | Coordinate sprint execution teams, delegate stories, synthesize results |
| `acm-research-lead` | Research team lead | Coordinate research/design teams, evaluate competing approaches |

## Phase 5: Verification & Documentation — `pending`
- Verify all agents load correctly
- Test agent team creation
- Update progress.md

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
| (none yet) | | |
