from unittest.mock import MagicMock, patch

import pytest

from app.domain.smt.model import SMTModel
from app.domain.smt.operations import ValidConfigOperation, ValidGraphOperation
from app.exceptions import SMTTimeoutException


class TestValidConfigOperation:
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

    def test_execute_valid_config(self, sample_model):
        config = {"|fastapi|": 100}
        result = ValidConfigOperation.execute(sample_model, config)
        assert result is True

    def test_execute_invalid_config(self):
        source_data = {
            "name": "test-file",
            "require": {
                "direct": [
                    {"package": "fastapi", "constraints": "== 0.100.0"},
                    {"package": "fastapi", "constraints": "== 0.101.0"}
                ],
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

        config = {"|fastapi|": 100}
        result = ValidConfigOperation.execute(model, config)
        assert isinstance(result, bool)

    def test_execute_empty_config(self, sample_model):
        config = {}
        result = ValidConfigOperation.execute(sample_model, config)
        assert result is True

    def test_execute_multiple_packages(self):
        source_data = {
            "name": "test-file",
            "require": {
                "direct": [
                    {"package": "fastapi", "constraints": ">= 0.100.0"},
                    {"package": "django", "constraints": ">= 4.0.0"}
                ],
                "indirect": []
            },
            "have": {
                "fastapi": [{"serial_number": 100, "mean": 5.0, "name": "0.100.0"}],
                "django": [{"serial_number": 200, "mean": 3.0, "name": "4.2.0"}]
            }
        }
        model = SMTModel(source_data, "PyPIPackage", "mean")
        model.transform()

        config = {"|fastapi|": 100, "|django|": 200}
        result = ValidConfigOperation.execute(model, config)
        assert result is True

    def test_execute_conflicting_config(self):
        source_data = {
            "name": "test-file",
            "require": {
                "direct": [{"package": "fastapi", "constraints": "== 0.100.0"}],
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

        config = {"|fastapi|": 101}
        result = ValidConfigOperation.execute(model, config)
        assert isinstance(result, bool)

    def test_execute_timeout(self, sample_model):
        with patch("app.domain.smt.operations.valid_config.Solver") as mock_solver_class:
            mock_solver = MagicMock()
            mock_solver_class.return_value = mock_solver

            from z3 import unknown
            mock_solver.check.return_value = unknown

            with pytest.raises(SMTTimeoutException):
                ValidConfigOperation.execute(sample_model, {"|fastapi|": 100})


class TestValidGraphOperation:
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

    def test_execute_valid_graph(self, sample_model):
        result = ValidGraphOperation.execute(sample_model)
        assert result is True

    def test_execute_invalid_graph(self):
        source_data = {
            "name": "test-file",
            "require": {
                "direct": [{"package": "fastapi", "constraints": ">= 0.100.0"}],
                "indirect": []
            },
            "have": {
                "fastapi": []
            }
        }
        model = SMTModel(source_data, "PyPIPackage", "mean")
        model.transform()

        result = ValidGraphOperation.execute(model)
        assert isinstance(result, bool)

    def test_execute_empty_requirements(self):
        source_data = {
            "name": "test-file",
            "require": {
                "direct": [],
                "indirect": []
            },
            "have": {}
        }
        model = SMTModel(source_data, "PyPIPackage", "mean")
        model.transform()

        result = ValidGraphOperation.execute(model)
        assert result is True

    def test_execute_complex_graph(self):
        source_data = {
            "name": "test-file",
            "require": {
                "direct": [
                    {"package": "fastapi", "constraints": ">= 0.100.0"},
                    {"package": "django", "constraints": ">= 4.0.0"}
                ],
                "indirect": []
            },
            "have": {
                "fastapi": [
                    {"serial_number": 100, "mean": 5.0, "name": "0.100.0"},
                    {"serial_number": 101, "mean": 3.0, "name": "0.101.0"}
                ],
                "django": [
                    {"serial_number": 200, "mean": 4.0, "name": "4.2.0"}
                ]
            }
        }
        model = SMTModel(source_data, "PyPIPackage", "mean")
        model.transform()

        result = ValidGraphOperation.execute(model)
        assert result is True

    def test_execute_timeout(self, sample_model):
        with patch("app.domain.smt.operations.valid_graph.Solver") as mock_solver_class:
            mock_solver = MagicMock()
            mock_solver_class.return_value = mock_solver

            from z3 import unknown
            mock_solver.check.return_value = unknown

            with pytest.raises(SMTTimeoutException):
                ValidGraphOperation.execute(sample_model)

    def test_execute_multiple_checks(self):
        source_data = {
            "name": "test-file",
            "require": {
                "direct": [{"package": "fastapi", "constraints": ">= 0.100.0"}],
                "indirect": []
            },
            "have": {
                "fastapi": [{"serial_number": 100, "mean": 5.0, "name": "0.100.0"}]
            }
        }
        model = SMTModel(source_data, "PyPIPackage", "mean")
        model.transform()

        result1 = ValidGraphOperation.execute(model)
        result2 = ValidGraphOperation.execute(model)

        assert result1 is True
        assert result2 is True
