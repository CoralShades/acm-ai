#!/usr/bin/env python3
"""
Claude Code Initialization Script

Initializes Claude Code configuration in a project directory.
Handles both new projects and existing projects with documentation.
"""

import argparse
import json
import os
import shutil
from pathlib import Path


def get_script_dir():
    """Get the directory containing this script."""
    return Path(__file__).parent.resolve()


def get_framework_dir():
    """Get the framework root directory."""
    return get_script_dir().parent


def create_directory_structure(project_dir: Path):
    """Create the .claude directory structure."""
    dirs = [
        project_dir / ".claude" / "commands",
        project_dir / ".claude" / "rules",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        print(f"Created: {d}")


def copy_settings(project_dir: Path, framework_dir: Path):
    """Copy settings.json template."""
    src = framework_dir / "templates" / "settings" / "settings.json"
    dst = project_dir / ".claude" / "settings.json"

    if dst.exists():
        print(f"Skipping: {dst} (already exists)")
        return

    if src.exists():
        shutil.copy(src, dst)
        print(f"Created: {dst}")
    else:
        # Create minimal settings
        settings = {
            "mcpServers": {
                "filesystem": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-filesystem", "."],
                },
                "memory": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-memory"],
                },
            }
        }
        with open(dst, "w") as f:
            json.dump(settings, f, indent=2)
        print(f"Created: {dst}")


def copy_commands(project_dir: Path, framework_dir: Path, commands: list = None):
    """Copy command templates."""
    src_dir = framework_dir / "templates" / "commands"
    dst_dir = project_dir / ".claude" / "commands"

    if commands is None:
        # Copy all commands except template
        commands = [f.stem for f in src_dir.glob("*.md") if f.stem != "_template"]

    for cmd in commands:
        src = src_dir / f"{cmd}.md"
        dst = dst_dir / f"{cmd}.md"

        if dst.exists():
            print(f"Skipping: {dst} (already exists)")
            continue

        if src.exists():
            shutil.copy(src, dst)
            print(f"Created: {dst}")
        else:
            print(f"Warning: Template not found: {src}")


def copy_rules(project_dir: Path, framework_dir: Path, rules: list = None):
    """Copy rule templates."""
    src_dir = framework_dir / "templates" / "rules"
    dst_dir = project_dir / ".claude" / "rules"

    if rules is None:
        # Copy all rules except template
        rules = [f.stem for f in src_dir.glob("*.md") if f.stem != "_template"]

    for rule in rules:
        src = src_dir / f"{rule}.md"
        dst = dst_dir / f"{rule}.md"

        if dst.exists():
            print(f"Skipping: {dst} (already exists)")
            continue

        if src.exists():
            shutil.copy(src, dst)
            print(f"Created: {dst}")
        else:
            print(f"Warning: Template not found: {src}")


def create_claude_md(project_dir: Path, framework_dir: Path):
    """Create CLAUDE.md if it doesn't exist."""
    dst = project_dir / "CLAUDE.md"

    if dst.exists():
        print(f"Skipping: {dst} (already exists)")
        return

    src = framework_dir / "CLAUDE_TEMPLATE.md"
    if src.exists():
        shutil.copy(src, dst)
        print(f"Created: {dst}")
    else:
        # Create minimal CLAUDE.md
        content = """# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Project Overview

**[Project Name]** - Brief description of what this project does.

## Key Commands

```bash
# Start development server
npm run dev

# Run tests
npm test
```

## Claude Code Custom Commands

Custom slash commands are available in `.claude/commands/`:

| Command | Description |
|---------|-------------|
| `/start` | Start development services |
| `/stop` | Stop all services |
| `/status` | Check service health |
| `/logs [service]` | View service logs |

## Claude Code Modular Rules

Domain-specific rules in `.claude/rules/`:

| Rule File | Applies To |
|-----------|------------|
| `docker-compose.md` | Docker Compose files |
| `mcp-servers.md` | MCP configuration files |

## MCP Configuration

MCP servers configured in `.claude/settings.json`:

| Server | Purpose | Status |
|--------|---------|--------|
| `filesystem` | File operations | Enabled |
| `memory` | Persistent context | Enabled |
"""
        with open(dst, "w") as f:
            f.write(content)
        print(f"Created: {dst}")


def update_gitignore(project_dir: Path):
    """Add settings.local.json to .gitignore."""
    gitignore = project_dir / ".gitignore"
    entry = ".claude/settings.local.json"

    if gitignore.exists():
        content = gitignore.read_text()
        if entry not in content:
            with open(gitignore, "a") as f:
                f.write(f"\n# Claude Code local settings\n{entry}\n")
            print(f"Updated: {gitignore}")
        else:
            print(f"Skipping: {entry} already in .gitignore")
    else:
        with open(gitignore, "w") as f:
            f.write(f"# Claude Code local settings\n{entry}\n")
        print(f"Created: {gitignore}")


def main():
    parser = argparse.ArgumentParser(
        description="Initialize Claude Code in a project directory"
    )
    parser.add_argument(
        "project_dir",
        nargs="?",
        default=".",
        help="Project directory (default: current directory)",
    )
    parser.add_argument(
        "--new",
        action="store_true",
        help="Initialize as new project (create all files)",
    )
    parser.add_argument(
        "--existing",
        action="store_true",
        help="Initialize in existing project (preserve existing files)",
    )
    parser.add_argument(
        "--commands", nargs="+", help="Specific commands to copy (default: all)"
    )
    parser.add_argument(
        "--rules", nargs="+", help="Specific rules to copy (default: all)"
    )
    parser.add_argument(
        "--no-claude-md", action="store_true", help="Skip creating CLAUDE.md"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )

    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()
    framework_dir = get_framework_dir()

    print(f"Initializing Claude Code in: {project_dir}")
    print(f"Using framework from: {framework_dir}")
    print()

    if args.dry_run:
        print("DRY RUN - No changes will be made")
        print()

    # Create directory structure
    if not args.dry_run:
        create_directory_structure(project_dir)
    else:
        print("Would create: .claude/commands/")
        print("Would create: .claude/rules/")

    # Copy settings
    if not args.dry_run:
        copy_settings(project_dir, framework_dir)
    else:
        print("Would create: .claude/settings.json")

    # Copy commands
    if not args.dry_run:
        copy_commands(project_dir, framework_dir, args.commands)
    else:
        print("Would copy command templates")

    # Copy rules
    if not args.dry_run:
        copy_rules(project_dir, framework_dir, args.rules)
    else:
        print("Would copy rule templates")

    # Create CLAUDE.md
    if not args.no_claude_md:
        if not args.dry_run:
            create_claude_md(project_dir, framework_dir)
        else:
            print("Would create: CLAUDE.md")

    # Update .gitignore
    if not args.dry_run:
        update_gitignore(project_dir)
    else:
        print("Would update: .gitignore")

    print()
    print("Claude Code initialization complete!")
    print()
    print("Next steps:")
    print("1. Edit CLAUDE.md with your project details")
    print("2. Customize commands in .claude/commands/")
    print("3. Add path-specific rules in .claude/rules/")
    print("4. Configure MCP servers in .claude/settings.json")


if __name__ == "__main__":
    main()
