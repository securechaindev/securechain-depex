import json
from pathlib import Path
from tempfile import TemporaryDirectory
from xml.etree.ElementTree import Element, SubElement, tostring

import pytest

from app.domain.repo_analyzer.requirement_files.spdx_sbom_analyzer import (
    SpdxSbomAnalyzer,
)


class TestSpdxSbomAnalyzer:
    @pytest.fixture
    def analyzer(self):
        return SpdxSbomAnalyzer()

    @pytest.fixture
    def temp_dir(self):
        with TemporaryDirectory() as tmpdir:
            yield tmpdir

    def create_spdx_json(self, temp_dir: str, filename: str, packages: list[dict]) -> str:
        sbom_data = {
            "spdxVersion": "SPDX-2.3",
            "dataLicense": "CC0-1.0",
            "SPDXID": "SPDXRef-DOCUMENT",
            "name": "Test SBOM",
            "packages": packages,
        }
        filepath = Path(temp_dir) / filename
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(sbom_data, f)
        return str(filepath)

    def create_spdx_xml(self, temp_dir: str, filename: str, purls: list[str]) -> str:
        root = Element("{http://spdx.org/rdf/terms}SpdxDocument")

        for purl in purls:
            package = SubElement(root, "{http://spdx.org/rdf/terms}package")
            external_refs = SubElement(package, "{http://spdx.org/rdf/terms}externalRefs")
            external_ref = SubElement(external_refs, "{http://spdx.org/rdf/terms}externalRef")

            ref_type = SubElement(external_ref, "{http://spdx.org/rdf/terms}referenceType")
            ref_type.text = "purl"

            ref_locator = SubElement(external_ref, "{http://spdx.org/rdf/terms}referenceLocator")
            ref_locator.text = purl

        filepath = Path(temp_dir) / filename
        with open(filepath, "wb") as f:
            f.write(tostring(root, encoding="utf-8"))
        return str(filepath)

    def test_analyzer_has_any_manager(self, analyzer):
        assert analyzer.manager == "ANY"

    def test_parse_json_pypi_package(self, analyzer, temp_dir):
        packages = [
            {
                "name": "requests",
                "SPDXID": "SPDXRef-Package-requests",
                "externalRefs": [
                    {
                        "referenceType": "purl",
                        "referenceLocator": "pkg:pypi/requests@2.28.0"
                    }
                ]
            }
        ]
        self.create_spdx_json(temp_dir, "sbom.spdx.json", packages)

        result = analyzer.parse_file(temp_dir, "sbom.spdx.json")

        assert "PyPI:requests" in result
        assert result["PyPI:requests"] == "==2.28.0"

    def test_parse_json_npm_package(self, analyzer, temp_dir):
        packages = [
            {
                "name": "axios",
                "SPDXID": "SPDXRef-Package-axios",
                "externalRefs": [
                    {
                        "referenceType": "purl",
                        "referenceLocator": "pkg:npm/axios@1.3.4"
                    }
                ]
            }
        ]
        self.create_spdx_json(temp_dir, "sbom.spdx.json", packages)

        result = analyzer.parse_file(temp_dir, "sbom.spdx.json")

        assert "NPM:axios" in result
        assert result["NPM:axios"] == "==1.3.4"

    def test_parse_json_npm_scoped_package(self, analyzer, temp_dir):
        packages = [
            {
                "name": "@angular/core",
                "SPDXID": "SPDXRef-Package-angular-core",
                "externalRefs": [
                    {
                        "referenceType": "purl",
                        "referenceLocator": "pkg:npm/%40angular/core@15.0.0"
                    }
                ]
            }
        ]
        self.create_spdx_json(temp_dir, "sbom.spdx.json", packages)

        result = analyzer.parse_file(temp_dir, "sbom.spdx.json")

        assert "NPM:@angular/core" in result
        assert result["NPM:@angular/core"] == "==15.0.0"

    def test_parse_json_maven_package(self, analyzer, temp_dir):
        packages = [
            {
                "name": "spring-core",
                "SPDXID": "SPDXRef-Package-spring-core",
                "externalRefs": [
                    {
                        "referenceType": "purl",
                        "referenceLocator": "pkg:maven/org.springframework/spring-core@5.3.20"
                    }
                ]
            }
        ]
        self.create_spdx_json(temp_dir, "sbom.spdx.json", packages)

        result = analyzer.parse_file(temp_dir, "sbom.spdx.json")

        assert "Maven:org.springframework:spring-core" in result
        assert result["Maven:org.springframework:spring-core"] == "[5.3.20]"

    def test_parse_json_cargo_package(self, analyzer, temp_dir):
        packages = [
            {
                "name": "serde",
                "SPDXID": "SPDXRef-Package-serde",
                "externalRefs": [
                    {
                        "referenceType": "purl",
                        "referenceLocator": "pkg:cargo/serde@1.0.152"
                    }
                ]
            }
        ]
        self.create_spdx_json(temp_dir, "sbom.spdx.json", packages)

        result = analyzer.parse_file(temp_dir, "sbom.spdx.json")

        assert "Cargo:serde" in result
        assert result["Cargo:serde"] == "==1.0.152"

    def test_parse_json_rubygems_package(self, analyzer, temp_dir):
        packages = [
            {
                "name": "rails",
                "SPDXID": "SPDXRef-Package-rails",
                "externalRefs": [
                    {
                        "referenceType": "purl",
                        "referenceLocator": "pkg:gem/rails@7.0.4"
                    }
                ]
            }
        ]
        self.create_spdx_json(temp_dir, "sbom.spdx.json", packages)

        result = analyzer.parse_file(temp_dir, "sbom.spdx.json")

        assert "RubyGems:rails" in result
        assert result["RubyGems:rails"] == "==7.0.4"

    def test_parse_json_nuget_package(self, analyzer, temp_dir):
        packages = [
            {
                "name": "Newtonsoft.Json",
                "SPDXID": "SPDXRef-Package-Newtonsoft-Json",
                "externalRefs": [
                    {
                        "referenceType": "purl",
                        "referenceLocator": "pkg:nuget/Newtonsoft.Json@13.0.2"
                    }
                ]
            }
        ]
        self.create_spdx_json(temp_dir, "sbom.spdx.json", packages)

        result = analyzer.parse_file(temp_dir, "sbom.spdx.json")

        assert "NuGet:Newtonsoft.Json" in result
        assert result["NuGet:Newtonsoft.Json"] == "==13.0.2"

    def test_parse_json_multiple_packages(self, analyzer, temp_dir):
        packages = [
            {
                "name": "requests",
                "SPDXID": "SPDXRef-Package-requests",
                "externalRefs": [
                    {"referenceType": "purl", "referenceLocator": "pkg:pypi/requests@2.28.0"}
                ]
            },
            {
                "name": "axios",
                "SPDXID": "SPDXRef-Package-axios",
                "externalRefs": [
                    {"referenceType": "purl", "referenceLocator": "pkg:npm/axios@1.3.4"}
                ]
            },
            {
                "name": "spring-core",
                "SPDXID": "SPDXRef-Package-spring-core",
                "externalRefs": [
                    {"referenceType": "purl", "referenceLocator": "pkg:maven/org.springframework/spring-core@5.3.20"}
                ]
            },
        ]
        self.create_spdx_json(temp_dir, "sbom.spdx.json", packages)

        result = analyzer.parse_file(temp_dir, "sbom.spdx.json")

        assert len(result) == 3
        assert "PyPI:requests" in result
        assert "NPM:axios" in result
        assert "Maven:org.springframework:spring-core" in result

    def test_parse_json_package_without_version(self, analyzer, temp_dir):
        packages = [
            {
                "name": "requests",
                "SPDXID": "SPDXRef-Package-requests",
                "externalRefs": [
                    {"referenceType": "purl", "referenceLocator": "pkg:pypi/requests"}
                ]
            }
        ]
        self.create_spdx_json(temp_dir, "sbom.spdx.json", packages)

        result = analyzer.parse_file(temp_dir, "sbom.spdx.json")

        assert "PyPI:requests" in result
        assert result["PyPI:requests"] == "any"

    def test_parse_json_ignores_unsupported_package_type(self, analyzer, temp_dir):
        packages = [
            {
                "name": "requests",
                "SPDXID": "SPDXRef-Package-requests",
                "externalRefs": [
                    {"referenceType": "purl", "referenceLocator": "pkg:pypi/requests@2.28.0"}
                ]
            },
            {
                "name": "gin",
                "SPDXID": "SPDXRef-Package-gin",
                "externalRefs": [
                    {"referenceType": "purl", "referenceLocator": "pkg:golang/github.com/gin-gonic/gin@1.8.1"}
                ]
            },
        ]
        self.create_spdx_json(temp_dir, "sbom.spdx.json", packages)

        result = analyzer.parse_file(temp_dir, "sbom.spdx.json")

        assert len(result) == 1
        assert "PyPI:requests" in result

    def test_parse_json_ignores_package_without_purl(self, analyzer, temp_dir):
        packages = [
            {
                "name": "requests",
                "SPDXID": "SPDXRef-Package-requests",
                "externalRefs": [
                    {"referenceType": "purl", "referenceLocator": "pkg:pypi/requests@2.28.0"}
                ]
            },
            {
                "name": "some-library",
                "SPDXID": "SPDXRef-Package-some-library",
                "versionInfo": "1.0.0"
            },
        ]
        self.create_spdx_json(temp_dir, "sbom.spdx.json", packages)

        result = analyzer.parse_file(temp_dir, "sbom.spdx.json")

        assert len(result) == 1
        assert "PyPI:requests" in result

    def test_parse_json_ignores_invalid_purl(self, analyzer, temp_dir):
        packages = [
            {
                "name": "requests",
                "SPDXID": "SPDXRef-Package-requests",
                "externalRefs": [
                    {"referenceType": "purl", "referenceLocator": "pkg:pypi/requests@2.28.0"}
                ]
            },
            {
                "name": "invalid",
                "SPDXID": "SPDXRef-Package-invalid",
                "externalRefs": [
                    {"referenceType": "purl", "referenceLocator": "invalid-purl-format"}
                ]
            },
        ]
        self.create_spdx_json(temp_dir, "sbom.spdx.json", packages)

        result = analyzer.parse_file(temp_dir, "sbom.spdx.json")

        assert len(result) == 1
        assert "PyPI:requests" in result

    def test_parse_json_handles_multiple_external_refs(self, analyzer, temp_dir):
        packages = [
            {
                "name": "requests",
                "SPDXID": "SPDXRef-Package-requests",
                "externalRefs": [
                    {"referenceType": "cpe23Type", "referenceLocator": "cpe:2.3:a:requests:requests:2.28.0"},
                    {"referenceType": "purl", "referenceLocator": "pkg:pypi/requests@2.28.0"}
                ]
            }
        ]
        self.create_spdx_json(temp_dir, "sbom.spdx.json", packages)

        result = analyzer.parse_file(temp_dir, "sbom.spdx.json")

        assert "PyPI:requests" in result
        assert result["PyPI:requests"] == "==2.28.0"

    def test_parse_json_packagejson_purl_format(self, analyzer, temp_dir):
        packages = [
            {
                "name": "cryptography",
                "SPDXID": "SPDXRef-PyPI-Cryptography",
                "versionInfo": "41.0.1",
                "packageJSON": {
                    "purl": "pkg:pypi/cryptography@41.0.1"
                }
            },
            {
                "name": "lodash",
                "SPDXID": "SPDXRef-NPM-Lodash",
                "versionInfo": "4.17.21",
                "packageJSON": {
                    "purl": "pkg:npm/lodash@4.17.21"
                }
            }
        ]
        self.create_spdx_json(temp_dir, "sbom.spdx.json", packages)

        result = analyzer.parse_file(temp_dir, "sbom.spdx.json")

        assert len(result) == 2
        assert "PyPI:cryptography" in result
        assert result["PyPI:cryptography"] == "==41.0.1"
        assert "NPM:lodash" in result
        assert result["NPM:lodash"] == "==4.17.21"

    def test_parse_xml_pypi_package(self, analyzer, temp_dir):
        purls = ["pkg:pypi/requests@2.28.0"]
        self.create_spdx_xml(temp_dir, "sbom.spdx.xml", purls)

        result = analyzer.parse_file(temp_dir, "sbom.spdx.xml")

        assert "PyPI:requests" in result
        assert result["PyPI:requests"] == "==2.28.0"

    def test_parse_xml_multiple_packages(self, analyzer, temp_dir):
        purls = [
            "pkg:pypi/requests@2.28.0",
            "pkg:npm/axios@1.3.4",
            "pkg:maven/org.springframework/spring-core@5.3.20",
        ]
        self.create_spdx_xml(temp_dir, "sbom.spdx.xml", purls)

        result = analyzer.parse_file(temp_dir, "sbom.spdx.xml")

        assert len(result) == 3
        assert "PyPI:requests" in result
        assert "NPM:axios" in result
        assert "Maven:org.springframework:spring-core" in result

    def test_parse_xml_reference_attribute_format(self, analyzer, temp_dir):
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<SpdxDocument xmlns="http://spdx.org/spdx/v2.3"
            spdxVersion="SPDX-2.3"
            dataLicense="CC0-1.0"
            SPDXID="SPDXRef-DOCUMENT"
            name="test-sbom"
            documentNamespace="http://spdx.org/spdxdocs/test">
