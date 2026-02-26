# AGENTS.md — ACM-AI Codex Configuration

## Project Context

This is the ACM-AI project — an intelligent Asbestos Containing Material compliance
management system. Read `CLAUDE.md` in the project root for full conventions.

## BMAD Project Awareness

When working on projects with `_bmad/` or `_bmad-output/` directories:

1. Read `CLAUDE.md` in the project root for conventions
2. Read the BMAD bridge skill for workflow routing
3. BMAD artifacts in `_bmad-output/` are the planning source of truth
4. Implementation plans go to `docs/plans/`
5. ALWAYS use the test-driven-development skill for coding
6. ALWAYS use the systematic-debugging skill for debugging

## Superpowers System

You have superpowers. RIGHT NOW run:
`~/.codex/superpowers/.codex/superpowers-codex bootstrap`
and follow the instructions it returns.

## Tech Stack
- Backend: FastAPI + SurrealDB + LangGraph (Python 3.11+)
- Frontend: Next.js 15 + AG Grid + Tailwind CSS 4 (TypeScript)
- PDF Processing: MinerU + Docling
- AI: Ollama via OpenRouter

## Conventions
- Conventional commits (feat:, fix:, docs:, refactor:, test:)
- Ruff for Python linting, ESLint for TypeScript
- Repository pattern, Domain-Driven Design
- Protected files: migrations/, tests/, pyproject.toml, package.json
