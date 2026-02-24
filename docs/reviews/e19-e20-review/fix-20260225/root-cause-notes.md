# Root Cause Notes

## Upload extraction failures
Observed in logs:
- `openai.AuthenticationError: Error code: 401 - User not found`
- intermittent SurrealDB connection refused (`127.0.0.1:8000`)

Preliminary diagnosis:
1. Authentication/model-provider mismatch or invalid API key in selected extraction model path (Sonnet via OpenRouter-like path)
2. Lack of runtime provider fallback when authentication fails at inference time
3. Separate environmental outage: DB not running/accessible causes follow-on API errors

Targeted fix direction:
- Add runtime extraction model fallback router for auth/provider failures:
  - keep Sonnet 4.6 as preferred when configured and healthy
  - preserve Ollama/Qwen support (no regression)
  - fallback chain when auth fails: provider-specific candidate model(s)
