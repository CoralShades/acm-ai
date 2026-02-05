---
description: Check health and status of ACM-AI services
allowed-tools: Bash
---

# ACM-AI Service Status Check

Check the health and status of all ACM-AI services.

## Instructions

1. **List Docker containers and their status**:
   ```bash
   docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
   ```

2. **Check SurrealDB** (port 8000):
   ```bash
   curl -s http://localhost:8000/health 2>/dev/null && echo "SurrealDB: OK" || echo "SurrealDB: NOT RESPONDING"
   ```

3. **Check API** (port 5055):
   ```bash
   curl -s http://localhost:5055/health 2>/dev/null && echo "API: OK" || echo "API: NOT RESPONDING"
   ```

4. **Check Frontend** (port 8502):
   ```bash
   curl -s http://localhost:8502 2>/dev/null | head -c 100 && echo "Frontend: OK" || echo "Frontend: NOT RESPONDING"
   ```

5. **Summarize status** in a table format for the user.

## Service Ports
| Service | Port | URL |
|---------|------|-----|
| SurrealDB | 8000 | http://localhost:8000 |
| FastAPI | 5055 | http://localhost:5055 |
| Next.js | 8502 | http://localhost:8502 |
