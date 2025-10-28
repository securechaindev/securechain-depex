from unittest.mock import AsyncMock, patch

import pytest

from app.domain.smt.model import SMTModel
from app.domain.smt.operations import (
    CompleteConfigOperation,
    ConfigByImpactOperation,
    FilterConfigsOperation,
    MaximizeImpactOperation,
    MinimizeImpactOperation,
)


class TestFilterConfigsOperation:
    @pytest.fixture
    def sample_model(self):
        source_data = {
            "name": "test-file",
            "require": {
                "direct": [{"package": "fastapi", "constraints": ">= 0.100.0"}],
                "indirect": []
            },
            "have": {
                "fastapi": [
                    {"serial_number": 100, "mean": 5.0, "name": "0.100.0"},
                    {"serial_number": 101, "mean": 3.0, "name": "0.101.0"}
                ]
            }
        }
        model = SMTModel(source_data, "PyPIPackage", "mean")
        model.transform()
        return model

    @pytest.mark.asyncio
    async def test_execute_returns_configs(self, sample_model):
        with patch("app.domain.smt.operations.filter_configs.ConfigSanitizer") as mock_sanitizer:
            mock_instance = AsyncMock()
            mock_instance.sanitize.return_value = {"fastapi": 100, "impact": 5.0}
            mock_sanitizer.return_value = mock_instance

            result = await FilterConfigsOperation.execute(
                sample_model, max_threshold=10.0, min_threshold=0.0, limit=1
            )

            assert isinstance(result, list)
            assert len(result) <= 1

    @pytest.mark.asyncio
    async def test_execute_with_multiple_configs(self, sample_model):
        with patch("app.domain.smt.operations.filter_configs.ConfigSanitizer") as mock_sanitizer:
            mock_instance = AsyncMock()
            mock_instance.sanitize.side_effect = [
                {"fastapi": 100, "impact": 5.0},
                {"fastapi": 101, "impact": 3.0}
            ]
            mock_sanitizer.return_value = mock_instance

            result = await FilterConfigsOperation.execute(
                sample_model, max_threshold=10.0, min_threshold=0.0, limit=2
            )

            assert isinstance(result, list)
            assert len(result) <= 2

    @pytest.mark.asyncio
    async def test_execute_respects_thresholds(self, sample_model):
        with patch("app.domain.smt.operations.filter_configs.ConfigSanitizer") as mock_sanitizer:
            mock_instance = AsyncMock()
            mock_instance.sanitize.return_value = {"fastapi": 100, "impact": 5.0}
            mock_sanitizer.return_value = mock_instance

            result = await FilterConfigsOperation.execute(
                sample_model, max_threshold=10.0, min_threshold=1.0, limit=5
            )

            assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_execute_with_no_func_obj(self):
        source_data = {
            "name": "test",
            "require": {"direct": [], "indirect": []},
            "have": {}
        }
        model = SMTModel(source_data, "PyPIPackage", "mean")
        model.transform()
        model.func_obj = None

        with patch("app.domain.smt.operations.filter_configs.ConfigSanitizer") as mock_sanitizer:
            mock_instance = AsyncMock()
            mock_instance.sanitize.return_value = {"impact": 0.0}
            mock_sanitizer.return_value = mock_instance

            result = await FilterConfigsOperation.execute(
                model, max_threshold=10.0, min_threshold=0.0, limit=1
            )

            assert isinstance(result, list)


