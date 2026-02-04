---
paths:
  - "docker-compose*.yml"
  - "docker-compose*.yaml"
---

# Docker Compose Rules

## Formatting
- Use YAML anchors for repeated configurations
- Quote port mappings: `"5678:5678"`
- Use environment variable substitution: `${VAR:-default}`

## Service Configuration
- Define explicit container names
- Use restart policies: `restart: unless-stopped`
- Set resource limits where appropriate

## Networks
- Define custom networks for service isolation
- Use network aliases for service discovery

## Volumes
- Use named volumes for persistent data
- Document volume mount points

## Common Commands
```bash
# Start services
docker compose up -d

# Stop services
docker compose down

# View logs
docker compose logs -f <service>

# Check status
docker compose ps
```

## Health Checks
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```
