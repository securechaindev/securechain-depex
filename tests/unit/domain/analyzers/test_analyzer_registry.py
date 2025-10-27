"""Unit tests for analyzer registry."""

from app.domain.repo_analyzer.requirement_files.analyzer_registry import (
    AnalyzerRegistry,
)
from app.domain.repo_analyzer.requirement_files.cargo_lock_analyzer import (
    CargoLockAnalyzer,
)
from app.domain.repo_analyzer.requirement_files.cargo_toml_analyzer import (
    CargoTomlAnalyzer,
)
from app.domain.repo_analyzer.requirement_files.gemfile_analyzer import (
    GemfileAnalyzer,
)
from app.domain.repo_analyzer.requirement_files.gemfile_lock_analyzer import (
    GemfileLockAnalyzer,
)
from app.domain.repo_analyzer.requirement_files.package_config_analyzer import (
    PackageConfigAnalyzer,
)
from app.domain.repo_analyzer.requirement_files.package_json_analyzer import (
    PackageJsonAnalyzer,
)
from app.domain.repo_analyzer.requirement_files.package_lock_json_analyzer import (
    PackageLockJsonAnalyzer,
)
from app.domain.repo_analyzer.requirement_files.pom_xml_analyzer import (
    PomXmlAnalyzer,
)
from app.domain.repo_analyzer.requirement_files.pyproject_toml_analyzer import (
    PyprojectTomlAnalyzer,
)
from app.domain.repo_analyzer.requirement_files.requirements_txt_analyzer import (
    RequirementsTxtAnalyzer,
)
from app.domain.repo_analyzer.requirement_files.setup_cfg_analyzer import (
    SetupCfgAnalyzer,
)
from app.domain.repo_analyzer.requirement_files.setup_py_analyzer import (
    SetupPyAnalyzer,
)


class TestAnalyzerRegistry:
    """Test suite for AnalyzerRegistry."""

    def test_get_analyzer_requirements_txt(self):
        """Test getting analyzer for requirements.txt."""
        registry = AnalyzerRegistry()
        analyzer = registry.get_analyzer("requirements.txt")
        assert isinstance(analyzer, RequirementsTxtAnalyzer)

    def test_get_analyzer_package_json(self):
        """Test getting analyzer for package.json."""
        registry = AnalyzerRegistry()
        analyzer = registry.get_analyzer("package.json")
        assert isinstance(analyzer, PackageJsonAnalyzer)

    def test_get_analyzer_pyproject_toml(self):
        """Test getting analyzer for pyproject.toml."""
        registry = AnalyzerRegistry()
        analyzer = registry.get_analyzer("pyproject.toml")
        assert isinstance(analyzer, PyprojectTomlAnalyzer)

    def test_get_analyzer_setup_py(self):
        """Test getting analyzer for setup.py."""
        registry = AnalyzerRegistry()
        analyzer = registry.get_analyzer("setup.py")
        assert isinstance(analyzer, SetupPyAnalyzer)

    def test_get_analyzer_setup_cfg(self):
        """Test getting analyzer for setup.cfg."""
        registry = AnalyzerRegistry()
        analyzer = registry.get_analyzer("setup.cfg")
        assert isinstance(analyzer, SetupCfgAnalyzer)

    def test_get_analyzer_package_lock_json(self):
        """Test getting analyzer for package-lock.json."""
        registry = AnalyzerRegistry()
        analyzer = registry.get_analyzer("package-lock.json")
        assert isinstance(analyzer, PackageLockJsonAnalyzer)

    def test_get_analyzer_gemfile(self):
        """Test getting analyzer for Gemfile."""
        registry = AnalyzerRegistry()
        analyzer = registry.get_analyzer("Gemfile")
        assert isinstance(analyzer, GemfileAnalyzer)

    def test_get_analyzer_gemfile_lock(self):
        """Test getting analyzer for Gemfile.lock."""
        registry = AnalyzerRegistry()
        analyzer = registry.get_analyzer("Gemfile.lock")
        assert isinstance(analyzer, GemfileLockAnalyzer)

    def test_get_analyzer_cargo_toml(self):
        """Test getting analyzer for Cargo.toml."""
        registry = AnalyzerRegistry()
        analyzer = registry.get_analyzer("Cargo.toml")
        assert isinstance(analyzer, CargoTomlAnalyzer)

    def test_get_analyzer_cargo_lock(self):
        """Test getting analyzer for Cargo.lock."""
        registry = AnalyzerRegistry()
        analyzer = registry.get_analyzer("Cargo.lock")
        assert isinstance(analyzer, CargoLockAnalyzer)

    def test_get_analyzer_pom_xml(self):
        """Test getting analyzer for pom.xml."""
        registry = AnalyzerRegistry()
        analyzer = registry.get_analyzer("pom.xml")
        assert isinstance(analyzer, PomXmlAnalyzer)

    def test_get_analyzer_packages_config(self):
        """Test getting analyzer for packages.config."""
        registry = AnalyzerRegistry()
        analyzer = registry.get_analyzer("packages.config")
        assert isinstance(analyzer, PackageConfigAnalyzer)

    def test_get_analyzer_with_path_prefix(self):
        """Test getting analyzer with path prefix like /master/."""
        registry = AnalyzerRegistry()
        # Registry doesn't normalize filenames - it looks up exact matches
        # The normalization happens inside the analyzer's analyze method
        analyzer = registry.get_analyzer("/master/requirements.txt")
        # This should return None because registry doesn't do normalization
        assert analyzer is None

        # But getting the base analyzer for "requirements.txt" works
        analyzer = registry.get_analyzer("requirements.txt")
        assert isinstance(analyzer, RequirementsTxtAnalyzer)

    def test_get_analyzer_unknown_file(self):
        """Test getting analyzer for unknown file type."""
        registry = AnalyzerRegistry()
        analyzer = registry.get_analyzer("unknown.file")
        assert analyzer is None

    def test_get_analyzer_case_sensitive(self):
        """Test that analyzer lookup is case-sensitive."""
        registry = AnalyzerRegistry()

        # Gemfile with capital G should work
        analyzer = registry.get_analyzer("Gemfile")
        assert isinstance(analyzer, GemfileAnalyzer)

        # gemfile with lowercase g should not work
        analyzer = registry.get_analyzer("gemfile")
        assert analyzer is None

    def test_registry_contains_all_analyzers(self):
        """Test that registry contains all expected file types."""
        registry = AnalyzerRegistry()
        expected_files = [
            "requirements.txt",
            "package.json",
            "pyproject.toml",
            "setup.py",
            "setup.cfg",
            "package-lock.json",
            "Gemfile",
            "Gemfile.lock",
            "Cargo.toml",
            "Cargo.lock",
            "pom.xml",
            "packages.config",
        ]

        for filename in expected_files:
            analyzer = registry.get_analyzer(filename)
            assert analyzer is not None, f"No analyzer found for {filename}"
