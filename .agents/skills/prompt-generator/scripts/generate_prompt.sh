#!/usr/bin/env bash
# generate_prompt.sh — Thin CLI wrapper for the prompt-generator skill
#
# Usage:
#   generate_prompt.sh "user request text" [OPTIONS]
#
# Options:
#   --save          Save generated prompt to docs/sprint-artifacts/prompt-packs/
#   --no-plan       Skip plan mode even if auto-detected
#   --with-plan     Force plan mode even if not auto-detected
#   --tmux          Force tmux agent team strategy
#   --format FORMAT Output format: terminal (default), copy-paste, prompt-pack
#
# This is a THIN WRAPPER. Actual prompt assembly is done by Claude Code reading
# the skill instructions in SKILL.md. This script:
#   1. Validates prerequisites (registry, request text)
#   2. Parses flags
#   3. Outputs a Claude Code invocation message with the right skill + options
#
# Examples:
#   ./generate_prompt.sh "Fix the building sidebar crash"
#   ./generate_prompt.sh "Add MinerU provider" --save --tmux
#   ./generate_prompt.sh "Refactor pre-extraction stages" --format prompt-pack

set -euo pipefail

# ── Constants ──────────────────────────────────────────────────────────────────
REPO_ROOT="${CLAUDE_PROJECT_DIR:-D:/ailocal/acm-ai}"
REGISTRY="$REPO_ROOT/skills-registry.json"
DISCOVERY_SCRIPT="$REPO_ROOT/.claude/skills/skill-discovery/scripts/scan_registry.sh"
OUTPUT_DIR="$REPO_ROOT/docs/sprint-artifacts/prompt-packs"
DATE=$(date +%Y-%m-%d)

# ── Colors ────────────────────────────────────────────────────────────────────
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

# ── Help ──────────────────────────────────────────────────────────────────────
show_help() {
  cat <<EOF
${BOLD}generate_prompt.sh${RESET} — Generate an optimized Claude Code session prompt

${BOLD}Usage:${RESET}
  generate_prompt.sh "request text" [OPTIONS]

${BOLD}Options:${RESET}
  --save            Save prompt to docs/sprint-artifacts/prompt-packs/
  --no-plan         Skip plan mode even if auto-detected
  --with-plan       Force plan mode
  --tmux            Force tmux agent team strategy
  --format FORMAT   Output: terminal (default) | copy-paste | prompt-pack
  -h, --help        Show this help

${BOLD}Examples:${RESET}
  generate_prompt.sh "Fix extraction pipeline timeout"
  generate_prompt.sh "Add MinerU v2 provider" --save --tmux
  generate_prompt.sh "Refactor pre-extraction stages" --format prompt-pack

${BOLD}What happens:${RESET}
  1. Checks skills-registry.json (refreshes if missing or >1 hour old)
  2. Classifies your request via /request-classifier
  3. Routes to optimal skills + strategy via /prompt-router
  4. Generates a complete prompt with glossary and verification checklist
  5. If plan mode: scaffolds task_plan.md, findings.md, progress.md
EOF
}

# ── Argument parsing ──────────────────────────────────────────────────────────
REQUEST=""
FLAG_SAVE=false
FLAG_NO_PLAN=false
FLAG_WITH_PLAN=false
FLAG_TMUX=false
FORMAT="terminal"

if [[ $# -eq 0 ]] || [[ "$1" == "-h" ]] || [[ "$1" == "--help" ]]; then
  show_help
  exit 0
fi

# First positional argument is the request
REQUEST="$1"
shift

# Parse remaining flags
while [[ $# -gt 0 ]]; do
  case "$1" in
    --save)
      FLAG_SAVE=true
      shift
      ;;
    --no-plan)
      FLAG_NO_PLAN=true
      shift
      ;;
    --with-plan)
      FLAG_WITH_PLAN=true
      shift
      ;;
    --tmux)
      FLAG_TMUX=true
      shift
      ;;
    --format)
      if [[ -z "${2:-}" ]]; then
        echo -e "${RED}ERROR: --format requires a value (terminal|copy-paste|prompt-pack)${RESET}" >&2
        exit 1
      fi
      FORMAT="$2"
      shift 2
      ;;
    --format=*)
      FORMAT="${1#--format=}"
      shift
      ;;
    -h|--help)
      show_help
      exit 0
      ;;
    *)
      echo -e "${YELLOW}WARNING: Unknown flag '$1' — ignoring${RESET}" >&2
      shift
      ;;
  esac
done

# ── Validate format ────────────────────────────────────────────────────────────
case "$FORMAT" in
  terminal|copy-paste|prompt-pack)
    ;;
  *)
    echo -e "${RED}ERROR: Invalid format '$FORMAT'. Must be: terminal, copy-paste, or prompt-pack${RESET}" >&2
    exit 1
    ;;
esac

# ── Validate request ──────────────────────────────────────────────────────────
if [[ -z "$REQUEST" ]]; then
  echo -e "${RED}ERROR: Request text is required.${RESET}" >&2
  echo ""
  show_help
  exit 1
fi

# ── Check/refresh registry ────────────────────────────────────────────────────
REGISTRY_OK=false

if [[ -f "$REGISTRY" ]]; then
  # Check age — works on Linux (stat -c) and macOS (stat -f)
  MTIME=$(stat -c "%Y" "$REGISTRY" 2>/dev/null || stat -f "%m" "$REGISTRY" 2>/dev/null || echo "0")
  NOW=$(date +%s)
  AGE=$((NOW - MTIME))

  if [[ $AGE -lt 3600 ]]; then
    REGISTRY_OK=true
    echo -e "${GREEN}Registry: current (${AGE}s old)${RESET}"
  else
    echo -e "${YELLOW}Registry: stale ($((AGE / 60)) min old) — refreshing...${RESET}"
  fi
