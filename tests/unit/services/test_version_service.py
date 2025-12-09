
from unittest.mock import AsyncMock, MagicMock

import pytest
from neo4j.exceptions import Neo4jError

from app.exceptions import MemoryOutException
from app.services.version_service import VersionService


class _TestNeo4jError(Neo4jError):
    def __init__(self, message: str, code: str):
        super().__init__(message)
        self._code = code

    @property
    def code(self):
        return self._code


class TestVersionService:

    @pytest.fixture
    def mock_db_manager(self):
        db_manager = MagicMock()
        driver = MagicMock()
        db_manager.get_neo4j_driver.return_value = driver
        return db_manager, driver

    @pytest.fixture
    def version_service(self, mock_db_manager):
        db_manager, _ = mock_db_manager
        return VersionService(db_manager)

    async def test_read_releases_by_serial_numbers_all_found(self, version_service, mock_db_manager):
        _, driver = mock_db_manager
        session_mock = AsyncMock()
        driver.session.return_value.__aenter__.return_value = session_mock

        result_mock = AsyncMock()
        result_mock.data.return_value = [
            {"package": "fastapi", "name": "0.100.0"},
            {"package": "pydantic", "name": "2.0.0"}
        ]

        session_mock.run.return_value = result_mock

        config = {"fastapi": 100, "pydantic": 200}
        result = await version_service.read_releases_by_serial_numbers("PyPIPackage", config)

        assert result == {"fastapi": "0.100.0", "pydantic": "2.0.0"}
        assert session_mock.run.call_count == 1

    async def test_read_releases_by_serial_numbers_partial_found(self, version_service, mock_db_manager):
        _, driver = mock_db_manager
        session_mock = AsyncMock()
        driver.session.return_value.__aenter__.return_value = session_mock

        result_mock = AsyncMock()
        result_mock.data.return_value = [
            {"package": "fastapi", "name": "0.100.0"}
            # "unknown" no está en los resultados, por lo que mantendrá el valor original
        ]

        session_mock.run.return_value = result_mock

        config = {"fastapi": 100, "unknown": 999}
        result = await version_service.read_releases_by_serial_numbers("PyPIPackage", config)

        assert result == {"fastapi": "0.100.0", "unknown": 999}

    async def test_read_releases_by_serial_numbers_empty_config(self, version_service, mock_db_manager):
        result = await version_service.read_releases_by_serial_numbers("PyPIPackage", {})

        assert result == {}

    async def test_read_serial_numbers_by_releases_all_found(self, version_service, mock_db_manager):
        _, driver = mock_db_manager
        session_mock = AsyncMock()
        driver.session.return_value.__aenter__.return_value = session_mock

        result_mock = AsyncMock()
        result_mock.data.return_value = [
            {"package": "fastapi", "serial_number": 100},
            {"package": "pydantic", "serial_number": 200}
        ]

        session_mock.run.return_value = result_mock

        config = {"fastapi": "0.100.0", "pydantic": "2.0.0"}
        result = await version_service.read_serial_numbers_by_releases("PyPIPackage", config)

        assert result == {"fastapi": 100, "pydantic": 200}

    async def test_read_serial_numbers_by_releases_not_found(self, version_service, mock_db_manager):
        _, driver = mock_db_manager
        session_mock = AsyncMock()
        driver.session.return_value.__aenter__.return_value = session_mock

        result_mock = AsyncMock()
        result_mock.single.return_value = None

        session_mock.run.return_value = result_mock

        config = {"nonexistent": "1.0.0"}
        result = await version_service.read_serial_numbers_by_releases("PyPIPackage", config)

        assert result == {}

    async def test_read_serial_numbers_by_releases_empty_config(self, version_service, mock_db_manager):
        result = await version_service.read_serial_numbers_by_releases("PyPIPackage", {})

        assert result == {}

    async def test_read_graph_for_version_ssc_info_operation_success(self, version_service, mock_db_manager):
        _, driver = mock_db_manager
        session_mock = AsyncMock()
        driver.session.return_value.__aenter__.return_value = session_mock

        graph_data = {
            "direct_dependencies": [
                {
                    "package_name": "pydantic",
                    "package_vendor": "n/a",
                    "package_constraints": "^2.0",
                    "versions": [{"name": "2.0.0", "mean": 5.5, "serial_number": 200}]
                }
            ],
            "total_direct_dependencies": 1,
            "indirect_dependencies_by_depth": {
                "2": [{"package_name": "typing-extensions"}]
            },
            "total_indirect_dependencies": 1
        }
        # execute_read devuelve el resultado del método read_graph_version
        # que debe ser un objeto con el método .get()
        record_mock = {"ssc_version_info": graph_data}
        session_mock.execute_read.return_value = record_mock

        result = await version_service.read_graph_for_version_ssc_info_operation(
            "PyPIPackage", "fastapi", "0.100.0", 3
        )

        assert result == graph_data
        assert result["total_direct_dependencies"] == 1

    async def test_read_graph_for_version_ssc_info_operation_not_found(self, version_service, mock_db_manager):
        _, driver = mock_db_manager
        session_mock = AsyncMock()
        driver.session.return_value.__aenter__.return_value = session_mock

        session_mock.execute_read.return_value = None

        result = await version_service.read_graph_for_version_ssc_info_operation(
            "PyPIPackage", "fastapi", "nonexistent", 3
        )

        assert result == {}

    async def test_read_graph_memory_out_error(self, version_service, mock_db_manager):
        _, driver = mock_db_manager
        session_mock = AsyncMock()
        driver.session.return_value.__aenter__.return_value = session_mock

        error = _TestNeo4jError(
            message="Memory pool out of memory",
            code="Neo.TransientError.General.MemoryPoolOutOfMemoryError"
        )
        session_mock.execute_read.side_effect = error

        with pytest.raises(MemoryOutException):
            await version_service.read_graph_for_version_ssc_info_operation(
                "PyPIPackage", "fastapi", "0.100.0", 10
            )

    async def test_read_graph_transaction_timeout_client(self, version_service, mock_db_manager):
        _, driver = mock_db_manager
        session_mock = AsyncMock()
        driver.session.return_value.__aenter__.return_value = session_mock

        error = _TestNeo4jError(
            message="Transaction timed out",
            code="Neo.ClientError.Transaction.TransactionTimedOutClientConfiguration"
        )
        session_mock.execute_read.side_effect = error

        with pytest.raises(MemoryOutException):
            await version_service.read_graph_for_version_ssc_info_operation(
                "PyPIPackage", "fastapi", "0.100.0", 5
            )

    async def test_read_graph_transaction_timeout(self, version_service, mock_db_manager):
        _, driver = mock_db_manager
        session_mock = AsyncMock()
        driver.session.return_value.__aenter__.return_value = session_mock

        error = _TestNeo4jError(
            message="Transaction timed out",
            code="Neo.ClientError.Transaction.TransactionTimedOut"
        )
        session_mock.execute_read.side_effect = error

        with pytest.raises(MemoryOutException):
            await version_service.read_graph_for_version_ssc_info_operation(
                "PyPIPackage", "fastapi", "0.100.0", 5
            )

