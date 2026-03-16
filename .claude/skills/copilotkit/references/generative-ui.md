# Generative UI

CopilotKit supports three approaches to dynamic, agent-driven UI rendering at runtime.

## Table of Contents
- [1. Static Generative UI (AG-UI Protocol)](#1-static-generative-ui-ag-ui-protocol)
- [2. Declarative Generative UI (A2UI / Open-JSON-UI)](#2-declarative-generative-ui-a2ui--open-json-ui)
- [3. Open-Ended Generative UI (MCP Apps)](#3-open-ended-generative-ui-mcp-apps)
- [Choosing an Approach](#choosing-an-approach)
- [AG-UI Protocol Events](#ag-ui-protocol-events)

## 1. Static Generative UI (AG-UI Protocol)

Highest developer control. Pre-build React components; agents select which to display and populate with data.

### Using `useFrontendTool` (frontend tool rendering)

Register a tool that agents can call, with a custom React render function:

```typescript
import { useFrontendTool } from "@copilotkit/react-core";
import { z } from "zod";

useFrontendTool({
  name: "get_weather",
  description: "Get current weather information for a location",
  parameters: z.object({
    location: z.string().describe("City name"),
    units: z.enum(["celsius", "fahrenheit"]).optional(),
  }),
  handler: async ({ location, units = "celsius" }) => {
    const data = await fetchWeather(location, units);
    return data;
  },
  render: ({ status, args, result }) => {
    if (status === "inProgress") {
      return <WeatherLoadingState location={args?.location} />;
    }
    if (status === "complete" && result) {
      return <WeatherCard {...parseWeatherData(result)} />;
    }
    if (status === "failed") {
      return <ErrorCard message="Failed to fetch weather" />;
    }
    return null;
  },
});
```

**Note:** `useFrontendTool` is a wrapper around `useCopilotAction` with added render support. Both register callable tools.

### Using `useRenderToolCall` (backend tool rendering)

Render custom UI for backend-defined tool calls:

```typescript
import { useRenderToolCall } from "@copilotkit/react-core";

useRenderToolCall({
  name: "search_results",
  render: ({ args, result, status }) => {
    if (status === "inProgress") {
      return <SearchSkeleton query={args.query} />;
    }
    return <SearchResultsCard query={args.query} results={result} />;
  },
});
```

### Lifecycle States

All render functions receive a `status` parameter:

| Status | Meaning | Typical UI |
|--------|---------|-----------|
| `"inProgress"` | Tool is executing | Loading spinner, skeleton, progress bar |
| `"executing"` | Handler running | Same as inProgress |
| `"complete"` | Tool finished successfully | Render final result |
| `"failed"` | Tool errored | Error message, retry button |

### Using `useDefaultTool` (fallback renderer)

Provide a default/fallback UI renderer for any tool calls that don't have a specific custom renderer registered via `useFrontendTool` or `useRenderToolCall`:

```typescript
import { useDefaultTool } from "@copilotkit/react-core";

useDefaultTool({
  render: ({ name, args, status, result }) => (
    <div className="default-tool-card">
      <h4>Tool: {name}</h4>
      {status === "inProgress" && <Spinner />}
      {status === "complete" && <pre>{JSON.stringify(result, null, 2)}</pre>}
      {status === "failed" && <ErrorMessage />}
    </div>
  ),
});
```

This is useful when working with many backend tools or agent-emitted tool calls where defining individual renderers for each is impractical. Tools with specific renderers take precedence over the default.

### Multiple Tools Example

```typescript
// Stock price tool
useFrontendTool({
  name: "stock_price",
  description: "Get real-time stock price",
  parameters: z.object({ symbol: z.string() }),
  handler: async ({ symbol }) => await getStockPrice(symbol),
  render: ({ status, result }) =>
    status === "complete" ? <StockTicker {...result} /> : <StockSkeleton />,
});

// Chart tool
useFrontendTool({
  name: "show_chart",
  description: "Display a data chart",
  parameters: z.object({
    data: z.array(z.object({ x: z.number(), y: z.number() })),
    type: z.enum(["line", "bar", "pie"]),
  }),
  handler: async ({ data, type }) => ({ data, type }),
  render: ({ status, result }) =>
    status === "complete" ? <Chart data={result.data} type={result.type} /> : <ChartSkeleton />,
});
```

## 2. Declarative Generative UI (A2UI / Open-JSON-UI)

Shared control. Agents return structured JSON UI specifications; the frontend renders them with type constraints and styling.

### A2UI (Google's specification)

1. Use the A2UI Composer to generate template specs
2. Include template in agent system prompt as reference
3. Agent emits JSONL-formatted UI descriptions

```typescript
// Agent emits structured messages like:
[
  { "beginRendering": { "surfaceId": "form-surface", "root": "form-column" } },
  {
    "surfaceUpdate": {
      "surfaceId": "form-surface",
      "components": [
        { "type": "text-input", "id": "name", "label": "Full Name" },
        { "type": "select", "id": "country", "options": ["US", "UK", "CA"] },
        { "type": "button", "id": "submit", "label": "Submit" }
      ]
    }
  },
  {
    "dataModelUpdate": {
      "surfaceId": "form-surface",
      "path": "/",
      "contents": [{ "key": "name", "value": "" }]
    }
  }
]
```

### A2UI Frontend Integration

```typescript
import { createA2UIMessageRenderer } from "@copilotkit/react-ui";

const A2UIRenderer = createA2UIMessageRenderer({
  theme: {
    primaryColor: "#3b82f6",
    borderRadius: "8px",
    fontFamily: "Inter, sans-serif",
  },
});

// Pass to provider
<CopilotKit
  runtimeUrl="/api/copilotkit"
  renderActivityMessages={[A2UIRenderer]}
>
  {children}
</CopilotKit>
```

### Open-JSON-UI (OpenAI's specification)

Similar declarative approach using OpenAI's JSON standardization for cross-platform compatibility. Agents emit JSON following the Open-JSON-UI schema, rendered by compatible frontends.

## 3. Open-Ended Generative UI (MCP Apps)

Lowest developer control, highest agent freedom. Agents return full UI surfaces (HTML, iframes, custom JSON) that the frontend hosts.

```typescript
import { MCPAppsMiddleware, BuiltInAgent } from "@copilotkit/runtime";

const agent = new BuiltInAgent({
  model: "openai/gpt-4o",
}).use(
  new MCPAppsMiddleware({
    mcpServers: [
      {
        type: "http",
        url: "http://localhost:3108/mcp",
        serverId: "my-server",
      },
    ],
  })
);
```

MCP Apps render interactive components from MCP servers directly in the chat interface.

## Choosing an Approach

| Approach | Dev Control | Agent Freedom | Best for |
|----------|------------|---------------|----------|
| Static (AG-UI) | High | Low | Well-defined, reusable components |
| Declarative (A2UI) | Medium | Medium | Structured forms, data display, rapid prototyping |
| Open-ended (MCP) | Low | High | Specialized tools, rich interactions, third-party UIs |

**Best practices:**
- Start with static (AG-UI) for predictable, branded components
- Evolve to declarative (A2UI) when you need agent-driven forms/layouts
- Use open-ended (MCP) only for specialized external tools
- Mix approaches in the same app — each tool can use a different pattern
- Always include loading states for `"inProgress"` status
- Use `useRenderToolCall` for backend tools, `useFrontendTool` for frontend tools

## AG-UI Protocol Events

The underlying event system powering all generative UI:

| Event | Emitted When |
|-------|-------------|
| `TEXT_MESSAGE_START` | New message begins (messageId, role) |
| `TEXT_MESSAGE_CONTENT` | Content chunk streamed (delta) |
| `TEXT_MESSAGE_END` | Message complete |
| `TOOL_CALL_START` | Tool invocation begins (toolCallId, toolName) |
| `TOOL_CALL_ARGS` | Tool arguments streamed (delta) |
| `TOOL_CALL_END` | Tool call complete |
| `STATE_SNAPSHOT` | Full agent state update |
| `CUSTOM` | Application-specific events (name/value) |

These events flow: Agent → CopilotRuntime → AG-UI event stream over HTTP → React hooks → UI re-render.
