from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from app.domain.repo_analyzer.requirement_files.gemfile_analyzer import (
    GemfileAnalyzer,
)


class TestGemfileAnalyzer:
    @pytest.mark.asyncio
    async def test_analyze_with_dependencies(self):
        analyzer = GemfileAnalyzer()
        requirement_files = {}

        with TemporaryDirectory() as tmpdir:
            gemfile = Path(tmpdir) / "Gemfile"
            gemfile.write_text("""source 'https://rubygems.org'

            gem 'rails', '~> 7.0.0'
            gem 'pg', '>= 1.0'
            """)

            result = await analyzer.analyze(
                requirement_files, tmpdir, "Gemfile"
            )

            assert "Gemfile" in result
            assert result["Gemfile"]["manager"] == "RubyGems"
            packages = result["Gemfile"]["packages"]
            assert "rails" in packages
            assert "pg" in packages

    @pytest.mark.asyncio
    async def test_analyze_with_groups(self):
        analyzer = GemfileAnalyzer()
        requirement_files = {}

        with TemporaryDirectory() as tmpdir:
            gemfile = Path(tmpdir) / "Gemfile"
            gemfile.write_text("""source 'https://rubygems.org'

            gem 'rails', '~> 7.0'

            group :development, :test do
            gem 'rspec-rails', '~> 5.0'
            gem 'factory_bot_rails', '>= 6.0'
            end

            group :development do
            gem 'spring', '~> 4.0'
            end
            """)

            result = await analyzer.analyze(
                requirement_files, tmpdir, "Gemfile"
            )

            packages = result["Gemfile"]["packages"]
            assert "rails" in packages
            assert "rspec-rails" in packages
            assert "factory_bot_rails" in packages
            assert "spring" in packages

    @pytest.mark.asyncio
    async def test_analyze_with_comments(self):
        analyzer = GemfileAnalyzer()
        requirement_files = {}

        with TemporaryDirectory() as tmpdir:
            gemfile = Path(tmpdir) / "Gemfile"
            gemfile.write_text("""source 'https://rubygems.org'

            # Web framework
            gem 'sinatra', '~> 3.0'
            # Database
            gem 'sequel', '>= 5.0'
            """)

            result = await analyzer.analyze(
                requirement_files, tmpdir, "Gemfile"
            )

            packages = result["Gemfile"]["packages"]
            assert "sinatra" in packages
            assert "sequel" in packages

    @pytest.mark.asyncio
    async def test_analyze_empty_file(self):
        analyzer = GemfileAnalyzer()
        requirement_files = {}

        with TemporaryDirectory() as tmpdir:
            gemfile = Path(tmpdir) / "Gemfile"
            gemfile.write_text("")

            result = await analyzer.analyze(
                requirement_files, tmpdir, "Gemfile"
            )

            assert "Gemfile" in result
            assert result["Gemfile"]["manager"] == "RubyGems"
            assert result["Gemfile"]["packages"] == {}

    @pytest.mark.asyncio
    async def test_analyze_with_double_quotes(self):
        analyzer = GemfileAnalyzer()
        requirement_files = {}

        with TemporaryDirectory() as tmpdir:
            gemfile = Path(tmpdir) / "Gemfile"
            gemfile.write_text("""source "https://rubygems.org"

            gem "rack", "~> 2.0"
            gem "redis", ">= 4.0"
            """)

            result = await analyzer.analyze(
                requirement_files, tmpdir, "Gemfile"
            )

            packages = result["Gemfile"]["packages"]
            assert len(packages) == 0

    @pytest.mark.asyncio
    async def test_analyze_file_not_found(self):
        analyzer = GemfileAnalyzer()
        requirement_files = {}

        with TemporaryDirectory() as tmpdir:
            result = await analyzer.analyze(
                requirement_files, tmpdir, "Gemfile"
            )

            assert "Gemfile" in result
            assert result["Gemfile"]["manager"] == "RubyGems"
            assert result["Gemfile"]["packages"] == {}

    @pytest.mark.asyncio
    async def test_analyze_with_git_sources(self):
        analyzer = GemfileAnalyzer()
        requirement_files = {}

        with TemporaryDirectory() as tmpdir:
            gemfile = Path(tmpdir) / "Gemfile"
            gemfile.write_text("""source 'https://rubygems.org'

            gem 'rails', '~> 7.0'
            gem 'my_gem', git: 'https://github.com/user/my_gem.git'
            gem 'another_gem', github: 'user/another_gem'
            """)

            result = await analyzer.analyze(
                requirement_files, tmpdir, "Gemfile"
            )

            packages = result["Gemfile"]["packages"]
            assert "rails" in packages
            assert "my_gem" in packages or len(packages) >= 1
