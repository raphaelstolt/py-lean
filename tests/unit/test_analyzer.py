"""Unit tests for the analyzer module."""

from __future__ import annotations

import textwrap
from pathlib import Path
from tempfile import TemporaryDirectory

import tomlkit

from py_lean_package.analyzer import (
    _artifact_exists,
    _get_source_exclude_patterns,
    _normalize_pattern,
    _pattern_covers,
    check_build_system,
    detect_missing_source_exclude,
    detect_toml_configs,
    is_gitignored,
    load_config,
    load_manifest,
    read_gitignore,
)
from py_lean_package.models import DEFAULT_SOURCE_EXCLUDE_PATTERNS, LeanConfig


def _gitignore_entries(root: Path) -> list[str]:
    """Helper: read gitignore entries from a test root."""
    return read_gitignore(root)


class TestNormalizePattern:
    """Tests for _normalize_pattern."""

    def test_strips_trailing_slash(self) -> None:
        assert _normalize_pattern("tests/") == "tests"

    def test_strips_multiple_trailing_slashes(self) -> None:
        assert _normalize_pattern("tests//") == "tests"

    def test_no_change_without_trailing_slash(self) -> None:
        assert _normalize_pattern("tests") == "tests"

    def test_preserves_leading_slash(self) -> None:
        assert _normalize_pattern("/tests/") == "/tests"

    def test_glob_pattern(self) -> None:
        assert _normalize_pattern("*.egg-info") == "*.egg-info"


class TestLoadManifest:
    """Tests for load_manifest."""

    def test_load_valid_manifest(self) -> None:
        with TemporaryDirectory() as tmp:
            manifest = Path(tmp) / "pyproject.toml"
            manifest.write_text('[project]\nname = "test"\n')
            doc = load_manifest(manifest)
            assert doc["project"]["name"] == "test"

    def test_missing_manifest_raises(self) -> None:
        with TemporaryDirectory() as tmp:
            manifest = Path(tmp) / "pyproject.toml"
            try:
                load_manifest(manifest)
                raise AssertionError("Expected FileNotFoundError")
            except FileNotFoundError:
                pass


class TestCheckBuildSystem:
    """Tests for check_build_system."""

    def test_uv_build_configured(self) -> None:
        content = textwrap.dedent(
            """
            [build-system]
            requires = ["uv_build"]
            build-backend = "uv_build"
            """
        )
        doc = tomlkit.parse(content)
        assert check_build_system(doc) is True

    def test_no_build_system_section(self) -> None:
        doc = tomlkit.parse('[project]\nname = "test"')
        assert check_build_system(doc) is False

    def test_hatchling_backend(self) -> None:
        content = textwrap.dedent(
            """
            [build-system]
            requires = ["hatchling"]
            build-backend = "hatchling.build"
            """
        )
        doc = tomlkit.parse(content)
        assert check_build_system(doc) is False

    def test_setuptools_backend(self) -> None:
        content = textwrap.dedent(
            """
            [build-system]
            requires = ["setuptools"]
            build-backend = "setuptools.build_meta"
            """
        )
        doc = tomlkit.parse(content)
        assert check_build_system(doc) is False

    def test_empty_build_system(self) -> None:
        doc = tomlkit.parse("[build-system]")
        assert check_build_system(doc) is False

    def test_missing_backend_key(self) -> None:
        content = textwrap.dedent(
            """
            [build-system]
            requires = ["uv_build"]
            """
        )
        doc = tomlkit.parse(content)
        assert check_build_system(doc) is False

    def test_missing_requires_key(self) -> None:
        content = textwrap.dedent(
            """
            [build-system]
            build-backend = "uv_build"
            """
        )
        doc = tomlkit.parse(content)
        assert check_build_system(doc) is False

    def test_uv_build_in_requires_with_version(self) -> None:
        content = textwrap.dedent(
            """
            [build-system]
            requires = ["uv_build>=0.5.0"]
            build-backend = "uv_build"
            """
        )
        doc = tomlkit.parse(content)
        assert check_build_system(doc) is True


