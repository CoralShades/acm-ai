#!/bin/bash
# Session start hook: Display project context reminders

cat << 'EOF'

╔══════════════════════════════════════════════════════════════════════════╗
║                        ACM-AI PROJECT CONTEXT                            ║
╔══════════════════════════════════════════════════════════════════════════╗

📚 ESSENTIAL DOCS:
   • CLAUDE.md - Project instructions and architecture
   • docs/sprint-artifacts/sprint-status.yaml - Current sprint state
   • MEMORY.md - Cross-session project memory

🔒 PROTECTED FILES (Pre-tool-use hook active):
   • tests/ - Test files require explicit approval
   • migrations/ - Database migrations protected
   • pyproject.toml, package.json - Dependency configs protected
   • docker-compose*.yml - Infrastructure configs protected
   • .github/workflows/ - CI/CD workflows protected
   • Lock files (uv.lock, package-lock.json) - Auto-generated

⚡ QUICK START:
   • Backend: uv run run_api.py (port 5055)
   • Frontend: cd frontend && npm run dev (port 8502)
   • Database: docker compose up -d surrealdb (port 8000)
   • All-in-one: start-all.bat (Windows) or make start-all (Unix)

🎯 CURRENT SPRINT:
   • 74 total stories (50 done, 24 remaining = 68% complete)
   • Active epics: E1, E8, E11, E12
   • See sprint-status.yaml for detailed breakdown

💡 REMEMBER:
   • Use AskUserQuestion for clarifications
   • Check MEMORY.md for model configs and known issues
   • Run Story Verification Protocol before marking stories done

╚══════════════════════════════════════════════════════════════════════════╝

EOF
