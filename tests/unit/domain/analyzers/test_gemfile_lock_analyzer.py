from unittest.mock import mock_open, patch

import pytest

from app.domain.repo_analyzer.requirement_files.gemfile_lock_analyzer import (
    GemfileLockAnalyzer,
)


class TestGemfileLockAnalyzer:
    @pytest.fixture
    def analyzer(self):
        return GemfileLockAnalyzer()

    def test_init(self, analyzer):
        assert analyzer.manager == "RubyGems"

    def test_parse_file_with_gems(self, analyzer):
        gemfile_lock_content = """
        GEM
        remote: https://rubygems.org/
        specs:
            rails (7.0.4)
            puma (5.6.5)
            pg (1.4.5)
        """
        with patch("builtins.open", mock_open(read_data=gemfile_lock_content)):
            result = analyzer.parse_file("/fake/path", "Gemfile.lock")

        assert result == {
            "rails": "== 7.0.4",
            "puma": "== 5.6.5",
            "pg": "== 1.4.5"
        }

    def test_parse_file_with_version_operators(self, analyzer):
        gemfile_lock_content = """
        GEM
        specs:
            nokogiri (>= 1.6)
            rake (~> 13.0)
            rspec (< 4.0)
        """
        with patch("builtins.open", mock_open(read_data=gemfile_lock_content)):
            result = analyzer.parse_file("/fake/path", "Gemfile.lock")

        assert result == {
            "nokogiri": ">= 1.6",
            "rake": "~> 13.0",
            "rspec": "< 4.0"
        }

    def test_parse_file_empty(self, analyzer):
        gemfile_lock_content = """
        GEM
        remote: https://rubygems.org/
        specs:
        """
        with patch("builtins.open", mock_open(read_data=gemfile_lock_content)):
            result = analyzer.parse_file("/fake/path", "Gemfile.lock")

        assert result == {}

    def test_parse_file_single_gem(self, analyzer):
        gemfile_lock_content = """
        GEM
        specs:
            bundler (2.3.26)
        """
        with patch("builtins.open", mock_open(read_data=gemfile_lock_content)):
            result = analyzer.parse_file("/fake/path", "Gemfile.lock")

        assert result == {"bundler": "== 2.3.26"}

        gemfile_lock_content = """
        GEM
        specs:
            standard_version (1.0.0)
            operator_version (>= 2.0)
            tilde_version (~> 3.1.0)
            less_than (< 5)
        """
        with patch("builtins.open", mock_open(read_data=gemfile_lock_content)):
            result = analyzer.parse_file("/fake/path", "Gemfile.lock")

        assert result == {
            "standard_version": "== 1.0.0",
            "operator_version": ">= 2.0",
            "tilde_version": "~> 3.1.0",
            "less_than": "< 5"
        }

    def test_parse_file_two_digit_version(self, analyzer):
        gemfile_lock_content = """
        GEM
        specs:
            gem_two (1.0)
        """
        with patch("builtins.open", mock_open(read_data=gemfile_lock_content)):
            result = analyzer.parse_file("/fake/path", "Gemfile.lock")

        assert result == {"gem_two": "1.0"}

    def test_parse_file_four_digit_version(self, analyzer):
        gemfile_lock_content = """
        GEM
        specs:
            gem_four (1.2.3.4)
        """
        with patch("builtins.open", mock_open(read_data=gemfile_lock_content)):
            result = analyzer.parse_file("/fake/path", "Gemfile.lock")

        assert result == {"gem_four": "1.2.3.4"}

    def test_parse_file_with_whitespace_variations(self, analyzer):
        gemfile_lock_content = """
        GEM
        specs:
            indented (1.0.0)
            normal (2.0.0)
            another (3.0.0)
        """
        with patch("builtins.open", mock_open(read_data=gemfile_lock_content)):
            result = analyzer.parse_file("/fake/path", "Gemfile.lock")

        assert result == {
            "indented": "== 1.0.0",
            "normal": "== 2.0.0",
            "another": "== 3.0.0"
        }
