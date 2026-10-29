"""Bundle all release checks into a single command."""

import subprocess
import sys


def run(command: list[str], label: str) -> bool:
    """Run a command and print the result."""
    print(f"\n{'=' * 60}")
    print(f"  {label}")
    print(f"{'=' * 60}")
    result = subprocess.run(command)
    if result.returncode != 0:
        print(f"\n✗ {label} failed")
        return False
    print(f"\n✓ {label} passed")
    return True


def main():
    """Run all release checks: pytest, py-lean lint, ruff check, ruff format."""
    checks = [
        (["uv", "run", "pytest"], "Tests"),
        (["uv", "run", "py-lean", "lint"], "Source-exclude patterns"),
        (["uv", "run", "ruff", "check", "."], "Ruff lint"),
        (["uv", "run", "ruff", "format", "--check", "."], "Ruff format"),
    ]

    all_passed = True
    for command, label in checks:
        if not run(command, label):
            all_passed = False

    print(f"\n{'=' * 60}")
    if all_passed:
        print("✓ All checks passed")
        print(f"{'=' * 60}")
        sys.exit(0)
    else:
        print("✗ Some checks failed")
        print(f"{'=' * 60}")
        sys.exit(1)


if __name__ == "__main__":
    main()
