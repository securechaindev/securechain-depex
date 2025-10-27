"""Unit tests for GemfileLockAnalyzer."""
import pytest
from unittest.mock import mock_open, patch

from app.domain.repo_analyzer.requirement_files.gemfile_lock_analyzer import GemfileLockAnalyzer


class TestGemfileLockAnalyzer:
    """Test suite for GemfileLockAnalyzer."""

    @pytest.fixture
    def analyzer(self):
        """Create a GemfileLockAnalyzer instance."""
        return GemfileLockAnalyzer()

    def test_init(self, analyzer):
        """Test GemfileLockAnalyzer initialization."""
        assert analyzer.manager == "RubyGems"

    def test_parse_file_with_gems(self, analyzer):
        """Test parsing a valid Gemfile.lock with gems."""
        gemfile_lock_content = """
GEM
  remote: https://rubygems.org/
  specs:
    rails (7.0.4)
    puma (5.6.5)
    pg (1.4.5)
"""
        with patch("builtins.open", mock_open(read_data=gemfile_lock_content)):
            result = analyzer._parse_file("/fake/path", "Gemfile.lock")

        assert result == {
            "rails": "== 7.0.4",
            "puma": "== 5.6.5",
            "pg": "== 1.4.5"
        }

    def test_parse_file_with_version_operators(self, analyzer):
        """Test parsing gems with version operators."""
        gemfile_lock_content = """
GEM
  specs:
    nokogiri (>= 1.6)
    rake (~> 13.0)
    rspec (< 4.0)
"""
        with patch("builtins.open", mock_open(read_data=gemfile_lock_content)):
            result = analyzer._parse_file("/fake/path", "Gemfile.lock")

        assert result == {
            "nokogiri": ">= 1.6",
            "rake": "~> 13.0",
            "rspec": "< 4.0"
        }

    def test_parse_file_empty(self, analyzer):
        """Test parsing an empty Gemfile.lock."""
        gemfile_lock_content = """
GEM
  remote: https://rubygems.org/
  specs:
"""
        with patch("builtins.open", mock_open(read_data=gemfile_lock_content)):
            result = analyzer._parse_file("/fake/path", "Gemfile.lock")

        assert result == {}

    def test_parse_file_single_gem(self, analyzer):
        """Test parsing a Gemfile.lock with a single gem."""
        gemfile_lock_content = """
GEM
  specs:
    bundler (2.3.26)
"""
        with patch("builtins.open", mock_open(read_data=gemfile_lock_content)):
            result = analyzer._parse_file("/fake/path", "Gemfile.lock")

        assert result == {"bundler": "== 2.3.26"}

    def test_parse_file_mixed_versions(self, analyzer):
        """Test parsing gems with mixed version formats."""
        gemfile_lock_content = """
GEM
  specs:
    standard_version (1.0.0)
    operator_version (>= 2.0)
    tilde_version (~> 3.1.0)
    less_than (< 5)
"""
        with patch("builtins.open", mock_open(read_data=gemfile_lock_content)):
            result = analyzer._parse_file("/fake/path", "Gemfile.lock")

        assert result == {
            "standard_version": "== 1.0.0",
            "operator_version": ">= 2.0",
            "tilde_version": "~> 3.1.0",
            "less_than": "< 5"
        }

    def test_parse_file_two_digit_version(self, analyzer):
        """Test parsing gems with two-digit versions (should not add ==)."""
        gemfile_lock_content = """
GEM
  specs:
    gem_two (1.0)
"""
        with patch("builtins.open", mock_open(read_data=gemfile_lock_content)):
            result = analyzer._parse_file("/fake/path", "Gemfile.lock")

        assert result == {"gem_two": "1.0"}

    def test_parse_file_four_digit_version(self, analyzer):
        """Test parsing gems with four-digit versions (should not add ==)."""
        gemfile_lock_content = """
GEM
  specs:
    gem_four (1.2.3.4)
"""
        with patch("builtins.open", mock_open(read_data=gemfile_lock_content)):
            result = analyzer._parse_file("/fake/path", "Gemfile.lock")

        assert result == {"gem_four": "1.2.3.4"}

    def test_parse_file_with_whitespace_variations(self, analyzer):
        """Test parsing with different whitespace patterns."""
        gemfile_lock_content = """
GEM
  specs:
      indented (1.0.0)
    normal (2.0.0)
      another (3.0.0)
"""
        with patch("builtins.open", mock_open(read_data=gemfile_lock_content)):
            result = analyzer._parse_file("/fake/path", "Gemfile.lock")

        assert result == {
            "indented": "== 1.0.0",
            "normal": "== 2.0.0",
            "another": "== 3.0.0"
        }
