"""Shortcut for running python-semantic-release version in local mode.

Usage:
    uv run python release.py              # auto-detect version bump
    uv run python release.py --patch      # force patch bump
    uv run python release.py --minor      # force minor bump
    uv run python release.py --major      # force major bump
    uv run python release.py --prerelease # force prerelease

This runs:
    uv run semantic-release version --no-commit --no-tag --no-push --no-vcs-release

Which updates the version in pyproject.toml and __init__.py, generates the
changelog, and builds the package — without committing, tagging, or pushing.
"""

import argparse
import subprocess
import sys


def main():
    """Run semantic-release version with local-only flags."""
    parser = argparse.ArgumentParser(
        description="Bump the version and update changelog (local only).",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--major", action="store_true", help="Force a major release")
    group.add_argument("--minor", action="store_true", help="Force a minor release")
    group.add_argument("--patch", action="store_true", help="Force a patch release")
    group.add_argument("--prerelease", action="store_true", help="Force a prerelease")

    args = parser.parse_args()

    command = [
        "uv",
        "run",
        "semantic-release",
        "version",
        "--no-commit",
        "--no-tag",
        "--no-push",
        "--no-vcs-release",
    ]

    if args.major:
        command.append("--major")
    elif args.minor:
        command.append("--minor")
    elif args.patch:
        command.append("--patch")
    elif args.prerelease:
        command.append("--prerelease")

    print("Running: " + " ".join(command))
    result = subprocess.run(command)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
