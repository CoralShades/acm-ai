# CopilotKit Troubleshooting Guide

## 1. Common Setup Issues

### API Key Configuration

CopilotKit supports multiple LLM providers. The correct environment variable must be set for your chosen provider:

| Provider | Environment Variable | Notes |
|----------|---------------------|-------|
| OpenAI | `OPENAI_API_KEY` | Most common default provider |
| Anthropic | `ANTHROPIC_API_KEY` | For Claude models |
| Google | `GOOGLE_API_KEY` | For Gemini models |
| Groq | `GROQ_API_KEY` | For Groq-hosted models |
| Azure OpenAI | `AZURE_OPENAI_API_KEY` | Also requires `AZURE_OPENAI_ENDPOINT` and `AZURE_OPENAI_DEPLOYMENT` |

**Next.js environment variable rules:**

- **Server-side only (API keys):** Place in `.env.local` without the `NEXT_PUBLIC_` prefix. These are only available in API routes and server components. API keys should NEVER be exposed to the client.
- **Client-side:** Variables prefixed with `NEXT_PUBLIC_` are bundled into the client JavaScript. Never use this prefix for secret keys.

```bash
# .env.local (correct)
OPENAI_API_KEY=sk-...

# WRONG - never expose API keys to the client
NEXT_PUBLIC_OPENAI_API_KEY=sk-...
```

After adding or changing environment variables, **restart the dev server** (`Ctrl+C` then `npm run dev`).

### Missing Styles Import

If the CopilotKit UI renders but looks unstyled or broken, you are likely missing the CSS import.

**Fix:** Add the following import in your root layout or the file where you use CopilotKit UI components:

```tsx
import "@copilotkit/react-ui/styles.css";
```

For Next.js App Router, add it to `app/layout.tsx`. For Pages Router, add it to `pages/_app.tsx`.

### Provider Not Wrapping App

All components that use CopilotKit hooks (`useCopilotAction`, `useCopilotReadable`, `useCopilotChat`, `useCoAgent`, etc.) must be rendered inside a `<CopilotKit>` provider.

**Symptom:** Errors like `useCopilotContext must be used within a CopilotKit provider` or actions/readables silently not registering.

**Fix:** Wrap your component tree at the highest appropriate level:

```tsx
import { CopilotKit } from "@copilotkit/react-core";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <CopilotKit runtimeUrl="/api/copilotkit">
      {children}
    </CopilotKit>
  );
}
```

---

## 2. Network & CORS Issues

### "Failed to fetch" Errors

This is one of the most common errors. It typically means the browser cannot reach the runtime endpoint.

**Checklist:**

1. **Verify the `runtimeUrl` is correct.** For Next.js App Router, the default is `/api/copilotkit`. For an external backend, use the full URL (e.g., `http://localhost:8000/copilotkit`).
2. **Ensure the backend is running.** Test with `curl http://localhost:8000/copilotkit` or visit the URL directly.
3. **Check for CORS errors** in the browser DevTools console (Network tab).

### CORS Configuration

When your frontend and backend run on different origins (e.g., `localhost:3000` and `localhost:8000`), CORS must be configured on the backend.

**Critical:** CORS middleware must be added BEFORE route definitions.

**Express.js:**

```js
const cors = require("cors");
const express = require("express");
const app = express();

// CORS must come BEFORE routes
app.use(cors({
  origin: "http://localhost:3000",
  methods: ["GET", "POST"],
  allowedHeaders: ["Content-Type", "Authorization"],
}));

// Routes come after CORS
app.use("/copilotkit", copilotKitRoute);
```

**FastAPI (Python):**

