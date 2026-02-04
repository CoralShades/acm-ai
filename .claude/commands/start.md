---
description: Start ACM-AI development services
allowed-tools: Bash, Read
argument-hint: [profile]
---

# Start ACM-AI Services

Start the development environment services for ACM-AI.

## Quick Start Options

### Option 1: Windows Batch File (Recommended)
```batch
start-all.bat
```

### Option 2: Docker Compose Only
```bash
docker compose up -d surrealdb
```
Then manually run API and frontend.

### Option 3: Full Docker Development
```bash
docker compose -f docker-compose.dev-local.yml up -d
```

## Instructions

1. **Check Docker Desktop** is running first:
   ```bash
   docker info
   ```

2. **Start SurrealDB** database:
   ```bash
   docker compose up -d surrealdb
   ```

3. **Verify database is ready**:
   ```bash
   docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
   ```

4. Report service URLs to user:
   - SurrealDB: http://localhost:8000
   - API (manual): http://localhost:5055
   - Frontend (manual): http://localhost:8502

## Notes
- For full stack, user should run `start-all.bat` (Windows) or `make start-all` (Unix)
- API and Worker require manual startup with `uv run`
