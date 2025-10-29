from unittest.mock import mock_open, patch

import pytest

from app.domain.repo_analyzer.requirement_files.cargo_lock_analyzer import (
    CargoLockAnalyzer,
)


class TestCargoLockAnalyzer:
    @pytest.fixture
    def analyzer(self):
        return CargoLockAnalyzer()

    def test_init(self, analyzer):
        assert analyzer.manager == "Cargo"

    def test_parse_file_with_packages(self, analyzer):
        cargo_lock_content = """
        [[package]]
        name = "serde"
        version = "1.0.152"

        [[package]]
        name = "tokio"
        version = "1.24.2"

        [[package]]
        name = "axum"
        version = "0.6.4"
        """
        with patch("builtins.open", mock_open(read_data=cargo_lock_content)):
            result = analyzer.parse_file("/fake/path", "Cargo.lock")

        assert result == {
            "serde": "== 1.0.152",
            "tokio": "== 1.24.2",
            "axum": "== 0.6.4"
        }

    def test_parse_file_empty_packages(self, analyzer):
        cargo_lock_content = """
        # This is a comment
        [metadata]
        """
        with patch("builtins.open", mock_open(read_data=cargo_lock_content)):
            result = analyzer.parse_file("/fake/path", "Cargo.lock")

        assert result == {}

    def test_parse_file_single_package(self, analyzer):
        cargo_lock_content = """
        [[package]]
        name = "libc"
        version = "0.2.139"
        """
        with patch("builtins.open", mock_open(read_data=cargo_lock_content)):
            result = analyzer.parse_file("/fake/path", "Cargo.lock")

        assert result == {"libc": "== 0.2.139"}

    def test_parse_file_missing_package_section(self, analyzer):
        cargo_lock_content = """
        [metadata]
        some = "data"
        """
        with patch("builtins.open", mock_open(read_data=cargo_lock_content)):
            result = analyzer.parse_file("/fake/path", "Cargo.lock")

        assert result == {}

    def test_parse_file_with_multiple_versions(self, analyzer):
        cargo_lock_content = """
        [[package]]
        name = "package1"
        version = "1.0.0"

        [[package]]
        name = "package2"
        version = "2.1.3"

        [[package]]
        name = "package3"
        version = "0.5.12"
        """
        with patch("builtins.open", mock_open(read_data=cargo_lock_content)):
            result = analyzer.parse_file("/fake/path", "Cargo.lock")

        assert result == {
            "package1": "== 1.0.0",
            "package2": "== 2.1.3",
            "package3": "== 0.5.12"
        }