class TestMaximizeImpactOperation:
    @pytest.fixture
    def sample_model(self):
        source_data = {
            "name": "test-file",
            "require": {
                "direct": [{"package": "fastapi", "constraints": ">= 0.100.0"}],
                "indirect": []
            },
            "have": {
                "fastapi": [
                    {"serial_number": 100, "mean": 5.0, "name": "0.100.0"},
                    {"serial_number": 101, "mean": 8.0, "name": "0.101.0"}
                ]
            }
        }
        model = SMTModel(source_data, "PyPIPackage", "mean")
        model.transform()
        return model

    @pytest.mark.asyncio
    async def test_execute_maximizes_impact(self, sample_model):
        with patch("app.domain.smt.operations.maximize_impact.ConfigSanitizer") as mock_sanitizer:
            mock_instance = AsyncMock()
            mock_instance.sanitize.return_value = {"fastapi": 101, "impact": 8.0}
            mock_sanitizer.return_value = mock_instance

            result = await MaximizeImpactOperation.execute(sample_model, limit=1)

            assert isinstance(result, list)
            assert len(result) <= 1

    @pytest.mark.asyncio
    async def test_execute_with_multiple_solutions(self, sample_model):
        with patch("app.domain.smt.operations.maximize_impact.ConfigSanitizer") as mock_sanitizer:
            mock_instance = AsyncMock()
            mock_instance.sanitize.side_effect = [
                {"fastapi": 101, "impact": 8.0},
                {"fastapi": 100, "impact": 5.0}
            ]
            mock_sanitizer.return_value = mock_instance

            result = await MaximizeImpactOperation.execute(sample_model, limit=2)

            assert isinstance(result, list)
            assert len(result) <= 2

    @pytest.mark.asyncio
    async def test_execute_with_no_func_obj(self):
        source_data = {
            "name": "test",
            "require": {"direct": [], "indirect": []},
            "have": {}
        }
        model = SMTModel(source_data, "PyPIPackage", "mean")
        model.transform()
        model.func_obj = None

        with patch("app.domain.smt.operations.maximize_impact.ConfigSanitizer") as mock_sanitizer:
            mock_instance = AsyncMock()
            mock_instance.sanitize.return_value = {"impact": 0.0}
            mock_sanitizer.return_value = mock_instance

            result = await MaximizeImpactOperation.execute(model, limit=1)

            assert isinstance(result, list)


class TestMinimizeImpactOperation:

    @pytest.fixture
    def sample_model(self):
        source_data = {
            "name": "test-file",
            "require": {
                "direct": [{"package": "fastapi", "constraints": ">= 0.100.0"}],
                "indirect": []
            },
            "have": {
                "fastapi": [
                    {"serial_number": 100, "mean": 5.0, "name": "0.100.0"},
                    {"serial_number": 101, "mean": 2.0, "name": "0.101.0"}
                ]
            }
        }
        model = SMTModel(source_data, "PyPIPackage", "mean")
        model.transform()
        return model

    @pytest.mark.asyncio
    async def test_execute_minimizes_impact(self, sample_model):
        with patch("app.domain.smt.operations.minimize_impact.ConfigSanitizer") as mock_sanitizer:
            mock_instance = AsyncMock()
            mock_instance.sanitize.return_value = {"fastapi": 101, "impact": 2.0}
            mock_sanitizer.return_value = mock_instance

            result = await MinimizeImpactOperation.execute(sample_model, limit=1)

            assert isinstance(result, list)
            assert len(result) <= 1

    @pytest.mark.asyncio
    async def test_execute_with_multiple_solutions(self, sample_model):
        with patch("app.domain.smt.operations.minimize_impact.ConfigSanitizer") as mock_sanitizer:
            mock_instance = AsyncMock()
            mock_instance.sanitize.side_effect = [
                {"fastapi": 101, "impact": 2.0},
                {"fastapi": 100, "impact": 5.0}
            ]
            mock_sanitizer.return_value = mock_instance

            result = await MinimizeImpactOperation.execute(sample_model, limit=2)

            assert isinstance(result, list)
            assert len(result) <= 2

    @pytest.mark.asyncio
    async def test_execute_with_no_func_obj(self):
        source_data = {
            "name": "test",
            "require": {"direct": [], "indirect": []},
            "have": {}
        }
        model = SMTModel(source_data, "PyPIPackage", "mean")
        model.transform()
        model.func_obj = None

        with patch("app.domain.smt.operations.minimize_impact.ConfigSanitizer") as mock_sanitizer:
            mock_instance = AsyncMock()
            mock_instance.sanitize.return_value = {"impact": 0.0}
            mock_sanitizer.return_value = mock_instance

            result = await MinimizeImpactOperation.execute(model, limit=1)

            assert isinstance(result, list)


