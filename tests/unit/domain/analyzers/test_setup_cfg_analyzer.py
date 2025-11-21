from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from app.domain.repo_analyzer.requirement_files.setup_cfg_analyzer import (
    SetupCfgAnalyzer,
)


class TestSetupCfgAnalyzer:
    @pytest.mark.asyncio
    async def test_analyze_with_install_requires(self):
        analyzer = SetupCfgAnalyzer()
        requirement_files = {}

        with TemporaryDirectory() as tmpdir:
            setup_cfg = Path(tmpdir) / "setup.cfg"
            setup_cfg.write_text("""[metadata]
            name = myproject
            version = 1.0.0

            [options]
            install_requires =
                requests>=2.25.0
                numpy>=1.19.0
                pandas
            """)

            result = await analyzer.analyze(
                requirement_files, tmpdir, "setup.cfg"
            )

            assert "setup.cfg" in result
            assert result["setup.cfg"]["manager"] == "PyPI"
            packages = result["setup.cfg"]["packages"]
            assert "requests" in packages
            assert "numpy" in packages
            assert "pandas" in packages

    @pytest.mark.asyncio
    async def test_analyze_with_extras_require(self):
        analyzer = SetupCfgAnalyzer()
        requirement_files = {}

        with TemporaryDirectory() as tmpdir:
            setup_cfg = Path(tmpdir) / "setup.cfg"
            setup_cfg.write_text("""[metadata]
            name = myproject

            [options]
            install_requires =
                flask>=2.0.0

            [options.extras_require]
            dev =
                pytest>=7.0.0
                black
            test =
                coverage
            """)

            result = await analyzer.analyze(
                requirement_files, tmpdir, "setup.cfg"
            )

            assert "setup.cfg" in result
            packages = result["setup.cfg"]["packages"]
            assert "flask" in packages

    @pytest.mark.asyncio
    async def test_analyze_with_comments(self):
        analyzer = SetupCfgAnalyzer()
        requirement_files = {}

        with TemporaryDirectory() as tmpdir:
            setup_cfg = Path(tmpdir) / "setup.cfg"
            setup_cfg.write_text("""[metadata]
            name = myproject

            [options]
            install_requires =
                # This is a comment
                django>=3.2.0
                # Another comment
                celery>=5.0.0
            """)

            result = await analyzer.analyze(
                requirement_files, tmpdir, "setup.cfg"
            )

            packages = result["setup.cfg"]["packages"]
            assert "django" in packages
            assert "celery" in packages

    @pytest.mark.asyncio
    async def test_analyze_empty_file(self):
        analyzer = SetupCfgAnalyzer()
        requirement_files = {}

        with TemporaryDirectory() as tmpdir:
            setup_cfg = Path(tmpdir) / "setup.cfg"
            setup_cfg.write_text("")

            result = await analyzer.analyze(
                requirement_files, tmpdir, "setup.cfg"
            )

            assert "setup.cfg" in result
            assert result["setup.cfg"]["manager"] == "PyPI"
            assert result["setup.cfg"]["packages"] == {}

    @pytest.mark.asyncio
    async def test_analyze_no_dependencies(self):
        analyzer = SetupCfgAnalyzer()
        requirement_files = {}

        with TemporaryDirectory() as tmpdir:
            setup_cfg = Path(tmpdir) / "setup.cfg"
            setup_cfg.write_text("""[metadata]
            name = myproject
            version = 1.0.0
            author = Test Author
            """)

            result = await analyzer.analyze(
                requirement_files, tmpdir, "setup.cfg"
            )

            assert "setup.cfg" in result
            assert result["setup.cfg"]["packages"] == {}

    @pytest.mark.asyncio
    async def test_analyze_with_python_version_marker(self):
        analyzer = SetupCfgAnalyzer()
        requirement_files = {}

        with TemporaryDirectory() as tmpdir:
            setup_cfg = Path(tmpdir) / "setup.cfg"
            setup_cfg.write_text("""[options]
            install_requires =
                typing-extensions>=4.0.0; python_version<"3.10"
                importlib-metadata>=4.0.0; python_version>="3.14"
                backports.zoneinfo; python_version<"3.9"
            """)

            result = await analyzer.analyze(
                requirement_files, tmpdir, "setup.cfg"
            )

            packages = result["setup.cfg"]["packages"]
            assert "typing-extensions" not in packages
            assert "importlib-metadata" in packages
            assert "backports.zoneinfo" not in packages

    @pytest.mark.asyncio
    async def test_analyze_multiline_dependencies(self):
        analyzer = SetupCfgAnalyzer()
        requirement_files = {}

        with TemporaryDirectory() as tmpdir:
            setup_cfg = Path(tmpdir) / "setup.cfg"
            setup_cfg.write_text("""[options]
            install_requires =
                fastapi>=0.100.0
                uvicorn[standard]>=0.20.0
                pydantic>=2.0.0
                sqlalchemy>=2.0.0
            """)

            result = await analyzer.analyze(
                requirement_files, tmpdir, "setup.cfg"
            )

            packages = result["setup.cfg"]["packages"]
            assert "fastapi" in packages
            assert "uvicorn" in packages
            assert "pydantic" in packages
            assert "sqlalchemy" in packages
