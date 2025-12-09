# Tech Spec: E4-S2 - Create ACM Context Toggle

> **Story:** E4-S2
> **Epic:** Chat with ACM Context
> **Status:** Draft
> **Created:** 2025-12-08

---

## Overview

Add a toggle switch to the chat panel that allows users to control whether ACM data is included in the chat context.

---

## User Story

**As a** user
**I want** to control whether ACM data is included in chat
**So that** I can have focused conversations

---

## Acceptance Criteria

- [ ] Toggle switch in chat panel header
- [ ] Default: ON when ACM data exists for selected source
- [ ] Visual indicator shows when ACM context is active
- [ ] Toggle state persists during session

---

## Technical Design

### 1. Chat Panel Header Update

Location: `frontend/src/components/source/ChatPanel.tsx`

```tsx
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { TableProperties } from 'lucide-react';

interface ChatPanelProps {
  sourceId: string;
  hasAcmData: boolean;
}

export function ChatPanel({ sourceId, hasAcmData }: ChatPanelProps) {
  const [includeAcmContext, setIncludeAcmContext] = useState(hasAcmData);

  // Persist toggle state in session storage
  useEffect(() => {
    const saved = sessionStorage.getItem(`acm-context-${sourceId}`);
    if (saved !== null) {
      setIncludeAcmContext(saved === 'true');
    }
  }, [sourceId]);

  const handleToggle = (checked: boolean) => {
    setIncludeAcmContext(checked);
    sessionStorage.setItem(`acm-context-${sourceId}`, String(checked));
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header with ACM Toggle */}
      <div className="flex items-center justify-between p-3 border-b">
        <h3 className="font-semibold">Chat</h3>

        {hasAcmData && (
          <div className="flex items-center gap-2">
            <TableProperties className="h-4 w-4 text-muted-foreground" />
            <Label htmlFor="acm-context" className="text-sm cursor-pointer">
              Include ACM Data
            </Label>
            <Switch
              id="acm-context"
              checked={includeAcmContext}
              onCheckedChange={handleToggle}
            />
          </div>
        )}
      </div>

      {/* ACM Context Indicator */}
      {includeAcmContext && hasAcmData && (
        <div className="px-3 py-2 bg-primary/10 text-primary text-xs flex items-center gap-2">
          <TableProperties className="h-3 w-3" />
          ACM Register data included in context
        </div>
      )}

      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto">
        <ChatMessages
          sourceId={sourceId}
          includeAcmContext={includeAcmContext}
        />
      </div>

      {/* Chat Input */}
      <ChatInput
        sourceId={sourceId}
        includeAcmContext={includeAcmContext}
      />
    </div>
  );
}
```

### 2. Pass Toggle State to API

Update chat mutation:

```tsx
// In useChatMutation hook
const sendMessage = async (message: string) => {
  const response = await fetch('/api/chat/source', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      source_id: sourceId,
      message: message,
      include_acm_context: includeAcmContext,  // New field
    }),
  });
  return response.json();
};
```

### 3. Backend Handler Update

Location: `api/routers/source_chat.py`

```python
class ChatRequest(BaseModel):
    source_id: str
    message: str
    include_acm_context: bool = True  # Default to include

@router.post("/chat/source")
async def chat_with_source(request: ChatRequest):
    source = await Source.get(request.source_id)

    # Build context
    context_parts = [source.full_text or ""]

    # Include ACM data if requested
    if request.include_acm_context:
        acm_records = await ACMRecord.get_by_source(request.source_id)
        if acm_records:
            acm_context = format_acm_context(acm_records)
            context_parts.append(acm_context)

    # Generate response...
```

### 4. Visual States

```tsx
// No ACM data available
{!hasAcmData && (
  <div className="px-3 py-2 text-muted-foreground text-xs">
    No ACM data available for this source
  </div>
)}

// ACM data available but toggled off
{hasAcmData && !includeAcmContext && (
  <div className="px-3 py-2 text-muted-foreground text-xs flex items-center gap-2">
    <TableProperties className="h-3 w-3" />
    ACM data not included (toggle to enable)
  </div>
)}
```

---

## File Changes

| File | Change |
|------|--------|
| `frontend/src/components/source/ChatPanel.tsx` | Add ACM toggle |
| `frontend/src/components/source/ChatInput.tsx` | Pass toggle state |
| `api/routers/source_chat.py` | Handle include_acm_context |

---

## Dependencies

- E4-S1: ACM data in chat context (base implementation)

---

## Testing

1. View source with ACM data - verify toggle shows
2. Toggle ON - verify indicator shows
3. Toggle OFF - verify indicator hides
4. Refresh page - verify toggle state persists
5. View source without ACM data - verify toggle hidden
6. Send chat with toggle ON - verify ACM context in response
7. Send chat with toggle OFF - verify no ACM context

---

## Estimated Complexity

**Low** - UI toggle with session persistence

---
