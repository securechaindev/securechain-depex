"""Unit tests for requirement file analyzers."""
from pathlib import Path
from tempfile import TemporaryDirectory

from app.domain.repo_analyzer.requirement_files.base_analyzer import (
    RequirementFileAnalyzer,
)
from app.domain.repo_analyzer.requirement_files.package_json_analyzer import (
    PackageJsonAnalyzer,
)
from app.domain.repo_analyzer.requirement_files.pyproject_toml_analyzer import (
    PyprojectTomlAnalyzer,
)
from app.domain.repo_analyzer.requirement_files.requirements_txt_analyzer import (
    RequirementsTxtAnalyzer,
)


class TestRequirementsTxtAnalyzer:
    """Test suite for RequirementsTxtAnalyzer."""

    def test_parse_simple_requirements(self):
        """Test parsing simple requirements.txt file."""
        analyzer = RequirementsTxtAnalyzer()

        with TemporaryDirectory() as tmpdir:
            req_file = Path(tmpdir) / "requirements.txt"
            req_file.write_text("fastapi>=0.100.0\nuvicorn==0.35.0\n")

            result = analyzer._parse_file(tmpdir, "requirements.txt")
            assert "fastapi" in result
            assert "uvicorn" in result

    def test_parse_requirements_with_comments(self):
        """Test parsing requirements.txt with comments."""
        analyzer = RequirementsTxtAnalyzer()

        with TemporaryDirectory() as tmpdir:
            req_file = Path(tmpdir) / "requirements.txt"
            req_file.write_text("fastapi>=0.100.0\n# This is a comment\nuvicorn==0.35.0\n")

            result = analyzer._parse_file(tmpdir, "requirements.txt")
            assert "fastapi" in result
            assert "uvicorn" in result

    def test_parse_requirements_with_extras(self):
        """Test parsing requirements with extras."""
        analyzer = RequirementsTxtAnalyzer()

        with TemporaryDirectory() as tmpdir:
            req_file = Path(tmpdir) / "requirements.txt"
            req_file.write_text("fastapi[all]>=0.100.0\n")

            result = analyzer._parse_file(tmpdir, "requirements.txt")
            assert "fastapi" in result


class TestPackageJsonAnalyzer:
    """Test suite for PackageJsonAnalyzer."""

    def test_parse_package_json(self):
        """Test parsing package.json file."""
        analyzer = PackageJsonAnalyzer()

        with TemporaryDirectory() as tmpdir:
            pkg_file = Path(tmpdir) / "package.json"
            pkg_file.write_text('{"dependencies": {"express": "^4.18.0", "react": "^18.0.0"}}')

            result = analyzer._parse_file(tmpdir, "package.json")
            assert "express" in result
            assert "react" in result

    def test_parse_package_json_no_dependencies(self):
        """Test parsing package.json without dependencies."""
        analyzer = PackageJsonAnalyzer()

        with TemporaryDirectory() as tmpdir:
            pkg_file = Path(tmpdir) / "package.json"
            pkg_file.write_text('{"name": "test-package"}')

            result = analyzer._parse_file(tmpdir, "package.json")
            assert isinstance(result, dict)
            assert len(result) == 0


class TestPyprojectTomlAnalyzer:
    """Test suite for PyprojectTomlAnalyzer."""

    def test_parse_pyproject_toml(self):
        """Test parsing pyproject.toml file."""
        analyzer = PyprojectTomlAnalyzer()

        with TemporaryDirectory() as tmpdir:
            toml_file = Path(tmpdir) / "pyproject.toml"
            toml_content = """
[project]
dependencies = [
    "fastapi>=0.100.0",
    "uvicorn==0.35.0",
]
"""
            toml_file.write_text(toml_content)

            result = analyzer._parse_file(tmpdir, "pyproject.toml")
            assert "fastapi" in result
            assert "uvicorn" in result

    def test_parse_pyproject_toml_no_dependencies(self):
        """Test parsing pyproject.toml without dependencies."""
        analyzer = PyprojectTomlAnalyzer()

        with TemporaryDirectory() as tmpdir:
            toml_file = Path(tmpdir) / "pyproject.toml"
            toml_file.write_text("[project]\nname = 'test'\n")

            result = analyzer._parse_file(tmpdir, "pyproject.toml")
            assert isinstance(result, dict)


class TestPythonVersionValidation:
    """Test suite for Python version validation in base analyzer."""

    def test_compatible_version_greater_than_3(self):
        """Test that >= 3 is compatible."""
        assert RequirementFileAnalyzer.is_compatible_python_version('>= "3"')

    def test_compatible_version_greater_than_2(self):
        """Test that > 2 is compatible."""
        assert RequirementFileAnalyzer.is_compatible_python_version('> "2"')

    def test_incompatible_version_equals_39(self):
        """Test that == 3.9 is incompatible (below minimum 3.13)."""
        assert not RequirementFileAnalyzer.is_compatible_python_version('== "3.9"')

    def test_compatible_version_greater_equal_39(self):
        """Test that >= 3.9 is compatible."""
        assert RequirementFileAnalyzer.is_compatible_python_version('>= "3.9"')

    def test_compatible_version_greater_equal_310(self):
        """Test that >= 3.10 is compatible."""
        assert RequirementFileAnalyzer.is_compatible_python_version('>= "3.10"')

    def test_compatible_version_less_equal_3(self):
        """Test that <= 3 is compatible."""
        assert RequirementFileAnalyzer.is_compatible_python_version('<= "3"')

    def test_incompatible_version_equals_2(self):
        """Test that == 2.7 is incompatible."""
        assert not RequirementFileAnalyzer.is_compatible_python_version('== "2.7"')

    def test_incompatible_version_less_than_3(self):
        """Test that < 3 is incompatible."""
        assert not RequirementFileAnalyzer.is_compatible_python_version('< "3"')

    def test_compatible_version_equals_313(self):
        """Test that == 3.13 is compatible."""
        assert RequirementFileAnalyzer.is_compatible_python_version('== "3.13"')

    def test_compatible_no_version_marker(self):
        """Test that strings without version markers are compatible."""
        assert RequirementFileAnalyzer.is_compatible_python_version('some_marker')

    def test_should_skip_dependency_with_extra(self):
        """Test that dependencies with extras are skipped."""
        dependency = ['package', 'extra == "dev"']
        assert RequirementFileAnalyzer.should_skip_dependency(dependency)

    def test_should_skip_dependency_incompatible_python(self):
        """Test that dependencies with incompatible Python versions are skipped."""
        dependency = ['package', 'python_version == "2.7"']
        assert RequirementFileAnalyzer.should_skip_dependency(dependency)

    def test_should_not_skip_dependency_compatible_python(self):
        """Test that dependencies with compatible Python versions are not skipped."""
        dependency = ['package', 'python_version >= "3.9"']
        assert not RequirementFileAnalyzer.should_skip_dependency(dependency)

    def test_should_not_skip_dependency_no_marker(self):
        """Test that dependencies without markers are not skipped."""
        dependency = ['package']
        assert not RequirementFileAnalyzer.should_skip_dependency(dependency)
