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
    @pytest.mark.asyncio
    async def test_analyze_success(self):
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
        analyzer = RequirementsTxtAnalyzer()
        requirement_files = {}

        with TemporaryDirectory() as tmpdir:
            req_file = Path(tmpdir) / "requirements.txt"
            req_file.write_text("uvicorn==0.35.0\n")

            result = await analyzer.analyze(
                requirement_files, tmpdir, "/master/requirements.txt"
            )

            assert "requirements.txt" in result
            assert "uvicorn" in result["requirements.txt"]["packages"]

    @pytest.mark.asyncio
    async def test_analyze_with_main_prefix(self):
        analyzer = RequirementsTxtAnalyzer()
        requirement_files = {}

        with TemporaryDirectory() as tmpdir:
            req_file = Path(tmpdir) / "requirements.txt"
            req_file.write_text("pydantic>=2.0.0\n")

            result = await analyzer.analyze(
                requirement_files, tmpdir, "/main/requirements.txt"
            )

            assert "requirements.txt" in result
            assert "pydantic" in result["requirements.txt"]["packages"]

    @pytest.mark.asyncio
    async def test_analyze_file_not_found(self):
        analyzer = RequirementsTxtAnalyzer()
        requirement_files = {}

        with TemporaryDirectory() as tmpdir:
            result = await analyzer.analyze(
                requirement_files, tmpdir, "nonexistent.txt"
            )

            assert "nonexistent.txt" in result
            assert result["nonexistent.txt"]["manager"] == "PyPI"
            assert result["nonexistent.txt"]["packages"] == {}

    def test_normalize_filename(self):
        analyzer = RequirementsTxtAnalyzer()

        assert analyzer._normalize_filename("/master/requirements.txt") == "requirements.txt"
        assert analyzer._normalize_filename("/main/package.json") == "package.json"
        assert analyzer._normalize_filename("simple.txt") == "simple.txt"

    def test_normalize_version_without_operator(self):
        analyzer = RequirementsTxtAnalyzer()

        assert analyzer._normalize_version("1.0.0") == "== 1.0.0"
        assert analyzer._normalize_version("2.3.4") == "== 2.3.4"

    def test_normalize_version_with_operator(self):
        analyzer = RequirementsTxtAnalyzer()

        assert analyzer._normalize_version(">=1.0.0") == ">=1.0.0"
        assert analyzer._normalize_version("<2.0.0") == "<2.0.0"
        assert analyzer._normalize_version("==1.2.3") == "==1.2.3"

    def test_normalize_version_partial(self):
        analyzer = RequirementsTxtAnalyzer()

        # Partial versions (not 2 dots) should remain unchanged
        assert analyzer._normalize_version("1.0") == "1.0"
        assert analyzer._normalize_version("2") == "2"

    def test_clean_dependency_name(self):
        assert RequirementFileAnalyzer.clean_dependency_name("package") == "package"
        assert RequirementFileAnalyzer.clean_dependency_name("(package)") == "package"
        assert RequirementFileAnalyzer.clean_dependency_name("pack age") == "package"
        assert RequirementFileAnalyzer.clean_dependency_name("'package'") == "package"
        assert RequirementFileAnalyzer.clean_dependency_name("(pack age)") == "package"
