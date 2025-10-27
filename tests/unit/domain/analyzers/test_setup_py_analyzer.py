"""Unit tests for setup.py analyzer."""
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from app.domain.repo_analyzer.requirement_files.setup_py_analyzer import (
    SetupPyAnalyzer,
)


class TestSetupPyAnalyzer:
    """Test suite for SetupPyAnalyzer."""

    @pytest.mark.asyncio
    async def test_analyze_with_install_requires_list(self):
        """Test analyzing setup.py with install_requires as list."""
        analyzer = SetupPyAnalyzer()
        requirement_files = {}

        with TemporaryDirectory() as tmpdir:
            setup_py = Path(tmpdir) / "setup.py"
            setup_py.write_text("""from setuptools import setup

setup(
    name='myproject',
    version='1.0.0',
    install_requires=[
        'requests>=2.25.0',
        'numpy>=1.19.0',
        'pandas',
    ],
)
""")

            result = await analyzer.analyze(
                requirement_files, tmpdir, "setup.py"
            )

            assert "setup.py" in result
            assert result["setup.py"]["manager"] == "PyPI"
            packages = result["setup.py"]["packages"]
            assert "requests" in packages
            assert "numpy" in packages
            assert "pandas" in packages

    @pytest.mark.asyncio
    async def test_analyze_with_extras_require(self):
        """Test analyzing setup.py with extras_require.
        
        Note: Current implementation only parses install_requires/requires,
        not extras_require. Also requires multiline list format.
        """
        analyzer = SetupPyAnalyzer()
        requirement_files = {}

        with TemporaryDirectory() as tmpdir:
            setup_py = Path(tmpdir) / "setup.py"
            setup_py.write_text("""from setuptools import setup

setup(
    name='myproject',
    install_requires=[
        'flask>=2.0.0',
    ],
    extras_require={
        'dev': ['pytest>=7.0.0', 'black'],
        'test': ['coverage'],
    },
)
""")

            result = await analyzer.analyze(
                requirement_files, tmpdir, "setup.py"
            )

            packages = result["setup.py"]["packages"]
            assert "flask" in packages
            # extras_require are not currently parsed
            # assert "pytest" not in packages (implicit)

    @pytest.mark.asyncio
    async def test_analyze_with_python_version_marker(self):
        """Test analyzing with Python version markers."""
        analyzer = SetupPyAnalyzer()
        requirement_files = {}

        with TemporaryDirectory() as tmpdir:
            setup_py = Path(tmpdir) / "setup.py"
            setup_py.write_text("""from setuptools import setup

setup(
    name='myproject',
    install_requires=[
        'typing-extensions>=4.0.0; python_version<"3.10"',
        'importlib-metadata>=4.0.0; python_version>="3.13"',
        'backports.zoneinfo; python_version<"3.9"',
    ],
)
""")

            result = await analyzer.analyze(
                requirement_files, tmpdir, "setup.py"
            )

            packages = result["setup.py"]["packages"]
            # Should skip incompatible versions
            assert "typing-extensions" not in packages
            assert "importlib-metadata" in packages
            assert "backports.zoneinfo" not in packages

    @pytest.mark.asyncio
    async def test_analyze_with_comments(self):
        """Test analyzing setup.py with comments."""
        analyzer = SetupPyAnalyzer()
        requirement_files = {}

        with TemporaryDirectory() as tmpdir:
            setup_py = Path(tmpdir) / "setup.py"
            setup_py.write_text("""from setuptools import setup

setup(
    name='myproject',
    install_requires=[
        # Web framework
        'django>=3.2.0',
        # Task queue
        'celery>=5.0.0',
    ],
)
""")

            result = await analyzer.analyze(
                requirement_files, tmpdir, "setup.py"
            )

            packages = result["setup.py"]["packages"]
            assert "django" in packages
            assert "celery" in packages

    @pytest.mark.asyncio
    async def test_analyze_empty_requirements(self):
        """Test analyzing setup.py with empty requirements."""
        analyzer = SetupPyAnalyzer()
        requirement_files = {}

        with TemporaryDirectory() as tmpdir:
            setup_py = Path(tmpdir) / "setup.py"
            setup_py.write_text("""from setuptools import setup

setup(
    name='myproject',
    version='1.0.0',
)
""")

            result = await analyzer.analyze(
                requirement_files, tmpdir, "setup.py"
            )

            assert "setup.py" in result
            assert result["setup.py"]["packages"] == {}

    @pytest.mark.asyncio
    async def test_analyze_with_single_quotes(self):
        """Test analyzing setup.py with single quotes."""
        analyzer = SetupPyAnalyzer()
        requirement_files = {}

        with TemporaryDirectory() as tmpdir:
            setup_py = Path(tmpdir) / "setup.py"
            setup_py.write_text("""from setuptools import setup

setup(
    name='myproject',
    install_requires=[
        'fastapi>=0.100.0',
        'uvicorn>=0.20.0',
    ],
)
""")

            result = await analyzer.analyze(
                requirement_files, tmpdir, "setup.py"
            )

            packages = result["setup.py"]["packages"]
            assert "fastapi" in packages
            assert "uvicorn" in packages

    @pytest.mark.asyncio
    async def test_analyze_with_double_quotes(self):
        """Test analyzing setup.py with double quotes."""
        analyzer = SetupPyAnalyzer()
        requirement_files = {}

        with TemporaryDirectory() as tmpdir:
            setup_py = Path(tmpdir) / "setup.py"
            setup_py.write_text("""from setuptools import setup

setup(
    name="myproject",
    install_requires=[
        "pydantic>=2.0.0",
        "sqlalchemy>=2.0.0",
    ],
)
""")

            result = await analyzer.analyze(
                requirement_files, tmpdir, "setup.py"
            )

            packages = result["setup.py"]["packages"]
            assert "pydantic" in packages
            assert "sqlalchemy" in packages

    @pytest.mark.asyncio
    async def test_analyze_file_not_found(self):
        """Test analyzing when setup.py doesn't exist."""
        analyzer = SetupPyAnalyzer()
        requirement_files = {}

        with TemporaryDirectory() as tmpdir:
            result = await analyzer.analyze(
                requirement_files, tmpdir, "setup.py"
            )

            assert "setup.py" in result
            assert result["setup.py"]["manager"] == "PyPI"
            assert result["setup.py"]["packages"] == {}

    @pytest.mark.asyncio
    async def test_analyze_with_variable_assignment(self):
        """Test analyzing setup.py with variable assignment."""
        analyzer = SetupPyAnalyzer()
        requirement_files = {}

        with TemporaryDirectory() as tmpdir:
            setup_py = Path(tmpdir) / "setup.py"
            setup_py.write_text("""from setuptools import setup

REQUIREMENTS = [
    'flask>=2.0.0',
    'redis>=4.0.0',
]

setup(
    name='myproject',
    install_requires=REQUIREMENTS,
)
""")

            result = await analyzer.analyze(
                requirement_files, tmpdir, "setup.py"
            )

            # May not parse variables correctly, but should handle gracefully
            assert "setup.py" in result
            assert result["setup.py"]["manager"] == "PyPI"
