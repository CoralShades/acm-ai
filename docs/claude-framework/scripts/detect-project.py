#!/usr/bin/env python3
"""
Project Detection Script

Analyzes an existing project structure to determine:
- Existing Claude Code setup
- Documentation structure
- Technology stack
- Infrastructure patterns
- Recommended configuration
"""

import argparse
import json
import os
from pathlib import Path
from typing import Dict, List, Any


def detect_documentation(project_dir: Path) -> Dict[str, Any]:
    """Detect existing documentation structure."""
    result = {
        "claude_md": (project_dir / "CLAUDE.md").exists(),
        "agents_md": (project_dir / "AGENTS.md").exists(),
        "claude_dir": (project_dir / ".claude").exists(),
        "docs_dir": (project_dir / "docs").exists(),
        "readme": (project_dir / "README.md").exists(),
        "existing_commands": [],
        "existing_rules": [],
        "docs_structure": None
    }

    # Check for existing Claude commands
    commands_dir = project_dir / ".claude" / "commands"
    if commands_dir.exists():
        result["existing_commands"] = [f.stem for f in commands_dir.glob("*.md")]

    # Check for existing rules
    rules_dir = project_dir / ".claude" / "rules"
    if rules_dir.exists():
        result["existing_rules"] = [f.stem for f in rules_dir.glob("*.md")]

    # Detect docs structure
    if result["docs_dir"]:
        docs = project_dir / "docs"
        if (docs / "architecture").exists():
            result["docs_structure"] = "bmad" if (docs / "adr").exists() else "architecture"
        elif (docs / "adr").exists():
            result["docs_structure"] = "adr"
        elif (docs / "api").exists():
            result["docs_structure"] = "api"
        else:
            result["docs_structure"] = "basic"

    return result


def detect_technology(project_dir: Path) -> Dict[str, Any]:
    """Detect technology stack."""
    result = {
        "language": None,
        "framework": None,
        "build_tool": None,
        "test_framework": None,
        "package_manager": None
    }

    # Language detection
    if (project_dir / "package.json").exists():
        result["language"] = "javascript/typescript"
        result["package_manager"] = "npm"

        # Check for specific package managers
        if (project_dir / "yarn.lock").exists():
            result["package_manager"] = "yarn"
        elif (project_dir / "pnpm-lock.yaml").exists():
            result["package_manager"] = "pnpm"

        # Read package.json for framework detection
        try:
            with open(project_dir / "package.json") as f:
                pkg = json.load(f)
                deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}

                if "next" in deps:
                    result["framework"] = "nextjs"
                elif "nuxt" in deps:
                    result["framework"] = "nuxt"
                elif "react" in deps:
                    result["framework"] = "react"
                elif "vue" in deps:
                    result["framework"] = "vue"
                elif "express" in deps:
                    result["framework"] = "express"
                elif "fastify" in deps:
                    result["framework"] = "fastify"

                if "jest" in deps:
                    result["test_framework"] = "jest"
                elif "vitest" in deps:
                    result["test_framework"] = "vitest"
                elif "mocha" in deps:
                    result["test_framework"] = "mocha"
        except:
            pass

    elif (project_dir / "pyproject.toml").exists() or (project_dir / "requirements.txt").exists():
        result["language"] = "python"
        result["package_manager"] = "pip"

        if (project_dir / "pyproject.toml").exists():
            result["package_manager"] = "poetry" if "poetry" in (project_dir / "pyproject.toml").read_text() else "pip"

        # Framework detection
        if (project_dir / "manage.py").exists():
            result["framework"] = "django"
        elif any((project_dir / f).exists() for f in ["main.py", "app.py"]):
            result["framework"] = "fastapi/flask"

    elif (project_dir / "Cargo.toml").exists():
        result["language"] = "rust"
        result["package_manager"] = "cargo"

    elif (project_dir / "go.mod").exists():
        result["language"] = "go"
        result["package_manager"] = "go"

    # Build tool detection
    if (project_dir / "Makefile").exists():
        result["build_tool"] = "make"
    elif (project_dir / "justfile").exists():
        result["build_tool"] = "just"
    elif (project_dir / "taskfile.yml").exists():
        result["build_tool"] = "task"

    return result


