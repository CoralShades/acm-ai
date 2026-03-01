#!/bin/bash
# ACM-AI Session Start Hook
# New sessions only — registered with matcher: "startup" in .claude/settings.json
# Skipped automatically on: resume, /clear, compaction
#
# Cloud environments (CLAUDE_CODE_REMOTE, Codespaces, GitHub Actions, Vercel, CI):
#   - Installs Python deps via uv sync (or pip fallback)
#   - Installs frontend deps via npm install
#   - Starts SurrealDB via Docker if not already running
#   - Persists .env vars + SurrealDB defaults via CLAUDE_ENV_FILE
#
# All environments:
#   - Persists BMAD context env vars (BMAD_PROJECT_ROOT, BMAD_OUTPUT_FOLDER)
#   - Outputs project context banner with live sprint status

set -uo pipefail

# ─── Parse hook input ────────────────────────────────────────────────────────
INPUT=$(cat 2>/dev/null || echo '{}')

SESSION_ID="unknown"
CWD=""
if command -v jq &>/dev/null 2>&1; then
  SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // "unknown"' 2>/dev/null || echo "unknown")
  CWD=$(echo "$INPUT" | jq -r '.cwd // ""' 2>/dev/null || echo "")
fi

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-${CWD:-$(pwd)}}"

# ─── Environment Detection ───────────────────────────────────────────────────
detect_env() {
  if   [ "${CLAUDE_CODE_REMOTE:-}" = "true" ];                      then echo "claude-web";        return; fi
  if   [ -n "${CODESPACE_NAME:-}${GITHUB_CODESPACE_TOKEN:-}" ];     then echo "github-codespaces"; return; fi
  if   [ -n "${GITHUB_ACTIONS:-}" ];                                then echo "github-actions";     return; fi
  if   [ -n "${VERCEL:-}${VERCEL_ENV:-}" ];                         then echo "vercel";             return; fi
  if   [ -n "${CI:-}" ];                                            then echo "ci";                 return; fi
  echo "local"
}

ENV_TYPE=$(detect_env)
IS_CLOUD=false
[ "$ENV_TYPE" != "local" ] && IS_CLOUD=true

# ─── Cloud Dependency Setup ──────────────────────────────────────────────────
if [ "$IS_CLOUD" = "true" ]; then
  printf '[ACM-AI] Cloud environment: %s — running setup...\n' "$ENV_TYPE" >&2

  # Python: uv (preferred) or pip fallback
  if command -v uv &>/dev/null 2>&1 && [ -f "$PROJECT_DIR/pyproject.toml" ]; then
    printf '[ACM-AI] Installing Python deps (uv sync)...\n' >&2
    (cd "$PROJECT_DIR" && uv sync --quiet 2>&1 | tail -3 >&2) \
      || printf '[ACM-AI] uv sync failed (non-fatal)\n' >&2
  elif command -v pip &>/dev/null 2>&1 && [ -f "$PROJECT_DIR/requirements.txt" ]; then
    pip install -r "$PROJECT_DIR/requirements.txt" -q 2>/dev/null || true
  fi

  # Node.js frontend dependencies
  if command -v npm &>/dev/null 2>&1 && [ -f "$PROJECT_DIR/frontend/package.json" ]; then
    printf '[ACM-AI] Installing frontend deps (npm install)...\n' >&2
    (cd "$PROJECT_DIR/frontend" && npm install --silent 2>/dev/null) \
      || printf '[ACM-AI] npm install failed (non-fatal)\n' >&2
  fi

  # SurrealDB via Docker
  if command -v docker &>/dev/null 2>&1 && [ -f "$PROJECT_DIR/docker-compose.yml" ]; then
    if ! docker ps 2>/dev/null | grep -q surrealdb; then
      printf '[ACM-AI] Starting SurrealDB...\n' >&2
      (cd "$PROJECT_DIR" && docker compose up -d surrealdb 2>&1 | tail -2 >&2) \
        || printf '[ACM-AI] SurrealDB start failed (non-fatal)\n' >&2
      # Wait up to 15s for SurrealDB to be ready
      _ready=false
      for _i in 1 2 3 4 5; do
        sleep 3
        if curl -sf http://localhost:8000/health &>/dev/null 2>&1; then
          printf '[ACM-AI] SurrealDB ready\n' >&2
          _ready=true
          break
        fi
      done
      [ "$_ready" = "false" ] && printf '[ACM-AI] SurrealDB not ready after 15s (check docker logs)\n' >&2
    else
      printf '[ACM-AI] SurrealDB already running\n' >&2
    fi
  fi
fi