else
  echo -e "${YELLOW}Registry: missing — running skill-discovery...${RESET}"
fi

if [[ "$REGISTRY_OK" == false ]]; then
  if [[ -f "$DISCOVERY_SCRIPT" ]]; then
    bash "$DISCOVERY_SCRIPT"
    if [[ -f "$REGISTRY" ]]; then
      echo -e "${GREEN}Registry: refreshed successfully${RESET}"
    else
      echo -e "${YELLOW}WARNING: Discovery ran but registry not found at $REGISTRY${RESET}" >&2
      echo -e "${YELLOW}Continuing without registry — skill selection may be incomplete${RESET}" >&2
    fi
  else
    echo -e "${YELLOW}WARNING: Discovery script not found at $DISCOVERY_SCRIPT${RESET}" >&2
    echo -e "${YELLOW}Continuing without registry refresh${RESET}" >&2
  fi
fi

# ── Build flags summary ───────────────────────────────────────────────────────
FLAGS_SUMMARY=""
[[ "$FLAG_SAVE" == true ]] && FLAGS_SUMMARY+=" --save"
[[ "$FLAG_NO_PLAN" == true ]] && FLAGS_SUMMARY+=" --no-plan"
[[ "$FLAG_WITH_PLAN" == true ]] && FLAGS_SUMMARY+=" --with-plan"
[[ "$FLAG_TMUX" == true ]] && FLAGS_SUMMARY+=" --tmux"
[[ "$FORMAT" != "terminal" ]] && FLAGS_SUMMARY+=" --format $FORMAT"
FLAGS_SUMMARY="${FLAGS_SUMMARY# }"  # trim leading space

# ── Determine output path ─────────────────────────────────────────────────────
if [[ "$FLAG_SAVE" == true ]] || [[ "$FORMAT" == "prompt-pack" ]]; then
  # Generate slug from request: lowercase, replace spaces/special chars with hyphens
  SLUG=$(echo "$REQUEST" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-\|-$//g' | cut -c1-60)
  OUTPUT_FILE="$OUTPUT_DIR/${DATE}-${SLUG}.md"
  mkdir -p "$OUTPUT_DIR"
  echo -e "${CYAN}Output file: $OUTPUT_FILE${RESET}"
fi

# ── Print Claude Code invocation message ──────────────────────────────────────
echo ""
echo -e "${BOLD}══════════════════════════════════════════════════════${RESET}"
echo -e "${BOLD}  PROMPT GENERATOR — Claude Code Invocation${RESET}"
echo -e "${BOLD}══════════════════════════════════════════════════════${RESET}"
echo ""
echo -e "${CYAN}Request:${RESET} $REQUEST"
[[ -n "$FLAGS_SUMMARY" ]] && echo -e "${CYAN}Flags:${RESET}   $FLAGS_SUMMARY"
echo -e "${CYAN}Format:${RESET}  $FORMAT"
echo ""
echo -e "${BOLD}Skills to load in Claude Code session:${RESET}"
echo "  /skill-discovery     (if registry is stale)"
echo "  /request-classifier  (classify the request)"
echo "  /prompt-router       (select skills + strategy)"
echo "  /prompt-generator    (generate the prompt)"
echo ""
echo -e "${BOLD}Paste this into Claude Code to generate your prompt:${RESET}"
echo ""

# Build the paste-ready invocation
INVOCATION="/generate-prompt \"$REQUEST\""
[[ "$FLAG_SAVE" == true ]] && INVOCATION+=" --save"
[[ "$FLAG_NO_PLAN" == true ]] && INVOCATION+=" --no-plan"
[[ "$FLAG_WITH_PLAN" == true ]] && INVOCATION+=" --with-plan"
[[ "$FLAG_TMUX" == true ]] && INVOCATION+=" --tmux"
[[ "$FORMAT" != "terminal" ]] && INVOCATION+=" --format $FORMAT"

echo "  $INVOCATION"
echo ""

# ── Hint for --save mode ──────────────────────────────────────────────────────
if [[ "$FLAG_SAVE" == true ]] || [[ "$FORMAT" == "prompt-pack" ]]; then
  echo -e "${BOLD}Expected output location:${RESET}"
  echo "  $OUTPUT_DIR/${DATE}-<generated-slug>.md"
  echo ""
fi

# ── Strategy hint based on flags ─────────────────────────────────────────────
echo -e "${BOLD}Strategy hints:${RESET}"

if [[ "$FLAG_TMUX" == true ]]; then
  echo "  Agent strategy: TMUX-TEAM (forced via --tmux)"
elif echo "$REQUEST" | grep -qiE "pipeline|graph|extraction|langgraph|node|provider"; then
  echo "  Agent strategy: TMUX-TEAM (detected pipeline/graph domain)"
elif echo "$REQUEST" | grep -qiE "add|implement|create|new feature|build"; then
  echo "  Agent strategy: SUBAGENT-DISPATCH or TMUX-TEAM (feature + complexity)"
else
  echo "  Agent strategy: SOLO (auto-detected; override with --tmux)"
fi

if [[ "$FLAG_NO_PLAN" == true ]]; then
  echo "  Plan mode: OFF (forced via --no-plan)"
elif [[ "$FLAG_WITH_PLAN" == true ]]; then
  echo "  Plan mode: ON (forced via --with-plan)"
else
  echo "  Plan mode: AUTO (determined by request-classifier)"
fi

echo ""
echo -e "${BOLD}══════════════════════════════════════════════════════${RESET}"
echo ""
echo -e "${GREEN}Ready. Paste the /generate-prompt command into Claude Code.${RESET}"
echo -e "${GREEN}Claude Code will run the full 5-phase pipeline and produce your prompt.${RESET}"
