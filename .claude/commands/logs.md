---
description: View logs from ACM-AI services
allowed-tools: Bash
argument-hint: [service]
---

# View ACM-AI Service Logs

View logs from one or more services.

## Available Services
- `surrealdb` - SurrealDB database
- `api` - FastAPI backend (if running in Docker)
- `worker` - Background worker (if running in Docker)
- `frontend` - Next.js frontend (if running in Docker)

## Instructions

1. **If service argument provided**, show logs for that service:
   ```bash
   docker compose logs -f --tail 100 $1
   ```

2. **If no service specified**, list available options and ask user:
   ```bash
   docker compose ps --format "{{.Name}}"
   ```

3. **For SurrealDB specifically** (most common):
   ```bash
   docker compose logs -f --tail 100 surrealdb
   ```

## Notes
- `--tail 100` limits to last 100 lines
- `-f` follows log output in real-time
- API and Worker logs are typically in terminal where `uv run` was executed
