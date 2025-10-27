"""Unit tests for PackageLockJsonAnalyzer."""
import pytest
from unittest.mock import mock_open, patch
import json

from app.domain.repo_analyzer.requirement_files.package_lock_json_analyzer import PackageLockJsonAnalyzer


class TestPackageLockJsonAnalyzer:
    """Test suite for PackageLockJsonAnalyzer."""

    @pytest.fixture
    def analyzer(self):
        """Create a PackageLockJsonAnalyzer instance."""
        return PackageLockJsonAnalyzer()

    def test_init(self, analyzer):
        """Test PackageLockJsonAnalyzer initialization."""
        assert analyzer.manager == "NPM"

    def test_parse_file_with_dependencies(self, analyzer):
        """Test parsing a valid package-lock.json with dependencies."""
        package_lock_data = {
            "dependencies": {
                "express": {"version": "4.18.2"},
                "lodash": {"version": "4.17.21"},
                "axios": {"version": "1.2.3"}
            }
        }
        with patch("builtins.open", mock_open(read_data=json.dumps(package_lock_data))):
            result = analyzer._parse_file("/fake/path", "package-lock.json")

        assert result == {
            "express": "== 4.18.2",
            "lodash": "== 4.17.21",
            "axios": "== 1.2.3"
        }

    def test_parse_file_no_dependencies(self, analyzer):
        """Test parsing a package-lock.json without dependencies."""
        package_lock_data = {"name": "my-project", "version": "1.0.0"}
        with patch("builtins.open", mock_open(read_data=json.dumps(package_lock_data))):
            result = analyzer._parse_file("/fake/path", "package-lock.json")

        assert result == {}

    def test_parse_file_empty_dependencies(self, analyzer):
        """Test parsing a package-lock.json with empty dependencies."""
        package_lock_data = {"dependencies": {}}
        with patch("builtins.open", mock_open(read_data=json.dumps(package_lock_data))):
            result = analyzer._parse_file("/fake/path", "package-lock.json")

        assert result == {}

    def test_parse_file_single_dependency(self, analyzer):
        """Test parsing a package-lock.json with a single dependency."""
        package_lock_data = {
            "dependencies": {
                "react": {"version": "18.2.0"}
            }
        }
        with patch("builtins.open", mock_open(read_data=json.dumps(package_lock_data))):
            result = analyzer._parse_file("/fake/path", "package-lock.json")

        assert result == {"react": "== 18.2.0"}

    def test_parse_file_missing_version(self, analyzer):
        """Test parsing when a dependency is missing version."""
        package_lock_data = {
            "dependencies": {
                "package1": {"version": "1.0.0"},
                "package2": {},  # No version
                "package3": {"version": "2.0.0"}
            }
        }
        with patch("builtins.open", mock_open(read_data=json.dumps(package_lock_data))):
            result = analyzer._parse_file("/fake/path", "package-lock.json")

        # package2 should be included with None as version
        assert result == {
            "package1": "== 1.0.0",
            "package2": None,
            "package3": "== 2.0.0"
        }

    def test_parse_file_version_with_operators(self, analyzer):
        """Test parsing versions with comparison operators."""
        package_lock_data = {
            "dependencies": {
                "pkg1": {"version": "^1.0.0"},
                "pkg2": {"version": "~2.1.3"},
                "pkg3": {"version": ">=3.0.0"}
            }
        }
        with patch("builtins.open", mock_open(read_data=json.dumps(package_lock_data))):
            result = analyzer._parse_file("/fake/path", "package-lock.json")

        # ^ and ~ are not in the operator list, so they get "==" prefix
        # Only <, >, = are checked
        assert result == {
            "pkg1": "== ^1.0.0",
            "pkg2": "== ~2.1.3",
            "pkg3": ">=3.0.0"
        }

    def test_parse_file_two_digit_version(self, analyzer):
        """Test parsing with two-digit versions."""
        package_lock_data = {
            "dependencies": {
                "pkg": {"version": "1.0"}
            }
        }
        with patch("builtins.open", mock_open(read_data=json.dumps(package_lock_data))):
            result = analyzer._parse_file("/fake/path", "package-lock.json")

        # Should not add "==" for non-standard versions
        assert result == {"pkg": "1.0"}

    def test_parse_file_four_digit_version(self, analyzer):
        """Test parsing with four-digit versions."""
        package_lock_data = {
            "dependencies": {
                "pkg": {"version": "1.2.3.4"}
            }
        }
        with patch("builtins.open", mock_open(read_data=json.dumps(package_lock_data))):
            result = analyzer._parse_file("/fake/path", "package-lock.json")

        # Should not add "==" for non-standard versions
        assert result == {"pkg": "1.2.3.4"}

    def test_parse_file_mixed_versions(self, analyzer):
        """Test parsing with mixed version formats."""
        package_lock_data = {
            "dependencies": {
                "standard": {"version": "1.2.3"},
                "caret": {"version": "^2.0.0"},
                "tilde": {"version": "~3.1.0"},
                "gte": {"version": ">=4.0.0"},
                "range": {"version": "1.0.0 - 2.0.0"}
            }
        }
        with patch("builtins.open", mock_open(read_data=json.dumps(package_lock_data))):
            result = analyzer._parse_file("/fake/path", "package-lock.json")

        assert result == {
            "standard": "== 1.2.3",
            "caret": "== ^2.0.0",  # ^ is not in operator list
            "tilde": "== ~3.1.0",  # ~ is not in operator list
            "gte": ">=4.0.0",
            "range": "1.0.0 - 2.0.0"
        }
