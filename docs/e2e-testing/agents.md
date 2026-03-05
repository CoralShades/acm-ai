# Agent Reference

Two agents and several skills support E2E testing workflows for ACM-AI.

## acm-e2e-tester (Full-Stack E2E)

**Model**: sonnet | **Max turns**: 40

**Tools**: Read, Glob, Grep, Write, Edit, Bash, WebFetch, Task

### Test Workflows

1. **PDF Upload -> Extraction -> Grid Verification**
   - Navigate to sources, upload PDF, configure settings
   - Wait for extraction to complete
   - Navigate to ACM register, verify records in AG Grid
   - Check record count, building navigation, field population

2. **BAR Export Verification**
   - Navigate to extracted data
   - Trigger CSV export (verify 47+ columns)
   - Trigger Excel export (verify BAR template compliance)
   - Check field mapping and building grouping

3. **API Integration Testing**
   - `POST /api/acm/extract` - Submit PDF
   - `GET /api/acm/records/{source_id}` - Verify records
   - `GET /api/acm/summary/{source_id}` - Verify stats
   - `POST /api/chat` - ACM-context query
   - `GET /api/search?q=asbestos` - Search verification

4. **Chat with ACM Context**
   - Navigate to chat, enable ACM context
   - Ask building-specific questions
   - Verify ACM record citations in response

### Key URLs

| Page | URL |
|------|-----|
| Dashboard | http://localhost:8503 |
| Sources | http://localhost:8503/sources |
| ACM Spreadsheet | http://localhost:8503/acm |
| Documents | http://localhost:8503/documents |
| Search | http://localhost:8503/search |
| Settings | http://localhost:8503/settings |

### Test Data Locations

| Data | Path |
|------|------|
| Sample PDFs | `docs/samplePDF/` |
| Expected output | `tests/fixtures/acm_extraction/expected_output.json` |
| Sample input | `tests/fixtures/acm_extraction/sample_input.txt` |
| Test data factory | `tests/support/helpers/test-data-factory.ts` |

### Self-Healing Framework Paths

| Path | Purpose |
|------|---------|
| `tests/e2e/framework/self-healing/` | Framework modules |
| `tests/support/fixtures/self-healing.ts` | HealingPage fixture |
| `tests/e2e/specs/` | Tiered spec files |
| `test-results/evidence/` | Evidence output |
| `test-results/healing-report.json` | Healing report |

### Workflow

1. Run smoke tests first: `npx playwright test --project=smoke`
2. If smoke passes, run targeted tests based on changed files
3. On failure: check healing report for auto-fix recommendations
4. Apply fixes (add data-testid, update selectors) and re-run
5. Collect evidence on persistent failures

---

## acm-ui-tester (Frontend UI)

**Model**: sonnet | **Max turns**: 35

**Tools**: Read, Glob, Grep, Write, Edit, Bash, Task

### Test Domains

1. **Component Rendering** - Dashboard components, AG Grid columns, form components, modals, sidebar navigation
2. **Form Testing** - Upload wizard, site config, settings forms, add source dialog
3. **AG Grid** - Sorting, filtering, row grouping, risk color coding, cell click, search, column visibility
4. **Responsive** - Sidebar collapse, grid adaptation, dialog centering, touch interactions
5. **Accessibility** - Keyboard navigation, focus management, ARIA labels, color contrast, screen reader compatibility

### Page Routes to Test

| Route | Key Elements |
|-------|-------------|
| `/` | BentoGrid, RecentSourcesList, RiskChart |
| `/acm` | ACMGrid, ACMToolbar, BuildingTabs, ACMStatsCards |
| `/sources` | SourcesGridView/TableView, AddSourceButton |
| `/sources/[id]` | SourceDetailContent, ChatPanel, SourceInsightsPanel |
| `/documents` | DocumentLibrary, BulkActions, ViewToggle |
| `/notebooks` | NotebookList, NotebookCard |
| `/search` | StreamingResponse, SaveToNotebooksDialog |
| `/settings` | SettingsForm |
| `/models` | AddModelForm, ModelTypeSection |

### Browser Automation Tools

- **Playwright**: navigate, snapshot, click, fill, screenshot, wait, press, resize
- **Agent-browser**: Interactive debugging sessions
- **Chrome DevTools**: DOM inspection via `browser_snapshot`

---

## Skills

### e2e-test

Self-healing E2E testing workflow. Trigger via `/e2e-test` or invoke the skill programmatically.

**Phases:**
1. Parallel research (analyze changed files, identify affected routes)
2. Test selection (choose tier based on change scope)
3. Execute with healing (selector fallback + state recovery)
4. Evidence collection (screenshots, logs, network traces)
5. Auto-fix (up to 3 attempts: analyze failure, apply fix, re-run)
6. Report (generate healing report with recommendations)

### agent-browser

Browser CLI for interactive debugging. See [Agent-Browser Patterns](agent-browser.md).

**Core workflow**: `open` -> `snapshot -i` -> interact with `@refs` -> re-snapshot

### Other Relevant Skills

| Skill | Use For |
|-------|---------|
| `webapp-testing` | General Playwright webapp verification |
| `playwright-skill` | Browser automation scripting |
| `dogfood` | Systematic app exploration for bugs/UX issues |

---

## When to Use Which

| Scenario | Use |
|----------|-----|
| Full-stack flow (upload -> extraction -> grid -> export) | `acm-e2e-tester` agent |
| Component-level UI checks (rendering, forms, responsive) | `acm-ui-tester` agent |
| Autonomous test execution with self-healing | `e2e-test` skill |
| Interactive debugging during failures | `agent-browser` skill |
| Quick API contract check | `apiValidator` fixture directly |
| Visual regression comparison | `agent-browser diff screenshot` |
