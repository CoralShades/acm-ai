---
description: Stop ACM-AI development services
allowed-tools: Bash
---

# Stop ACM-AI Services

Stop all running development services gracefully.

## Quick Stop Options

### Option 1: Windows Batch File (Recommended)
```batch
stop-all.bat
```

### Option 2: Docker Compose
```bash
docker compose down
```

## Instructions

1. **Stop Docker Compose services**:
   ```bash
   docker compose down
   ```

2. **Verify all containers are stopped**:
   ```bash
   docker compose ps
   ```

3. Report completion status to user.

## Notes
- Use `docker compose down -v` to also remove volumes (destructive - loses database data)
- The batch file also stops API/Worker processes running in separate terminals
