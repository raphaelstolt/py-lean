# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

## [0.1.0] - 2026-10-29

### Added

- Initial release of `py-lean`.
- `lint` command: analyze projects for missing `source-exclude` patterns.
- `create` command: add missing `source-exclude` patterns to `pyproject.toml`.
- `update` command: automatically add missing `source-exclude` patterns to `pyproject.toml`.
- Support for `--format json` output.
- Support for `--dry-run` and `--diff` flags.
- Customizable artefact patterns via `--patterns` CLI option.
- Default patterns for common directories (`tests/`, `.venv/`, `__pycache__/`, etc.).
- Gitignore awareness: artefacts covered by `.gitignore` are skipped.
