"""Integration tests for the CLI."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path
from tempfile import TemporaryDirectory

from typer.testing import CliRunner

from py_lean_package.cli import app

runner = CliRunner()


class TestLintCommand:
    """Integration tests for the lint command."""

    def test_lint_clean_project(self) -> None:
        """Lint a project with no issues."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / "pyproject.toml"
            manifest.write_text(
                textwrap.dedent(
                    """
                    [build-system]
                    requires = ["uv_build"]
                    build-backend = "uv_build"

                    [project]
                    name = "test"

                    [tool.uv.build-backend]
                    source-exclude = ["tests"]
                    """
                )
            )
            (root / "tests").mkdir()

            result = runner.invoke(app, ["lint", "-m", str(manifest)])
            assert result.exit_code == 0
            assert "No issues found" in result.output

    def test_lint_finds_missing_source_exclude(self) -> None:
        """Lint should detect missing source-exclude patterns."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / "pyproject.toml"
            manifest.write_text(
                textwrap.dedent(
                    """
                    [build-system]
                    requires = ["uv_build"]
                    build-backend = "uv_build"

                    [project]
                    name = "test"
                    """
                )
            )
            (root / "tests").mkdir()
            (root / "docs").mkdir()

            result = runner.invoke(app, ["lint", "-m", str(manifest)])
            assert result.exit_code == 1
            assert "tests" in result.output
            assert "docs" in result.output

    def test_lint_skips_gitignored_artifacts(self) -> None:
        """Lint should skip artefacts that are already covered by .gitignore."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / "pyproject.toml"
            manifest.write_text(
                textwrap.dedent(
                    """
                    [build-system]
                    requires = ["uv_build"]
                    build-backend = "uv_build"

                    [project]
                    name = "test"
                    """
                )
            )
            (root / "tests").mkdir()
            (root / "docs").mkdir()
            (root / ".gitignore").write_text("tests\n")

            result = runner.invoke(app, ["lint", "-m", str(manifest)])
            # docs should be reported, tests should be skipped (gitignored)
            assert result.exit_code == 1
            assert "docs" in result.output
            assert "tests" not in result.output

    def test_lint_reads_source_exclude_patterns(self) -> None:
        """Lint should use source-exclude patterns when no CLI patterns provided."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / "pyproject.toml"
            manifest.write_text(
                textwrap.dedent(
                    """
                    [build-system]
                    requires = ["uv_build"]
                    build-backend = "uv_build"

                    [project]
                    name = "test"

                    [tool.uv.build-backend]
                    source-exclude = ["tests", "docs"]
                    """
                )
            )
            (root / "tests").mkdir()
            (root / "docs").mkdir()

            result = runner.invoke(app, ["lint", "-m", str(manifest)])
            # Both tests and docs are in source-exclude, so no issues
            assert result.exit_code == 0
            assert "No issues found" in result.output

    def test_lint_cli_patterns_override_source_exclude(self) -> None:
        """CLI --patterns should override source-exclude config."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / "pyproject.toml"
            manifest.write_text(
                textwrap.dedent(
                    """
                    [build-system]
                    requires = ["uv_build"]
                    build-backend = "uv_build"

                    [project]
                    name = "test"

                    [tool.uv.build-backend]
                    source-exclude = ["tests", "docs"]
                    """
                )
            )
            (root / "tests").mkdir()
            (root / "docs").mkdir()

            # CLI patterns override source-exclude — only benchmarks is checked
            result = runner.invoke(app, ["lint", "-m", str(manifest), "-p", "benchmarks/"])
            # No benchmarks directory exists, so no issues
            assert result.exit_code == 0
            assert "No issues found" in result.output

    def test_lint_json_output(self) -> None:
        """Lint should support JSON output."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / "pyproject.toml"
            manifest.write_text(
                textwrap.dedent(
                    """
                    [build-system]
                    requires = ["uv_build"]
                    build-backend = "uv_build"

                    [project]
                    name = "test"
                    """
                )
            )
            (root / "tests").mkdir()

            result = runner.invoke(app, ["lint", "-m", str(manifest), "--format", "json"])
            data = json.loads(result.output)
            assert "issues" in data
            assert len(data["issues"]) > 0

    def test_lint_requires_uv_build(self) -> None:
        """Lint should fail when the project does not use uv_build."""
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

            result = runner.invoke(app, ["lint", "-m", str(manifest)])
            assert result.exit_code == 1
            assert "uv_build" in result.output

    def test_lint_requires_uv_build_hatchling(self) -> None:
        """Lint should fail when the project uses hatchling instead of uv_build."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / "pyproject.toml"
            manifest.write_text(
                textwrap.dedent(
                    """
                    [build-system]
                    requires = ["hatchling"]
                    build-backend = "hatchling.build"

                    [project]
                    name = "test"
                    """
                )
            )
            (root / "tests").mkdir()

            result = runner.invoke(app, ["lint", "-m", str(manifest)])
            assert result.exit_code == 1
            assert "uv_build" in result.output


