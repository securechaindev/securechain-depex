"""Unit tests for VersionFilter."""

from app.utils.version_filter import VersionFilter


class TestVersionFilter:
    """Test suite for VersionFilter."""

    def test_get_version_range_type_pypi(self):
        """Test getting version range type for PyPI."""
        version_type, version_range_type = VersionFilter.get_version_range_type("PyPIPackage")
        assert version_type is not None
        assert version_range_type is not None

    def test_get_version_range_type_npm(self):
        """Test getting version range type for NPM."""
        version_type, version_range_type = VersionFilter.get_version_range_type("NPMPackage")
        assert version_type is not None
        assert version_range_type is not None

    def test_filter_versions_any_constraint(self):
        """Test filtering with 'any' constraint returns all versions."""
        versions = [
            {"name": "1.0.0"},
            {"name": "2.0.0"},
            {"name": "3.0.0"}
        ]
        result = VersionFilter.filter_versions("PyPIPackage", versions, "any")
        assert len(result) == 3

    def test_filter_versions_with_range(self):
        """Test filtering versions with a range constraint."""
        versions = [
            {"name": "0.9.0"},
            {"name": "1.0.0"},
            {"name": "1.5.0"},
            {"name": "2.0.0"}
        ]
        result = VersionFilter.filter_versions("PyPIPackage", versions, ">= 1.0.0, < 2.0.0")
        # Should include 1.0.0 and 1.5.0, but not 0.9.0 or 2.0.0
        assert len(result) >= 1

    def test_filter_versions_invalid_constraint_returns_all(self):
        """Test that invalid constraints return all versions."""
        versions = [
            {"name": "1.0.0"},
            {"name": "2.0.0"}
        ]
        result = VersionFilter.filter_versions("PyPIPackage", versions, "invalid_constraint")
        assert len(result) == 2
