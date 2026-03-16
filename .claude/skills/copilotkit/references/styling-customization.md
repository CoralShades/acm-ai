# Styling & Customization

## Import Default Styles

```typescript
import "@copilotkit/react-ui/styles.css";
```

## CSS Custom Properties

Override CopilotKit CSS variables for quick theming:

```css
:root {
  --copilot-kit-primary-color: #your-brand-color;
  --copilot-kit-background-color: #ffffff;
  --copilot-kit-response-button-background-color: #f0f0f0;
  --copilot-kit-response-button-color: #333333;
}
```

## Custom Sub-Components

Replace any part of the chat UI by passing custom components as props:

```typescript
<CopilotSidebar
  instructions="You are a helpful assistant."
  labels={{
    title: "My AI",
    initial: "Ask me anything!",
    placeholder: "Type your message...",
  }}
  // Custom components
  Header={MyCustomHeader}
  Messages={MyCustomMessages}
  Input={MyCustomInput}
  ResponseButton={MyCustomButton}
/>
```

## Chat Component Props

All chat components (`CopilotChat`, `CopilotSidebar`, `CopilotPopup`) share these props:

```typescript
interface ChatComponentProps {
  // Core
  instructions?: string;           // System message for AI behavior
  labels?: {
    title?: string;                // Chat window title
    initial?: string;              // Initial greeting message
    placeholder?: string;          // Input placeholder text
    stopGenerating?: string;       // Stop button text
    regenerateResponse?: string;   // Regenerate button text
  };

  // Suggestions
  suggestions?: SuggestionConfig;  // auto | manual | static array

  // Custom rendering
  Header?: React.ComponentType;
  Messages?: React.ComponentType;
  Input?: React.ComponentType;
  ResponseButton?: React.ComponentType;

  // Observability
  observabilityHooks?: {
    onMessage?: (message) => void;
    onToolCall?: (toolCall) => void;
    onError?: (error) => void;
  };

  // Markdown
  makeSystemMessage?: (instructions: string) => string;
}
```

## Fully Headless Mode

Build completely custom UI using hooks directly — no pre-built components:

```typescript
import { useCopilotChat } from "@copilotkit/react-core";

function MyCustomChat() {
  const {
    visibleMessages,
    appendMessage,
    stopGeneration,
    reset,
    reloadMessages,
    isLoading,
  } = useCopilotChat();

  return (
    <div className="my-chat">
      {visibleMessages.map((msg) => (
        <div key={msg.id} className={`message-${msg.role}`}>
          {msg.content}
        </div>
      ))}

      <form onSubmit={(e) => {
        e.preventDefault();
        appendMessage({ role: "user", content: input });
      }}>
        <input value={input} onChange={(e) => setInput(e.target.value)} />
        <button type="submit">Send</button>
      </form>

      {isLoading && <button onClick={stopGeneration}>Stop</button>}
    </div>
  );
}
```

### Headless with `useAgent`

```typescript
import { useAgent } from "@copilotkit/react-core";

function AgentDrivenUI() {
  const { agent } = useAgent({ agentId: "my_agent" });

  return (
    <div>
      <p>Status: {agent.state.status}</p>
      <p>Result: {agent.state.result}</p>
      <button onClick={() => agent.setState({ query: "search term" })}>
        Trigger Agent
      </button>
    </div>
  );
}
```

## CopilotTextarea

AI-powered drop-in textarea replacement:

```typescript
import { CopilotTextarea } from "@copilotkit/react-ui";

<CopilotTextarea
  placeholder="Start typing..."
  autosuggestionsConfig={{
    textareaPurpose: "A professional email to a client",
    chatApiConfigs: {},
  }}
/>
```

## Suggestions Configuration

```typescript
// Auto-generated from app state
<CopilotPopup suggestions={{ mode: "auto" }} />

// Manual control
<CopilotPopup suggestions={{ mode: "manual", items: suggestionsArray }} />

// Static suggestions
<CopilotPopup suggestions={[
  { title: "Summarize data", message: "Give me a summary of the dashboard" },
  { title: "Export report", message: "Export this data as a CSV" },
]} />
```

## Markdown Rendering

Chat components support markdown by default. Customize rendering:

```typescript
<CopilotChat
  makeSystemMessage={(instructions) =>
    `${instructions}\n\nFormat responses using markdown.`
  }
/>
```

## Dark Mode

Override CSS variables for dark theme:

```css
[data-theme="dark"] {
  --copilot-kit-background-color: #1a1a2e;
  --copilot-kit-primary-color: #e94560;
  --copilot-kit-response-button-background-color: #16213e;
  --copilot-kit-response-button-color: #eaeaea;
}
```
