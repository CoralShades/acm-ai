# Agent-Browser Patterns for ACM-AI

Curated patterns for using `agent-browser` to debug and verify ACM-AI pages.

## Core Workflow

Every interaction follows: **navigate -> snapshot -> interact -> re-snapshot**.

```bash
agent-browser open http://localhost:8503/source/source%3Atest001
agent-browser snapshot -i
# Output: @e1 [button] "Main Block", @e2 [input] "Search records...", @e3 [button] "Group by Room"

agent-browser click @e1
agent-browser snapshot -i   # MUST re-snapshot after page changes (refs invalidated)
```

## ACM Page Debugging

### Building Sidebar

```bash
agent-browser open http://localhost:8503/source/source%3Atest001
agent-browser snapshot -i

# Extract building list
agent-browser eval --stdin <<'EVALEOF'
JSON.stringify(
  Array.from(document.querySelectorAll('[data-testid="building-sidebar"] button'))
    .map(b => b.textContent?.trim())
)
EVALEOF

# Click a building
agent-browser click @e1   # Use ref from snapshot
agent-browser wait --load networkidle
agent-browser snapshot -i  # Check item grid updated
```

### Item Grid (AG Grid)

```bash
# Count grid rows
agent-browser eval 'document.querySelectorAll(".ag-row").length'

# Get column headers
agent-browser eval --stdin <<'EVALEOF'
JSON.stringify(
  Array.from(document.querySelectorAll('.ag-header-cell-text'))
    .map(h => h.textContent?.trim())
)
EVALEOF

# Scroll to see virtual rows
agent-browser scroll down 500 --selector ".ag-body-viewport"
agent-browser snapshot -i
```

### Upload Wizard

```bash
agent-browser open http://localhost:8503/upload
agent-browser snapshot -i
# Look for: @eN [input type="file"], @eN [button] "Upload"

# Verify wizard steps
agent-browser snapshot -i -s "[data-testid='upload-step-1']"
```

### Extraction Progress

```bash
agent-browser open http://localhost:8503/extraction-monitor
agent-browser snapshot -i -s "[data-testid='extraction-progress']"
```

## Visual Regression

### Baseline + Compare

```bash
# Save baseline before changes
agent-browser open http://localhost:8503/acm && agent-browser wait --load networkidle
agent-browser screenshot baseline-acm.png

# After code changes, compare
agent-browser open http://localhost:8503/acm && agent-browser wait --load networkidle
agent-browser diff screenshot --baseline baseline-acm.png
# Output: mismatch percentage and diff image with changed pixels in red
```

### Multi-Page Baseline

```bash
for page in "" "/acm" "/sources" "/settings"; do
  agent-browser open "http://localhost:8503${page}" && agent-browser wait --load networkidle
  agent-browser screenshot "baseline${page//\//-}.png"
done
```

## Data Extraction

### AG Grid Rows

```bash
agent-browser eval 'document.querySelectorAll(".ag-row").length'
```

### Building Counts

```bash
agent-browser eval --stdin <<'EVALEOF'
JSON.stringify({
  buildings: document.querySelectorAll('[data-testid="building-sidebar"] button').length,
  gridRows: document.querySelectorAll('.ag-row').length
})
EVALEOF
```

### Form Values

```bash
agent-browser eval --stdin <<'EVALEOF'
JSON.stringify(
  Array.from(document.querySelectorAll('input, select, textarea'))
    .map(el => ({
      name: el.name || el.id || el.placeholder,
      value: el.value,
      type: el.type
    }))
)
EVALEOF
```

### Network Requests

```bash
agent-browser eval --stdin <<'EVALEOF'
JSON.stringify(
  performance.getEntriesByType("resource")
    .filter(r => r.name.includes("/api/"))
    .map(r => ({ url: r.name, duration: Math.round(r.duration) }))
)
EVALEOF
```

## Responsive Testing

```bash
# Desktop (default)
agent-browser open http://localhost:8503 --viewport 1280x720
agent-browser screenshot desktop.png

# Tablet
agent-browser open http://localhost:8503 --viewport 768x1024
agent-browser screenshot tablet.png

# Mobile
agent-browser open http://localhost:8503 --viewport 375x667
agent-browser screenshot mobile.png
```

## Failure Investigation

When a Playwright test fails:

```bash
# 1. Open the exact URL that failed
agent-browser open http://localhost:8503/source/source%3Atest001

# 2. Check for the missing element
agent-browser snapshot -i -s "[data-testid='item-grid']"
# If empty: element is missing or has wrong testid

# 3. Get full page text for debugging
agent-browser get text body > /tmp/page-content.txt

# 4. Check console errors
agent-browser eval 'JSON.stringify(window.__e2e_errors || [])'

# 5. Check for JS errors in console
agent-browser eval --stdin <<'EVALEOF'
JSON.stringify(
  performance.getEntriesByType("resource")
    .filter(r => r.responseStatus >= 400)
    .map(r => ({ url: r.name, status: r.responseStatus }))
)
EVALEOF

# 6. Take annotated screenshot as evidence
agent-browser screenshot --annotate --full test-results/evidence/failure.png
```

## Diff Workflow

Use diffs to verify that actions had the intended effect:

```bash
# Snapshot before action
agent-browser snapshot -i

# Perform action
agent-browser click @e3

# Diff after action
agent-browser diff snapshot
# Output shows + additions and - removals (like git diff)
```

## Settings Page Verification

```bash
agent-browser open http://localhost:8503/settings/models
agent-browser snapshot -i
# Look for form inputs, save buttons

agent-browser open http://localhost:8503/settings/field-schema
agent-browser snapshot -i
# Verify field schema configuration
```

## Session Management

```bash
# Named sessions for parallel work
agent-browser --session acm-test open http://localhost:8503/acm
agent-browser --session upload-test open http://localhost:8503/upload

# Check active sessions
agent-browser session list

# Always close when done
agent-browser --session acm-test close
agent-browser --session upload-test close
```
