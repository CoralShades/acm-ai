# JBM: Jira Bridge Module

Bridge BMAD methodology artifacts with Jira project management.

## Overview

Jira Bridge is an Expert Agent that translates BMAD documents (PRDs, Epics, Stories, Tech Specs) into structured Jira work items. It maintains persistent memory of project mappings and learns project-specific conventions over time.

## Installation

1. Run the BMAD installer: `npx bmad-method@alpha install`
2. Select "Install a local custom module"
3. Provide path to this folder

## Prerequisites

- **Atlassian MCP** must be configured in your Claude Code settings for Jira API access
- Access to target Jira project(s)

## Agent: Jira Bridge

| Property | Value |
|----------|-------|
| **Type** | Expert Agent (with sidecar memory) |
| **Commands** | 17 (Creation, Mapping, Management, Reporting) |
| **Personality** | Analytical forensic investigator |
| **Memory** | Persistent project mappings |

### Commands

**Creation:** `create-epic`, `create-story`, `create-task`, `create-from-doc`
**Mapping:** `map-project`, `sync-status`, `link-issues`, `update-from-doc`
**Management:** `edit-issue`, `comment`, `transition`, `bulk-update`
**Reporting:** `status-report`, `find-issues`, `show-hierarchy`, `coverage-check`

## File Structure

```
jira-bridge-module/
├── module.yaml
├── README.md
├── agents/
│   └── jira-bridge/
│       ├── jira-bridge.agent.yaml
│       └── jira-bridge-sidecar/
│           ├── memories.md
│           ├── instructions.md
│           └── knowledge/
│               ├── project-mappings.md
│               ├── field-conventions.md
│               └── issue-cache.md
└── workflows/
```