class TestCreateCommand:
    """Integration tests for the create command."""

    def test_create_adds_existing_patterns(self) -> None:
        """Create should add source-exclude patterns only for artefacts that exist in the repo."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / "pyproject.toml"
            manifest.write_text(
                textwrap.dedent(
                    """
                    [build-system]
                    requires = ["uv_build"]
                    build-backend = "uv_build"

                    [project]
                    name = "test"
                    """
                )
            )
            (root / "tests").mkdir()
            (root / "docs").mkdir()

            result = runner.invoke(app, ["create", "-m", str(manifest)])
            assert result.exit_code == 0

            content = manifest.read_text()
            assert "source-exclude" in content
            # Only existing artefacts should be added
            assert '"tests"' in content
            assert '"docs"' in content
            # .venv does not exist, so it should NOT be added
            assert '".venv"' not in content

    def test_create_skips_existing_patterns(self) -> None:
        """Create should not duplicate patterns already in source-exclude."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / "pyproject.toml"
            manifest.write_text(
                textwrap.dedent(
                    """
                    [build-system]
                    requires = ["uv_build"]
                    build-backend = "uv_build"

                    [project]
                    name = "test"

                    [tool.uv.build-backend]
                    source-exclude = ["tests"]
                    """
                )
            )
            (root / "tests").mkdir()

            result = runner.invoke(app, ["create", "-m", str(manifest)])
            assert result.exit_code == 0

            content = manifest.read_text()
            # tests should appear only once in source-exclude
            assert content.count('"tests"') == 1

    def test_create_dry_run(self) -> None:
        """Create with --dry-run should not modify the file."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / "pyproject.toml"
            manifest.write_text(
                textwrap.dedent(
                    """
                    [build-system]
                    requires = ["uv_build"]
                    build-backend = "uv_build"

                    [project]
                    name = "test"
                    """
                )
            )
            (root / "tests").mkdir()

            result = runner.invoke(app, ["create", "-m", str(manifest), "--dry-run"])
            assert result.exit_code == 0
            assert "dry-run" in result.output

            content = manifest.read_text()
            assert "source-exclude" not in content

    def test_create_merges_with_configured_patterns(self) -> None:
        """Create should merge configured patterns with built-in defaults."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / "pyproject.toml"
            manifest.write_text(
                textwrap.dedent(
                    """
                    [build-system]
                    requires = ["uv_build"]
                    build-backend = "uv_build"

                    [project]
                    name = "test"

                    [tool.uv.build-backend]
                    source-exclude = ["benchmarks"]
                    """
                )
            )
            (root / "tests").mkdir()
            (root / "docs").mkdir()
            (root / "benchmarks").mkdir()

            result = runner.invoke(app, ["create", "-m", str(manifest)])
            assert result.exit_code == 0

            content = manifest.read_text()
            # Configured pattern should be preserved
            assert '"benchmarks"' in content
            # Missing patterns for existing artefacts should be added
            assert '"tests"' in content
            assert '"docs"' in content

    def test_create_requires_uv_build(self) -> None:
        """Create should fail when the project does not use uv_build."""
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

            result = runner.invoke(app, ["create", "-m", str(manifest)])
            assert result.exit_code == 1
            assert "uv_build" in result.output


