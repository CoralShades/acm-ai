---
description: View logs from development services
allowed-tools: Bash
argument-hint: [service]
---

# View Service Logs

View logs from one or more services.

## Available Services
<!-- List your project's services here -->
- `web` - Web application
- `api` - API server
- `db` - Database

## Instructions

1. If service argument provided, show logs for that service:
   ```bash
   docker compose logs -f --tail 100 $1
   ```

2. If no service specified, ask the user which service they want to see logs for.

3. For all services combined (use sparingly):
   ```bash
   docker compose logs -f --tail 50
   ```

## Notes
- `--tail 100` limits to last 100 lines
- `-f` follows log output in real-time
