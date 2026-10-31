# Release Process

This document describes how to release a new version of `py-lean-package` using [python-semantic-release](https://python-semantic-release.readthedocs.io/).

## Prerequisites

- [uv](https://github.com/astral-sh/uv) installed
- Conventional commit messages in the Git history

## How it works

python-semantic-release automatically determines the next version based on your commit history using
[Conventional Commits](https://www.conventionalcommits.org/):

- `fix:` commits → patch bump (0.2.0 → 0.2.1)
- `feat:` commits → minor bump (0.2.0 → 0.3.0)
- `BREAKING CHANGE` in commit footer → major bump (0.2.0 → 1.0.0)

It will:
1. Calculate the next version number
2. Update `pyproject.toml` and `src/py_lean_package/__init__.py`
3. Generate or update `CHANGELOG.md`

## Steps

### 1. Run all checks

```bash
uv run python all-qa-checks.py
```

This runs all tests, checks source-exclude patterns, and verifies lint and format in one command.

### 2. Preview the release

```bash
uv run semantic-release --noop version
```

This shows what changes would be made without actually applying them. Use this to verify the next version number and
changelog entries.

### 3. Create the release

```bash
uv run python release.py
```

This updates the version in `pyproject.toml` and `__init__.py`, and generates the changelog. `release.py` is a shortcut
for `semantic-release version --no-commit --no-tag --no-push --no-vcs-release` — nothing is committed or pushed
automatically, so you control when to commit and push.

By default, the version bump is auto-detected from commit history. To force a specific bump type:

```bash
uv run python release.py --patch       # Force a patch release (0.2.0 → 0.2.1)
uv run python release.py --minor       # Force a minor release (0.2.0 → 0.3.0)
uv run python release.py --major       # Force a major release (0.2.0 → 1.0.0)
uv run python release.py --prerelease  # Force a prerelease (0.2.0 → 0.3.0.dev0)
```

### 4. Review and commit

```bash
git diff
git add pyproject.toml src/py_lean_package/__init__.py CHANGELOG.md
git commit -m "dist: ship version X.Y.Z"
git tag vX.Y.Z
git push origin main vX.Y.Z
```

### 5. Build and publish (optional)

```bash
uv build
uv publish
```
