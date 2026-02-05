# CLAUDE.md Template

This template provides a starting point for CLAUDE.md files. Customize for your project.

---

# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Project Overview

<!-- Replace with your project description -->
**[Project Name]** - Brief description of what this project does.

### Key Technologies
- **Language**: [TypeScript/Python/etc.]
- **Framework**: [Next.js/FastAPI/etc.]
- **Database**: [PostgreSQL/Supabase/etc.]
- **Infrastructure**: [Docker/Kubernetes/etc.]

## Key Commands

### Development
```bash
# Start development server
npm run dev

# Run tests
npm test

# Build for production
npm run build
```

### Docker (if applicable)
```bash
# Start services
docker compose up -d

# Stop services
docker compose down

# View logs
docker compose logs -f [service]
```

## Architecture

<!-- Add architecture overview or link to docs -->
See @docs/architecture/README.md for detailed architecture documentation.

### Directory Structure
```
src/
├── app/          # Application layer
├── components/   # UI components
├── lib/          # Shared utilities
└── types/        # TypeScript types
```

## Code Style

### General Rules
- Use descriptive variable and function names
- Keep functions small and focused
- Write tests for new features
- Document complex logic

### Language-Specific
<!-- Add language-specific conventions -->
- Follow [language] best practices
- Use [linter/formatter] for consistency

## Environment Configuration

Copy `.env.example` to `.env` and configure:
```bash
# Required
DATABASE_URL=
API_KEY=

# Optional
DEBUG=false
```

## Testing

```bash
# Run all tests
npm test

# Run specific test
npm test -- path/to/test

# Run with coverage
npm test -- --coverage
```

## Claude Code Custom Commands

Custom slash commands are available in `.claude/commands/`:

| Command | Description |
|---------|-------------|
| `/start` | Start development services |
| `/stop` | Stop all services |
| `/status` | Check service health |
| `/logs [service]` | View service logs |
| `/build` | Build the project |
| `/test` | Run tests |

## Claude Code Modular Rules

Domain-specific rules in `.claude/rules/`:

| Rule File | Applies To |
|-----------|------------|
| `typescript.md` | `**/*.ts`, `**/*.tsx` files |
| `testing.md` | `**/*.test.ts`, `**/*.spec.ts` files |
| `api.md` | `src/api/**/*` files |

## MCP Configuration

MCP servers configured in `.claude/settings.json`:

| Server | Purpose | Status |
|--------|---------|--------|
| `filesystem` | File operations | Enabled |
| `memory` | Persistent context | Enabled |
| `github` | GitHub integration | Enabled (requires GITHUB_TOKEN) |

### Environment Variables for MCP

```bash
export GITHUB_TOKEN="your-token"
# Add other required variables
```

## Important Notes

<!-- Add project-specific warnings and notes -->
- Note 1: Important consideration
- Note 2: Common gotcha
- Note 3: Required setup step

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Common error 1 | How to fix |
| Common error 2 | How to fix |

## Related Documentation

- @README.md - Project readme
- @docs/architecture/README.md - Architecture docs
- @docs/api/README.md - API documentation
- @CONTRIBUTING.md - Contribution guidelines