class TestUpdateCommand:
    """Integration tests for the update command."""

    def test_update_adds_existing_patterns(self) -> None:
        """Update should add source-exclude patterns only for artefacts that exist in the repo."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / "pyproject.toml"
            manifest.write_text(
                textwrap.dedent(
                    """
                    [build-system]
                    requires = ["uv_build"]
                    build-backend = "uv_build"

                    [project]
                    name = "test"
                    """
                )
            )
            (root / "tests").mkdir()
            (root / "docs").mkdir()

            result = runner.invoke(app, ["update", "-m", str(manifest)])
            assert result.exit_code == 0

            content = manifest.read_text()
            assert "source-exclude" in content
            # Only existing artefacts should be added
            assert '"tests"' in content
            assert '"docs"' in content
            # .venv does not exist, so it should NOT be added
            assert '".venv"' not in content

    def test_update_skips_existing_patterns(self) -> None:
        """Update should not duplicate patterns already in source-exclude."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / "pyproject.toml"
            manifest.write_text(
                textwrap.dedent(
                    """
                    [build-system]
                    requires = ["uv_build"]
                    build-backend = "uv_build"

                    [project]
                    name = "test"

                    [tool.uv.build-backend]
                    source-exclude = ["tests"]
                    """
                )
            )
            (root / "tests").mkdir()

            result = runner.invoke(app, ["update", "-m", str(manifest)])
            assert result.exit_code == 0

            content = manifest.read_text()
            # tests should appear only once in source-exclude
            assert content.count('"tests"') == 1

    def test_update_dry_run(self) -> None:
        """Update with --dry-run should not modify the file."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / "pyproject.toml"
            manifest.write_text(
                textwrap.dedent(
                    """
                    [build-system]
                    requires = ["uv_build"]
                    build-backend = "uv_build"

                    [project]
                    name = "test"
                    """
                )
            )
            (root / "tests").mkdir()

            result = runner.invoke(app, ["update", "-m", str(manifest), "--dry-run"])
            assert result.exit_code == 0
            assert "dry-run" in result.output

            content = manifest.read_text()
            assert "source-exclude" not in content

    def test_update_merges_with_configured_patterns(self) -> None:
        """Update should merge configured patterns with built-in defaults."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / "pyproject.toml"
            manifest.write_text(
                textwrap.dedent(
                    """
                    [build-system]
                    requires = ["uv_build"]
                    build-backend = "uv_build"

                    [project]
                    name = "test"

                    [tool.uv.build-backend]
                    source-exclude = ["benchmarks"]
                    """
                )
            )
            (root / "tests").mkdir()
            (root / "docs").mkdir()
            (root / "benchmarks").mkdir()

            result = runner.invoke(app, ["update", "-m", str(manifest)])
            assert result.exit_code == 0

            content = manifest.read_text()
            # Configured pattern should be preserved
            assert '"benchmarks"' in content
            # Missing patterns for existing artefacts should be added
            assert '"tests"' in content
            assert '"docs"' in content

    def test_update_requires_uv_build(self) -> None:
        """Update should fail when the project does not use uv_build."""
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

            result = runner.invoke(app, ["update", "-m", str(manifest)])
            assert result.exit_code == 1
            assert "uv_build" in result.output

    def test_lint_detects_toml_configs(self) -> None:
        """Lint should detect TOML config files not in source-exclude."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / "pyproject.toml"
            manifest.write_text(
                textwrap.dedent(
                    """
                    [build-system]
                    requires = ["uv_build"]
                    build-backend = "uv_build"

                    [project]
                    name = "test"
                    """
                )
            )
            (root / ".ruff.toml").write_text("line-length = 88\n")

            result = runner.invoke(app, ["lint", "-m", str(manifest)])
            assert result.exit_code == 1
            assert ".ruff.toml" in result.output

    def test_update_adds_toml_configs(self) -> None:
        """Update should add TOML config files to source-exclude."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / "pyproject.toml"
            manifest.write_text(
                textwrap.dedent(
                    """
                    [build-system]
                    requires = ["uv_build"]
                    build-backend = "uv_build"

                    [project]
                    name = "test"
                    """
                )
            )
            (root / ".ruff.toml").write_text("line-length = 88\n")

            result = runner.invoke(app, ["update", "-m", str(manifest)])
            assert result.exit_code == 0

            content = manifest.read_text()
            assert '".ruff.toml"' in content


class TestVersion:
    """Test the version flag."""

    def test_version_flag(self) -> None:
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "py-lean" in result.output


class TestHelp:
    """Test the help output."""

    def test_help(self) -> None:
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "py-lean" in result.output
        assert "lint" in result.output
        assert "create" in result.output
        assert "update" in result.output
