# Human-in-the-Loop (HITL)

CopilotKit supports two HITL patterns: buildtime (cognitive architecture design) and runtime (interactive collaboration during execution).

## Table of Contents
- [Buildtime HITL](#buildtime-hitl)
- [Runtime HITL](#runtime-hitl)
- [Design Principles](#design-principles)

## Buildtime HITL

Encode domain expert knowledge as agent workflows **before deployment**. The cognitive architecture becomes an adjustable parameter optimized per domain.

### Pattern: Agentic SOPs (Standard Operating Procedures)

Define step-by-step workflows in LangGraph that encode expert decision-making:

```python
from langgraph.graph import StateGraph

class ResearchState(MessagesState):
    query: str = ""
    sub_queries: list = []
    raw_results: list = []
    analyzed_results: list = []
    summary: str = ""

# Step 1: Parse main query into sub-queries
async def decompose(state): ...

# Step 2: Execute each sub-query in parallel
async def search(state): ...

# Step 3: Analyze and rank results
async def analyze(state): ...

# Step 4: Summarize and synthesize
async def synthesize(state): ...

builder = StateGraph(ResearchState)
builder.add_node("decompose", decompose)
builder.add_node("search", search)
builder.add_node("analyze", analyze)
builder.add_node("synthesize", synthesize)
builder.add_edge("decompose", "search")
builder.add_edge("search", "analyze")
builder.add_edge("analyze", "synthesize")
builder.set_entry_point("decompose")
```

The SOP structure is tunable — add/remove/reorder nodes to optimize for each domain.

## Runtime HITL

Four key capabilities during agent execution:

### 1. Streaming Intermediate States

Show agent work-in-progress to prevent long loading blank screens. Stream real-time progress to the UI:

```typescript
import { useCoAgentStateRender } from "@copilotkit/react-core";

// Show search progress
useCoAgentStateRender({
  name: "research_agent",
  node: "searching",
  render: ({ state, status }) => (
    <div className="search-progress">
      <Spinner />
      <p>Searching {state.sourcesChecked} of {state.totalSources} sources...</p>
      <ul>
        {state.resultsFound.map((r) => (
          <li key={r.id}>{r.title} - {r.relevanceScore}%</li>
        ))}
      </ul>
    </div>
  ),
});

// Show analysis progress
useCoAgentStateRender({
  name: "research_agent",
  node: "analyzing",
  render: ({ state }) => (
    <ProgressBar
      value={state.progress}
      label={`Analyzing: ${state.currentStep}`}
    />
  ),
});
```

### 2. Shared State (Collaborative Editing)

Agent and human both update the same state object in real-time via `useCoAgent`:

```typescript
const { state, setState } = useCoAgent({
  name: "document_agent",
  initialState: { title: "", content: "", suggestions: [] },
});

// Human edits title — agent sees change
<input
  value={state.title}
  onChange={(e) => setState({ title: e.target.value })}
/>

// Agent updates suggestions — human sees them
<SuggestionList items={state.suggestions} />
```

See [coagents-shared-state.md](coagents-shared-state.md) for full details.

### 3. Agent Q&A (Structured User Input)

Agent pauses execution to ask the user questions. Supports text responses (chat UI) and structured JSON responses with native UI components.

```typescript
import { useHumanInTheLoop } from "@copilotkit/react-core";

// Simple confirmation dialog
useHumanInTheLoop({
  name: "confirm_delete",
  render: ({ question, respond }) => (
    <ConfirmDialog
      title="Confirm Action"
      message={question}
      onConfirm={() => respond({ approved: true })}
      onReject={() => respond({ approved: false })}
    />
  ),
});

// Complex form input
useHumanInTheLoop({
  name: "get_preferences",
  render: ({ question, respond }) => (
    <PreferencesForm
      prompt={question}
      onSubmit={(formData) => respond(formData)}
    />
  ),
});

// Multi-choice selection
useHumanInTheLoop({
  name: "select_option",
  render: ({ question, respond }) => (
    <div>
      <p>{question}</p>
      <button onClick={() => respond({ choice: "A" })}>Option A</button>
      <button onClick={() => respond({ choice: "B" })}>Option B</button>
      <button onClick={() => respond({ choice: "C" })}>Option C</button>
    </div>
  ),
});
```

### 4. Agent Steering (Error Correction)

Allow users to correct agent mistakes mid-process. Uses LangGraph's checkpoint and time-travel capabilities to replay from the corrected point.

```typescript
import { useLangGraphInterrupt } from "@copilotkit/react-core";

useLangGraphInterrupt({
  render: ({ event, resume }) => {
    const agentState = event.value;

    return (
      <div className="interrupt-dialog">
        <h3>Agent paused — review and correct</h3>

        {/* Show what the agent has done so far */}
        <pre>{JSON.stringify(agentState, null, 2)}</pre>

        {/* Let user edit state before resuming */}
        <StateEditor
          state={agentState}
          onSave={(correctedState) => resume(correctedState)}
        />

        {/* Or approve as-is */}
        <button onClick={() => resume(agentState)}>
          Approve & Continue
        </button>
      </div>
    );
  },
});
```

**How agent steering works:**
1. Agent reaches a checkpoint/interrupt point in LangGraph
2. Frontend receives interrupt event via `useLangGraphInterrupt`
3. User reviews agent state, optionally corrects it
4. `resume(correctedState)` replays the graph from the checkpoint with corrected state
5. All subsequent nodes re-execute with the corrected input

## Design Principles

- **70-95% autonomy is the sweet spot.** Agents don't need to be perfect — pair them with human judgment for critical decisions.
- **Gate irreversible actions.** Use approval workflows for purchases, deletions, sends, data modifications.
- **Stream everything.** Show intermediate states to keep users engaged during long operations. A black box with a spinner feels broken after 5 seconds.
- **Collect correction signals.** HITL corrections are valuable training data for improving agent performance over time.
- **Use checkpoints strategically.** Place LangGraph interrupts before high-risk nodes, not after every step.
- **Keep dialogs simple.** Confirmation should be one click. Complex input should use structured forms, not free text.