<creationInfo>
    <creators><creator>Tool: Test</creator></creators>
    <created>2025-11-19T12:00:00Z</created>
</creationInfo>
<packages>
    <package SPDXID="SPDXRef-PyPI-Cryptography">
    <name>cryptography</name>
    <versionInfo>41.0.1</versionInfo>
    <downloadLocation>https://pypi.org/project/cryptography/41.0.1/</downloadLocation>
    <filesAnalyzed>false</filesAnalyzed>
    <externalRefs>
        <reference category="PACKAGE-MANAGER" type="purl">pkg:pypi/cryptography@41.0.1</reference>
    </externalRefs>
    </package>
    <package SPDXID="SPDXRef-NPM-Lodash">
    <name>lodash</name>
    <versionInfo>4.17.21</versionInfo>
    <downloadLocation>https://registry.npmjs.org/lodash/-/lodash-4.17.21.tgz</downloadLocation>
    <filesAnalyzed>false</filesAnalyzed>
    <externalRefs>
        <reference category="PACKAGE-MANAGER" type="purl">pkg:npm/lodash@4.17.21</reference>
    </externalRefs>
    </package>
</packages>
</SpdxDocument>"""
        filepath = Path(temp_dir) / "sbom.spdx.xml"
        filepath.write_text(xml_content)

        result = analyzer.parse_file(temp_dir, "sbom.spdx.xml")

        assert len(result) == 2
        assert "PyPI:cryptography" in result
        assert result["PyPI:cryptography"] == "==41.0.1"
        assert "NPM:lodash" in result
        assert result["NPM:lodash"] == "==4.17.21"

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
        packages = [
            {
                "name": "requests",
                "SPDXID": "SPDXRef-Package-requests",
                "externalRefs": [
                    {"referenceType": "purl", "referenceLocator": "pkg:pypi/requests@2.28.0"}
                ]
            },
            {
                "name": "axios",
                "SPDXID": "SPDXRef-Package-axios",
                "externalRefs": [
                    {"referenceType": "purl", "referenceLocator": "pkg:npm/axios@1.3.4"}
                ]
            },
        ]
        self.create_spdx_json(temp_dir, "sbom.spdx.json", packages)

        requirement_files = {}
        result = await analyzer.analyze(requirement_files, temp_dir, "sbom.spdx.json")

        assert "sbom.spdx.json" in result
        assert result["sbom.spdx.json"]["manager"] == "ANY"
        assert "PyPI:requests" in result["sbom.spdx.json"]["packages"]
        assert "NPM:axios" in result["sbom.spdx.json"]["packages"]

    @pytest.mark.asyncio
    async def test_analyze_handles_parse_failure_gracefully(self, analyzer, temp_dir):
        filepath = Path(temp_dir) / "invalid.json"
        filepath.write_text("{ invalid }")

        requirement_files = {}
        result = await analyzer.analyze(requirement_files, temp_dir, "invalid.json")

        assert result == {}

    @pytest.mark.asyncio
    async def test_analyze_skips_empty_packages(self, analyzer, temp_dir):
        packages = []
        self.create_spdx_json(temp_dir, "sbom.spdx.json", packages)

        requirement_files = {}
        result = await analyzer.analyze(requirement_files, temp_dir, "sbom.spdx.json")

        assert result == {}
