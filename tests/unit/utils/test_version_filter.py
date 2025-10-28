
from app.utils.version_filter import VersionFilter


class TestVersionFilter:

    def test_get_version_range_type_pypi(self):
        version_type, version_range_type = VersionFilter.get_version_range_type("PyPIPackage")
        assert version_type is not None
        assert version_range_type is not None

    def test_get_version_range_type_npm(self):
        version_type, version_range_type = VersionFilter.get_version_range_type("NPMPackage")
        assert version_type is not None
        assert version_range_type is not None

    def test_filter_versions_any_constraint(self):
        versions = [
            {"name": "1.0.0"},
            {"name": "2.0.0"},
            {"name": "3.0.0"}
        ]
        result = VersionFilter.filter_versions("PyPIPackage", versions, "any")
        assert len(result) == 3

    def test_filter_versions_with_range(self):
        versions = [
            {"name": "0.9.0"},
            {"name": "1.0.0"},
            {"name": "1.5.0"},
            {"name": "2.0.0"}
        ]
        result = VersionFilter.filter_versions("PyPIPackage", versions, ">= 1.0.0, < 2.0.0")
        assert len(result) >= 1

    def test_filter_versions_invalid_constraint_returns_all(self):
        versions = [
            {"name": "1.0.0"},
            {"name": "2.0.0"}
        ]
        result = VersionFilter.filter_versions("PyPIPackage", versions, "invalid_constraint")
        assert len(result) == 2
