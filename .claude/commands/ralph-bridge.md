Generate `prd.json` from BMAD V3 planning artifacts.

This command reads the V3 epic/story definitions and sprint plan, then outputs a machine-readable `prd.json` at the project root containing all 33 stories with dependency graph and 4 gate nodes.

## Steps

### 1. Read Source Artifacts

Read these files to extract story definitions:
- `_bmad-output/project-planning-artifacts/acm-ai/05-epics-and-stories.md` — All story definitions
- `_bmad-output/project-planning-artifacts/acm-ai/04-architecture.md` — Architecture context
- `docs/sprint-artifacts/v3-sprint-plan.md` — Sprint assignments and schedule
- `docs/sprint-artifacts/sprint-status.yaml` — Current story status (if any already done)

### 2. Build Story Objects

For each of the 33 V3 stories (E30-S1 through E34-S4), create a JSON object:

```json
{
  "id": "E30-S1",
  "title": "Salesforce Schema Config Loader",
  "epic": "E30",
  "sprint": "V3-1",
  "storyPoints": 5,
  "riskLevel": "HIGH|MEDIUM|LOW",
  "storyType": "backend|frontend|both",
  "acceptanceCriteria": ["AC1: ...", "AC2: ..."],
  "passes": false,
  "notes": "",
  "model": "sonnet",
  "complexity": "complex|moderate|simple",
  "priority": "P0|P1|P2",
  "dependencies": [],
  "keyFiles": ["open_notebook/extractors/parsers/config_loader.py"],
  "techSpecFile": null,
  "implementedDate": null
}
```

### 3. Apply Dependency Map

Use this exact dependency graph for all 33 stories:

**E30 — Foundation:**
- E30-S1: `[]` (no deps — entry point)
- E30-S2: `["E30-S1"]`
- E30-S3: `["E30-S1"]`
- E30-S4: `["E30-S1"]`
- E30-S5: `["E30-S2", "E30-S3"]`
- E30-S6: `["E30-S3"]`
- E30-S7: `["GATE:SCHEMA_FREEZE", "E31-S2"]`
- E30-S8: `["E30-S1"]`

**E31 — Extraction:**
- E31-S1: `["GATE:SCHEMA_FREEZE"]`
- E31-S2: `["E31-S1"]`
- E31-S3: `["E31-S2"]`
- E31-S4: `["E31-S2"]`
- E31-S5: `["E31-S3", "E31-S4"]`
- E31-S6: `["E31-S5"]`
- E31-S7: `["E31-S5"]`

**E32 — AI Processing:**
- E32-S1: `["E31-S5", "E30-S7"]`
- E32-S2: `["E32-S1"]`
- E32-S3: `["E32-S2", "E30-S4"]`
- E32-S4: `["E30-S6"]`
- E32-S5: `["E32-S1", "E32-S2", "E32-S3", "E32-S4"]`
- E32-S6: `["E30-S8"]`

**E33 — Frontend:**
- E33-S1: `["GATE:SCHEMA_FREEZE", "E31-S7"]`
- E33-S2: `["GATE:SCHEMA_FREEZE", "E30-S2"]`
- E33-S3: `["GATE:AI_COMPLETE", "E30-S4"]`
- E33-S4: `["E33-S2", "E33-S3", "E30-S4"]`
- E33-S5: `["E31-S4", "E33-S2"]`
- E33-S6: `["E31-S4", "E33-S2"]`
- E33-S7: `["E30-S2", "E33-S2"]`
- E33-S8: `["E30-S2", "E30-S3", "E33-S4"]`

**E34 — Integration:**
- E34-S1: `["E31-S7", "E33-S2"]`
- E34-S2: `["E33-S2", "E33-S4", "E31-S7"]`
- E34-S3: `["E31-S5", "E32-S5"]`
- E34-S4: `["GATE:UI_COMPLETE"]`

### 4. Apply Risk & Complexity

HIGH risk stories (need architect guidance):
- E30-S1 (first V3 story, defines patterns), E30-S2 (building model, FK design), E30-S4 (36 combos + 114 mappings)
- E31-S3 (consensus layer core), E32-S3 (AI correction loop), E33-S2 (two-view AG Grid)

### 5. Apply Story Types

- `backend`: E30-S1, S3, S4, S5, S6, S7, S8, E31-S1..S7, E32-S1..S6
- `frontend`: E33-S1..S8
- `both`: E30-S2 (building model + API + frontend list), E34-S1..S4

### 6. Build Gates Array

```json
{
  "gates": [
    {
      "id": "GATE:SCHEMA_FREEZE",
      "name": "Schema Freeze",
      "triggerStory": "E30-S6",
      "unlocked": false,
      "blocksEpics": ["E31", "E32", "E33", "E34"],
      "description": "All SF schema definitions finalized. BAR->SF vocabulary locked."
    },
    {
      "id": "GATE:EXTRACTION_COMPLETE",
      "name": "Extraction Complete",
      "triggerStory": "E31-S6",
      "unlocked": false,
      "blocksEpics": [],
      "description": "Multi-provider extraction pipeline operational with consensus layer."
    },
    {
      "id": "GATE:AI_COMPLETE",
      "name": "AI Complete",
      "triggerStory": "E32-S5",
      "unlocked": false,
      "blocksEpics": [],
      "description": "AI validation, correction, and batching pipeline operational."
    },
    {
      "id": "GATE:UI_COMPLETE",
      "name": "UI Complete",
      "triggerStory": "E33-S8",
      "unlocked": false,
      "blocksEpics": [],
      "description": "All frontend views operational with AG Grid, provenance UI, and dashboards."
    }
  ]
}
```

### 7. Write prd.json

Write the complete JSON to `prd.json` at the project root with this top-level structure:

```json
{
  "version": "3.0",
  "project": "ACM-AI V3",
  "generatedAt": "<ISO timestamp>",
  "totalStories": 33,
  "totalStoryPoints": 97,
  "sprints": 7,
  "stories": [ ... ],
  "gates": [ ... ],
  "metadata": {
    "source": "ralph-bridge",
    "artifacts": [
      "05-epics-and-stories.md",
      "04-architecture.md",
      "v3-sprint-plan.md"
    ]
  }
}
```

### 8. Validate

After writing, verify:
- Exactly 33 stories in the `stories` array
- Exactly 4 gates in the `gates` array
- E30-S1 has `dependencies: []`
- All gate IDs referenced in story dependencies exist in `gates` array
- No circular dependencies
- All story IDs are unique
- Sprint assignments cover all stories

Report the result: total stories, total SP, gates, and first eligible story (should be E30-S1).
