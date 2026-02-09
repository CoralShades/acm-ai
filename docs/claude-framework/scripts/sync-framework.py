#!/usr/bin/env python3
"""
Framework Sync Script

Updates Claude Code framework files in a project from the framework templates.
Preserves existing customizations while adding new features.
"""

import argparse
import json
import os
import shutil
from pathlib import Path
from typing import Dict, List, Set


def get_script_dir():
    """Get the directory containing this script."""
    return Path(__file__).parent.resolve()


def get_framework_dir():
    """Get the framework root directory."""
    return get_script_dir().parent


def get_template_files(framework_dir: Path) -> Dict[str, List[Path]]:
    """Get all template files from framework."""
    templates = {"commands": [], "rules": [], "settings": []}

    commands_dir = framework_dir / "templates" / "commands"
    if commands_dir.exists():
        templates["commands"] = [
            f for f in commands_dir.glob("*.md") if f.stem != "_template"
        ]

    rules_dir = framework_dir / "templates" / "rules"
    if rules_dir.exists():
        templates["rules"] = [
            f for f in rules_dir.glob("*.md") if f.stem != "_template"
        ]

    settings_dir = framework_dir / "templates" / "settings"
    if settings_dir.exists():
        templates["settings"] = list(settings_dir.glob("*.json"))

    return templates


def get_project_files(project_dir: Path) -> Dict[str, Set[str]]:
    """Get existing files in project's Claude Code setup."""
    existing = {"commands": set(), "rules": set(), "settings": set()}

    commands_dir = project_dir / ".claude" / "commands"
    if commands_dir.exists():
        existing["commands"] = {f.stem for f in commands_dir.glob("*.md")}

    rules_dir = project_dir / ".claude" / "rules"
    if rules_dir.exists():
        existing["rules"] = {f.stem for f in rules_dir.glob("*.md")}

    if (project_dir / ".claude" / "settings.json").exists():
        existing["settings"].add("settings")
    if (project_dir / ".claude" / "settings.local.json").exists():
        existing["settings"].add("settings.local")

    return existing


def sync_commands(
    project_dir: Path,
    framework_dir: Path,
    templates: List[Path],
    existing: Set[str],
    force: bool = False,
    dry_run: bool = False,
) -> List[str]:
    """Sync command templates to project."""
    changes = []
    dst_dir = project_dir / ".claude" / "commands"

    for template in templates:
        name = template.stem
        dst = dst_dir / template.name

        if name in existing and not force:
            continue

        action = "Update" if name in existing else "Add"
        changes.append(f"{action}: {dst}")

        if not dry_run:
            dst_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy(template, dst)

    return changes


def sync_rules(
    project_dir: Path,
    framework_dir: Path,
    templates: List[Path],
    existing: Set[str],
    force: bool = False,
    dry_run: bool = False,
) -> List[str]:
    """Sync rule templates to project."""
    changes = []
    dst_dir = project_dir / ".claude" / "rules"

    for template in templates:
        name = template.stem
        dst = dst_dir / template.name

        if name in existing and not force:
            continue

        action = "Update" if name in existing else "Add"
        changes.append(f"{action}: {dst}")

        if not dry_run:
            dst_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy(template, dst)

    return changes


def sync_settings(
    project_dir: Path, framework_dir: Path, dry_run: bool = False
) -> List[str]:
    """Sync MCP server configurations (merge, don't overwrite)."""
    changes = []

    src = framework_dir / "templates" / "settings" / "settings.json"
    dst = project_dir / ".claude" / "settings.json"

    if not src.exists():
        return changes

    if not dst.exists():
        changes.append(f"Add: {dst}")
        if not dry_run:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(src, dst)
    else:
        # Merge settings
        with open(src) as f:
            template_settings = json.load(f)
        with open(dst) as f:
            project_settings = json.load(f)

        # Add new MCP servers that don't exist
        template_servers = template_settings.get("mcpServers", {})
        project_servers = project_settings.get("mcpServers", {})

        new_servers = []
        for name, config in template_servers.items():
            if name not in project_servers:
                new_servers.append(name)
                if not dry_run:
                    project_servers[name] = config

        if new_servers:
            changes.append(f"Add MCP servers to {dst}: {', '.join(new_servers)}")
            if not dry_run:
                project_settings["mcpServers"] = project_servers
                with open(dst, "w") as f:
                    json.dump(project_settings, f, indent=2)

    return changes


def main():
    parser = argparse.ArgumentParser(
        description="Sync Claude Code framework to a project"
    )
    parser.add_argument(
        "project_dir",
        nargs="?",
        default=".",
        help="Project directory (default: current directory)",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    parser.add_argument(
        "--commands-only", action="store_true", help="Only sync commands"
    )
    parser.add_argument("--rules-only", action="store_true", help="Only sync rules")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )

    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()
    framework_dir = get_framework_dir()

    print(f"Syncing Claude Code framework")
    print(f"  From: {framework_dir}")
    print(f"  To: {project_dir}")
    print()

    if args.dry_run:
        print("DRY RUN - No changes will be made")
        print()

    # Get template and existing files
    templates = get_template_files(framework_dir)
    existing = get_project_files(project_dir)

    all_changes = []

    # Sync commands
    if not args.rules_only:
        changes = sync_commands(
            project_dir,
            framework_dir,
            templates["commands"],
            existing["commands"],
            args.force,
            args.dry_run,
        )
        all_changes.extend(changes)

    # Sync rules
    if not args.commands_only:
        changes = sync_rules(
            project_dir,
            framework_dir,
            templates["rules"],
            existing["rules"],
            args.force,
            args.dry_run,
        )
        all_changes.extend(changes)

    # Sync settings (always merge, never overwrite)
    if not args.commands_only and not args.rules_only:
        changes = sync_settings(project_dir, framework_dir, args.dry_run)
        all_changes.extend(changes)

    if all_changes:
        print("Changes:")
        for change in all_changes:
            print(f"  {change}")
    else:
        print("No changes needed - project is up to date")

    print()
    print("Sync complete!")


if __name__ == "__main__":
    main()
