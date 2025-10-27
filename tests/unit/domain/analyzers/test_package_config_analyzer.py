"""Unit tests for PackageConfigAnalyzer."""
import pytest
from unittest.mock import mock_open, patch
from xml.etree import ElementTree

from app.domain.repo_analyzer.requirement_files.package_config_analyzer import PackageConfigAnalyzer


class TestPackageConfigAnalyzer:
    """Test suite for PackageConfigAnalyzer."""

    @pytest.fixture
    def analyzer(self):
        """Create a PackageConfigAnalyzer instance."""
        return PackageConfigAnalyzer()

    def test_init(self, analyzer):
        """Test PackageConfigAnalyzer initialization."""
        assert analyzer.manager == "NuGet"

    def test_parse_file_with_packages(self, analyzer):
        """Test parsing a valid packages.config with packages."""
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
                result = analyzer._parse_file("/fake/path", "packages.config")

        assert result == {
            "Newtonsoft.Json": "== 13.0.2",
            "EntityFramework": "== 6.4.4",
            "AutoMapper": "== 12.0.1"
        }

    def test_parse_file_empty_packages(self, analyzer):
        """Test parsing a packages.config with no packages."""
        packages_config_content = """<?xml version="1.0" encoding="utf-8"?>
<packages>
</packages>
"""
        with patch("xml.etree.ElementTree.parse") as mock_parse:
            mock_parse.return_value.getroot.return_value = ElementTree.fromstring(
                packages_config_content
            )
            result = analyzer._parse_file("/fake/path", "packages.config")

        assert result == {}

    def test_parse_file_single_package(self, analyzer):
        """Test parsing a packages.config with a single package."""
        packages_config_content = """<?xml version="1.0" encoding="utf-8"?>
<packages>
  <package id="Serilog" version="3.0.1" />
</packages>
"""
        with patch("xml.etree.ElementTree.parse") as mock_parse:
            mock_parse.return_value.getroot.return_value = ElementTree.fromstring(
                packages_config_content
            )
            result = analyzer._parse_file("/fake/path", "packages.config")

        assert result == {"Serilog": "== 3.0.1"}

    def test_parse_file_missing_id(self, analyzer):
        """Test parsing when a package is missing id attribute."""
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
            result = analyzer._parse_file("/fake/path", "packages.config")

        # Package without id should be skipped
        assert result == {
            "Package1": "== 1.0.0",
            "Package3": "== 3.0.0"
        }

    def test_parse_file_missing_version(self, analyzer):
        """Test parsing when a package is missing version attribute."""
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
            result = analyzer._parse_file("/fake/path", "packages.config")

        # Package without version should be skipped
        assert result == {
            "Package1": "== 1.0.0",
            "Package3": "== 3.0.0"
        }

    def test_parse_file_version_with_operators(self, analyzer):
        """Test parsing versions with comparison operators."""
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
            result = analyzer._parse_file("/fake/path", "packages.config")

        # [1.0.0] counts as 3 dots, so it gets "==" prefix (brackets are not operators)
        # [1.0.0,2.0.0) has comma which is not in operator list, so no "=="
        assert result == {
            "Pkg1": "== [1.0.0]",
            "Pkg2": "[1.0.0,2.0.0)",
            "Pkg3": ">=3.0.0"
        }

    def test_parse_file_two_digit_version(self, analyzer):
        """Test parsing with two-digit versions."""
        packages_config_content = """<?xml version="1.0" encoding="utf-8"?>
<packages>
  <package id="Pkg" version="1.0" />
</packages>
"""
        with patch("xml.etree.ElementTree.parse") as mock_parse:
            mock_parse.return_value.getroot.return_value = ElementTree.fromstring(
                packages_config_content
            )
            result = analyzer._parse_file("/fake/path", "packages.config")

        # Should not add "==" for non-standard versions
        assert result == {"Pkg": "1.0"}

    def test_parse_file_four_digit_version(self, analyzer):
        """Test parsing with four-digit versions."""
        packages_config_content = """<?xml version="1.0" encoding="utf-8"?>
<packages>
  <package id="Pkg" version="1.2.3.4" />
</packages>
"""
        with patch("xml.etree.ElementTree.parse") as mock_parse:
            mock_parse.return_value.getroot.return_value = ElementTree.fromstring(
                packages_config_content
            )
            result = analyzer._parse_file("/fake/path", "packages.config")

        # Should not add "==" for non-standard versions
        assert result == {"Pkg": "1.2.3.4"}

    def test_parse_file_mixed_versions(self, analyzer):
        """Test parsing with mixed version formats."""
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
            result = analyzer._parse_file("/fake/path", "packages.config")

        assert result == {
            "Standard": "== 1.2.3",
            "Range": "[1.0.0,2.0.0]",
            "Gte": ">=4.0.0",
            "TwoDigit": "5.1"
        }

    def test_parse_file_with_additional_attributes(self, analyzer):
        """Test parsing packages with additional attributes."""
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
            result = analyzer._parse_file("/fake/path", "packages.config")

        # Should extract id and version regardless of other attributes
        assert result == {
            "Package1": "== 1.0.0",
            "Package2": "== 2.0.0"
        }
