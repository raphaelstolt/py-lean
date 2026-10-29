# py-lean

Detect and fix missing `source-exclude` patterns in Python projects built with `uv_build`.

`py-lean` is a Python counterpart to [cargo-lean](https://github.com/raphaelstolt/cargo-lean). It checks the source-distribution configuration in
`pyproject.toml` so repository-only files don't unnecessarily end up in published archives.

## Why?

A Python package's source repository often contains more than consumers need to install and use it. Tests, CI workflows,
development configuration, and other repository-specific files can add unnecessary noise and size to source distributions.

`py-lean` helps make distribution contents intentional by identifying common repository artefacts that are missing from
`tool.uv.build-backend.source-exclude`. It can also add the missing patterns to `pyproject.toml`.

Your working repository remains intact: `py-lean` configures what is excluded from the built source distribution; it does
not delete those files from your project.

## Features

- __Lint__ — Detect common repository artefacts that are not listed in `source-exclude`.
- __Create__ — Add a `source-exclude` configuration for detected artefacts.
- __Update__ — Add missing exclusion patterns to an existing configuration.
- __Preview changes__ — Use `--dry-run` and `--diff` to review proposed edits before applying them.
- __Machine-readable output__ — Emit lint results as JSON.

## Requirements

- Python 3.11 or newer
- [uv](https://github.com/astral-sh/uv) and a project using the `uv_build` build backend

### Required build-system configuration

`py-lean` manages `tool.uv.build-backend.source-exclude`, which is a `uv_build` configuration. The target project must
therefore use `uv_build` as its build backend for this setting to apply.

For example, the target project's `pyproject.toml` should include:

```toml
[build-system]
requires = ["uv_build"]
build-backend = "uv_build"
```

If the project uses a different build backend, `py-lean`'s `source-exclude` configuration will not control that backend's
source-distribution contents.

## Installation

Install with `uv`:

```bash
uv tool install py-lean-package
```

Or install from source:

```bash
git clone https://github.com/raphaelstolt/py-lean.git
cd py-lean
uv sync
uv run --project . py-lean --help
```

## Usage

### Lint

Check for missing patterns in `source-exclude`:

```bash
py-lean lint
```

Options:

| Flag | Description |
|------|-------------|
| `-m, --manifest-path <PATH>` | Path to `pyproject.toml` (default: `pyproject.toml`) |
| `--format <text\|json>` | Output format (default: `text`) |
| `-p, --patterns <PATTERNS>` | Space-separated artefact patterns to check, e.g., `"tests/ benchmarks/"` |
| `--dry-run` | Show what would be done without making changes |
| `--diff` | Show a diff of the proposed changes |

Examples:

```bash
# Lint with JSON output
py-lean lint --format json

# Use a custom manifest path
py-lean lint -m path/to/pyproject.toml

# Check selected artefact patterns
py-lean lint -p "tests/ benchmarks/"
```

### Create

Create a `tool.uv.build-backend.source-exclude` configuration containing common repository artefacts:

```bash
py-lean create
```

This scans the project for common artefacts, such as `tests/`, `docs/`, and `.git/`, and adds the detected patterns to
`pyproject.toml`.

Options:

| Flag | Description |
|------|-------------|
| `--dry-run` | Preview changes without modifying files |
| `--diff` | Show a unified diff of the proposed changes |

### Update

Add missing patterns to an existing `source-exclude` configuration:

```bash
py-lean update
```

Options:

| Flag | Description |
|------|-------------|
| `--dry-run` | Preview changes without modifying files |
| `--diff` | Show a unified diff of the proposed changes |

Examples:

```bash
# Preview changes
py-lean update --dry-run --diff

# Apply changes
py-lean update
```

## Configuration

### Pattern precedence

`py-lean` determines which artefact patterns to check using the following precedence:

1. __CLI `--patterns`__ — highest priority; replaces other pattern sources.
2. __`tool.uv.build-backend.source-exclude`__ in `pyproject.toml` — patterns already configured for the build backend.
3. __Built-in defaults__ — used when neither of the above is configured.

Use `--patterns` to override the default patterns:

```bash
py-lean lint -p "tests/ benchmarks/"
```

### Default artefact patterns

By default, `py-lean` checks for these 20 patterns:

```
tests/, docs/, dist/, build/, htmlcov/,
.venv/, __pycache__/, .tox/, .mypy_cache/, .pytest_cache/, .github/,
.idea/, .vscode/, .vs/, .ruff_cache/,
*.egg-info, .DS_Store, *.pyc, *.pyo, .coverage
```

Note: `.git` is not included as it is automatically excluded by build backends.

Override them with `--patterns`:

```bash
py-lean lint -p ".idea/ __pycache__/"
```

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for development instructions.

## License

This project is licensed under the MIT License. See [LICENSE.md](LICENSE.md) for details.

## Related projects

- [lean-package-validator](https://github.com/raphaelstolt/lean-package-validator) — The `PHP` equivalent
- [cargo-lean](https://github.com/raphaelstolt/cargo-lean) — The `Rust` equivalent.