```python
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS must be added before routes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Docker Networking

When the frontend runs on the host and the backend runs in a Docker container (or vice versa), `localhost` inside a container refers to the container itself, not the host machine.

**Fix:** Use `host.docker.internal` instead of `localhost`:

```tsx
<CopilotKit runtimeUrl="http://host.docker.internal:8000/copilotkit">
```

Or from a Docker container reaching the host:

```
http://host.docker.internal:3000
```

### Runtime URL Format

| Setup | `runtimeUrl` Value |
|-------|-------------------|
| Next.js App Router (same project) | `/api/copilotkit` |
| Next.js Pages Router (same project) | `/api/copilotkit` |
| External Express/FastAPI backend | `http://localhost:8000/copilotkit` (full URL) |
| Docker backend from host frontend | `http://host.docker.internal:8000/copilotkit` |
| Production | `https://api.yourdomain.com/copilotkit` |

---

## 3. LangGraph Integration Issues

### State Serialization

LangGraph agent state passed through CopilotKit must be JSON-serializable. Custom Python objects, datetime instances, or other non-serializable types will cause silent failures or errors.

**Fix:** Ensure all state fields are primitive types (str, int, float, bool, list, dict) or convert them before returning:

```python
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    results: list[dict]  # dict, not custom objects
    count: int           # primitive types only
```

### `useCoAgentStateRender` Not Rendering

If you set up `useCoAgentStateRender` but nothing renders during agent execution, the most common cause is a **node name mismatch**.

**Fix:** The `nodeName` parameter must match the exact node name in your LangGraph graph definition:

```python
# Python graph definition
graph.add_node("research_node", research_function)
```

```tsx
// React - node name must match exactly (case-sensitive)
useCoAgentStateRender({
  name: "research_agent",
  nodeName: "research_node",  // Must match the Python node name exactly
  render: ({ state }) => <ResearchProgress state={state} />,
});
```

### Empty State with PostgreSQL Persistence

When using PostgreSQL-backed persistence with LangGraph, agent state may appear empty on reconnection.

**Common causes:**

- Thread ID not being passed correctly on reconnection
- Serialization issues with the PostgreSQL checkpointer
- Schema mismatch between the state definition and stored data

**Fix:** Verify the thread ID is consistent and check PostgreSQL logs for serialization errors.

### INCOMPLETE_STREAM Errors

This error occurs when the streaming connection between the agent and the frontend is interrupted before completion.

**Common causes:**

- Request timeout on the server or reverse proxy (e.g., Nginx, Vercel)
- Agent execution exceeding maximum step count
- Network interruption

**Fix:**

- Increase timeout settings on your server/proxy (Vercel serverless functions have a 60s limit on the Hobby plan)
- Increase `maxSteps` if the agent needs more iterations
- Add error handling with retry logic on the frontend

---

## 4. Version Compatibility

### Pin All CopilotKit Packages to the Same Version

Mixing different versions of `@copilotkit/*` packages is the most frequent source of cryptic errors.

**Fix:** Ensure all CopilotKit packages use the exact same version:

```json
{
  "dependencies": {
    "@copilotkit/react-core": "1.55.0",
    "@copilotkit/react-ui": "1.55.0",
    "@copilotkit/react-textarea": "1.55.0",
    "@copilotkit/runtime": "1.55.0"
  }
}
```

To update all packages at once:

```bash
npm install @copilotkit/react-core@latest @copilotkit/react-ui@latest @copilotkit/react-textarea@latest @copilotkit/runtime@latest
```

### `useCoAgent` vs `useAgent` (v2 Migration)

CopilotKit v2 renamed `useCoAgent` to `useAgent` (and `useCoAgentStateRender` to `useAgentStateRender`).

**If migrating to v2:**

```tsx
// v1
import { useCoAgent } from "@copilotkit/react-core";
const { state, setState } = useCoAgent({ name: "my_agent" });

// v2
import { useAgent } from "@copilotkit/react-core";
const { state, setState } = useAgent({ name: "my_agent" });
```

### LangChainAdapter Regression in v1.50.0+

Starting from v1.50.0, the `LangChainAdapter` had breaking changes. If you were using `LangChainAdapter` with an older version and upgraded, your runtime may stop working.

