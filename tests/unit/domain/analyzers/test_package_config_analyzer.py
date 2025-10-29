from unittest.mock import mock_open, patch
from xml.etree import ElementTree

import pytest

from app.domain.repo_analyzer.requirement_files.package_config_analyzer import (
    PackageConfigAnalyzer,
)


class TestPackageConfigAnalyzer:
    @pytest.fixture
    def analyzer(self):
        return PackageConfigAnalyzer()

    def test_init(self, analyzer):
        assert analyzer.manager == "NuGet"

    def test_parse_file_with_packages(self, analyzer):
        packages_config_content = """<?xml version="1.0" encoding="utf-8"?>
        <packages>
            <package id="Newtonsoft.Json" version="13.0.2" />
            <package id="EntityFramework" version="6.4.4" />
            <package id="AutoMapper" version="12.0.1" />
        </packages>
        """
        mock_file = mock_open(read_data=packages_config_content)
        with patch("builtins.open", mock_file):
            with patch("xml.etree.ElementTree.parse") as mock_parse:
                mock_parse.return_value.getroot.return_value = ElementTree.fromstring(
                    packages_config_content
                )
                result = analyzer.parse_file("/fake/path", "packages.config")

        assert result == {
            "Newtonsoft.Json": "== 13.0.2",
            "EntityFramework": "== 6.4.4",
            "AutoMapper": "== 12.0.1"
        }

    def test_parse_file_empty_packages(self, analyzer):
        packages_config_content = """<?xml version="1.0" encoding="utf-8"?>
        <packages>
        </packages>
        """
        with patch("xml.etree.ElementTree.parse") as mock_parse:
            mock_parse.return_value.getroot.return_value = ElementTree.fromstring(
                packages_config_content
            )
            result = analyzer.parse_file("/fake/path", "packages.config")

        assert result == {}

    def test_parse_file_single_package(self, analyzer):
        packages_config_content = """<?xml version="1.0" encoding="utf-8"?>
        <packages>
            <package id="Serilog" version="3.0.1" />
        </packages>
        """
        with patch("xml.etree.ElementTree.parse") as mock_parse:
            mock_parse.return_value.getroot.return_value = ElementTree.fromstring(
                packages_config_content
            )
            result = analyzer.parse_file("/fake/path", "packages.config")

        assert result == {"Serilog": "== 3.0.1"}

    def test_parse_file_missing_id(self, analyzer):
        packages_config_content = """<?xml version="1.0" encoding="utf-8"?>
        <packages>
            <package id="Package1" version="1.0.0" />
            <package version="2.0.0" />
            <package id="Package3" version="3.0.0" />
        </packages>
        """
        with patch("xml.etree.ElementTree.parse") as mock_parse:
            mock_parse.return_value.getroot.return_value = ElementTree.fromstring(
                packages_config_content
            )
            result = analyzer.parse_file("/fake/path", "packages.config")

        assert result == {
            "Package1": "== 1.0.0",
            "Package3": "== 3.0.0"
        }

    def test_parse_file_missing_version(self, analyzer):
        packages_config_content = """<?xml version="1.0" encoding="utf-8"?>
        <packages>
            <package id="Package1" version="1.0.0" />
            <package id="Package2" />
            <package id="Package3" version="3.0.0" />
        </packages>
        """
        with patch("xml.etree.ElementTree.parse") as mock_parse:
            mock_parse.return_value.getroot.return_value = ElementTree.fromstring(
                packages_config_content
            )
            result = analyzer.parse_file("/fake/path", "packages.config")

        assert result == {
            "Package1": "== 1.0.0",
            "Package3": "== 3.0.0"
        }

    def test_parse_file_version_with_operators(self, analyzer):
        packages_config_content = """<?xml version="1.0" encoding="utf-8"?>
        <packages>
            <package id="Pkg1" version="[1.0.0]" />
            <package id="Pkg2" version="[1.0.0,2.0.0)" />
            <package id="Pkg3" version=">=3.0.0" />
        </packages>
        """
        with patch("xml.etree.ElementTree.parse") as mock_parse:
            mock_parse.return_value.getroot.return_value = ElementTree.fromstring(
                packages_config_content
            )
            result = analyzer.parse_file("/fake/path", "packages.config")

        assert result == {
            "Pkg1": "== [1.0.0]",
            "Pkg2": "[1.0.0,2.0.0)",
            "Pkg3": ">=3.0.0"
        }

    def test_parse_file_two_digit_version(self, analyzer):
        packages_config_content = """<?xml version="1.0" encoding="utf-8"?>
        <packages>
            <package id="Pkg" version="1.0" />
        </packages>
        """
        with patch("xml.etree.ElementTree.parse") as mock_parse:
            mock_parse.return_value.getroot.return_value = ElementTree.fromstring(
                packages_config_content
            )
            result = analyzer.parse_file("/fake/path", "packages.config")

        assert result == {"Pkg": "1.0"}

    def test_parse_file_four_digit_version(self, analyzer):
        packages_config_content = """<?xml version="1.0" encoding="utf-8"?>
        <packages>
            <package id="Pkg" version="1.2.3.4" />
        </packages>
        """
        with patch("xml.etree.ElementTree.parse") as mock_parse:
            mock_parse.return_value.getroot.return_value = ElementTree.fromstring(
                packages_config_content
            )
            result = analyzer.parse_file("/fake/path", "packages.config")

        assert result == {"Pkg": "1.2.3.4"}

    def test_parse_file_mixed_versions(self, analyzer):
        packages_config_content = """<?xml version="1.0" encoding="utf-8"?>
        <packages>
            <package id="Standard" version="1.2.3" />
            <package id="Range" version="[1.0.0,2.0.0]" />
            <package id="Gte" version=">=4.0.0" />
            <package id="TwoDigit" version="5.1" />
        </packages>
        """
        with patch("xml.etree.ElementTree.parse") as mock_parse:
            mock_parse.return_value.getroot.return_value = ElementTree.fromstring(
                packages_config_content
            )
            result = analyzer.parse_file("/fake/path", "packages.config")

        assert result == {
            "Standard": "== 1.2.3",
            "Range": "[1.0.0,2.0.0]",
            "Gte": ">=4.0.0",
            "TwoDigit": "5.1"
        }

    def test_parse_file_with_additional_attributes(self, analyzer):
        packages_config_content = """<?xml version="1.0" encoding="utf-8"?>
        <packages>
            <package id="Package1" version="1.0.0" targetFramework="net472" />
            <package id="Package2" version="2.0.0" developmentDependency="true" />
        </packages>
        """
        with patch("xml.etree.ElementTree.parse") as mock_parse:
            mock_parse.return_value.getroot.return_value = ElementTree.fromstring(
                packages_config_content
            )
            result = analyzer.parse_file("/fake/path", "packages.config")

        assert result == {
            "Package1": "== 1.0.0",
            "Package2": "== 2.0.0"
        }
