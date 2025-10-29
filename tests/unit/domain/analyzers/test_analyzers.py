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
    def test_parse_simple_requirements(self):
        analyzer = RequirementsTxtAnalyzer()

        with TemporaryDirectory() as tmpdir:
            req_file = Path(tmpdir) / "requirements.txt"
            req_file.write_text("fastapi>=0.100.0\nuvicorn==0.35.0\n")

            result = analyzer.parse_file(tmpdir, "requirements.txt")
            assert "fastapi" in result
            assert "uvicorn" in result

    def test_parse_requirements_with_comments(self):
        analyzer = RequirementsTxtAnalyzer()

        with TemporaryDirectory() as tmpdir:
            req_file = Path(tmpdir) / "requirements.txt"
            req_file.write_text("fastapi>=0.100.0\n# This is a comment\nuvicorn==0.35.0\n")

            result = analyzer.parse_file(tmpdir, "requirements.txt")
            assert "fastapi" in result
            assert "uvicorn" in result

    def test_parse_requirements_with_extras(self):
        analyzer = RequirementsTxtAnalyzer()

        with TemporaryDirectory() as tmpdir:
            req_file = Path(tmpdir) / "requirements.txt"
            req_file.write_text("fastapi[all]>=0.100.0\n")

            result = analyzer.parse_file(tmpdir, "requirements.txt")
            assert "fastapi" in result


class TestPackageJsonAnalyzer:
    def test_parse_package_json(self):
        analyzer = PackageJsonAnalyzer()

        with TemporaryDirectory() as tmpdir:
            pkg_file = Path(tmpdir) / "package.json"
            pkg_file.write_text('{"dependencies": {"express": "^4.18.0", "react": "^18.0.0"}}')

            result = analyzer.parse_file(tmpdir, "package.json")
            assert "express" in result
            assert "react" in result

    def test_parse_package_json_no_dependencies(self):
        analyzer = PackageJsonAnalyzer()

        with TemporaryDirectory() as tmpdir:
            pkg_file = Path(tmpdir) / "package.json"
            pkg_file.write_text('{"name": "test-package"}')

            result = analyzer.parse_file(tmpdir, "package.json")
            assert isinstance(result, dict)
            assert len(result) == 0


class TestPyprojectTomlAnalyzer:
    def test_parse_pyproject_toml(self):
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

            result = analyzer.parse_file(tmpdir, "pyproject.toml")
            assert "fastapi" in result
            assert "uvicorn" in result

    def test_parse_pyproject_toml_no_dependencies(self):
        analyzer = PyprojectTomlAnalyzer()

        with TemporaryDirectory() as tmpdir:
            toml_file = Path(tmpdir) / "pyproject.toml"
            toml_file.write_text("[project]\nname = 'test'\n")

            result = analyzer.parse_file(tmpdir, "pyproject.toml")
            assert isinstance(result, dict)


class TestPythonVersionValidation:
    def test_compatible_version_greater_than_3(self):
        assert RequirementFileAnalyzer.is_compatible_python_version('>= "3"')

    def test_compatible_version_greater_than_2(self):
        assert RequirementFileAnalyzer.is_compatible_python_version('> "2"')

    def test_incompatible_version_equals_39(self):
        assert not RequirementFileAnalyzer.is_compatible_python_version('== "3.9"')

    def test_compatible_version_greater_equal_39(self):
        assert RequirementFileAnalyzer.is_compatible_python_version('>= "3.9"')

    def test_compatible_version_greater_equal_310(self):
        assert RequirementFileAnalyzer.is_compatible_python_version('>= "3.10"')

    def test_compatible_version_less_equal_3(self):
        assert RequirementFileAnalyzer.is_compatible_python_version('<= "3"')

    def test_incompatible_version_equals_2(self):
        assert not RequirementFileAnalyzer.is_compatible_python_version('== "2.7"')

    def test_incompatible_version_less_than_3(self):
        assert not RequirementFileAnalyzer.is_compatible_python_version('< "3"')

    def test_compatible_version_equals_313(self):
        assert RequirementFileAnalyzer.is_compatible_python_version('== "3.13"')

    def test_compatible_no_version_marker(self):
        assert RequirementFileAnalyzer.is_compatible_python_version('some_marker')

    def test_should_skip_dependency_with_extra(self):
        dependency = ['package', 'extra == "dev"']
        assert RequirementFileAnalyzer.should_skip_dependency(dependency)

    def test_should_skip_dependency_incompatible_python(self):
        dependency = ['package', 'python_version == "2.7"']
        assert RequirementFileAnalyzer.should_skip_dependency(dependency)

    def test_should_not_skip_dependency_compatible_python(self):
        dependency = ['package', 'python_version >= "3.9"']
        assert not RequirementFileAnalyzer.should_skip_dependency(dependency)

    def test_should_not_skip_dependency_no_marker(self):
        dependency = ['package']
        assert not RequirementFileAnalyzer.should_skip_dependency(dependency)
