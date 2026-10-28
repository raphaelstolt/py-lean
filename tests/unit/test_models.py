"""Unit tests for the models module."""

from __future__ import annotations

import json
from pathlib import Path

from py_lean.models import (
    DEFAULT_SOURCE_EXCLUDE_PATTERNS,
    AnalysisResult,
    Issue,
    IssueType,
    LeanConfig,
    OutputFormat,
)


class TestIssue:
    """Tests for the Issue dataclass."""

    def test_to_dict_basic(self) -> None:
        issue = Issue(
            issue_type=IssueType.MISSING_SOURCE_EXCLUDE,
            subject="tests",
            description="Artefact 'tests' is not excluded.",
        )
        d = issue.to_dict()
        assert d["type"] == "missing_source_exclude"
        assert d["subject"] == "tests"
        assert "location" not in d
        assert "suggestion" not in d

    def test_to_dict_with_optional_fields(self) -> None:
        issue = Issue(
            issue_type=IssueType.MISSING_SOURCE_EXCLUDE,
            subject="tests",
            description="Not excluded.",
            location="pyproject.toml",
            suggestion="Add it.",
        )
        d = issue.to_dict()
        assert d["location"] == "pyproject.toml"
        assert d["suggestion"] == "Add it."


class TestAnalysisResult:
    """Tests for the AnalysisResult dataclass."""

    def test_is_clean_when_no_issues(self) -> None:
        result = AnalysisResult(manifest_path=Path("pyproject.toml"))
        assert result.is_clean is True

    def test_is_clean_when_has_issues(self) -> None:
        result = AnalysisResult(
            manifest_path=Path("pyproject.toml"),
            issues=[
                Issue(
                    issue_type=IssueType.MISSING_SOURCE_EXCLUDE,
                    subject="tests",
                    description="Not excluded.",
                )
            ],
        )
        assert result.is_clean is False

    def test_to_dict(self) -> None:
        result = AnalysisResult(
            manifest_path=Path("pyproject.toml"),
            issues=[
                Issue(
                    issue_type=IssueType.MISSING_SOURCE_EXCLUDE,
                    subject="tests",
                    description="Not excluded.",
                )
            ],
        )
        d = result.to_dict()
        assert d["manifest_path"] == "pyproject.toml"
        assert len(d["issues"]) == 1
        json.dumps(d)


class TestLeanConfig:
    """Tests for the LeanConfig dataclass."""

    def test_default_patterns_empty(self) -> None:
        config = LeanConfig()
        assert config.patterns == []

    def test_effective_patterns_uses_defaults(self) -> None:
        config = LeanConfig()
        effective = config.effective_patterns()
        assert "tests" in effective
        assert effective == DEFAULT_SOURCE_EXCLUDE_PATTERNS

    def test_effective_patterns_uses_custom(self) -> None:
        config = LeanConfig(patterns=["tests", "docs"])
        effective = config.effective_patterns()
        assert effective == ["tests", "docs"]



class TestOutputFormat:
    """Tests for OutputFormat enum."""

    def test_text_value(self) -> None:
        assert OutputFormat.TEXT.value == "text"

    def test_json_value(self) -> None:
        assert OutputFormat.JSON.value == "json"


class TestIssueType:
    """Tests for IssueType enum."""

    def test_missing_source_exclude(self) -> None:
        assert IssueType.MISSING_SOURCE_EXCLUDE.value == "missing_source_exclude"


class TestDefaultSourceExcludePatterns:
    """Tests for DEFAULT_SOURCE_EXCLUDE_PATTERNS."""

    def test_contains_common_patterns(self) -> None:
        assert "tests" in DEFAULT_SOURCE_EXCLUDE_PATTERNS
        assert "docs" in DEFAULT_SOURCE_EXCLUDE_PATTERNS
        assert "dist" in DEFAULT_SOURCE_EXCLUDE_PATTERNS
        assert "build" in DEFAULT_SOURCE_EXCLUDE_PATTERNS
        assert "__pycache__" in DEFAULT_SOURCE_EXCLUDE_PATTERNS

    def test_contains_glob_patterns(self) -> None:
        assert "*.egg-info" in DEFAULT_SOURCE_EXCLUDE_PATTERNS
        assert "*.pyc" in DEFAULT_SOURCE_EXCLUDE_PATTERNS
        assert "*.pyo" in DEFAULT_SOURCE_EXCLUDE_PATTERNS
