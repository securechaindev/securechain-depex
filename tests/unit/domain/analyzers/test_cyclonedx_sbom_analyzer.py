import json
from pathlib import Path
from tempfile import TemporaryDirectory
from xml.etree.ElementTree import Element, SubElement, tostring

import pytest

from app.domain.repo_analyzer.requirement_files.cyclonedx_sbom_analyzer import (
    CycloneDxSbomAnalyzer,
)


class TestCycloneDxSbomAnalyzer:
    @pytest.fixture
    def analyzer(self):
        return CycloneDxSbomAnalyzer()

    @pytest.fixture
    def temp_dir(self):
        with TemporaryDirectory() as tmpdir:
            yield tmpdir

    def create_cyclonedx_json(self, temp_dir: str, filename: str, components: list[dict]) -> str:
        sbom_data = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.4",
            "version": 1,
            "components": components,
        }
        filepath = Path(temp_dir) / filename
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(sbom_data, f)
        return str(filepath)

    def create_cyclonedx_xml(self, temp_dir: str, filename: str, purls: list[str]) -> str:
        root = Element("{http://cyclonedx.org/schema/bom/1.4}bom")
        root.set("version", "1")

        components = SubElement(root, "{http://cyclonedx.org/schema/bom/1.4}components")
        for purl in purls:
            component = SubElement(components, "{http://cyclonedx.org/schema/bom/1.4}component")
            purl_elem = SubElement(component, "{http://cyclonedx.org/schema/bom/1.4}purl")
            purl_elem.text = purl

        filepath = Path(temp_dir) / filename
        with open(filepath, "wb") as f:
            f.write(tostring(root, encoding="utf-8"))
        return str(filepath)

    def test_analyzer_has_any_manager(self, analyzer):
        assert analyzer.manager == "ANY"

    def test_parse_json_pypi_package(self, analyzer, temp_dir):
        components = [
            {
                "purl": "pkg:pypi/requests@2.28.0",
            }
        ]
        self.create_cyclonedx_json(temp_dir, "sbom.json", components)

        result = analyzer.parse_file(temp_dir, "sbom.json")

        assert "PyPI:requests" in result
        assert result["PyPI:requests"] == "==2.28.0"

    def test_parse_json_npm_package(self, analyzer, temp_dir):
        components = [
            {
                "purl": "pkg:npm/axios@1.3.4",
            }
        ]
        self.create_cyclonedx_json(temp_dir, "sbom.json", components)

        result = analyzer.parse_file(temp_dir, "sbom.json")

        assert "NPM:axios" in result
        assert result["NPM:axios"] == "==1.3.4"

    def test_parse_json_npm_scoped_package(self, analyzer, temp_dir):
        components = [
            {
                "purl": "pkg:npm/%40angular/core@15.0.0",
            }
        ]
        self.create_cyclonedx_json(temp_dir, "sbom.json", components)

        result = analyzer.parse_file(temp_dir, "sbom.json")

        assert "NPM:@angular/core" in result
        assert result["NPM:@angular/core"] == "==15.0.0"

    def test_parse_json_maven_package(self, analyzer, temp_dir):
        components = [
            {
                "purl": "pkg:maven/org.springframework/spring-core@5.3.20",
            }
        ]
        self.create_cyclonedx_json(temp_dir, "sbom.json", components)

        result = analyzer.parse_file(temp_dir, "sbom.json")

        assert "Maven:org.springframework:spring-core" in result
        assert result["Maven:org.springframework:spring-core"] == "[5.3.20]"

    def test_parse_json_cargo_package(self, analyzer, temp_dir):
        components = [
            {
                "purl": "pkg:cargo/serde@1.0.152",
            }
        ]
        self.create_cyclonedx_json(temp_dir, "sbom.json", components)

        result = analyzer.parse_file(temp_dir, "sbom.json")

        assert "Cargo:serde" in result
        assert result["Cargo:serde"] == "==1.0.152"

    def test_parse_json_rubygems_package(self, analyzer, temp_dir):
        components = [
            {
                "purl": "pkg:gem/rails@7.0.4",
            }
        ]
        self.create_cyclonedx_json(temp_dir, "sbom.json", components)

        result = analyzer.parse_file(temp_dir, "sbom.json")

        assert "RubyGems:rails" in result
        assert result["RubyGems:rails"] == "==7.0.4"

    def test_parse_json_nuget_package(self, analyzer, temp_dir):
        components = [
            {
                "purl": "pkg:nuget/Newtonsoft.Json@13.0.2",
            }
        ]
        self.create_cyclonedx_json(temp_dir, "sbom.json", components)

        result = analyzer.parse_file(temp_dir, "sbom.json")

        assert "NuGet:Newtonsoft.Json" in result
        assert result["NuGet:Newtonsoft.Json"] == "==13.0.2"

    def test_parse_json_multiple_packages(self, analyzer, temp_dir):
        components = [
            {"purl": "pkg:pypi/requests@2.28.0"},
            {"purl": "pkg:npm/axios@1.3.4"},
            {"purl": "pkg:maven/org.springframework/spring-core@5.3.20"},
        ]
        self.create_cyclonedx_json(temp_dir, "sbom.json", components)

        result = analyzer.parse_file(temp_dir, "sbom.json")

        assert len(result) == 3
        assert "PyPI:requests" in result
        assert "NPM:axios" in result
        assert "Maven:org.springframework:spring-core" in result

    def test_parse_json_package_without_version(self, analyzer, temp_dir):
        components = [
            {
                "purl": "pkg:pypi/requests",
            }
        ]
        self.create_cyclonedx_json(temp_dir, "sbom.json", components)

        result = analyzer.parse_file(temp_dir, "sbom.json")

        assert "PyPI:requests" in result
        assert result["PyPI:requests"] == "any"

    def test_parse_json_ignores_unsupported_package_type(self, analyzer, temp_dir):
        components = [
            {"purl": "pkg:pypi/requests@2.28.0"},
            {"purl": "pkg:golang/github.com/gin-gonic/gin@1.8.1"},  # Not supported
        ]
        self.create_cyclonedx_json(temp_dir, "sbom.json", components)

        result = analyzer.parse_file(temp_dir, "sbom.json")

        assert len(result) == 1
        assert "PyPI:requests" in result

    def test_parse_json_ignores_component_without_purl(self, analyzer, temp_dir):
        components = [
            {"purl": "pkg:pypi/requests@2.28.0"},
            {"name": "some-library", "version": "1.0.0"},  # No purl
        ]
        self.create_cyclonedx_json(temp_dir, "sbom.json", components)

        result = analyzer.parse_file(temp_dir, "sbom.json")

        assert len(result) == 1
        assert "PyPI:requests" in result

    def test_parse_json_ignores_invalid_purl(self, analyzer, temp_dir):
        components = [
            {"purl": "pkg:pypi/requests@2.28.0"},
            {"purl": "invalid-purl-format"},
        ]
        self.create_cyclonedx_json(temp_dir, "sbom.json", components)

        result = analyzer.parse_file(temp_dir, "sbom.json")

        assert len(result) == 1
        assert "PyPI:requests" in result

    def test_parse_xml_pypi_package(self, analyzer, temp_dir):
        purls = ["pkg:pypi/requests@2.28.0"]
        self.create_cyclonedx_xml(temp_dir, "sbom.xml", purls)

        result = analyzer.parse_file(temp_dir, "sbom.xml")

        assert "PyPI:requests" in result
        assert result["PyPI:requests"] == "==2.28.0"

    def test_parse_xml_multiple_packages(self, analyzer, temp_dir):
        purls = [
            "pkg:pypi/requests@2.28.0",
            "pkg:npm/axios@1.3.4",
            "pkg:maven/org.springframework/spring-core@5.3.20",
        ]
        self.create_cyclonedx_xml(temp_dir, "sbom.xml", purls)

        result = analyzer.parse_file(temp_dir, "sbom.xml")

        assert len(result) == 3
        assert "PyPI:requests" in result
        assert "NPM:axios" in result
        assert "Maven:org.springframework:spring-core" in result

    def test_parse_file_returns_empty_for_unknown_extension(self, analyzer, temp_dir):
        filepath = Path(temp_dir) / "sbom.txt"
        filepath.write_text("not a valid sbom")

        result = analyzer.parse_file(temp_dir, "sbom.txt")

        assert result == {}

    def test_parse_file_returns_empty_on_invalid_json(self, analyzer, temp_dir):
        filepath = Path(temp_dir) / "invalid.json"
        filepath.write_text("{ invalid json }")

        result = analyzer.parse_file(temp_dir, "invalid.json")

        assert result == {}

    def test_parse_file_returns_empty_on_invalid_xml(self, analyzer, temp_dir):
        filepath = Path(temp_dir) / "invalid.xml"
        filepath.write_text("<invalid><xml")

        result = analyzer.parse_file(temp_dir, "invalid.xml")

        assert result == {}

    def test_normalize_version_for_maven(self, analyzer):
        result = analyzer.normalize_version_for_type("5.3.20", "maven")
        assert result == "[5.3.20]"

    def test_normalize_version_for_pypi(self, analyzer):
        result = analyzer.normalize_version_for_type("2.28.0", "pypi")
        assert result == "==2.28.0"

    def test_normalize_version_for_npm(self, analyzer):
        result = analyzer.normalize_version_for_type("1.3.4", "npm")
        assert result == "==1.3.4"

    @pytest.mark.asyncio
    async def test_analyze_adds_sbom_to_requirement_files(self, analyzer, temp_dir):
        components = [
            {"purl": "pkg:pypi/requests@2.28.0"},
            {"purl": "pkg:npm/axios@1.3.4"},
        ]
        self.create_cyclonedx_json(temp_dir, "sbom.json", components)

        requirement_files = {}
        result = await analyzer.analyze(requirement_files, temp_dir, "sbom.json")

        assert "sbom.json" in result
        assert result["sbom.json"]["manager"] == "ANY"
        assert "PyPI:requests" in result["sbom.json"]["packages"]
        assert "NPM:axios" in result["sbom.json"]["packages"]

    @pytest.mark.asyncio
    async def test_analyze_normalizes_filename(self, analyzer, temp_dir):
        components = [{"purl": "pkg:pypi/requests@2.28.0"}]
        self.create_cyclonedx_json(temp_dir, "sbom.cdx.json", components)

        requirement_files = {}
        result = await analyzer.analyze(requirement_files, temp_dir, "sbom.cdx.json")

        # Should preserve filename (only /master/ and /main/ are removed by normalize_filename)
        assert "sbom.cdx.json" in result

    @pytest.mark.asyncio
    async def test_analyze_handles_parse_failure_gracefully(self, analyzer, temp_dir):
        filepath = Path(temp_dir) / "invalid.json"
        filepath.write_text("{ invalid }")

        requirement_files = {}
        result = await analyzer.analyze(requirement_files, temp_dir, "invalid.json")

        assert result == {}

    @pytest.mark.asyncio
    async def test_analyze_skips_empty_packages(self, analyzer, temp_dir):
        components = []
        self.create_cyclonedx_json(temp_dir, "sbom.json", components)

        requirement_files = {}
        result = await analyzer.analyze(requirement_files, temp_dir, "sbom.json")

        assert result == {}
