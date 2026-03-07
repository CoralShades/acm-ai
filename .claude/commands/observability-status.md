---
description: Health check all observability services and environment variables
allowed-tools: Bash
---

# Observability Status Check

Check the health and configuration of all 6 observability tools.

## Instructions

### 1. Check Environment Variables

```bash
echo "=== Observability Environment Variables ==="
echo "LANGFUSE_ENABLED:        ${LANGFUSE_ENABLED:-not set}"
echo "LANGFUSE_PUBLIC_KEY:     ${LANGFUSE_PUBLIC_KEY:+SET (hidden)}"
echo "LANGFUSE_SECRET_KEY:     ${LANGFUSE_SECRET_KEY:+SET (hidden)}"
echo "LANGFUSE_BASE_URL:       ${LANGFUSE_BASE_URL:-not set (default: https://cloud.langfuse.com)}"
echo "LOGFIRE_ENABLED:         ${LOGFIRE_ENABLED:-not set}"
echo "LANGCHAIN_TRACING_V2:   ${LANGCHAIN_TRACING_V2:-not set}"
echo "LANGCHAIN_API_KEY:       ${LANGCHAIN_API_KEY:+SET (hidden)}"
```

### 2. Check Service Endpoints

```bash
echo "=== Service Health ==="

# Langfuse (self-hosted)
LANGFUSE_URL="${LANGFUSE_BASE_URL:-http://localhost:3000}"
curl -s -o /dev/null -w "Langfuse ($LANGFUSE_URL): HTTP %{http_code}\n" "$LANGFUSE_URL/api/public/health" 2>/dev/null || echo "Langfuse ($LANGFUSE_URL): NOT RESPONDING"

# LangGraph API
curl -s -o /dev/null -w "LangGraph API (localhost:2024): HTTP %{http_code}\n" "http://127.0.0.1:2024/ok" 2>/dev/null || echo "LangGraph API (localhost:2024): NOT RESPONDING"

# JSON Crack
curl -s -o /dev/null -w "JSON Crack (localhost:8888): HTTP %{http_code}\n" "http://localhost:8888" 2>/dev/null || echo "JSON Crack (localhost:8888): NOT RESPONDING"
```

### 3. Check Docker Containers (Observability)

```bash
echo "=== Docker Containers ==="
docker compose -f docker-compose.yml -f docker-compose.observability.yml ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "No observability containers found"
```

### 4. Check Tool Availability

```bash
echo "=== Tool Availability ==="

# erdantic
python -c "import erdantic; print(f'erdantic: installed (v{erdantic.__version__})')" 2>/dev/null || echo "erdantic: NOT INSTALLED (pip install erdantic)"

# Graphviz (required by erdantic)
dot -V 2>/dev/null && echo "Graphviz: installed" || echo "Graphviz: NOT INSTALLED (required by erdantic)"

# Logfire
python -c "import logfire; print('logfire: installed')" 2>/dev/null || echo "logfire: NOT INSTALLED"

# Langfuse SDK
python -c "import langfuse; print(f'langfuse: installed (v{langfuse.version})')" 2>/dev/null || echo "langfuse: NOT INSTALLED"
```

### 5. Present Summary

Present results as a status table:

| Tool | Status | Endpoint | Notes |
|------|--------|----------|-------|
| Langfuse | UP/DOWN | :3000 | Self-hosted tracing |
| LangGraph API | UP/DOWN | :2024 | Graph state inspection |
| JSON Crack | UP/DOWN | :8888 | JSON viewer |
| LangSmith | CONFIGURED/NOT | cloud | Auto-tracing |
| Logfire | CONFIGURED/NOT | via Langfuse | Pydantic tracing |
| erdantic | INSTALLED/NOT | local CLI | ER diagrams |

Include actionable suggestions for any DOWN/NOT CONFIGURED items.