class TestGetSourceExcludePatterns:
    """Tests for _get_source_exclude_patterns."""

    def test_empty_manifest(self) -> None:
        doc = tomlkit.parse("")
        assert _get_source_exclude_patterns(doc) == []

    def test_no_tool_section(self) -> None:
        doc = tomlkit.parse('[project]\nname = "test"')
        assert _get_source_exclude_patterns(doc) == []

    def test_no_uv_section(self) -> None:
        doc = tomlkit.parse('[tool.ruff]\ntarget-version = "py311"')
        assert _get_source_exclude_patterns(doc) == []

    def test_source_exclude_patterns(self) -> None:
        content = textwrap.dedent(
            """
            [project]
            name = "test"

            [tool.uv.build-backend]
            source-exclude = ["tests", "docs"]
            """
        )
        doc = tomlkit.parse(content)
        patterns = _get_source_exclude_patterns(doc)
        assert "tests" in patterns
        assert "docs" in patterns


class TestPatternCovers:
    """Tests for _pattern_covers."""

    def test_exact_match(self) -> None:
        assert _pattern_covers("tests", "tests") is True

    def test_glob_match(self) -> None:
        assert _pattern_covers("tests", "test*") is True

    def test_parent_directory(self) -> None:
        assert _pattern_covers("tests/unit", "tests") is True

    def test_no_match(self) -> None:
        assert _pattern_covers("docs", "tests") is False

    def test_wildcard_match(self) -> None:
        assert _pattern_covers("*.egg-info", "*.egg-info") is True

    def test_trailing_slash_on_pattern(self) -> None:
        assert _pattern_covers("tests/", "tests") is True

    def test_trailing_slash_on_exclude(self) -> None:
        assert _pattern_covers("tests", "tests/") is True

    def test_trailing_slash_on_both(self) -> None:
        assert _pattern_covers("tests/", "tests/") is True


