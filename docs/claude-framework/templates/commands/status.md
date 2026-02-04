---
description: Check health and status of all services
allowed-tools: Bash
---

# Service Status Check

Check the health and status of all services.

## Instructions

1. List all containers and their status:
   ```bash
   docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
   ```

2. Check key service endpoints (customize for your project):
   ```bash
   # Example health checks
   curl -s http://localhost:8080/health 2>/dev/null || echo "Service not responding"
   ```

3. Summarize status in a table format for the user.

## Notes
- Add health check URLs specific to your services
- Include database connectivity checks if applicable