# ─── Persist Env Vars (CLAUDE_ENV_FILE: SessionStart-only feature) ───────────
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  # Load project .env (valid KEY=value lines only — skip comments/blanks)
  if [ -f "$PROJECT_DIR/.env" ]; then
    while IFS= read -r line; do
      [[ "$line" =~ ^[[:space:]]*# ]] && continue
      [[ -z "${line// }" ]] && continue
      [[ "$line" =~ ^[A-Z_][A-Z0-9_]*= ]] && printf 'export %s\n' "$line" >> "$CLAUDE_ENV_FILE"
    done < "$PROJECT_DIR/.env"
  fi

  # BMAD context vars (available to all tools in this session)
  {
    printf 'export BMAD_PROJECT_ROOT=%s\n'       "$PROJECT_DIR"
    printf 'export BMAD_OUTPUT_FOLDER=%s/_bmad-output\n' "$PROJECT_DIR"
    printf 'export BMAD_USER=Demi\n'
    printf 'export BMAD_LANGUAGE=English\n'
  } >> "$CLAUDE_ENV_FILE"

  # SurrealDB defaults for cloud when no .env present
  if [ "$IS_CLOUD" = "true" ] && [ ! -f "$PROJECT_DIR/.env" ]; then
    {
      printf 'export SURREAL_URL=ws://localhost:8000/rpc\n'
      printf 'export SURREAL_USER=root\n'
      printf 'export SURREAL_PASSWORD=root\n'
      printf 'export SURREAL_NAMESPACE=open_notebook\n'
      printf 'export SURREAL_DATABASE=development\n'
    } >> "$CLAUDE_ENV_FILE"
  fi
fi

# ─── Dynamic Project State ───────────────────────────────────────────────────
SPRINT_LINE="docs/sprint-artifacts/sprint-status.yaml"
SPRINT_FILE="$PROJECT_DIR/docs/sprint-artifacts/sprint-status.yaml"
if [ -f "$SPRINT_FILE" ]; then
  _total=$(grep -m1 'total_stories:'     "$SPRINT_FILE" 2>/dev/null | awk '{print $2}' || true)
  _done=$(grep -m1  'completed_stories:' "$SPRINT_FILE" 2>/dev/null | awk '{print $2}' || true)
  [ -n "$_total" ] && \
    SPRINT_LINE="${_done}/${_total} stories done | Ready: E2-S8 E2-S11 E5-S3 E5-S4 E1-S23 E9-S3 E10-S1"
fi

GIT_BRANCH=$(cd "$PROJECT_DIR" && git branch --show-current 2>/dev/null || echo "unknown")

CLOUD_NOTE=""
[ "$IS_CLOUD" = "true" ] && CLOUD_NOTE="Cloud setup complete (deps installed, SurrealDB started)"

# ─── Context Banner ───────────────────────────────────────────────────────────
printf '\n'
printf '╔══════════════════════════════════════════════════════════════════════════╗\n'
printf '║  ACM-AI — NEW SESSION                                                    ║\n'
printf '╠══════════════════════════════════════════════════════════════════════════╣\n'
printf '║  Env: %-68s║\n' "$ENV_TYPE  |  Branch: $GIT_BRANCH"
printf '║  Sprint: %-63s║\n' "$SPRINT_LINE"
[ -n "$CLOUD_NOTE" ] && printf '║  %-71s║\n' "$CLOUD_NOTE"
printf '║                                                                           ║\n'
printf '║  ESSENTIAL DOCS:                                                          ║\n'
printf '║    CLAUDE.md | docs/sprint-artifacts/sprint-status.yaml | MEMORY.md      ║\n'
printf '║                                                                           ║\n'
printf '║  BMAD WORKFLOWS:  /bmad:mmm:workflows:<name>                              ║\n'
printf '║    User: Demi | Language: English | Output: _bmad-output/                ║\n'
printf '║    Agents: architect, pm, dev, sm, analyst, tea, tech-writer             ║\n'
printf '║                                                                           ║\n'
printf '║  SERVICES:  :8000 SurrealDB  |  :5055 FastAPI  |  :8502 Frontend         ║\n'
printf '║    Local:  make start-all  OR  start-all.bat (Windows)                   ║\n'
printf '║    Cloud:  docker compose up -d surrealdb && uv run run_api.py           ║\n'
printf '║                                                                           ║\n'
printf '║  PROTECTED:  tests/  migrations/  pyproject.toml  package.json           ║\n'
printf '╚══════════════════════════════════════════════════════════════════════════╝\n'
printf '\n'

# ─── Superpowers × BMAD Bridge ────────────────────────────────────────────────
# Superpowers skills are symlinked at ~/.claude/skills/superpowers
# This section connects superpowers workflow routing with BMAD methodology
SUPERPOWERS_DIR="${HOME}/.claude/superpowers"
if [ -d "$SUPERPOWERS_DIR/skills" ]; then
  printf '━━━ SUPERPOWERS × BMAD BRIDGE ━━━\n'
  printf '\n'
  printf 'WORKFLOW ROUTING:\n'
  printf '  Planning (BMAD):     /party-mode | /analyst | /pm | /architect\n'
  printf '  Brainstorm:          superpowers:brainstorming\n'
  printf '  Impl. planning:      superpowers:writing-plans (reads BMAD stories)\n'
  printf '  Autonomous impl:     Ralph loop OR superpowers:executing-plans\n'
  printf '  Debugging:           ALWAYS superpowers:systematic-debugging\n'
  printf '  Code review:         ALWAYS superpowers:requesting-code-review\n'
  printf '  TDD:                 ALWAYS superpowers:test-driven-development\n'
  printf '\n'
  printf 'RULE: If a Superpowers skill exists for the task, you MUST use it.\n'
  printf 'RULE: BMAD artifacts in _bmad-output/ are the source of truth for planning.\n'
  printf 'RULE: Implementation plans go to docs/plans/ (Superpowers convention).\n'
  printf '\n'
fi

exit 0
