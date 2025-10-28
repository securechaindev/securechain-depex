from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from app.domain.repo_analyzer.requirement_files.cargo_toml_analyzer import (
    CargoTomlAnalyzer,
)


class TestCargoTomlAnalyzer:
    @pytest.mark.asyncio
    async def test_analyze_with_dependencies(self):
        analyzer = CargoTomlAnalyzer()
        requirement_files = {}

        with TemporaryDirectory() as tmpdir:
            cargo_toml = Path(tmpdir) / "Cargo.toml"
            cargo_toml.write_text("""[package]
            name = "myproject"
            version = "0.1.0"

            [dependencies]
            serde = "1.0"
            axum = "0.6.0"
            """)

            result = await analyzer.analyze(
                requirement_files, tmpdir, "Cargo.toml"
            )

            assert "Cargo.toml" in result
            assert result["Cargo.toml"]["manager"] == "Cargo"
            packages = result["Cargo.toml"]["packages"]
            assert "serde" in packages
            assert "axum" in packages

    @pytest.mark.asyncio
    async def test_analyze_with_dev_dependencies(self):
        analyzer = CargoTomlAnalyzer()
        requirement_files = {}

        with TemporaryDirectory() as tmpdir:
            cargo_toml = Path(tmpdir) / "Cargo.toml"
            cargo_toml.write_text("""[package]
            name = "myproject"
            version = "0.1.0"

            [dependencies]
            serde = "1.0"

            [dev-dependencies]
            tokio-test = "0.4"
            criterion = "0.5"
            """)

            result = await analyzer.analyze(
                requirement_files, tmpdir, "Cargo.toml"
            )

            packages = result["Cargo.toml"]["packages"]
            assert "serde" in packages

    @pytest.mark.asyncio
    async def test_analyze_empty_file(self):
        analyzer = CargoTomlAnalyzer()
        requirement_files = {}

        with TemporaryDirectory() as tmpdir:
            cargo_toml = Path(tmpdir) / "Cargo.toml"
            cargo_toml.write_text("")

            result = await analyzer.analyze(
                requirement_files, tmpdir, "Cargo.toml"
            )

            assert "Cargo.toml" in result
            assert result["Cargo.toml"]["manager"] == "Cargo"
            assert result["Cargo.toml"]["packages"] == {}

    @pytest.mark.asyncio
    async def test_analyze_no_dependencies(self):
        analyzer = CargoTomlAnalyzer()
        requirement_files = {}

        with TemporaryDirectory() as tmpdir:
            cargo_toml = Path(tmpdir) / "Cargo.toml"
            cargo_toml.write_text("""[package]
            name = "myproject"
            version = "0.1.0"
            edition = "2021"
            """)

            result = await analyzer.analyze(
                requirement_files, tmpdir, "Cargo.toml"
            )

            assert "Cargo.toml" in result
            assert result["Cargo.toml"]["packages"] == {}

    @pytest.mark.asyncio
    async def test_analyze_with_workspace(self):
        analyzer = CargoTomlAnalyzer()
        requirement_files = {}

        with TemporaryDirectory() as tmpdir:
            cargo_toml = Path(tmpdir) / "Cargo.toml"
            cargo_toml.write_text("""[workspace]
            members = ["crate1", "crate2"]

            [dependencies]
            serde = "1.0"
            tokio = "1.0"
            """)

            result = await analyzer.analyze(
                requirement_files, tmpdir, "Cargo.toml"
            )

            packages = result["Cargo.toml"]["packages"]
            assert "serde" in packages
            assert "tokio" in packages

    @pytest.mark.asyncio
    async def test_analyze_with_version_ranges(self):
        analyzer = CargoTomlAnalyzer()
        requirement_files = {}

        with TemporaryDirectory() as tmpdir:
            cargo_toml = Path(tmpdir) / "Cargo.toml"
            cargo_toml.write_text("""[dependencies]
            serde = ">=1.0.0"
            tokio = "^1.0"
            axum = "~0.6"
            reqwest = "1.*"
            """)

            result = await analyzer.analyze(
                requirement_files, tmpdir, "Cargo.toml"
            )

            packages = result["Cargo.toml"]["packages"]
            assert "serde" in packages
            assert "tokio" in packages
            assert "axum" in packages
            assert "reqwest" in packages

    @pytest.mark.asyncio
    async def test_analyze_file_not_found(self):
        analyzer = CargoTomlAnalyzer()
        requirement_files = {}

        with TemporaryDirectory() as tmpdir:
            result = await analyzer.analyze(
                requirement_files, tmpdir, "Cargo.toml"
            )

            assert "Cargo.toml" in result
            assert result["Cargo.toml"]["manager"] == "Cargo"
            assert result["Cargo.toml"]["packages"] == {}