class TestArtifactExists:
    """Tests for _artifact_exists."""

    def test_directory_exists(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "tests").mkdir()
            assert _artifact_exists(root, "tests") is True

    def test_directory_not_exists(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            assert _artifact_exists(root, "tests") is False

    def test_glob_pattern_matches(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "mypackage.egg-info").mkdir()
            assert _artifact_exists(root, "*.egg-info") is True

    def test_glob_pattern_no_match(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            assert _artifact_exists(root, "*.egg-info") is False

    def test_trailing_slash_directory_exists(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "tests").mkdir()
            assert _artifact_exists(root, "tests/") is True


class TestReadGitignore:
    """Tests for read_gitignore."""

    def test_no_gitignore_file(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            assert read_gitignore(root) == []

    def test_empty_gitignore(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".gitignore").write_text("")
            assert read_gitignore(root) == []

    def test_parses_simple_patterns(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".gitignore").write_text("__pycache__\n*.pyc\n.venv\n")
            patterns = read_gitignore(root)
            assert "__pycache__" in patterns
            assert "*.pyc" in patterns
            assert ".venv" in patterns

    def test_skips_comments(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".gitignore").write_text("# This is a comment\n.venv\n")
            patterns = read_gitignore(root)
            assert patterns == [".venv"]

    def test_skips_empty_lines(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".gitignore").write_text(".venv\n\n\n__pycache__\n")
            patterns = read_gitignore(root)
            assert patterns == [".venv", "__pycache__"]

    def test_skips_negation_patterns(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".gitignore").write_text("*.log\n!important.log\n.venv\n")
            patterns = read_gitignore(root)
            assert "*.log" in patterns
            assert "!important.log" not in patterns
            assert ".venv" in patterns

    def test_strips_leading_slash(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".gitignore").write_text("/build/\n/dist\n")
            patterns = read_gitignore(root)
            assert "build" in patterns
            assert "dist" in patterns

    def test_strips_trailing_slash(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".gitignore").write_text("tests/\ndocs/\n")
            patterns = read_gitignore(root)
            assert "tests" in patterns
            assert "docs" in patterns


class TestIsGitignored:
    """Tests for is_gitignored."""

    def test_direct_match(self) -> None:
        assert is_gitignored("tests", ["tests", "docs"]) is True

    def test_no_match(self) -> None:
        assert is_gitignored("benchmarks", ["tests", "docs"]) is False

    def test_glob_match(self) -> None:
        assert is_gitignored("app.egg-info", ["*.egg-info"]) is True

    def test_empty_entries(self) -> None:
        assert is_gitignored("tests", []) is False

    def test_pattern_with_trailing_slash(self) -> None:
        assert is_gitignored("tests/", ["tests"]) is True


class TestDetectMissingSourceExclude:
    """Tests for detect_missing_source_exclude."""

    def test_detects_missing_exclude(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / "pyproject.toml"
            manifest.write_text(
                textwrap.dedent(
                    """
                    [project]
                    name = "test"
                    """
                )
            )
            (root / "tests").mkdir()
            (root / "docs").mkdir()

            doc = load_manifest(manifest)
            config = LeanConfig(patterns=["tests", "docs"])
            issues = detect_missing_source_exclude(doc, root, config)

            subjects = [i.subject for i in issues]
            assert "tests" in subjects
            assert "docs" in subjects

    def test_no_issue_when_excluded(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / "pyproject.toml"
            manifest.write_text(
                textwrap.dedent(
                    """
                    [project]
                    name = "test"

                    [tool.uv.build-backend]
                    source-exclude = ["tests", "docs"]
                    """
                )
            )
            (root / "tests").mkdir()
            (root / "docs").mkdir()

            doc = load_manifest(manifest)
            config = LeanConfig(patterns=["tests", "docs"])
            issues = detect_missing_source_exclude(doc, root, config)
            assert len(issues) == 0

    def test_no_issue_when_artifact_missing(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / "pyproject.toml"
            manifest.write_text(
                textwrap.dedent(
                    """
                    [project]
                    name = "test"
                    """
                )
            )

            doc = load_manifest(manifest)
            config = LeanConfig(patterns=["tests", "docs"])
            issues = detect_missing_source_exclude(doc, root, config)
            assert len(issues) == 0

    def test_partial_exclude(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / "pyproject.toml"
            manifest.write_text(
                textwrap.dedent(
                    """
                    [project]
                    name = "test"

                    [tool.uv.build-backend]
                    source-exclude = ["tests"]
                    """
                )
            )
            (root / "tests").mkdir()
            (root / "docs").mkdir()

            doc = load_manifest(manifest)
            config = LeanConfig(patterns=["tests", "docs"])
            issues = detect_missing_source_exclude(doc, root, config)

            # Only docs should be reported as missing
            assert len(issues) == 1
            assert issues[0].subject == "docs"

    def test_skips_gitignored_artifacts(self) -> None:
        """Artefacts covered by .gitignore should not be reported as missing."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / "pyproject.toml"
            manifest.write_text(
                textwrap.dedent(
                    """
                    [project]
                    name = "test"
                    """
                )
            )
            (root / "tests").mkdir()
            (root / "docs").mkdir()
            (root / ".gitignore").write_text("tests\n")

            doc = load_manifest(manifest)
            config = LeanConfig(patterns=["tests", "docs"])
            gitignore = _gitignore_entries(root)
            issues = detect_missing_source_exclude(doc, root, config, gitignore)

            # tests is gitignored, so only docs should be reported
            assert len(issues) == 1
            assert issues[0].subject == "docs"

    def test_gitignored_via_glob(self) -> None:
        """Glob patterns in .gitignore should match artefacts."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / "pyproject.toml"
            manifest.write_text(
                textwrap.dedent(
                    """
                    [project]
                    name = "test"
                    """
                )
            )
            (root / "mypackage.egg-info").mkdir()
            (root / ".gitignore").write_text("*.egg-info\n")

            doc = load_manifest(manifest)
            config = LeanConfig(patterns=["*.egg-info"])
            gitignore = _gitignore_entries(root)
            issues = detect_missing_source_exclude(doc, root, config, gitignore)

            # *.egg-info is covered by .gitignore
            assert len(issues) == 0

    def test_gitignore_with_leading_slash(self) -> None:
        """Leading / in .gitignore should be stripped and still match."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / "pyproject.toml"
            manifest.write_text(
                textwrap.dedent(
                    """
                    [project]
                    name = "test"
                    """
                )
            )
            (root / "build").mkdir()
            (root / ".gitignore").write_text("/build/\n")

            doc = load_manifest(manifest)
            config = LeanConfig(patterns=["build"])
            gitignore = _gitignore_entries(root)
            issues = detect_missing_source_exclude(doc, root, config, gitignore)

            assert len(issues) == 0


class TestLoadConfig:
    """Tests for load_config precedence logic."""

    def test_cli_patterns_override_all(self) -> None:
        """CLI --patterns should completely override source-exclude config."""
        content = textwrap.dedent(
            """
            [project]
            name = "test"

            [tool.uv.build-backend]
            source-exclude = ["tests", "docs"]
            """
        )
        doc = tomlkit.parse(content)
        config = load_config(manifest=doc, patterns=["benchmarks"])
        assert config.effective_patterns() == ["benchmarks"]

    def test_source_exclude_used_when_no_cli_patterns(self) -> None:
        """source-exclude patterns should be used when CLI provides none."""
        content = textwrap.dedent(
            """
            [project]
            name = "test"

            [tool.uv.build-backend]
            source-exclude = ["tests", "docs", "benchmarks"]
            """
        )
        doc = tomlkit.parse(content)
        config = load_config(manifest=doc, patterns=None)
        assert config.effective_patterns() == ["tests", "docs", "benchmarks"]

    def test_defaults_used_when_no_config(self) -> None:
        """DEFAULT_SOURCE_EXCLUDE_PATTERNS should be used when nothing is configured."""
        doc = tomlkit.parse('[project]\nname = "test"')
        config = load_config(manifest=doc, patterns=None)
        assert config.effective_patterns() == DEFAULT_SOURCE_EXCLUDE_PATTERNS

    def test_no_manifest_uses_defaults(self) -> None:
        """When no manifest is provided, defaults should be used."""
        config = load_config(manifest=None, patterns=None)
        assert config.effective_patterns() == DEFAULT_SOURCE_EXCLUDE_PATTERNS

    def test_empty_source_exclude_uses_defaults(self) -> None:
        """Empty source-exclude should fall back to defaults."""
        content = textwrap.dedent(
            """
            [project]
            name = "test"

            [tool.uv.build-backend]
            source-exclude = []
            """
        )
        doc = tomlkit.parse(content)
        config = load_config(manifest=doc, patterns=None)
        assert config.effective_patterns() == DEFAULT_SOURCE_EXCLUDE_PATTERNS

    def test_cli_patterns_normalize_trailing_slash(self) -> None:
        """CLI patterns with trailing slashes should be normalized."""
        config = load_config(manifest=None, patterns=["tests/", "docs/"])
        assert config.effective_patterns() == ["tests", "docs"]

    def test_source_exclude_normalizes_trailing_slash(self) -> None:
        """Source-exclude patterns with trailing slashes should be normalized."""
        content = textwrap.dedent(
            """
            [project]
            name = "test"

            [tool.uv.build-backend]
            source-exclude = ["tests/", "docs/"]
            """
        )
        doc = tomlkit.parse(content)
        config = load_config(manifest=doc, patterns=None)
        assert config.effective_patterns() == ["tests", "docs"]


class TestDetectTomlConfigs:
    """Tests for detect_toml_configs."""

    def test_no_toml_files(self) -> None:
        """No issues when no TOML files exist."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / "pyproject.toml"
            manifest.write_text(
                textwrap.dedent(
                    """
                    [project]
                    name = "test"
                    """
                )
            )
            doc = load_manifest(manifest)
            issues = detect_toml_configs(doc, root)
            assert len(issues) == 0

    def test_only_pyproject_toml(self) -> None:
        """pyproject.toml should be ignored."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / "pyproject.toml"
            manifest.write_text(
                textwrap.dedent(
                    """
                    [project]
                    name = "test"
                    """
                )
            )
            doc = load_manifest(manifest)
            issues = detect_toml_configs(doc, root)
            assert len(issues) == 0

    def test_detects_single_toml_config(self) -> None:
        """A single TOML config file should be reported."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / "pyproject.toml"
            manifest.write_text(
                textwrap.dedent(
                    """
                    [project]
                    name = "test"
                    """
                )
            )
            (root / ".ruff.toml").write_text("line-length = 88\n")
            doc = load_manifest(manifest)
            issues = detect_toml_configs(doc, root)
            assert len(issues) == 1
            assert issues[0].subject == ".ruff.toml"

    def test_detects_multiple_toml_configs(self) -> None:
        """Multiple TOML config files should all be reported."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / "pyproject.toml"
            manifest.write_text(
                textwrap.dedent(
                    """
                    [project]
                    name = "test"
                    """
                )
            )
            (root / ".ruff.toml").write_text("line-length = 88\n")
            (root / ".mypy.toml").write_text("[mypy]\nstrict = true\n")
            doc = load_manifest(manifest)
            issues = detect_toml_configs(doc, root)
            assert len(issues) == 2
            subjects = [i.subject for i in issues]
            assert ".ruff.toml" in subjects
            assert ".mypy.toml" in subjects

    def test_skips_excluded_toml_config(self) -> None:
        """TOML configs already in source-exclude should be skipped."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / "pyproject.toml"
            manifest.write_text(
                textwrap.dedent(
                    """
                    [project]
                    name = "test"

                    [tool.uv.build-backend]
                    source-exclude = [".ruff.toml"]
                    """
                )
            )
            (root / ".ruff.toml").write_text("line-length = 88\n")
            doc = load_manifest(manifest)
            issues = detect_toml_configs(doc, root)
            assert len(issues) == 0

    def test_skips_gitignored_toml_config(self) -> None:
        """TOML configs covered by .gitignore should be skipped."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / "pyproject.toml"
            manifest.write_text(
                textwrap.dedent(
                    """
                    [project]
                    name = "test"
                    """
                )
            )
            (root / ".ruff.toml").write_text("line-length = 88\n")
            (root / ".gitignore").write_text(".ruff.toml\n")
            doc = load_manifest(manifest)
            gitignore = _gitignore_entries(root)
            issues = detect_toml_configs(doc, root, gitignore)
            assert len(issues) == 0

    def test_glob_pattern_covers_toml_config(self) -> None:
        """A glob pattern in source-exclude should cover TOML configs."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / "pyproject.toml"
            manifest.write_text(
                textwrap.dedent(
                    """
                    [project]
                    name = "test"

                    [tool.uv.build-backend]
                    source-exclude = ["*.toml"]
                    """
                )
            )
            (root / ".ruff.toml").write_text("line-length = 88\n")
            doc = load_manifest(manifest)
            issues = detect_toml_configs(doc, root)
            assert len(issues) == 0

    def test_non_dotfile_toml(self) -> None:
        """Non-dotfile TOML configs should also be detected."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / "pyproject.toml"
            manifest.write_text(
                textwrap.dedent(
                    """
                    [project]
                    name = "test"
                    """
                )
            )
            (root / "ruff.toml").write_text("line-length = 88\n")
            doc = load_manifest(manifest)
            issues = detect_toml_configs(doc, root)
            assert len(issues) == 1
            assert issues[0].subject == "ruff.toml"

    def test_skips_toml_directories(self) -> None:
        """TOML directories should be skipped, only files are checked."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / "pyproject.toml"
            manifest.write_text(
                textwrap.dedent(
                    """
                    [project]
                    name = "test"
                    """
                )
            )
            (root / "config.toml").mkdir()
            doc = load_manifest(manifest)
            issues = detect_toml_configs(doc, root)
            assert len(issues) == 0

    def test_toml_in_subdirectory_ignored(self) -> None:
        """TOML files in subdirectories should be ignored."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / "pyproject.toml"
            manifest.write_text(
                textwrap.dedent(
                    """
                    [project]
                    name = "test"
                    """
                )
            )
            (root / "subdir").mkdir()
            (root / "subdir" / ".ruff.toml").write_text("line-length = 88\n")
            doc = load_manifest(manifest)
            issues = detect_toml_configs(doc, root)
            assert len(issues) == 0
