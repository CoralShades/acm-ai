---
description: Stop all development services gracefully
allowed-tools: Bash
---

# Stop Services

Stop all running development services gracefully.

## Instructions

1. Stop services with Docker Compose:
   ```bash
   docker compose down
   ```

2. Verify all containers are stopped:
   ```bash
   docker compose ps
   ```

3. Report completion status to user.

## Notes
- Use `docker compose down -v` to also remove volumes (destructive)
- Customize for your project's shutdown requirements
