# AG-UI (Agent-User Interaction Protocol)

AG-UI is an open-source, lightweight, event-based protocol for real-time agent-to-frontend communication. It was created by the CopilotKit team and is the core communication layer in CopilotKit v1.50+.

## What is AG-UI

- Open-source protocol for agent-to-frontend communication
- Replaces the GraphQL-based architecture from earlier CopilotKit versions
- Defines 17 core event types for structured agent-UI interaction
- Framework-agnostic: any AG-UI compatible agent works with CopilotKit
- NPM packages:
  - `@ag-ui/core` — types, event definitions, base classes
  - `@ag-ui/client` — client-side implementation for consuming AG-UI streams

## Core Event Types

| Event | Purpose |
|-------|---------|
| `RUN_STARTED` | Agent run begins |
| `RUN_FINISHED` | Agent run complete |
| `RUN_ERROR` | Agent run failed |
| `TEXT_MESSAGE_START` | New text message begins (messageId, role) |
| `TEXT_MESSAGE_CONTENT` | Content chunk streamed (delta) |
| `TEXT_MESSAGE_END` | Message complete |
| `TOOL_CALL_START` | Tool invocation begins (toolCallId, toolName) |
| `TOOL_CALL_ARGS` | Tool arguments streamed (delta) |
| `TOOL_CALL_END` | Tool call complete |
| `STATE_SNAPSHOT` | Full agent state update |
| `STATE_DELTA` | Partial state update (JSON patch) |
| `MESSAGES_SNAPSHOT` | Full messages array update |
| `CUSTOM` | Application-specific events |
| `RAW` | Pass-through raw data |
| `STEP_STARTED` | Pipeline step begins |
| `STEP_FINISHED` | Pipeline step complete |

### Event Categories

- **Run lifecycle**: `RUN_STARTED`, `RUN_FINISHED`, `RUN_ERROR`
- **Text streaming**: `TEXT_MESSAGE_START`, `TEXT_MESSAGE_CONTENT`, `TEXT_MESSAGE_END`
- **Tool calls**: `TOOL_CALL_START`, `TOOL_CALL_ARGS`, `TOOL_CALL_END`
- **State management**: `STATE_SNAPSHOT`, `STATE_DELTA`
- **Messages**: `MESSAGES_SNAPSHOT`
- **Pipeline**: `STEP_STARTED`, `STEP_FINISHED`
- **Extensibility**: `CUSTOM`, `RAW`

## Event Flow Architecture

```
Agent (Python/JS)
  → emits AG-UI events
  → CopilotRuntime streams over HTTP
  → Frontend hooks consume events
  → React components re-render
```

A typical run emits events in this order:

```
RUN_STARTED
  → TEXT_MESSAGE_START
    → TEXT_MESSAGE_CONTENT (repeated for each chunk)
  → TEXT_MESSAGE_END
  → TOOL_CALL_START
    → TOOL_CALL_ARGS (repeated for each chunk)
  → TOOL_CALL_END
  → STATE_DELTA (as state changes)
RUN_FINISHED
```

## AG-UI CLI Scaffolding

```bash
npx create-ag-ui-app my-agent-app
```

This scaffolds a new project with AG-UI agent integration preconfigured.

## Compatible Agent Frameworks

All of the following frameworks work with CopilotKit via AG-UI:

- **LangGraph** — deep integration via `ag-ui-langgraph` adapter
- **CrewAI**
- **Google ADK**
- **AWS Strands**
- **Microsoft Agent Framework**
- **Mastra**
- **AG2 (AutoGen2)**
- **LlamaIndex**
- **PydanticAI**
- **Agno**

Any framework that can emit AG-UI events is compatible with CopilotKit's frontend.

## Agent Protocols Comparison

| Protocol | Direction | Purpose |
|----------|-----------|---------|
| **AG-UI** | Agent → User | Real-time UI streaming, state sync |
| **MCP** | Agent → Tools | External tool integration |
| **A2A** | Agent → Agent | Multi-agent communication |

