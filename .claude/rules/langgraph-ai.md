---
paths:
  - "open_notebook/graphs/**/*"
  - "prompts/**/*"
---

# LangGraph AI Workflow Rules

## Graph Structure
Location: `open_notebook/graphs/`

### Workflow Organization
Each graph module should:
- Define clear state schema
- Use typed state transitions
- Handle errors gracefully

### Node Functions
```python
async def node_function(state: GraphState) -> GraphState:
    """Process state and return updated state."""
    # Process
    return {"key": updated_value}
```

## Prompt Templates
Location: `prompts/`

### Template Format
- Use Jinja2 templating
- Keep prompts in separate `.j2` files
- Include clear variable documentation

### Best Practices
- Test prompts with various inputs
- Version control prompt changes
- Document expected outputs

## Esperanto Integration
Multi-provider abstraction for LLM calls:
- Supports OpenAI, Anthropic, and others
- Configure models in `model` table

## Error Handling
- Catch and log LLM API errors
- Implement retry logic with backoff
- Provide fallback responses where appropriate
