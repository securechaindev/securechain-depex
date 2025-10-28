import json
from unittest.mock import mock_open, patch

import pytest

from app.domain.repo_analyzer.requirement_files.package_lock_json_analyzer import (
    PackageLockJsonAnalyzer,
)


class TestPackageLockJsonAnalyzer:
    @pytest.fixture
    def analyzer(self):
        return PackageLockJsonAnalyzer()

    def test_init(self, analyzer):
        assert analyzer.manager == "NPM"

    def test_parse_file_with_dependencies(self, analyzer):
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
        package_lock_data = {"name": "my-project", "version": "1.0.0"}
        with patch("builtins.open", mock_open(read_data=json.dumps(package_lock_data))):
            result = analyzer._parse_file("/fake/path", "package-lock.json")

        assert result == {}

    def test_parse_file_empty_dependencies(self, analyzer):
        package_lock_data = {"dependencies": {}}
        with patch("builtins.open", mock_open(read_data=json.dumps(package_lock_data))):
            result = analyzer._parse_file("/fake/path", "package-lock.json")

        assert result == {}

    def test_parse_file_single_dependency(self, analyzer):
        package_lock_data = {
            "dependencies": {
                "react": {"version": "18.2.0"}
            }
        }
        with patch("builtins.open", mock_open(read_data=json.dumps(package_lock_data))):
            result = analyzer._parse_file("/fake/path", "package-lock.json")

        assert result == {"react": "== 18.2.0"}

    def test_parse_file_missing_version(self, analyzer):
        package_lock_data = {
            "dependencies": {
                "package1": {"version": "1.0.0"},
                "package2": {},
                "package3": {"version": "2.0.0"}
            }
        }
        with patch("builtins.open", mock_open(read_data=json.dumps(package_lock_data))):
            result = analyzer._parse_file("/fake/path", "package-lock.json")

        assert result == {
            "package1": "== 1.0.0",
            "package2": None,
            "package3": "== 2.0.0"
        }

    def test_parse_file_version_with_operators(self, analyzer):
        package_lock_data = {
            "dependencies": {
                "pkg1": {"version": "^1.0.0"},
                "pkg2": {"version": "~2.1.3"},
                "pkg3": {"version": ">=3.0.0"}
            }
        }
        with patch("builtins.open", mock_open(read_data=json.dumps(package_lock_data))):
            result = analyzer._parse_file("/fake/path", "package-lock.json")

        assert result == {
            "pkg1": "== ^1.0.0",
            "pkg2": "== ~2.1.3",
            "pkg3": ">=3.0.0"
        }

    def test_parse_file_two_digit_version(self, analyzer):
        package_lock_data = {
            "dependencies": {
                "pkg": {"version": "1.0"}
            }
        }
        with patch("builtins.open", mock_open(read_data=json.dumps(package_lock_data))):
            result = analyzer._parse_file("/fake/path", "package-lock.json")

        assert result == {"pkg": "1.0"}

    def test_parse_file_four_digit_version(self, analyzer):
        package_lock_data = {
            "dependencies": {
                "pkg": {"version": "1.2.3.4"}
            }
        }
        with patch("builtins.open", mock_open(read_data=json.dumps(package_lock_data))):
            result = analyzer._parse_file("/fake/path", "package-lock.json")

        assert result == {"pkg": "1.2.3.4"}

    def test_parse_file_mixed_versions(self, analyzer):
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
            "caret": "== ^2.0.0",
            "tilde": "== ~3.1.0",
            "gte": ">=4.0.0",
            "range": "1.0.0 - 2.0.0"
        }
