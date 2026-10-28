"""CLI entry point for py-lean."""

from __future__ import annotations

import json
from difflib import unified_diff
from pathlib import Path

import tomlkit
import typer

from py_lean import __version__
from py_lean.analyzer import _get_source_exclude_patterns, analyze, check_build_system, load_manifest
from py_lean.models import DEFAULT_SOURCE_EXCLUDE_PATTERNS, IssueType, OutputFormat

app = typer.Typer(
    name="py-lean",
    help="Detect and fix missing source-exclude patterns in Python projects.",
    add_completion=False,
)


# Common options
def manifest_path_callback(ctx: typer.Context, value: str) -> Path:
    """Validate and resolve the manifest path."""
    path = Path(value)
    if not path.exists():
        raise typer.Exit(1)
    return path.resolve()


#
# Commands
#

@app.command("lint")
def cmd_lint(
    manifest_path: Path = typer.Option(
        "pyproject.toml",
        "-m",
        "--manifest-path",
        callback=manifest_path_callback,
        help="Path to the pyproject.toml file.",
    ),
    format: OutputFormat = typer.Option(
        OutputFormat.TEXT,
        "--format",
        help="Output format: text or json.",
    ),
    patterns: list[str] | None = typer.Option(
        None,
        "-p",
        "--patterns",
        help="Artefact patterns to check for source-exclude (e.g., tests).",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be done without making changes.",
    ),
    diff: bool = typer.Option(
        False,
        "--diff",
        help="Show a diff of the changes that would be made.",
    ),
) -> None:
    """Analyze a project for missing source-exclude patterns."""
    manifest = load_manifest(manifest_path)
    if not check_build_system(manifest):
        typer.echo(
            "Error: This project is not configured with uv_build as its build backend.\n\n"
            "py-lean requires the following in pyproject.toml:\n\n"
            "  [build-system]\n"
            '  requires = ["uv_build"]\n'
            '  build-backend = "uv_build.build"',
            err=True,
        )
        raise typer.Exit(1)
    result = analyze(manifest_path, patterns)

    if format == OutputFormat.JSON:
        typer.echo(json.dumps(result.to_dict(), indent=2))
    else:
        if result.is_clean:
            typer.echo("✓ No issues found.")
        else:
            _print_issues(result.issues)
            typer.echo(f"\nFound {len(result.issues)} issue(s).", err=True)
            raise typer.Exit(1)

    if dry_run:
        typer.echo("(dry-run: no changes made)")
    if diff:
        _show_diff(manifest_path, result.issues)


@app.command("create")
def cmd_create(
    manifest_path: Path = typer.Option(
        "pyproject.toml",
        "-m",
        "--manifest-path",
        callback=manifest_path_callback,
        help="Path to the pyproject.toml file.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be done without making changes.",
    ),
    diff: bool = typer.Option(
        False,
        "--diff",
        help="Show a diff of the changes that would be made.",
    ),
) -> None:
    """Add source-exclude patterns for repository artefacts to tool.uv.build-backend in pyproject.toml.

    Merges configured patterns with built-in defaults and validates against the Git repository.
    Only adds patterns for artefacts that actually exist in the project.
    """
    manifest = load_manifest(manifest_path)
    if not check_build_system(manifest):
        typer.echo(
            "Error: This project is not configured with uv_build as its build backend.\n\n"
            "py-lean requires the following in pyproject.toml:\n\n"
            "  [build-system]\n"
            '  requires = ["uv_build"]\n'
            '  build-backend = "uv_build.build"',
            err=True,
        )
        raise typer.Exit(1)
    # Merge configured patterns with built-in defaults
    manifest = tomlkit.parse(manifest_path.read_text(encoding="utf-8"))
    current_excludes = _get_source_exclude_patterns(manifest)
    merged_patterns = list(current_excludes)
    for pattern in DEFAULT_SOURCE_EXCLUDE_PATTERNS:
        if pattern not in merged_patterns:
            merged_patterns.append(pattern)

    # Analyze with merged patterns to find which artefacts exist in the repo
    result = analyze(manifest_path, merged_patterns)

    if result.is_clean:
        typer.echo("✓ No missing source-exclude patterns to add.")
        return

    original_content = manifest_path.read_text(encoding="utf-8")
    manifest = tomlkit.parse(original_content)

    # Ensure tool.uv.build-backend section exists
    if "tool" not in manifest:
        manifest["tool"] = {}
    if "uv" not in manifest["tool"]:
        manifest["tool"]["uv"] = {}
    if "build-backend" not in manifest["tool"]["uv"]:
        manifest["tool"]["uv"]["build-backend"] = {}

    bb = manifest["tool"]["uv"]["build-backend"]
    current = list(bb.get("source-exclude", []))

    # Add only the missing patterns that exist in the repo
    added = 0
    for issue in result.issues:
        if issue.issue_type == IssueType.MISSING_SOURCE_EXCLUDE:
            pattern = issue.subject
            if pattern not in current:
                current.append(pattern)
                added += 1

    bb["source-exclude"] = current
    new_content = tomlkit.dumps(manifest)

    if dry_run or diff:
        if diff:
            _print_diff(original_content, new_content, str(manifest_path))
        if dry_run:
            typer.echo("(dry-run: no changes made)")
        return

    manifest_path.write_text(new_content, encoding="utf-8")
    typer.echo(f"Added {added} source-exclude pattern(s) to {manifest_path}")


