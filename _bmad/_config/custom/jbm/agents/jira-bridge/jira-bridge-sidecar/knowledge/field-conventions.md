# Jira Field Conventions

## Standard Fields

### Summary
- **Max Length**: 255 characters (80 recommended)
- **Format**: `[Type] Brief description of work`
- **Examples**:
  - `[Epic] User Authentication System`
  - `[Story] User can reset password via email`
  - `[Task] Implement JWT token validation`

### Description
- **Format**: Structured markdown
- **Sections to include**:
  - Overview (1-2 sentences)
  - Context (why this work matters)
  - Requirements (bullet list)
  - Technical Notes (if applicable)
  - Source Document link

### Acceptance Criteria
- **Format**: Checkbox list or Given/When/Then
- **Requirements**:
  - Each criterion independently verifiable
  - Include happy path and error cases
  - Quantifiable where possible

### Priority
- **P1 - Critical**: Production blocker, security issue
- **P2 - High**: Sprint commitment, business critical
- **P3 - Medium**: Normal priority work
- **P4 - Low**: Nice to have, tech debt

### Story Points
- **1 point**: Few hours, trivial change
- **2 points**: Half day, small feature
- **3 points**: 1 day, moderate complexity
- **5 points**: 2-3 days, significant work
- **8 points**: 1 week, complex feature
- **13 points**: Consider breaking down

## Custom Field Patterns

### Epic Link
- Required for all Stories and Tasks
- Use Epic key, not name
- Verify Epic exists before linking

### Sprint
- Only assign when work is planned
- Do not backlog into future sprints
- Move unfinished work to next sprint

### Components
- Map to system areas (frontend, backend, database)
- Can have multiple components
- Use existing components when possible

### Labels
- Use for cross-cutting concerns
- Standard labels: `tech-debt`, `bug`, `enhancement`
- Project-specific labels as needed

## Workflow States

### Standard Flow
```
Open -> In Progress -> In Review -> Done
```

### Extended Flow
```
Open -> Refinement -> Ready -> In Progress -> In Review -> QA -> Done
```

### Transition Rules
- **Open -> In Progress**: Assignee required
- **In Progress -> In Review**: Code submitted
- **In Review -> Done**: All checks passed

## Linking Conventions

### Link Types to Use
- **blocks**: Work cannot start until blocker done
- **is blocked by**: Inverse of blocks
- **relates to**: General relationship
- **duplicates**: Same work, different ticket

### When to Link
- Always link to parent Epic/Story
- Link dependencies before sprint starts
- Link related work for context
