---
description: Render a Jinja2 prompt template with sample data and preview
allowed-tools: Bash, Read, Glob
argument-hint: <prompt_path> [--vars key=value] [--preview-only]
---

# Prompt Test

Render a Jinja2 prompt template from `prompts/` with sample data for preview and testing.

## Instructions

### 1. Parse Arguments

- `$1` = path to prompt template (e.g., `prompts/acm_extraction.jinja2`)
- `--vars` = space-separated key=value pairs to substitute (optional)
- `--preview-only` = just render, don't reference LangSmith (default)

If no path provided, list available templates:
```bash
echo "=== Available Prompt Templates ==="
find prompts/ -name "*.jinja2" -o -name "*.j2" 2>/dev/null | sort
```

### 2. Read the Template

Read the template file to understand its variables and structure.

### 3. Render with Sample Data

```bash
uv run python -c "
from jinja2 import Environment, FileSystemLoader
import sys

env = Environment(loader=FileSystemLoader('.'))
template = env.get_template('${PROMPT_PATH}')

# Default sample data — override with --vars
sample_vars = {
    'content': '[Sample ACM table content would go here]',
    'building_name': 'Sample School',
    'page_number': '5',
    'total_pages': '20',
    'format_instructions': '{JSON schema instructions}',
}

# Apply user overrides
# (parse --vars arguments here)

rendered = template.render(**sample_vars)
print(rendered)
"
```

### 4. Present Output

```markdown
## Prompt Template Preview: {path}

### Template Variables
| Variable | Value Used |
|----------|-----------|

### Rendered Output
\`\`\`
{rendered template text}
\`\`\`

### Template Size
- Characters: {count}
- Estimated Tokens: ~{count / 4}

### LangSmith Playground
To iterate on this prompt interactively:
1. Open LangSmith at https://smith.langchain.com
2. Navigate to Prompts > Playground
3. Paste the rendered output
4. Edit and re-run with different models
```

## Notes

- Templates are Jinja2 files in `prompts/` directory
- LangSmith Playground requires `LANGCHAIN_API_KEY` and `LANGCHAIN_TRACING_V2=true`
- For production prompt changes, modify the `.jinja2` file directly, not LangSmith
