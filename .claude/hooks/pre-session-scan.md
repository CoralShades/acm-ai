---
name: pre-session-scan
trigger: PreSession
description: Auto-refresh the skills registry at session start so prompt generation always has current data.
---

# Pre-Session Skills Scan

On every new Claude Code session:

1. Check if `skills-registry.json` exists at repo root
2. If missing OR last modified > 24 hours ago:
   - Run: `bash .claude/skills/skill-discovery/scripts/scan_registry.sh`
   - This updates `skills-registry.json` with current skills, commands, hooks
3. If exists and fresh (< 24 hours):
   - Skip scan, use cached registry
4. Report: "Skills registry: {N} skills, {M} commands, {K} hooks available"

This ensures `/generate-prompt` always has an up-to-date catalog without manual intervention.
