---
description: Start development services
allowed-tools: Bash, Read
argument-hint: [profile/config]
---

# Start Services

Start the development environment services.

## Instructions

1. Start services with Docker Compose:
   ```bash
   docker compose up -d
   ```

2. Wait for services to initialize, then verify status:
   ```bash
   docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
   ```

3. Report which services are running and their access URLs.

## Notes
- Customize this command for your project's specific startup needs
- Add environment-specific logic as needed (dev/staging/prod)
