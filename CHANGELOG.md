# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [0.2.1] - 2026-10-30

### Fixed

- `check_build_system` now only accepts `uv_build` as a valid build backend — the invalid `uv_build.build` variant has
been removed, as it is not a valid uv convention.

## [0.2.0] - 2026-10-30

### Changed

- `--patterns` option now accepts a single space-separated string (e.g., `-p "tests/ benchmarks/ docs/"`) instead of
requiring repeated flags.

### Fixed

- Patterns are now normalized by stripping trailing slashes, so `tests/` and `tests` are treated identically
across all commands and configuration sources.

## [0.1.1] - 2026-10-29

### Changed

- Rename package `py-lean` to `py-lean-package`.

## [0.1.0] - 2026-10-29

### Added

- Initial release of `py-lean-package`.
- `lint` command: analyze projects for missing `source-exclude` patterns.
- `create` command: add missing `source-exclude` patterns to `pyproject.toml`.
- `update` command: automatically add missing `source-exclude` patterns to `pyproject.toml`.
- Support for `--format json` output.
- Support for `--dry-run` and `--diff` flags.
- Customizable artefact patterns via `--patterns` CLI option.
- Default patterns for common directories (`tests/`, `.venv/`, `__pycache__/`, etc.).
- Gitignore awareness: artefacts covered by `.gitignore` are skipped.
