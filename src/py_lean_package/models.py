"""Data models for py-lean."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path


class IssueType(StrEnum):
    """Types of issues that py-lean can detect."""

    MISSING_SOURCE_EXCLUDE = "missing_source_exclude"


class OutputFormat(StrEnum):
    """Output format for py-lean results."""

    TEXT = "text"
    JSON = "json"


@dataclass
class Issue:
    """A single issue detected by py-lean."""

    issue_type: IssueType
    subject: str
    description: str
    location: str | None = None
    suggestion: str | None = None

    def to_dict(self) -> dict:
        """Convert the issue to a dictionary for JSON serialization."""
        result: dict = {
            "type": self.issue_type.value,
            "subject": self.subject,
            "description": self.description,
        }
        if self.location:
            result["location"] = self.location
        if self.suggestion:
            result["suggestion"] = self.suggestion
        return result


@dataclass
class AnalysisResult:
    """Result of analyzing a project."""

    manifest_path: Path
    issues: list[Issue] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        """Return True if no issues were found."""
        return len(self.issues) == 0

    def to_dict(self) -> dict:
        """Convert the result to a dictionary for JSON serialization."""
        return {
            "manifest_path": str(self.manifest_path),
            "issues": [issue.to_dict() for issue in self.issues],
        }


# Default artifact patterns that should typically be excluded from builds.
# These are common repository artefacts that should not end up in wheels or sdists.
DEFAULT_SOURCE_EXCLUDE_PATTERNS: list[str] = [
    "tests",
    "docs",
    ".venv",
    "__pycache__",
    "*.egg-info",
    ".tox",
    ".mypy_cache",
    ".pytest_cache",
    "dist",
    "build",
    ".github",
    ".idea",
    ".vscode",
    ".vs",
    ".DS_Store",
    "*.pyc",
    "*.pyo",
    ".coverage",
    "htmlcov",
    ".ruff_cache",
]


@dataclass
class LeanConfig:
    """Configuration for py-lean.

    Patterns are determined by the following precedence:
    1. CLI --patterns (highest priority)
    2. tool.uv.build-backend.source-exclude from pyproject.toml
    3. Built-in defaults (DEFAULT_SOURCE_EXCLUDE_PATTERNS)
    """

    # Source exclude patterns to check for (defaults to DEFAULT_SOURCE_EXCLUDE_PATTERNS)
    patterns: list[str] = field(default_factory=list)

    def effective_patterns(self) -> list[str]:
        """Return the patterns to use, falling back to defaults if none configured."""
        if self.patterns:
            return self.patterns
        return list(DEFAULT_SOURCE_EXCLUDE_PATTERNS)
