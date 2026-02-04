# E2E Tests: Custom Commands

Test checklist for verifying custom slash commands work correctly.

## Prerequisites

- [ ] Claude Code CLI installed (`claude --version`)
- [ ] Project has `.claude/commands/` directory
- [ ] Commands have valid YAML frontmatter

## Test: Command Discovery

### Steps
1. Run `claude` in project directory
2. Type `/` to see available commands
3. Verify custom commands appear in list

### Expected
- All commands from `.claude/commands/` appear
- Commands show description from frontmatter

### Result
- [ ] PASS
- [ ] FAIL (note reason):

---

## Test: /start Command

### Steps
1. Run `/start` command
2. Observe output

### Expected
- Command executes without errors
- Services start as expected
- Status is reported

### Result
- [ ] PASS
- [ ] FAIL (note reason):

---

## Test: /stop Command

### Steps
1. Run `/stop` command
2. Observe output

### Expected
- Command executes without errors
- Services stop gracefully
- Confirmation is shown

### Result
- [ ] PASS
- [ ] FAIL (note reason):

---

## Test: /status Command

### Steps
1. Run `/status` command
2. Observe output

### Expected
- Shows current service status
- Health checks execute
- Clear table output

### Result
- [ ] PASS
- [ ] FAIL (note reason):

---

## Test: /logs Command

### Steps
1. Run `/logs n8n` (or relevant service)
2. Observe output

### Expected
- Shows recent logs for service
- Logs stream if `-f` behavior
- Service argument works

### Result
- [ ] PASS
- [ ] FAIL (note reason):

---

## Test: Command Arguments

### Steps
1. Run command with argument: `/start gpu-nvidia`
2. Observe how argument is used

### Expected
- Argument is passed to instructions
- Command uses argument appropriately

### Result
- [ ] PASS
- [ ] FAIL (note reason):

---

## Test: Invalid Command

### Steps
1. Run non-existent command: `/nonexistent`
2. Observe behavior

### Expected
- Graceful error handling
- Suggests available commands

### Result
- [ ] PASS
- [ ] FAIL (note reason):

---

## Troubleshooting

### Commands not appearing
1. Check YAML frontmatter syntax
2. Verify file is `.md` extension
3. Restart Claude Code session

### Command fails to execute
1. Check `allowed-tools` in frontmatter
2. Verify bash commands in instructions
3. Check file permissions

### Argument not passed
1. Check `argument-hint` in frontmatter
2. Verify `$1` usage in instructions

---

## Test Summary

| Test | Status |
|------|--------|
| Command Discovery | |
| /start Command | |
| /stop Command | |
| /status Command | |
| /logs Command | |
| Command Arguments | |
| Invalid Command | |

**Overall Result**: [ ] PASS / [ ] FAIL

**Tester**: _______________
**Date**: _______________
