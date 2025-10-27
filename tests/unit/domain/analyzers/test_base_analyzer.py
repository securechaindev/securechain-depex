"""Unit tests for base analyzer functionality."""
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from app.domain.repo_analyzer.requirement_files.base_analyzer import (
    RequirementFileAnalyzer,
)
from app.domain.repo_analyzer.requirement_files.requirements_txt_analyzer import (
    RequirementsTxtAnalyzer,
)


class TestBaseAnalyzer:
    """Test suite for RequirementFileAnalyzer base class."""

    @pytest.mark.asyncio
    async def test_analyze_success(self):
        """Test successful analysis of a requirement file."""
        analyzer = RequirementsTxtAnalyzer()
        requirement_files = {}

        with TemporaryDirectory() as tmpdir:
            req_file = Path(tmpdir) / "requirements.txt"
            req_file.write_text("fastapi>=0.100.0\n")

            result = await analyzer.analyze(
                requirement_files, tmpdir, "requirements.txt"
            )

            assert "requirements.txt" in result
            assert result["requirements.txt"]["manager"] == "PyPI"
            assert "packages" in result["requirements.txt"]
            assert "fastapi" in result["requirements.txt"]["packages"]

    @pytest.mark.asyncio
    async def test_analyze_with_branch_prefix(self):
        """Test analysis with master/main branch prefix in filename."""
        analyzer = RequirementsTxtAnalyzer()
        requirement_files = {}

        with TemporaryDirectory() as tmpdir:
            req_file = Path(tmpdir) / "requirements.txt"
            req_file.write_text("uvicorn==0.35.0\n")

            result = await analyzer.analyze(
                requirement_files, tmpdir, "/master/requirements.txt"
            )

            # Should normalize filename by removing /master/
            assert "requirements.txt" in result
            assert "uvicorn" in result["requirements.txt"]["packages"]

    @pytest.mark.asyncio
    async def test_analyze_with_main_prefix(self):
        """Test analysis with main branch prefix in filename."""
        analyzer = RequirementsTxtAnalyzer()
        requirement_files = {}

        with TemporaryDirectory() as tmpdir:
            req_file = Path(tmpdir) / "requirements.txt"
            req_file.write_text("pydantic>=2.0.0\n")

            result = await analyzer.analyze(
                requirement_files, tmpdir, "/main/requirements.txt"
            )

            # Should normalize filename by removing /main/
            assert "requirements.txt" in result
            assert "pydantic" in result["requirements.txt"]["packages"]

    @pytest.mark.asyncio
    async def test_analyze_file_not_found(self):
        """Test analysis when file doesn't exist - should handle gracefully."""
        analyzer = RequirementsTxtAnalyzer()
        requirement_files = {}

        with TemporaryDirectory() as tmpdir:
            result = await analyzer.analyze(
                requirement_files, tmpdir, "nonexistent.txt"
            )

            # Should create entry but with empty packages
            assert "nonexistent.txt" in result
            assert result["nonexistent.txt"]["manager"] == "PyPI"
            assert result["nonexistent.txt"]["packages"] == {}

    def test_normalize_filename(self):
        """Test filename normalization."""
        analyzer = RequirementsTxtAnalyzer()

        assert analyzer._normalize_filename("/master/requirements.txt") == "requirements.txt"
        assert analyzer._normalize_filename("/main/package.json") == "package.json"
        assert analyzer._normalize_filename("simple.txt") == "simple.txt"

    def test_normalize_version_without_operator(self):
        """Test version normalization without operator."""
        analyzer = RequirementsTxtAnalyzer()

        # Version with 2 dots and no operator should get "== " prefix
        assert analyzer._normalize_version("1.0.0") == "== 1.0.0"
        assert analyzer._normalize_version("2.3.4") == "== 2.3.4"

    def test_normalize_version_with_operator(self):
        """Test version normalization with operator."""
        analyzer = RequirementsTxtAnalyzer()

        # Versions with operators should remain unchanged
        assert analyzer._normalize_version(">=1.0.0") == ">=1.0.0"
        assert analyzer._normalize_version("<2.0.0") == "<2.0.0"
        assert analyzer._normalize_version("==1.2.3") == "==1.2.3"

    def test_normalize_version_partial(self):
        """Test version normalization with partial versions."""
        analyzer = RequirementsTxtAnalyzer()

        # Partial versions (not 2 dots) should remain unchanged
        assert analyzer._normalize_version("1.0") == "1.0"
        assert analyzer._normalize_version("2") == "2"

    def test_clean_dependency_name(self):
        """Test cleaning dependency names."""
        assert RequirementFileAnalyzer.clean_dependency_name("package") == "package"
        assert RequirementFileAnalyzer.clean_dependency_name("(package)") == "package"
        assert RequirementFileAnalyzer.clean_dependency_name("pack age") == "package"
        assert RequirementFileAnalyzer.clean_dependency_name("'package'") == "package"
        assert RequirementFileAnalyzer.clean_dependency_name("(pack age)") == "package"
