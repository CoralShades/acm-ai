---
paths:
  - "docker-compose*.yml"
  - "docker-compose*.yaml"
---

# Docker Compose Rules for ACM-AI

## Service Configuration

### Port Mappings
- SurrealDB: `8000:8000`
- FastAPI: `5055:5055`
- Frontend: `8502:8502`

### Environment Variables
- Always use `${VAR:-default}` syntax for variable substitution
- Store secrets in `.env`, never commit them

## Formatting
- Use YAML anchors for repeated configurations
- Quote port mappings: `"5055:5055"`
- Define explicit container names

## Health Checks
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:5055/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```

## Network Configuration
- Use the default `acm-ai_default` network for service communication
- Services reference each other by container name

## Volume Mounts
- Database data: Named volumes for persistence
- Code mounts: Bind mounts for hot-reload development
