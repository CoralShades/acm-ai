# E2E Tests: Modular Rules

Test checklist for verifying modular rules apply correctly.

## Prerequisites

- [ ] Claude Code CLI installed
- [ ] `.claude/rules/` directory exists
- [ ] Rules have valid YAML frontmatter with `paths:` pattern

## Test: Rule Discovery

### Steps
1. Check `.claude/rules/` contains rule files
2. Verify each rule has valid YAML frontmatter
3. Run Claude and work with matching files

### Expected
- Rules are loaded on Claude start
- No syntax errors
- Rules only apply to matching paths

### Result
- [ ] PASS
- [ ] FAIL (note reason):

---

## Test: Path Pattern Matching

### Steps
1. Create rule with specific path pattern:
   ```yaml
   paths:
     - "src/**/*.ts"
   ```
2. Ask Claude to edit a file matching the pattern
3. Ask Claude to edit a file NOT matching the pattern

### Expected
- Rule context shown for matching files
- Rule NOT applied to non-matching files
- Glob patterns work correctly

### Result
- [ ] PASS
- [ ] FAIL (note reason):

---

## Test: Multiple Path Patterns

### Steps
1. Create rule with multiple patterns:
   ```yaml
   paths:
     - "docker-compose*.yml"
     - "docker-compose*.yaml"
   ```
2. Test with files matching different patterns

### Expected
- Rule applies to all matching patterns
- Both `.yml` and `.yaml` work
- Wildcards behave correctly

### Result
- [ ] PASS
- [ ] FAIL (note reason):

---

## Test: Rule Content Application

### Steps
1. Create rule with specific guidance
2. Ask Claude to create/edit file matching pattern
3. Observe if Claude follows rule guidance

### Expected
- Claude follows rule conventions
- Rules influence code style
- Best practices applied

### Result
- [ ] PASS
- [ ] FAIL (note reason):

---

## Test: Multiple Rules

### Steps
1. Create multiple rules for different paths
2. Work with files matching different rules
3. Work with file matching no rules

### Expected
- Correct rule applies per file
- No rule conflicts
- Graceful fallback when no rule matches

### Result
- [ ] PASS
- [ ] FAIL (note reason):

---

## Test: Overlapping Paths

### Steps
1. Create rules with overlapping patterns:
   - `src/**/*` (general)
   - `src/api/**/*` (specific)
2. Edit file in `src/api/`

### Expected
- More specific rule takes precedence
- Or both rules apply (document behavior)
- No errors

### Result
- [ ] PASS
- [ ] FAIL (note reason):

---

## Test: Invalid Rule Syntax

### Steps
1. Create rule with invalid YAML frontmatter
2. Start Claude Code
3. Observe behavior

### Expected
- Invalid rule is skipped
- Other rules still work
- Warning message shown

### Result
- [ ] PASS
- [ ] FAIL (note reason):

---

## Test: Rule Updates

### Steps
1. Modify an existing rule file
2. Test if changes take effect

### Expected
- Rules reload on change (or require restart)
- Document reload behavior
- New rules apply correctly

### Result
- [ ] PASS
- [ ] FAIL (note reason):

---

## Troubleshooting

### Rules not applying
1. Verify YAML frontmatter is valid
2. Check `paths:` uses correct glob syntax
3. Ensure file path matches pattern
4. Restart Claude Code

### Glob patterns not matching
Common patterns:
- `**/*.ts` - All .ts files recursively
- `src/**/*` - All files under src/
- `*.md` - .md files in current directory only
- `**/test/**/*.ts` - All .ts in any test/ directory

### Rule conflicts
1. Use more specific path patterns
2. Consolidate overlapping rules
3. Document precedence rules

---

## Test Summary

| Test | Status |
|------|--------|
| Rule Discovery | |
| Path Pattern Matching | |
| Multiple Path Patterns | |
| Rule Content Application | |
| Multiple Rules | |
| Overlapping Paths | |
| Invalid Rule Syntax | |
| Rule Updates | |

**Overall Result**: [ ] PASS / [ ] FAIL

**Tester**: _______________
**Date**: _______________