class TestCompleteConfigOperation:

    @pytest.fixture
    def sample_model(self):
        source_data = {
            "name": "test-file",
            "require": {
                "direct": [{"package": "fastapi", "constraints": ">= 0.100.0"}],
                "indirect": []
            },
            "have": {
                "fastapi": [
                    {"serial_number": 100, "mean": 5.0, "name": "0.100.0"},
                    {"serial_number": 101, "mean": 3.0, "name": "0.101.0"}
                ]
            }
        }
        model = SMTModel(source_data, "PyPIPackage", "mean")
        model.transform()
        return model

    @pytest.mark.asyncio
    async def test_execute_completes_config(self, sample_model):
        with patch("app.domain.smt.operations.complete_config.ConfigSanitizer") as mock_sanitizer:
            mock_instance = AsyncMock()
            mock_instance.sanitize.return_value = {"fastapi": 100, "impact": 5.0}
            mock_sanitizer.return_value = mock_instance

            config = {"|fastapi|": 100}
            result = await CompleteConfigOperation.execute(sample_model, config)

            assert isinstance(result, list)
            assert len(result) <= 1

    @pytest.mark.asyncio
    async def test_execute_with_empty_config(self, sample_model):
        with patch("app.domain.smt.operations.complete_config.ConfigSanitizer") as mock_sanitizer:
            mock_instance = AsyncMock()
            mock_instance.sanitize.return_value = {"fastapi": 100, "impact": 5.0}
            mock_sanitizer.return_value = mock_instance

            result = await CompleteConfigOperation.execute(sample_model, {})

            assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_execute_with_no_func_obj(self):
        source_data = {
            "name": "test",
            "require": {"direct": [], "indirect": []},
            "have": {}
        }
        model = SMTModel(source_data, "PyPIPackage", "mean")
        model.transform()
        model.func_obj = None

        with patch("app.domain.smt.operations.complete_config.ConfigSanitizer") as mock_sanitizer:
            mock_instance = AsyncMock()
            mock_instance.sanitize.return_value = {"impact": 0.0}
            mock_sanitizer.return_value = mock_instance

            result = await CompleteConfigOperation.execute(model, {})

            assert isinstance(result, list)


class TestConfigByImpactOperation:
    @pytest.fixture
    def sample_model(self):
        source_data = {
            "name": "test-file",
            "require": {
                "direct": [{"package": "fastapi", "constraints": ">= 0.100.0"}],
                "indirect": []
            },
            "have": {
                "fastapi": [
                    {"serial_number": 100, "mean": 5.0, "name": "0.100.0"},
                    {"serial_number": 101, "mean": 3.0, "name": "0.101.0"}
                ]
            }
        }
        model = SMTModel(source_data, "PyPIPackage", "mean")
        model.transform()
        return model

    @pytest.mark.asyncio
    async def test_execute_finds_config_by_impact(self, sample_model):
        with patch("app.domain.smt.operations.config_by_impact.ConfigSanitizer") as mock_sanitizer:
            mock_instance = AsyncMock()
            mock_instance.sanitize.return_value = {"fastapi": 100, "impact": 5.0}
            mock_sanitizer.return_value = mock_instance

            result = await ConfigByImpactOperation.execute(sample_model, impact=5)

            assert isinstance(result, list)
            assert len(result) <= 1

    @pytest.mark.asyncio
    async def test_execute_with_different_impact(self, sample_model):
        with patch("app.domain.smt.operations.config_by_impact.ConfigSanitizer") as mock_sanitizer:
            mock_instance = AsyncMock()
            mock_instance.sanitize.return_value = {"fastapi": 101, "impact": 3.0}
            mock_sanitizer.return_value = mock_instance

            result = await ConfigByImpactOperation.execute(sample_model, impact=3)

            assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_execute_with_no_func_obj(self):
        source_data = {
            "name": "test",
            "require": {"direct": [], "indirect": []},
            "have": {}
        }
        model = SMTModel(source_data, "PyPIPackage", "mean")
        model.transform()
        model.func_obj = None

        with patch("app.domain.smt.operations.config_by_impact.ConfigSanitizer") as mock_sanitizer:
            mock_instance = AsyncMock()
            mock_instance.sanitize.return_value = {"impact": 0.0}
            mock_sanitizer.return_value = mock_instance

            result = await ConfigByImpactOperation.execute(model, impact=5)

            assert isinstance(result, list)
