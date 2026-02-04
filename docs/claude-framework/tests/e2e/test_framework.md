# E2E Tests: Framework Integration

Test checklist for verifying the full Claude Code framework works when copied to a new project.

## Prerequisites

- [ ] Claude Code CLI installed
- [ ] Target project directory available
- [ ] Python 3.x installed (for scripts)
- [ ] Framework directory accessible

## Test: Project Detection

### Steps
1. Navigate to target project
2. Run: `python docs/claude-framework/scripts/detect-project.py`
3. Review output

### Expected
- Detects existing documentation
- Identifies technology stack
- Provides recommendations
- JSON output option works

### Result
- [ ] PASS
- [ ] FAIL (note reason):

---

## Test: New Project Initialization

### Steps
1. Create empty directory
2. Run: `python docs/claude-framework/scripts/init-claude-code.py /path/to/new --new`
3. Verify created structure

### Expected
- `.claude/` directory created
- `commands/` populated
- `rules/` populated
- `settings.json` created
- `CLAUDE.md` created

### Result
- [ ] PASS
- [ ] FAIL (note reason):

---

## Test: Existing Project Integration

### Steps
1. Use project with existing CLAUDE.md
2. Run: `python docs/claude-framework/scripts/init-claude-code.py /path/to/existing --existing`
3. Verify integration

### Expected
- Existing CLAUDE.md preserved
- Missing components added
- No overwrites without `--force`
- Clean merge

### Result
- [ ] PASS
- [ ] FAIL (note reason):

---

## Test: Framework Sync

### Steps
1. Initialize project with framework
2. Update framework templates
3. Run: `python docs/claude-framework/scripts/sync-framework.py /path/to/project`

### Expected
- New templates added
- Existing files preserved
- Settings merged (not replaced)
- Dry-run works

### Result
- [ ] PASS
- [ ] FAIL (note reason):

---

## Test: CLAUDE.md Template

### Steps
1. Copy CLAUDE_TEMPLATE.md to new project
2. Customize project sections
3. Run Claude Code

### Expected
- Template has all required sections
- Placeholders are clear
- Claude reads context correctly
- References work

### Result
- [ ] PASS
- [ ] FAIL (note reason):

---

## Test: Copy Framework to New Project

### Steps
1. Copy entire `docs/claude-framework/` to new project
2. Run init script
3. Verify full functionality

### Expected
- Framework is self-contained
- Scripts find templates
- All paths relative
- Works from any location

### Result
- [ ] PASS
- [ ] FAIL (note reason):

---

## Test: Different Project Types

### Test with Node.js Project
- [ ] package.json detected
- [ ] Framework/test framework detected
- [ ] Appropriate rules suggested

### Test with Python Project
- [ ] pyproject.toml detected
- [ ] Framework detected
- [ ] Appropriate rules suggested

### Test with Docker Project
- [ ] docker-compose detected
- [ ] Docker rules added
- [ ] Commands work

### Result
- [ ] PASS
- [ ] FAIL (note reason):

---

## Test: BMAD Architecture Detection

### Steps
1. Use project with BMAD v6 structure
2. Run detection
3. Verify integration

### Expected
- Detects `docs/architecture/`
- Detects `docs/adr/`
- Recommends minimal strategy
- Preserves existing docs

### Result
- [ ] PASS
- [ ] FAIL (note reason):
- [ ] SKIP (no BMAD project available)

---

## Test: Full E2E Flow

### Steps
1. Start with empty directory
2. Run detect (should show no setup)
3. Run init
4. Start Claude Code
5. Test /status command
6. Edit file matching rule
7. Verify rule applies
8. Test MCP servers

### Expected
- Complete workflow succeeds
- All components work together
- No errors

### Result
- [ ] PASS
- [ ] FAIL (note reason):

---

## Troubleshooting

### Scripts fail to run
1. Check Python version
2. Verify script has execute permission
3. Check relative paths

### Templates not found
1. Ensure framework directory complete
2. Check script `get_framework_dir()` returns correct path
3. Verify `templates/` structure

### Integration conflicts
1. Use `--dry-run` first
2. Check for file permission issues
3. Review merge logic

---

## Test Summary

| Test | Status |
|------|--------|
| Project Detection | |
| New Project Initialization | |
| Existing Project Integration | |
| Framework Sync | |
| CLAUDE.md Template | |
| Copy to New Project | |
| Different Project Types | |
| BMAD Architecture Detection | |
| Full E2E Flow | |

**Overall Result**: [ ] PASS / [ ] FAIL

**Tester**: _______________
**Date**: _______________

---

## Notes

<!-- Add any observations or issues found during testing -->
