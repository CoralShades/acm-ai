#!/usr/bin/env bash
# scan_registry.sh — Scan and catalog all AI capabilities in the ACM-AI project
# Outputs: skills-registry.json at repo root
#
# POSIX-compatible bash. Dependencies: bash, sed, awk, grep, python3 (for JSON)
# Usage: bash .claude/skills/skill-discovery/scripts/scan_registry.sh

set -euo pipefail

# ---------------------------------------------------------------------------
# Resolve repo root
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
OUTPUT_FILE="$REPO_ROOT/skills-registry.json"

TMPDIR_SCAN="$(mktemp -d)"
trap 'rm -rf "$TMPDIR_SCAN"' EXIT

echo "[skill-discovery] Scanning repo: $REPO_ROOT" >&2

# ---------------------------------------------------------------------------
# Helper: extract one YAML frontmatter field from a SKILL.md file
# ---------------------------------------------------------------------------
extract_fm() {
    local file="$1"
    local field="$2"
    awk -v f="$field" '
        /^---$/ { fm++; next }
        fm == 1 {
            line = $0
            key = f ": "
            if (index(line, key) == 1) {
                val = substr(line, length(key) + 1)
                # strip surrounding double or single quotes
                gsub(/^"/, "", val); gsub(/"$/, "", val)
                gsub(/^'"'"'/, "", val); gsub(/'"'"'$/, "", val)
                print val
                exit
            }
        }
        fm >= 2 { exit }
    ' "$file"
}

# ---------------------------------------------------------------------------
# 1. Scan skills directories
# ---------------------------------------------------------------------------
SKILLS_TSV="$TMPDIR_SCAN/skills.tsv"
> "$SKILLS_TSV"

CLAUDE_SKILLS="$REPO_ROOT/.claude/skills"
AGENTS_SKILLS="$REPO_ROOT/.agents/skills"

scan_skill_dir() {
    local base_dir="$1"
    local platform_tag="$2"

    [ -d "$base_dir" ] || return 0

    for skill_dir in "$base_dir"/*/; do
        # Remove trailing slash for clean path construction
        skill_dir="${skill_dir%/}"
        local skill_md="$skill_dir/SKILL.md"
        [ -f "$skill_md" ] || continue

        local name desc scr_flag ref_flag rel_loc
        name="$(extract_fm "$skill_md" "name")"
        desc="$(extract_fm "$skill_md" "description")"
        [ -z "$name" ] && name="$(basename "$skill_dir")"

        # Make location relative to repo root (no leading slash)
        rel_loc="${skill_md#"$REPO_ROOT/"}"

        scr_flag="false"
        ref_flag="false"
        { [ -d "$skill_dir/scripts" ] && ls -A "$skill_dir/scripts" 2>/dev/null | grep -q .; } && scr_flag="true"
        { [ -d "$skill_dir/references" ] && ls -A "$skill_dir/references" 2>/dev/null | grep -q .; } && ref_flag="true"

        # Write TSV row: name|desc|location|has_scripts|has_references|platform
        printf '%s\t%s\t%s\t%s\t%s\t%s\n' \
            "$name" "$desc" "$rel_loc" "$scr_flag" "$ref_flag" "$platform_tag" \
            >> "$SKILLS_TSV"
    done
}

scan_skill_dir "$CLAUDE_SKILLS" "claude-code"
scan_skill_dir "$AGENTS_SKILLS" "agents"

# ---------------------------------------------------------------------------
# 2. Scan commands directory
# ---------------------------------------------------------------------------
COMMANDS_TSV="$TMPDIR_SCAN/commands.tsv"
> "$COMMANDS_TSV"

COMMANDS_DIR="$REPO_ROOT/commands"
if [ -d "$COMMANDS_DIR" ]; then
    for cmd_file in "$COMMANDS_DIR"/*.md; do
        [ -f "$cmd_file" ] || continue
        cmd_name="$(basename "$cmd_file" .md)"
        cmd_desc="$(extract_fm "$cmd_file" "description")"
        if [ -z "$cmd_desc" ]; then
            # First meaningful non-blank, non-header line after frontmatter
            cmd_desc="$(awk '
                BEGIN { fm=0 }
                /^---$/ { fm++; next }
                fm == 1 { next }
                /^[[:space:]]*$/ { next }
                /^#/ { next }
                { print; exit }
            ' "$cmd_file")"
        fi
        printf '%s\t%s\tcommands/%s.md\n' \
            "$cmd_name" "${cmd_desc:-No description}" "$cmd_name" \
            >> "$COMMANDS_TSV"
    done

    for cmd_file in "$COMMANDS_DIR"/*.py; do
        [ -f "$cmd_file" ] || continue
        cmd_name="$(basename "$cmd_file" .py)"
        # Skip __init__ and __pycache__
        case "$cmd_name" in __*) continue ;; esac
        # Extract first docstring line or first comment line
        cmd_desc="$(awk '
            NR == 1 && /^#!/ { next }
            /^"""/ { in_doc=1; next }
            in_doc && /"""/ { exit }
            in_doc { gsub(/^[[:space:]]+/, ""); print; exit }
            /^#[^!]/ && NR <= 5 { sub(/^#[[:space:]]*/, ""); print; exit }
        ' "$cmd_file" | head -1)"
        printf '%s\t%s\tcommands/%s.py\n' \
            "$cmd_name" "${cmd_desc:-Python command handler}" "$cmd_name" \
            >> "$COMMANDS_TSV"
    done
