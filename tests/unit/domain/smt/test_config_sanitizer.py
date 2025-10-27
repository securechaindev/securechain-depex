"""Unit tests for ConfigSanitizer."""
from unittest.mock import AsyncMock, patch

import pytest
from z3 import Int, Real, Solver, sat

from app.domain.smt.config_sanitizer import ConfigSanitizer


class TestConfigSanitizer:
    """Test suite for ConfigSanitizer class."""

    @pytest.fixture
    def sanitizer(self):
        """Create a ConfigSanitizer instance."""
        with patch("app.domain.smt.config_sanitizer.config_sanitizer.ServiceContainer") as mock_container:
            mock_version_service = AsyncMock()
            mock_container.return_value.get_version_service.return_value = mock_version_service
            sanitizer = ConfigSanitizer()
            sanitizer._version_service = mock_version_service
            return sanitizer

    def test_singleton_pattern(self):
        """Test that ConfigSanitizer follows singleton pattern."""
        with patch("app.domain.smt.config_sanitizer.config_sanitizer.ServiceContainer"):
            sanitizer1 = ConfigSanitizer()
            sanitizer2 = ConfigSanitizer()
            assert sanitizer1 is sanitizer2

    @pytest.mark.asyncio
    async def test_sanitize_simple_config(self, sanitizer):
        """Test sanitize with simple integer configuration."""
        # Create a simple Z3 model
        solver = Solver()
        x = Int("fastapi")
        solver.add(x == 100)
        assert solver.check() == sat
        model = solver.model()

        sanitizer._version_service.read_releases_by_serial_numbers.return_value = {
            "fastapi": "0.100.0"
        }

        result = await sanitizer.sanitize("PyPIPackage", model)

        assert "fastapi" in result
        sanitizer._version_service.read_releases_by_serial_numbers.assert_called_once_with(
            "PyPIPackage", {"fastapi": 100}
        )

    @pytest.mark.asyncio
    async def test_sanitize_with_impact_variables(self, sanitizer):
        """Test sanitize with impact variables."""
        solver = Solver()
        x = Int("fastapi")
        impact_x = Real("impact_fastapi")
        solver.add(x == 100)
        solver.add(impact_x == 5.5)
        assert solver.check() == sat
        model = solver.model()

        sanitizer._version_service.read_releases_by_serial_numbers.return_value = {
            "fastapi": "0.100.0",
            "impact_fastapi": 5.5
        }

        result = await sanitizer.sanitize("PyPIPackage", model)

        # Verify impact variable is included
        sanitizer._version_service.read_releases_by_serial_numbers.assert_called_once()
        call_args = sanitizer._version_service.read_releases_by_serial_numbers.call_args[0][1]
        assert "fastapi" in call_args
        assert "impact_fastapi" in call_args

    @pytest.mark.asyncio
    async def test_sanitize_excludes_func_obj(self, sanitizer):
        """Test that func_obj variables are excluded."""
        solver = Solver()
        x = Int("fastapi")
        func = Int("func_obj")
        solver.add(x == 100)
        solver.add(func == 10)
        assert solver.check() == sat
        model = solver.model()

        sanitizer._version_service.read_releases_by_serial_numbers.return_value = {
            "fastapi": "0.100.0"
        }

        result = await sanitizer.sanitize("PyPIPackage", model)

        # func_obj should not be included
        call_args = sanitizer._version_service.read_releases_by_serial_numbers.call_args[0][1]
        assert "fastapi" in call_args
        assert "func_obj" not in call_args

    def test_extract_variable_value_integer(self, sanitizer):
        """Test extracting integer variable value."""
        solver = Solver()
        x = Int("package")
        solver.add(x == 42)
        assert solver.check() == sat
        model = solver.model()

        value = sanitizer.extract_variable_value(model, x)
        assert value == 42

    def test_extract_variable_value_rational(self, sanitizer):
        """Test extracting rational (float) variable value."""
        solver = Solver()
        x = Real("impact")
        solver.add(x == 3.14)
        assert solver.check() == sat
        model = solver.model()

        value = sanitizer.extract_variable_value(model, x)
        assert isinstance(value, float)
        assert value == 3.14

    def test_extract_variable_value_rational_with_fraction(self, sanitizer):
        """Test extracting rational value that needs division."""
        solver = Solver()
        x = Real("impact")
        solver.add(x * 3 == 10)  # x = 10/3 = 3.33...
        assert solver.check() == sat
        model = solver.model()

        value = sanitizer.extract_variable_value(model, x)
        assert isinstance(value, float)
        assert abs(value - 3.33) < 0.01  # Rounded to 2 decimals

    def test_extract_variable_value_minus_one(self, sanitizer):
        """Test that -1 values are treated as None."""
        solver = Solver()
        x = Int("package")
        solver.add(x == -1)
        assert solver.check() == sat
        model = solver.model()

        value = sanitizer.extract_variable_value(model, x)
        assert value is None

    def test_extract_variable_value_with_slash_zero(self, sanitizer):
        """Test that /0 variables are excluded."""
        solver = Solver()
        x = Int("/0")
        solver.add(x == 100)
        assert solver.check() == sat
        model = solver.model()

        value = sanitizer.extract_variable_value(model, x)
        assert value is None

    def test_process_impact_variables(self, sanitizer):
        """Test processing impact variables."""
        final_config = {"fastapi": 100, "django": 200}
        impact_vars = {"impact_fastapi": 5.5, "impact_django": 3.2, "impact_other": 1.0}

        sanitizer.process_impact_variables(final_config, impact_vars)

        # Only impact variables for existing packages should be added
        assert "impact_fastapi" in final_config
        assert final_config["impact_fastapi"] == 5.5
        assert "impact_django" in final_config
        assert final_config["impact_django"] == 3.2
        assert "impact_other" not in final_config  # No corresponding package

    def test_process_impact_variables_empty(self, sanitizer):
        """Test processing with no impact variables."""
        final_config = {"fastapi": 100}
        impact_vars = {}

        sanitizer.process_impact_variables(final_config, impact_vars)

        # Should not add any impact variables
        assert len(final_config) == 1
        assert "fastapi" in final_config

    @pytest.mark.asyncio
    async def test_sanitize_multiple_packages(self, sanitizer):
        """Test sanitize with multiple packages."""
        solver = Solver()
        x = Int("fastapi")
        y = Int("django")
        z = Int("flask")
        solver.add(x == 100)
        solver.add(y == 200)
        solver.add(z == 300)
        assert solver.check() == sat
        model = solver.model()

        sanitizer._version_service.read_releases_by_serial_numbers.return_value = {
            "fastapi": "0.100.0",
            "django": "4.2.0",
            "flask": "2.3.0"
        }

        result = await sanitizer.sanitize("PyPIPackage", model)

        call_args = sanitizer._version_service.read_releases_by_serial_numbers.call_args[0][1]
        assert len(call_args) == 3
        assert call_args["fastapi"] == 100
        assert call_args["django"] == 200
        assert call_args["flask"] == 300

    @pytest.mark.asyncio
    async def test_sanitize_filters_minus_one_values(self, sanitizer):
        """Test that -1 values are filtered out."""
        solver = Solver()
        x = Int("fastapi")
        y = Int("django")
        solver.add(x == 100)
        solver.add(y == -1)
        assert solver.check() == sat
        model = solver.model()

        sanitizer._version_service.read_releases_by_serial_numbers.return_value = {
            "fastapi": "0.100.0"
        }

        result = await sanitizer.sanitize("PyPIPackage", model)

        # Only fastapi should be in the final config
        call_args = sanitizer._version_service.read_releases_by_serial_numbers.call_args[0][1]
        assert "fastapi" in call_args
        assert "django" not in call_args
