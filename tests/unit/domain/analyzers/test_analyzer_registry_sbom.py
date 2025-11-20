import json
from pathlib import Path
from tempfile import TemporaryDirectory
from xml.etree.ElementTree import Element, SubElement, tostring

import pytest

from app.domain.repo_analyzer.requirement_files.analyzer_registry import (
    AnalyzerRegistry,
)
from app.domain.repo_analyzer.requirement_files.cyclonedx_sbom_analyzer import (
    CycloneDxSbomAnalyzer,
)


class TestAnalyzerRegistrySbomDetection:
    @pytest.fixture
    def registry(self):
        return AnalyzerRegistry()

    @pytest.fixture
    def temp_dir(self):
        with TemporaryDirectory() as tmpdir:
            yield tmpdir

    def create_cyclonedx_json(self, temp_dir: str, filename: str) -> str:
        sbom_data = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.4",
            "version": 1,
            "components": [{"purl": "pkg:pypi/requests@2.28.0"}],
        }
        filepath = Path(temp_dir) / filename
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(sbom_data, f)
        return str(filepath)

    def create_cyclonedx_xml(self, temp_dir: str, filename: str) -> str:
        root = Element("{http://cyclonedx.org/schema/bom/1.4}bom")
        root.set("version", "1")

        components = SubElement(root, "{http://cyclonedx.org/schema/bom/1.4}components")
        component = SubElement(components, "{http://cyclonedx.org/schema/bom/1.4}component")
        purl_elem = SubElement(component, "{http://cyclonedx.org/schema/bom/1.4}purl")
        purl_elem.text = "pkg:pypi/requests@2.28.0"

        filepath = Path(temp_dir) / filename
        with open(filepath, "wb") as f:
            f.write(tostring(root, encoding="utf-8"))
        return str(filepath)

    def create_invalid_json(self, temp_dir: str, filename: str) -> str:
        data = {
            "name": "my-project",
            "version": "1.0.0",
            "dependencies": {},
        }
        filepath = Path(temp_dir) / filename
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f)
        return str(filepath)

    def test_is_sbom_file_detects_sbom_json(self, registry):
        assert registry.is_sbom_file("sbom.json") is True
        assert registry.is_sbom_file("bom.json") is True
        assert registry.is_sbom_file("cyclonedx.json") is True

    def test_is_sbom_file_detects_sbom_xml(self, registry):
        assert registry.is_sbom_file("sbom.xml") is True
        assert registry.is_sbom_file("bom.xml") is True
        assert registry.is_sbom_file("cyclonedx.xml") is True

    def test_is_sbom_file_case_insensitive(self, registry):
        assert registry.is_sbom_file("SBOM.json") is True
        assert registry.is_sbom_file("BOM.XML") is True
        assert registry.is_sbom_file("CycloneDX.Json") is True

    def test_is_sbom_file_with_prefix(self, registry):
        assert registry.is_sbom_file("project-sbom.json") is True
        assert registry.is_sbom_file("app.bom.xml") is True

    def test_is_sbom_file_rejects_non_sbom(self, registry):
        assert registry.is_sbom_file("package.json") is False
        assert registry.is_sbom_file("requirements.txt") is False
        assert registry.is_sbom_file("data.json") is False

    def test_detect_cyclonedx_json_format(self, registry, temp_dir):
        self.create_cyclonedx_json(temp_dir, "sbom.json")

        result = registry.detect_sbom_format("sbom.json", temp_dir)

        assert result == "cyclonedx"

    def test_detect_cyclonedx_xml_format(self, registry, temp_dir):
        self.create_cyclonedx_xml(temp_dir, "sbom.xml")

        result = registry.detect_sbom_format("sbom.xml", temp_dir)

        assert result == "cyclonedx"

    def test_detect_sbom_format_returns_none_for_invalid_json(self, registry, temp_dir):
        self.create_invalid_json(temp_dir, "not-sbom.json")

        result = registry.detect_sbom_format("not-sbom.json", temp_dir)

        assert result is None

    def test_detect_sbom_format_handles_missing_file(self, registry, temp_dir):
        result = registry.detect_sbom_format("nonexistent.json", temp_dir)

        assert result is None

    def test_detect_sbom_format_handles_invalid_json_syntax(self, registry, temp_dir):
        filepath = Path(temp_dir) / "invalid.json"
        filepath.write_text("{ invalid json }")

        result = registry.detect_sbom_format("invalid.json", temp_dir)

        assert result is None

    def test_detect_sbom_format_handles_invalid_xml_syntax(self, registry, temp_dir):
        filepath = Path(temp_dir) / "invalid.xml"
        filepath.write_text("<invalid><xml")

        result = registry.detect_sbom_format("invalid.xml", temp_dir)

        assert result is None

    def test_get_analyzer_returns_cyclonedx_for_valid_sbom_json(self, registry, temp_dir):
        self.create_cyclonedx_json(temp_dir, "sbom.json")

        analyzer = registry.get_analyzer("sbom.json", temp_dir)

        assert analyzer is not None
        assert isinstance(analyzer, CycloneDxSbomAnalyzer)

    def test_get_analyzer_returns_cyclonedx_for_valid_sbom_xml(self, registry, temp_dir):
        self.create_cyclonedx_xml(temp_dir, "bom.xml")

        analyzer = registry.get_analyzer("bom.xml", temp_dir)

        assert analyzer is not None
        assert isinstance(analyzer, CycloneDxSbomAnalyzer)

    def test_get_analyzer_returns_none_for_invalid_sbom(self, registry, temp_dir):
        self.create_invalid_json(temp_dir, "sbom.json")

        analyzer = registry.get_analyzer("sbom.json", temp_dir)

        assert analyzer is None

    def test_get_analyzer_without_repository_path_skips_sbom_detection(self, registry):
        analyzer = registry.get_analyzer("sbom.json", "")

        assert analyzer is None

    def test_get_analyzer_prefers_exact_match_over_sbom_detection(self, registry, temp_dir):
        analyzer = registry.get_analyzer("package.json", temp_dir)

        assert analyzer is not None
        assert not isinstance(analyzer, CycloneDxSbomAnalyzer)

    def test_detect_json_sbom_format_requires_bomformat_field(self, registry, temp_dir):
        data = {
            "specVersion": "1.4",
            "version": 1,
            "components": [],
        }
        filepath = Path(temp_dir) / "sbom.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f)

        result = registry.detect_sbom_format("sbom.json", temp_dir)

        assert result is None

    def test_detect_xml_sbom_format_requires_cyclonedx_namespace(self, registry, temp_dir):
        root = Element("bom")
        root.set("version", "1")

        filepath = Path(temp_dir) / "sbom.xml"
        with open(filepath, "wb") as f:
            f.write(tostring(root, encoding="utf-8"))

        result = registry.detect_sbom_format("sbom.xml", temp_dir)

        assert result is None

    def test_sbom_detection_with_different_cyclonedx_versions(self, registry, temp_dir):
        for version in ["1.2", "1.3", "1.4", "1.5"]:
            sbom_data = {
                "bomFormat": "CycloneDX",
                "specVersion": version,
                "version": 1,
                "components": [],
            }
            filepath = Path(temp_dir) / f"sbom-{version}.json"
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(sbom_data, f)

            result = registry.detect_sbom_format(f"sbom-{version}.json", temp_dir)

            assert result == "cyclonedx", f"Failed for version {version}"
