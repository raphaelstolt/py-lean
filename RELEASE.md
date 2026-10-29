# Release Process

This document describes how to release a new version of `py-lean-package`.

## Prerequisites

- [uv](https://github.com/astral-sh/uv) installed
- Access to PyPI for publishing

## Steps

### 1. Update version

Update the version in `pyproject.toml` and `py_lean_package/__init__.py`:

```bash
# Edit pyproject.toml
# Change version = "X.Y.Z" to the new version

# Edit py_lean_package/__init__.py
# Change __version__ = "X.Y.Z" to the new version
```

### 2. Update CHANGELOG.md

Move the `[Unreleased]` section in `CHANGELOG.md` to a new versioned section:

```markdown
## [0.1.0] - 2025-01-15

### Added
- ...
```

### 3. Run tests and lint

```bash
# Run all tests
uv run pytest

# Run linter
uv run ruff check .

# Format check
uv run ruff format --check .
```

### 4. Build the package

```bash
uv build
```

This creates source distribution (`.tar.gz`) and wheel (`.whl`) in the `dist/` directory.

### 5. Publish to PyPI

```bash
uv publish
```

### 6. Create a Git tag

```bash
git commit -m 'dist: ship version 0.1.0'
git tag v0.1.0
git push origin v0.1.0
```
