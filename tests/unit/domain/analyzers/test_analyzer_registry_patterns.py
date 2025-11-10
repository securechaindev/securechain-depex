import pytest

from app.domain.repo_analyzer.requirement_files.analyzer_registry import (
    AnalyzerRegistry,
)
from app.domain.repo_analyzer.requirement_files.gemfile_analyzer import GemfileAnalyzer
from app.domain.repo_analyzer.requirement_files.package_json_analyzer import (
    PackageJsonAnalyzer,
)
from app.domain.repo_analyzer.requirement_files.requirements_txt_analyzer import (
    RequirementsTxtAnalyzer,
)


class TestAnalyzerRegistryPatternMatching:
    @pytest.fixture
    def registry(self):
        return AnalyzerRegistry()

    def test_exact_match_requirements_txt(self, registry):
        analyzer = registry.get_analyzer("requirements.txt")
        assert analyzer is not None
        assert isinstance(analyzer, RequirementsTxtAnalyzer)

    def test_pattern_match_safe_requirements(self, registry):
        analyzer = registry.get_analyzer("safe_requirements.txt")
        assert analyzer is not None
        assert isinstance(analyzer, RequirementsTxtAnalyzer)

    def test_pattern_match_vulnerable_requirements(self, registry):
        analyzer = registry.get_analyzer("vulnerable_requirements.txt")
        assert analyzer is not None
        assert isinstance(analyzer, RequirementsTxtAnalyzer)

    def test_pattern_match_dev_requirements(self, registry):
        analyzer = registry.get_analyzer("dev-requirements.txt")
        assert analyzer is not None
        assert isinstance(analyzer, RequirementsTxtAnalyzer)

    def test_pattern_match_test_requirements(self, registry):
        analyzer = registry.get_analyzer("test_requirements.txt")
        assert analyzer is not None
        assert isinstance(analyzer, RequirementsTxtAnalyzer)

    def test_pattern_match_prod_requirements(self, registry):
        analyzer = registry.get_analyzer("prod.requirements.txt")
        assert analyzer is not None
        assert isinstance(analyzer, RequirementsTxtAnalyzer)

    def test_pattern_match_with_path(self, registry):
        analyzer = registry.get_analyzer("path/to/safe_requirements.txt")
        assert analyzer is not None
        assert isinstance(analyzer, RequirementsTxtAnalyzer)

    def test_case_insensitive_requirements(self, registry):
        analyzer = registry.get_analyzer("Safe_Requirements.txt")
        assert analyzer is not None
        assert isinstance(analyzer, RequirementsTxtAnalyzer)

    def test_exact_match_package_json(self, registry):
        analyzer = registry.get_analyzer("package.json")
        assert analyzer is not None
        assert isinstance(analyzer, PackageJsonAnalyzer)

    def test_pattern_match_fails_for_wrong_extension(self, registry):
        analyzer = registry.get_analyzer("requirements.py")
        assert analyzer is None

    def test_pattern_match_fails_for_non_requirement_file(self, registry):
        analyzer = registry.get_analyzer("random.txt")
        assert analyzer is None

    def test_exact_match_gemfile(self, registry):
        analyzer = registry.get_analyzer("Gemfile")
        assert analyzer is not None
        assert isinstance(analyzer, GemfileAnalyzer)

    def test_pattern_match_gemfile_variants(self, registry):
        analyzer = registry.get_analyzer("gemfile.dev")
        assert analyzer is not None
        assert isinstance(analyzer, GemfileAnalyzer)

    def test_singleton_pattern(self):
        registry1 = AnalyzerRegistry()
        registry2 = AnalyzerRegistry()
        assert registry1 is registry2

    def test_all_standard_analyzers_registered(self, registry):
        standard_files = [
            "requirements.txt",
            "pyproject.toml",
            "setup.py",
            "setup.cfg",
            "package.json",
            "package-lock.json",
            "Gemfile",
            "Gemfile.lock",
            "Cargo.toml",
            "Cargo.lock",
            "pom.xml",
            "packages.config",
        ]

        for filename in standard_files:
            analyzer = registry.get_analyzer(filename)
            assert analyzer is not None, f"No analyzer found for {filename}"