fi

# ---------------------------------------------------------------------------
# 3. Scan hooks
# ---------------------------------------------------------------------------
HOOKS_TSV="$TMPDIR_SCAN/hooks.tsv"
> "$HOOKS_TSV"

HOOKS_DIR="$REPO_ROOT/.claude/hooks"
if [ -d "$HOOKS_DIR" ]; then
    for hook_file in "$HOOKS_DIR"/*; do
        [ -f "$hook_file" ] || continue
        hook_name="$(basename "$hook_file")"
        case "$hook_name" in
            pre-tool-use*)   trigger="PreToolUse" ;;
            post-tool-use*)  trigger="PostToolUse" ;;
            pre-commit*)     trigger="PreCommit" ;;
            session-start*)  trigger="SessionStart" ;;
            ralph-gate-*)    trigger="RalphGate" ;;
            ralph-progress*) trigger="RalphProgress" ;;
            ralph-stop*)     trigger="RalphStop" ;;
            scope-guard*)    trigger="ScopeGuard" ;;
            story-done*)     trigger="StoryDone" ;;
            task-quality*)   trigger="TaskQualityGate" ;;
            auto-commit*)    trigger="PostCommit" ;;
            stop*)           trigger="Stop" ;;
            *)               trigger="Custom" ;;
        esac
        printf '%s\t%s\n' "$hook_name" "$trigger" >> "$HOOKS_TSV"
    done
fi

# ---------------------------------------------------------------------------
# 4. Extract CLAUDE.md section headers (## level)
# ---------------------------------------------------------------------------
RULES_TXT="$TMPDIR_SCAN/rules.txt"
> "$RULES_TXT"

CLAUDE_MD="$REPO_ROOT/CLAUDE.md"
if [ -f "$CLAUDE_MD" ]; then
    grep '^## ' "$CLAUDE_MD" | sed 's/^## //' > "$RULES_TXT"
fi

# ---------------------------------------------------------------------------
# 5. Generate JSON via Python
# ---------------------------------------------------------------------------
SCANNED_AT="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

echo "[skill-discovery] Generating JSON..." >&2

python3 - "$SKILLS_TSV" "$COMMANDS_TSV" "$HOOKS_TSV" "$RULES_TXT" "$SCANNED_AT" "$OUTPUT_FILE" <<'PYEOF'
import sys, json
from collections import OrderedDict

skills_tsv, commands_tsv, hooks_tsv, rules_txt, scanned_at, out_path = sys.argv[1:]

# ---- Skills ----
# TSV columns: name | description | location | has_scripts | has_references | platform_tag
skill_map = OrderedDict()  # ordered by first-seen

with open(skills_tsv, encoding='utf-8') as f:
    for line in f:
        line = line.rstrip('\n')
        if not line:
            continue
        parts = line.split('\t')
        if len(parts) < 6:
            continue
        name, desc, location, has_scripts, has_references, platform_tag = parts[:6]
        if name not in skill_map:
            skill_map[name] = {
                "name": name,
                "description": desc,
                "location": location,
                "has_scripts": has_scripts == "true",
                "has_references": has_references == "true",
                "platform": [platform_tag],
            }
        else:
            # Duplicate from second directory — track as also_at
            entry = skill_map[name]
            if platform_tag not in entry["platform"]:
                entry["platform"].append(platform_tag)
            if location != entry["location"]:
                entry.setdefault("also_at", [])
                if location not in entry["also_at"]:
                    entry["also_at"].append(location)
            if has_scripts == "true":
                entry["has_scripts"] = True
            if has_references == "true":
                entry["has_references"] = True

skills = sorted(skill_map.values(), key=lambda s: s["name"])

# ---- Commands ----
commands = []
with open(commands_tsv, encoding='utf-8') as f:
    for line in f:
        line = line.rstrip('\n')
        if not line:
            continue
        parts = line.split('\t')
        if len(parts) < 3:
            continue
        commands.append({
            "name": parts[0],
            "description": parts[1],
            "location": parts[2],
        })
commands.sort(key=lambda c: c["name"])

# ---- Hooks ----
hooks = []
with open(hooks_tsv, encoding='utf-8') as f:
    for line in f:
        line = line.rstrip('\n')
        if not line:
            continue
        parts = line.split('\t')
        if len(parts) < 2:
            continue
        hooks.append({"name": parts[0], "trigger": parts[1]})
hooks.sort(key=lambda h: h["name"])

# ---- Rules ----
rule_sections = []
with open(rules_txt, encoding='utf-8') as f:
    for line in f:
        s = line.strip()
        if s:
            rule_sections.append(s)

registry = {
    "version": "1.0",
    "scanned_at": scanned_at,
    "skills": skills,
    "commands": commands,
    "hooks": hooks,
    "rules": {
        "source": "CLAUDE.md",
        "sections": rule_sections,
    }
}

output = json.dumps(registry, indent=2, ensure_ascii=False)
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(output)
    f.write('\n')

print(f"[skill-discovery] Written: {out_path}", file=__import__('sys').stderr)
print(f"[skill-discovery] Skills: {len(skills)}, Commands: {len(commands)}, Hooks: {len(hooks)}", file=__import__('sys').stderr)
PYEOF

echo "[skill-discovery] Done. Registry at: $OUTPUT_FILE" >&2
