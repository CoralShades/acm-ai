# Runtime & Adapters

## Table of Contents
- [CopilotRuntime](#copilotruntime)
- [Framework Endpoints](#framework-endpoints)
- [LLM Adapters](#llm-adapters)
- [Backend Actions](#backend-actions)
- [Deployment Modes](#deployment-modes)
- [Processing Flow](#processing-flow)

## CopilotRuntime

Backend orchestrator managing LLM requests, tool execution, agent routing, and event streaming.

**Responsibilities:**
1. Request orchestration — processes HTTP requests from frontend
2. LLM adapter management — interfaces with provider adapters
3. Agent execution — manages agent lifecycle and state sync
4. Action discovery — exposes frontend `useCopilotAction` definitions as tools
5. Event streaming — streams AG-UI events over HTTP
6. Context management — aggregates `useCopilotReadable` context

## Framework Endpoints

| Framework | Function | Typical route file |
|-----------|----------|-------------------|
| Next.js App Router | `copilotRuntimeNextJSAppRouterEndpoint` | `app/api/copilotkit/route.ts` |
| Next.js Pages Router | `copilotRuntimeNextJSPagesRouterEndpoint` | `pages/api/copilotkit.ts` |
| Express/Node.js | `copilotRuntimeNodeHttpEndpoint` | Any Express route |
| NestJS | `copilotRuntimeNestEndpoint` | NestJS controller |

### Next.js App Router (most common)

```typescript
import {
  CopilotRuntime,
  OpenAIAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import { NextRequest } from "next/server";

const serviceAdapter = new OpenAIAdapter({ model: "gpt-4o" });
const runtime = new CopilotRuntime();

export const POST = async (req: NextRequest) => {
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter,
    endpoint: "/api/copilotkit",
  });
  return handleRequest(req);
};
```

### Next.js Pages Router

```typescript
import {
  CopilotRuntime,
  OpenAIAdapter,
  copilotRuntimeNextJSPagesRouterEndpoint,
} from "@copilotkit/runtime";
import { NextApiRequest, NextApiResponse } from "next";

const serviceAdapter = new OpenAIAdapter({ model: "gpt-4o" });
const runtime = new CopilotRuntime();

export default copilotRuntimeNextJSPagesRouterEndpoint({
  runtime,
  serviceAdapter,
  endpoint: "/api/copilotkit",
});
```

### Express / Node.js

```typescript
import {
  CopilotRuntime,
  OpenAIAdapter,
  copilotRuntimeNodeHttpEndpoint,
} from "@copilotkit/runtime";
import express from "express";

const app = express();
const serviceAdapter = new OpenAIAdapter({ model: "gpt-4o" });
const runtime = new CopilotRuntime();

app.use("/api/copilotkit", copilotRuntimeNodeHttpEndpoint({
  runtime,
  serviceAdapter,
}));

app.listen(3001);
```

### With Remote Agent (Python backend)

```typescript
import {
  CopilotRuntime,
  OpenAIAdapter,
  CustomHttpAgent,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";

const serviceAdapter = new OpenAIAdapter({ model: "gpt-4o" });
const runtime = new CopilotRuntime({
  agents: [
    new CustomHttpAgent({
      name: "research_agent",
      url: "http://localhost:8000/copilotkit",
    }),
    new CustomHttpAgent({
      name: "writer_agent",
      url: "http://localhost:8001/copilotkit",
    }),
  ],
});

export const POST = async (req: NextRequest) => {
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter,
    endpoint: "/api/copilotkit",
  });
  return handleRequest(req);
};
```

## LLM Adapters

### OpenAIAdapter
```typescript
import { OpenAIAdapter } from "@copilotkit/runtime";
const adapter = new OpenAIAdapter({ model: "gpt-4o" });
// Also supports: gpt-4o-mini, gpt-4-turbo, o1, o3, etc.
```

### AnthropicAdapter
```typescript
import { AnthropicAdapter } from "@copilotkit/runtime";
const adapter = new AnthropicAdapter({ model: "claude-sonnet-4-5-20250929" });
// Also supports: claude-opus-4-6, claude-haiku-4-5-20251001
```

### GoogleGenerativeAIAdapter
```typescript
import { GoogleGenerativeAIAdapter } from "@copilotkit/runtime";
const adapter = new GoogleGenerativeAIAdapter({ model: "gemini-2.0-flash" });
// Also supports: gemini-2.5-pro, gemini-2.5-flash
```

### GroqAdapter
```typescript
import { GroqAdapter } from "@copilotkit/runtime";
const adapter = new GroqAdapter({ model: "llama-3.3-70b-versatile" });
```

### LangChainAdapter (custom chains)
```typescript
import { LangChainAdapter } from "@copilotkit/runtime";
const adapter = new LangChainAdapter({
  chainFn: async ({ messages, tools }) => {
    // Build any LangChain/LangGraph workflow
    const chain = prompt.pipe(model).pipe(parser);
    return chain.stream({ messages });
  },
});
```

### OpenAIAssistantAdapter
```typescript
import { OpenAIAssistantAdapter } from "@copilotkit/runtime";
const adapter = new OpenAIAssistantAdapter({
  assistantId: "asst_abc123",
});
```

## Backend Actions

Define server-side actions accessible to agents:

```typescript
const runtime = new CopilotRuntime({
  actions: [
    {
      name: "queryDatabase",
      description: "Execute a database query and return results",
      parameters: [
        { name: "query", type: "string", description: "SQL query", required: true },
        { name: "limit", type: "number", description: "Max rows", required: false },
      ],
      handler: async ({ query, limit = 100 }) => {
        const results = await db.query(query, { limit });
        return JSON.stringify(results);
      },
    },
    {
      name: "sendEmail",
      description: "Send an email notification",
      parameters: [
        { name: "to", type: "string", required: true },
        { name: "subject", type: "string", required: true },
        { name: "body", type: "string", required: true },
      ],
      handler: async ({ to, subject, body }) => {
        await emailService.send({ to, subject, body });
        return "Email sent successfully";
      },
    },
  ],
});
```

## Deployment Modes

| Mode | Frontend Config | Use case |
|------|----------------|----------|
| **Self-hosted** | `runtimeUrl="/api/copilotkit"` | Full control, own infrastructure |
| **Copilot Cloud** | `publicApiKey="ck_..."` | Managed runtime, no backend needed |
| **Hybrid** | Both props | Cloud features + custom runtime |

### Self-hosted
```typescript
<CopilotKit runtimeUrl="/api/copilotkit">
```

### Copilot Cloud
```typescript
<CopilotKit publicApiKey="ck_your_key_here">
```

### Hybrid (Cloud + custom agents)
```typescript
<CopilotKit publicApiKey="ck_..." runtimeUrl="/api/copilotkit">
```

### Authentication

```typescript
// Custom headers
<CopilotKit
  runtimeUrl="/api/copilotkit"
  headers={{ Authorization: `Bearer ${token}` }}
/>

// Cookies (cross-origin)
<CopilotKit
  runtimeUrl="https://api.example.com/copilotkit"
  credentials="include"
/>

// LangGraph Platform auth
<CopilotKit
  runtimeUrl="/api/copilotkit"
  properties={{ authorization: { token: langGraphToken } }}
/>
```

## Built-in Agents

### BuiltInAgent

Pre-configured agent that runs directly in the CopilotRuntime with middleware support (e.g., MCP Apps):

```typescript
import { BuiltInAgent, MCPAppsMiddleware } from "@copilotkit/runtime";

const agent = new BuiltInAgent({
  model: "openai/gpt-4o",
}).use(
  new MCPAppsMiddleware({
    mcpServers: [{ type: "http", url: "http://localhost:3108/mcp", serverId: "my-server" }],
  })
);

const runtime = new CopilotRuntime({ agents: [agent] });
```

### BasicAgent

Simplified agent for direct-to-LLM scenarios without middleware. Lighter-weight alternative to BuiltInAgent for straightforward use cases:

```typescript
import { BasicAgent } from "@copilotkit/runtime";

const agent = new BasicAgent({
  name: "simple_assistant",
  model: "openai/gpt-4o",
  instructions: "You are a helpful coding assistant.",
});

const runtime = new CopilotRuntime({ agents: [agent] });
```

Use `BasicAgent` when you need a simple agent without middleware pipelines. Use `BuiltInAgent` when you need `.use()` middleware like `MCPAppsMiddleware`.

## Thread Model & Persistence

CopilotKit conversations are organized into threads, each identified by a unique thread ID.

### Thread IDs

Each conversation session gets a thread ID automatically. Thread IDs enable conversation continuity, state persistence, and reconnection after disconnects.

### Storage Runners (Development)

For development and testing, CopilotKit provides built-in storage runners:

```typescript
import { CopilotRuntime, InMemoryStorageRunner } from "@copilotkit/runtime";

// In-memory (resets on restart — dev only)
const runtime = new CopilotRuntime({
  storageRunner: new InMemoryStorageRunner(),
});
```

```typescript
import { CopilotRuntime, SQLiteStorageRunner } from "@copilotkit/runtime";

// SQLite (persists to file — dev/testing)
const runtime = new CopilotRuntime({
  storageRunner: new SQLiteStorageRunner({ dbPath: "./copilotkit.db" }),
});
```

### Thread Restoration & Reconnection

Threads support restoration after page reloads or disconnects. The frontend automatically reconnects to the existing thread using the stored thread ID.

### Copilot Cloud Persistence (Production)

For production deployments, use Copilot Cloud which provides managed persistence, thread storage, and automatic scaling:

```typescript
<CopilotKit publicApiKey="ck_..." />
```

## Authenticated Actions

Pass authentication context from the frontend to backend actions:

```typescript
// Frontend: pass auth via properties
<CopilotKit
  runtimeUrl="/api/copilotkit"
  properties={{ authorization: { token: userToken, userId: user.id } }}
/>

// Backend: access auth in action handlers
const runtime = new CopilotRuntime({
  actions: [
    {
      name: "getUserData",
      description: "Fetch authenticated user data",
      parameters: [{ name: "dataType", type: "string", required: true }],
      handler: async ({ dataType }, { properties }) => {
        const { token, userId } = properties.authorization;
        // Validate token and fetch data for userId
        return await fetchUserData(userId, dataType, token);
      },
    },
  ],
});
```

## Processing Flow

```
1. Framework endpoint receives HTTP request from frontend
2. Runtime aggregates context from all useCopilotReadable() calls
3. Frontend actions from useCopilotAction() converted to tool definitions
4. If agent name specified → route to agent (CustomHttpAgent)
   Otherwise → direct LLM call via service adapter
5. LLM processes messages + context + tools
6. Tool calls executed (frontend or backend), results returned
7. All events streamed to frontend via AG-UI event streaming over HTTP:
   - TEXT_MESSAGE_START/CONTENT/END
   - TOOL_CALL_START/ARGS/END
   - STATE_SNAPSHOT
8. Frontend hooks re-render UI with new data
```