@app.command("update")
def cmd_update(
    manifest_path: Path = typer.Option(
        "pyproject.toml",
        "-m",
        "--manifest-path",
        callback=manifest_path_callback,
        help="Path to the pyproject.toml file.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be done without making changes.",
    ),
    diff: bool = typer.Option(
        False,
        "--diff",
        help="Show a diff of the changes that would be made.",
    ),
) -> None:
    """Merge configured patterns with built-in defaults and update source-exclude in pyproject.toml.

    Validates against the Git repository — only adds patterns for artefacts that actually exist.
    """
    manifest = load_manifest(manifest_path)
    if not check_build_system(manifest):
        typer.echo(
            "Error: This project is not configured with uv_build as its build backend.\n\n"
            "py-lean requires the following in pyproject.toml:\n\n"
            "  [build-system]\n"
            '  requires = ["uv_build"]\n'
            '  build-backend = "uv_build.build"',
            err=True,
        )
        raise typer.Exit(1)
    # Merge configured patterns with built-in defaults
    manifest = tomlkit.parse(manifest_path.read_text(encoding="utf-8"))
    current_excludes = _get_source_exclude_patterns(manifest)
    merged_patterns = list(current_excludes)
    for pattern in DEFAULT_SOURCE_EXCLUDE_PATTERNS:
        if pattern not in merged_patterns:
            merged_patterns.append(pattern)

    # Analyze with merged patterns to find which artefacts exist in the repo
    result = analyze(manifest_path, merged_patterns)

    if result.is_clean:
        typer.echo("✓ No missing source-exclude patterns to add.")
        return

    original_content = manifest_path.read_text(encoding="utf-8")
    manifest = tomlkit.parse(original_content)

    # Ensure tool.uv.build-backend section exists
    if "tool" not in manifest:
        manifest["tool"] = {}
    if "uv" not in manifest["tool"]:
        manifest["tool"]["uv"] = {}
    if "build-backend" not in manifest["tool"]["uv"]:
        manifest["tool"]["uv"]["build-backend"] = {}

    bb = manifest["tool"]["uv"]["build-backend"]
    current = list(bb.get("source-exclude", []))

    # Add only the missing patterns that exist in the repo
    added = 0
    for issue in result.issues:
        if issue.issue_type == IssueType.MISSING_SOURCE_EXCLUDE:
            pattern = issue.subject
            if pattern not in current:
                current.append(pattern)
                added += 1

    bb["source-exclude"] = current
    new_content = tomlkit.dumps(manifest)

    if dry_run or diff:
        if diff:
            _print_diff(original_content, new_content, str(manifest_path))
        if dry_run:
            typer.echo("(dry-run: no changes made)")
        return

    manifest_path.write_text(new_content, encoding="utf-8")
    typer.echo(f"Added {added} source-exclude pattern(s) to {manifest_path}")


#
# Helpers
#

def _print_issues(issues: list) -> None:
    """Print issues in a human-readable format."""
    for issue in issues:
        icon = _issue_icon(issue.issue_type)
        typer.echo(f"{icon} {issue.subject}")
        typer.echo(f"   {issue.description}")
        if issue.suggestion:
            typer.echo(f"   → {issue.suggestion}")
        typer.echo()


def _issue_icon(issue_type: IssueType) -> str:
    """Get a display icon for an issue type."""
    icons = {
        IssueType.MISSING_SOURCE_EXCLUDE: "✕",
    }
    return icons.get(issue_type, "?")


def _print_diff(old: str, new: str, path: str) -> None:
    """Print a unified diff between old and new content."""
    old_lines = old.splitlines(keepends=True)
    new_lines = new.splitlines(keepends=True)

    diff_lines = unified_diff(old_lines, new_lines, fromfile=f"a/{path}", tofile=f"b/{path}")
    for line in diff_lines:
        typer.echo(line, nl=False)


def _show_diff(manifest_path: Path, issues: list) -> None:
    """Show what changes would be made to fix the issues."""
    original_content = manifest_path.read_text(encoding="utf-8")
    manifest = tomlkit.parse(original_content)

    # Handle missing source-exclude
    missing_excludes = [i for i in issues if i.issue_type == IssueType.MISSING_SOURCE_EXCLUDE]
    if missing_excludes:
        if "tool" not in manifest:
            manifest["tool"] = {}
        if "uv" not in manifest["tool"]:
            manifest["tool"]["uv"] = {}
        if "build-backend" not in manifest["tool"]["uv"]:
            manifest["tool"]["uv"]["build-backend"] = {}

        bb = manifest["tool"]["uv"]["build-backend"]
        current_excludes = list(bb.get("source-exclude", []))
        for issue in missing_excludes:
            if issue.subject not in current_excludes:
                current_excludes.append(issue.subject)
        if current_excludes:
            bb["source-exclude"] = current_excludes

    new_content = tomlkit.dumps(manifest)
    if new_content != original_content:
        _print_diff(original_content, new_content, str(manifest_path))


def version_callback(value: bool) -> None:
    """Print the version and exit."""
    if value:
        typer.echo(f"py-lean {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    _version: bool = typer.Option(
        False,
        "--version",
        "-V",
        callback=version_callback,
        is_eager=True,
        help="Show the version and exit.",
    ),
) -> None:
    """py-lean: Detect and fix missing source-exclude patterns in Python projects."""
    pass


if __name__ == "__main__":
    app()
