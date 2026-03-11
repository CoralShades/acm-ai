# CoAgents & Shared State

**CopilotKit v1.51.3**

## Table of Contents
- [One-Way State: useCopilotReadable](#one-way-state-usecopilotreadable)
- [useAgent (v2 — Recommended)](#useagent-v2--recommended)
- [Bidirectional State: useCoAgent (v1)](#bidirectional-state-usecoagent-v1)
- [Agent State Rendering: useCoAgentStateRender](#agent-state-rendering-usecoagentstaterender)
- [LangGraph Integration](#langgraph-integration)
- [State Flow Architecture](#state-flow-architecture)
- [Multiple CoAgents](#multiple-coagents)

## One-Way State: `useCopilotReadable`

Expose React state to agents (frontend → agent only). Agent can read but not modify.

```typescript
import { useCopilotReadable } from "@copilotkit/react-core";

// Expose simple state
useCopilotReadable({
  description: "The current shopping cart items and total",
  value: {
    items: cart.items,
    total: cart.total,
    itemCount: cart.items.length,
  },
});

// Expose derived/computed state
useCopilotReadable({
  description: "User's current page and navigation context",
  value: {
    currentPage: router.pathname,
    isAuthenticated: !!session,
    userRole: session?.user?.role,
  },
});

// Multiple readables for different contexts
useCopilotReadable({
  description: "Available product categories",
  value: categories,
});

useCopilotReadable({
  description: "Active filters and sort order",
  value: { filters, sortBy, sortOrder },
});
```

**How it works:** Values are serialized and sent as `CopilotContextItem` objects in the runtime context. Agents receive them as structured context alongside conversation messages.

## useAgent (v2 — Recommended)

`useAgent` is the v2 superset of `useCoAgent`. It provides full bidirectional state sync plus time travel, multi-agent execution, and agent mutual awareness. **Recommended for all new projects.**

Import from `@copilotkit/react-core`:

```typescript
import { useAgent } from "@copilotkit/react-core";

const { agent } = useAgent({ agentId: "my_agent" });

// Shared state — read and write
agent.state                          // read current state
agent.setState({ key: "value" })     // write / merge state

// Time travel — reset conversation to a previous point
agent.setMessages(previousMessages)

// Multi-agent — multiple useAgent calls in the same component/app
const { agent: agentA } = useAgent({ agentId: "agent_a" });
const { agent: agentB } = useAgent({ agentId: "agent_b" });
// Agents are aware of each other when configured on the same runtime
```

### useAgent in a component

```typescript
import { useAgent } from "@copilotkit/react-core";

function WeatherDashboard() {
  const { agent } = useAgent({ agentId: "weather_agent" });

  return (
    <div>
      <h1>Weather in {agent.state.city}</h1>
      <p>Temperature: {agent.state.temperature}F</p>
      <button onClick={() => agent.setState({ city: "London" })}>
        Switch to London
      </button>
      {/* Time travel: rewind to earlier messages */}
      <button onClick={() => agent.setMessages(previousMessages)}>
        Undo last exchange
      </button>
    </div>
  );
}
```

### Key differences from useCoAgent

| Feature | `useAgent` (v2) | `useCoAgent` (v1) |
|---------|-----------------|-------------------|
| Bidirectional state | Yes | Yes |
| Time travel (`setMessages`) | Yes | No |
| Multi-agent mutual awareness | Yes | Limited |
| AG-UI protocol access | Full | Partial |
| Identifier prop | `agentId` | `name` |

## Bidirectional State: `useCoAgent` (v1)

> **Note:** `useCoAgent` is still fully supported but `useAgent` (above) is recommended for new projects. `useCoAgent` may be deprecated in a future major release.

Full two-way state sync between UI and agent. Both can read and write.

```typescript
import { useCoAgent } from "@copilotkit/react-core";

const { state, setState } = useCoAgent({
  name: "research_agent",
  initialState: {
    query: "",
    results: [],
    status: "idle",
    selectedResult: null,
  },
});

// Read agent state in UI
function ResearchDashboard() {
  return (
    <div>
      {state.status === "searching" && <Spinner text="Searching..." />}
      {state.status === "analyzing" && <ProgressBar />}

      <ResultsList
        results={state.results}
        onSelect={(r) => setState({ selectedResult: r })}
      />

      {state.selectedResult && <DetailView item={state.selectedResult} />}

      {/* Update state from UI — agent sees changes immediately */}
      <SearchInput
        value={state.query}
        onChange={(query) => setState({ query })}
        onSubmit={() => setState({ status: "searching" })}
      />
    </div>
  );
}
```

**State merge strategy:** Deep merge with "last write wins" conflict resolution. Partial updates are merged into existing state.

## Agent State Rendering: `useCoAgentStateRender`

Render agent intermediate state as generative UI during execution. Shows real-time progress for specific agent workflow nodes.

```typescript
import { useCoAgentStateRender } from "@copilotkit/react-core";

// Render progress during "searching" node
useCoAgentStateRender({
  name: "research_agent",
  node: "searching",
  render: ({ state, nodeName, status }) => {
    if (status === "inProgress") {
      return (
        <SearchProgress
          query={state.query}
          sourcesFound={state.results.length}
          currentSource={state.currentSource}
        />
      );
    }
    return <SearchComplete count={state.results.length} />;
  },
});

// Render during "analyzing" node
useCoAgentStateRender({
  name: "research_agent",
  node: "analyzing",
  render: ({ state }) => (
    <AnalysisProgress
      logs={state.logs}
      percentage={state.progress}
    />
  ),
});
```

## LangGraph Integration

### Python agent setup

```python
from copilotkit import CopilotKitRemoteEndpoint, LangGraphAgent
from copilotkit.fastapi import add_fastapi_endpoint
from langgraph.graph import StateGraph, MessagesState
from fastapi import FastAPI

class ResearchState(MessagesState):
    query: str = ""
    results: list = []
    status: str = "idle"

async def search_node(state: ResearchState):
    # Access frontend context from useCopilotReadable
    context = state.get("copilotkit", {}).get("context", [])
    results = await perform_search(state["query"], context)
    return {"results": results, "status": "complete"}

builder = StateGraph(ResearchState)
builder.add_node("search", search_node)
builder.set_entry_point("search")
graph = builder.compile()

agent = LangGraphAgent(name="research_agent", graph=graph)
endpoint = CopilotKitRemoteEndpoint(agents=[agent])
app = FastAPI()
add_fastapi_endpoint(app, endpoint, "/copilotkit")
```

### Connect from frontend runtime

```typescript
import { CopilotRuntime, OpenAIAdapter, CustomHttpAgent } from "@copilotkit/runtime";

const runtime = new CopilotRuntime({
  serviceAdapter: new OpenAIAdapter({ model: "gpt-4o" }),
  agents: [
    new CustomHttpAgent({
      name: "research_agent",
      url: "http://localhost:8000/copilotkit",
    }),
  ],
});
```

### Use in frontend

```typescript
// layout.tsx — specify the agent
<CopilotKit runtimeUrl="/api/copilotkit" agent="research_agent">
  {children}
</CopilotKit>

// Or per-component
const { state, setState } = useCoAgent({ name: "research_agent" });
```

## State Flow Architecture

```
Frontend                          Backend
────────                          ───────

useCopilotReadable(value)
        │
        ▼
  HTTP request ────────────────→ CopilotRuntime
  (context + messages)             │
                                   ▼
                              Agent (LangGraph)
                              reads context,
                              executes nodes
                                   │
                                   ▼
                              AG-UI Events
                              STATE_SNAPSHOT
                                   │
  AG-UI event stream ◄─────────────┘
        │
        ▼
  useCoAgent.state updated
  useCoAgentStateRender triggers
  UI re-renders
```

Both directions stream in real-time via AG-UI event streaming over HTTP.

## Multiple CoAgents

Run multiple agents in the same app, each with independent state:

```typescript
const { state: researchState } = useCoAgent({ name: "research_agent" });
const { state: writerState } = useCoAgent({ name: "writer_agent" });
const { state: reviewState } = useCoAgent({ name: "review_agent" });

// Each agent has independent state managed by its own backend
// Agents can communicate via A2A protocol if needed
```

Switch active agent dynamically:

```typescript
<CopilotKit runtimeUrl="/api/copilotkit" agent={activeAgent}>
  {children}
</CopilotKit>
```
