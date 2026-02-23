# Project Mappings Knowledge Base

## BMAD to Jira Issue Type Mapping

### Standard Mappings

| BMAD Artifact | Jira Issue Type | Notes |
|---------------|-----------------|-------|
| PRD | Epic | High-level feature or initiative |
| Product Brief | Epic | Business-focused requirements |
| Epic (BMAD) | Epic | Direct mapping |
| User Story | Story | Contains acceptance criteria |
| Tech Spec | Task | Implementation details |
| Subtask | Sub-task | Granular work items |

### Document Structure Indicators

**Epic-level indicators:**
- Contains "Objectives" or "Goals" section
- Describes multiple features
- References business value
- Has "Success Criteria" or "KPIs"

**Story-level indicators:**
- Contains "As a [user]" format
- Has "Acceptance Criteria" section
- Describes single user-facing feature
- Contains "Given/When/Then" scenarios

**Task-level indicators:**
- Contains technical implementation details
- References code, APIs, databases
- Has step-by-step implementation approach
- Contains time estimates or complexity notes

## Field Mapping Reference

### Summary (Jira) <- Title (BMAD)
- Max 80 characters recommended
- Start with action verb when possible
- Include scope identifier if needed

### Description (Jira) <- Content (BMAD)
- Convert to Atlassian Document Format or Markdown
- Preserve headers as h2/h3
- Include links back to source doc

### Acceptance Criteria (Jira) <- Acceptance Criteria (BMAD)
- Convert to checklist format
- Each criterion should be independently verifiable
- Include edge cases and error scenarios

### Labels (Jira) <- Tags/Categories (BMAD)
- Normalize to lowercase-hyphenated
- Include epic-name as label for discoverability

## Relationship Mapping

### Parent-Child
- PRD -> Epics (contains relationship)
- Epic -> Stories (parent relationship)
- Story -> Tasks (parent relationship)
- Task -> Sub-tasks (subtask relationship)

### Cross-References
- "depends on" -> blocks relationship
- "related to" -> relates relationship
- "implements" -> is implemented by relationship
- "tests" -> is tested by relationship
