# AGENTS.md — ACM-AI Codex Configuration

## Project Context

This is the ACM-AI project — an intelligent Asbestos Containing Material compliance
management system. Read `CLAUDE.md` in the project root for full conventions.

## BMAD Project Awareness

When working on projects with `_bmad/` or `_bmad-output/` directories:

1. Read `CLAUDE.md` in the project root for conventions
2. Read `.codex/skills/acm-ai-context/SKILL.md` for BMAD workflow routing
3. BMAD artifacts in `_bmad-output/` are the planning source of truth
4. Implementation plans go to `docs/plans/`
5. ALWAYS use `superpowers:test-driven-development` for coding
6. ALWAYS use `superpowers:systematic-debugging` for debugging

## Superpowers System

You have superpowers. If the superpowers bootstrap is available, run it:
`~/.codex/superpowers/.codex/superpowers-codex bootstrap`
If the path doesn't exist, check `~/.agents/skills/superpowers/` for available skills.

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