These three protocols are complementary:
- AG-UI handles the frontend-facing communication
- MCP handles tool/service integration
- A2A handles inter-agent coordination

## Implementing a Custom AG-UI Agent

To create an AG-UI compatible agent that works with CopilotKit:

```typescript
import { AbstractAgent, RunAgentInput } from "@ag-ui/core";

class MyCustomAgent extends AbstractAgent {
  async *run(input: RunAgentInput) {
    yield { type: "RUN_STARTED", runId: input.runId };

    yield { type: "TEXT_MESSAGE_START", messageId: "msg-1", role: "assistant" };
    yield { type: "TEXT_MESSAGE_CONTENT", messageId: "msg-1", delta: "Hello!" };
    yield { type: "TEXT_MESSAGE_END", messageId: "msg-1" };

    yield { type: "RUN_FINISHED", runId: input.runId };
  }
}
```

### Key patterns for custom agents:

1. **Extend `AbstractAgent`** from `@ag-ui/core`
2. **Implement `async *run()`** as an async generator that yields events
3. **Always start with `RUN_STARTED`** and end with `RUN_FINISHED` or `RUN_ERROR`
4. **Pair start/end events** — every `TEXT_MESSAGE_START` needs a `TEXT_MESSAGE_END`, every `TOOL_CALL_START` needs a `TOOL_CALL_END`
5. **Use consistent IDs** — `runId`, `messageId`, and `toolCallId` must be consistent across related events
6. **Stream content incrementally** — use `delta` fields in `TEXT_MESSAGE_CONTENT` and `TOOL_CALL_ARGS` for real-time streaming

### With tool calls:

```typescript
async *run(input: RunAgentInput) {
  yield { type: "RUN_STARTED", runId: input.runId };

  // Invoke a frontend-defined tool
  yield {
    type: "TOOL_CALL_START",
    toolCallId: "tc-1",
    toolName: "searchDatabase",
  };
  yield {
    type: "TOOL_CALL_ARGS",
    toolCallId: "tc-1",
    delta: JSON.stringify({ query: "example" }),
  };
  yield { type: "TOOL_CALL_END", toolCallId: "tc-1" };

  // Stream a text response
  yield { type: "TEXT_MESSAGE_START", messageId: "msg-1", role: "assistant" };
  yield { type: "TEXT_MESSAGE_CONTENT", messageId: "msg-1", delta: "Found results." };
  yield { type: "TEXT_MESSAGE_END", messageId: "msg-1" };

  yield { type: "RUN_FINISHED", runId: input.runId };
}
```

### With state management:

```typescript
async *run(input: RunAgentInput) {
  yield { type: "RUN_STARTED", runId: input.runId };

  // Send full state snapshot
  yield {
    type: "STATE_SNAPSHOT",
    snapshot: { status: "processing", results: [] },
  };

  // Send incremental state update (JSON Patch format)
  yield {
    type: "STATE_DELTA",
    delta: [{ op: "replace", path: "/status", value: "complete" }],
  };

  yield { type: "RUN_FINISHED", runId: input.runId };
}
```

## AG-UI vs Previous CopilotKit Architecture

| Aspect | Before v1.50 | After v1.50 (AG-UI) |
|--------|-------------|---------------------|
| Protocol | GraphQL request/response | AG-UI event streaming over HTTP |
| Communication | Request-response cycles | Real-time event stream |
| Agent coupling | Tightly coupled to CopilotKit | Framework-agnostic |
| State updates | Full state on each response | Incremental deltas (JSON Patch) |
| Streaming | Limited | Native first-class streaming |
| Weight | Heavier (GraphQL schema) | Lightweight (simple events) |

### Migration benefits:
- **Lighter** — no GraphQL schema overhead
- **Faster** — real-time streaming instead of request/response
- **Framework-agnostic** — any agent framework can emit AG-UI events
- **Real-time streaming** — incremental content and state updates
- **Simpler** — 17 well-defined event types cover all use cases