**Fix:** Either pin to a version before 1.50.0 or migrate to the new adapter API. Check the CopilotKit changelog for migration instructions.

### Python SDK Compatibility

For LangGraph-based agents, ensure minimum compatible versions:

```
copilotkit>=0.1.78
langgraph>=0.3.25
langchain-core>=0.3.0
```

Install or update:

```bash
pip install --upgrade copilotkit langgraph langchain-core
```

---

## 5. CopilotTextarea Issues

### Missing Markdown / Rich Text Support

`CopilotTextarea` currently operates as a **plain text** textarea with AI autocompletion. It does not support markdown rendering or rich text formatting (bold, italic, headers, etc.).

If you need rich text with AI features, you will need to integrate CopilotKit with a separate rich text editor (e.g., TipTap, Slate, or ProseMirror) using `useCopilotAction` and `useCopilotReadable`.

### Ctrl+K Not Working on Windows

In versions prior to v1.51, the `Ctrl+K` keyboard shortcut for triggering AI editing in `CopilotTextarea` did not work on Windows.

**Fix:** Upgrade to `@copilotkit/react-textarea@1.51.0` or later:

```bash
npm install @copilotkit/react-textarea@latest
```

---

## 6. Production Deployment Checklist

Before deploying a CopilotKit application to production, verify:

- [ ] **API keys in server-side env vars only** -- Never expose keys via `NEXT_PUBLIC_` or client-side bundles
- [ ] **CORS configured for your production domain** -- Update `allow_origins` from `localhost` to your actual domain
- [ ] **Error handler via `onError` prop** -- Add error handling to `<CopilotKit>` or your runtime to catch and log failures gracefully
- [ ] **Thread persistence configured** -- Use `SQLiteStorageRunner`, PostgreSQL, or CopilotKit Cloud for persistent conversation threads (default `InMemoryStorageRunner` loses data on restart)
- [ ] **Rate limiting on runtime endpoint** -- Protect your LLM API costs by adding rate limiting middleware
- [ ] **Auth headers or properties configured** -- Pass authentication tokens via the `headers` or `properties` prop on `<CopilotKit>` and validate them in your runtime
- [ ] **Styles imported in layout** -- Confirm `@copilotkit/react-ui/styles.css` is imported
- [ ] **Version pinned across all packages** -- All `@copilotkit/*` packages at the same version in `package.json`

---

## 7. Quick Fixes Table

| Symptom | Cause | Fix |
|---------|-------|-----|
| "OpenAI API key is missing" | Env var not set or not loaded | Add `OPENAI_API_KEY` to `.env.local`, restart dev server |
| Chat UI shows but no response | Wrong `runtimeUrl` | Check endpoint path matches your API route exactly |
| "Failed to fetch" | CORS misconfiguration or network issue | Configure CORS on backend, verify URL is reachable |
| Actions not appearing in chat | Missing provider | Wrap component tree with `<CopilotKit>` at a higher level |
| Styles broken / unstyled UI | Missing CSS import | Add `import "@copilotkit/react-ui/styles.css"` to layout |
| Agent state not syncing | Node name mismatch | Ensure `nodeName` in `useCoAgentStateRender` matches Python graph node name exactly |
| Python agent not connecting | Wrong URL in Docker | Use `http://host.docker.internal:8000/copilotkit` instead of `localhost` |
| Multiple connect requests in dev | React StrictMode | Normal behavior in development; only one connection in production builds |
| Thread state lost on refresh | No persistence configured | Add `InMemoryStorageRunner` (dev) or `SQLiteStorageRunner` (prod) to your runtime |
| "Cannot read properties of undefined" | Version mismatch | Pin all `@copilotkit/*` packages to the same version |
| Agent runs but UI does not update | State not JSON-serializable | Ensure all agent state fields are primitive/serializable types |
| Streaming cuts off mid-response | Server timeout | Increase timeout on server/proxy; check Vercel function duration limits |