def detect_infrastructure(project_dir: Path) -> Dict[str, Any]:
    """Detect infrastructure patterns."""
    result = {
        "docker": False,
        "docker_compose": False,
        "ci_cd": None,
        "database": None,
        "deployment": None
    }

    # Docker detection
    result["docker"] = (project_dir / "Dockerfile").exists()
    result["docker_compose"] = any(project_dir.glob("docker-compose*.yml")) or any(project_dir.glob("docker-compose*.yaml"))

    # CI/CD detection
    if (project_dir / ".github" / "workflows").exists():
        result["ci_cd"] = "github-actions"
    elif (project_dir / ".gitlab-ci.yml").exists():
        result["ci_cd"] = "gitlab-ci"
    elif (project_dir / "Jenkinsfile").exists():
        result["ci_cd"] = "jenkins"
    elif (project_dir / ".circleci").exists():
        result["ci_cd"] = "circleci"

    # Database detection
    if (project_dir / "supabase").exists():
        result["database"] = "supabase"
    elif (project_dir / "prisma").exists():
        result["database"] = "prisma"
    elif any(project_dir.glob("**/mongodb*")):
        result["database"] = "mongodb"

    # Deployment detection
    if (project_dir / "vercel.json").exists():
        result["deployment"] = "vercel"
    elif (project_dir / "netlify.toml").exists():
        result["deployment"] = "netlify"
    elif (project_dir / "fly.toml").exists():
        result["deployment"] = "fly"
    elif (project_dir / "render.yaml").exists():
        result["deployment"] = "render"

    return result


def generate_recommendations(
    documentation: Dict[str, Any],
    technology: Dict[str, Any],
    infrastructure: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate setup recommendations based on detection."""
    recommendations = {
        "strategy": "standard",
        "commands": ["start", "stop", "status", "logs"],
        "rules": [],
        "mcp_servers": ["filesystem", "memory"]
    }

    # Determine strategy
    if documentation["claude_md"] and documentation["existing_commands"]:
        recommendations["strategy"] = "minimal"
    elif not documentation["claude_md"] and not documentation["claude_dir"]:
        recommendations["strategy"] = "full"

    # Add technology-specific rules
    if technology["language"] == "javascript/typescript":
        recommendations["rules"].append("typescript")
    if technology["framework"] == "nextjs":
        recommendations["rules"].append("nextjs")
    if technology["framework"] == "react":
        recommendations["rules"].append("react")

    # Add infrastructure-specific rules
    if infrastructure["docker_compose"]:
        recommendations["rules"].append("docker-compose")
    if infrastructure["database"] == "supabase":
        recommendations["rules"].append("supabase")
        recommendations["mcp_servers"].append("supabase")

    # Add CI/CD MCP
    if infrastructure["ci_cd"] == "github-actions":
        recommendations["mcp_servers"].append("github")

    return recommendations


def main():
    parser = argparse.ArgumentParser(
        description="Detect project structure for Claude Code setup"
    )
    parser.add_argument(
        "project_dir",
        nargs="?",
        default=".",
        help="Project directory (default: current directory)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Write output to file"
    )

    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()

    # Run detection
    documentation = detect_documentation(project_dir)
    technology = detect_technology(project_dir)
    infrastructure = detect_infrastructure(project_dir)
    recommendations = generate_recommendations(documentation, technology, infrastructure)

    result = {
        "project_dir": str(project_dir),
        "documentation": documentation,
        "technology": technology,
        "infrastructure": infrastructure,
        "recommendations": recommendations
    }

    if args.json or args.output:
        output = json.dumps(result, indent=2)
        if args.output:
            with open(args.output, 'w') as f:
                f.write(output)
            print(f"Output written to: {args.output}")
        else:
            print(output)
    else:
        # Human-readable output
        print(f"Project Detection Report: {project_dir}")
        print("=" * 60)

        print("\nDocumentation:")
        print(f"  CLAUDE.md: {'Yes' if documentation['claude_md'] else 'No'}")
        print(f"  AGENTS.md: {'Yes' if documentation['agents_md'] else 'No'}")
        print(f"  .claude/: {'Yes' if documentation['claude_dir'] else 'No'}")
        print(f"  docs/: {documentation['docs_structure'] or 'No'}")
        if documentation['existing_commands']:
            print(f"  Existing commands: {', '.join(documentation['existing_commands'])}")
        if documentation['existing_rules']:
            print(f"  Existing rules: {', '.join(documentation['existing_rules'])}")

        print("\nTechnology:")
        print(f"  Language: {technology['language'] or 'Unknown'}")
        print(f"  Framework: {technology['framework'] or 'Unknown'}")
        print(f"  Package manager: {technology['package_manager'] or 'Unknown'}")
        print(f"  Build tool: {technology['build_tool'] or 'None'}")
        print(f"  Test framework: {technology['test_framework'] or 'Unknown'}")

        print("\nInfrastructure:")
        print(f"  Docker: {'Yes' if infrastructure['docker'] else 'No'}")
        print(f"  Docker Compose: {'Yes' if infrastructure['docker_compose'] else 'No'}")
        print(f"  CI/CD: {infrastructure['ci_cd'] or 'None'}")
        print(f"  Database: {infrastructure['database'] or 'Unknown'}")
        print(f"  Deployment: {infrastructure['deployment'] or 'Unknown'}")

        print("\nRecommendations:")
        print(f"  Strategy: {recommendations['strategy']}")
        print(f"  Commands: {', '.join(recommendations['commands'])}")
        print(f"  Rules: {', '.join(recommendations['rules']) or 'None specific'}")
        print(f"  MCP Servers: {', '.join(recommendations['mcp_servers'])}")


if __name__ == "__main__":
    main()
