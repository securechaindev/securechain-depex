from unittest.mock import AsyncMock, MagicMock

import pytest
from neo4j.exceptions import Neo4jError

from app.exceptions import MemoryOutException
from app.services.package_service import PackageService


class _TestNeo4jError(Neo4jError):
    def __init__(self, message: str, code: str):
        super().__init__(message)
        self._code = code

    @property
    def code(self):
        return self._code


class TestPackageService:

    @pytest.fixture
    def mock_db_manager(self):
        db_manager = MagicMock()
        driver = MagicMock()
        db_manager.get_neo4j_driver.return_value = driver
        return db_manager, driver

    @pytest.fixture
    def package_service(self, mock_db_manager):
        db_manager, _ = mock_db_manager
        return PackageService(db_manager)

    async def test_read_package_status_by_name_found(self, package_service, mock_db_manager):
        _, driver = mock_db_manager
        session_mock = AsyncMock()
        driver.session.return_value.__aenter__.return_value = session_mock

        result_mock = AsyncMock()
        record = {"package": {"name": "fastapi", "versions": [{"name": "0.100.0"}]}}
        result_mock.single.return_value = record
        session_mock.run.return_value = result_mock

        status = await package_service.read_package_status_by_name("PyPIPackage", "fastapi")

        assert status == {"name": "fastapi", "versions": [{"name": "0.100.0"}]}
        session_mock.run.assert_called_once()

    async def test_read_package_status_by_name_not_found(self, package_service, mock_db_manager):
        _, driver = mock_db_manager
        session_mock = AsyncMock()
        driver.session.return_value.__aenter__.return_value = session_mock

        result_mock = AsyncMock()
        result_mock.single.return_value = None
        session_mock.run.return_value = result_mock

        status = await package_service.read_package_status_by_name("PyPIPackage", "nonexistent")

        assert status is None

    async def test_read_version_status_by_package_and_name_found(self, package_service, mock_db_manager):
        _, driver = mock_db_manager
        session_mock = AsyncMock()
        driver.session.return_value.__aenter__.return_value = session_mock

        result_mock = AsyncMock()
        record = {"version": {"id": "abc123", "name": "0.100.0", "mean": 5.5}}
        result_mock.single.return_value = record
        session_mock.run.return_value = result_mock

        version = await package_service.read_version_status_by_package_and_name(
            "PyPIPackage", "fastapi", "0.100.0"
        )

        assert version == {"id": "abc123", "name": "0.100.0", "mean": 5.5}

    async def test_read_version_status_by_package_and_name_not_found(self, package_service, mock_db_manager):
        _, driver = mock_db_manager
        session_mock = AsyncMock()
        driver.session.return_value.__aenter__.return_value = session_mock

        result_mock = AsyncMock()
        result_mock.single.return_value = None
        session_mock.run.return_value = result_mock

        version = await package_service.read_version_status_by_package_and_name(
            "PyPIPackage", "fastapi", "nonexistent"
        )

        assert version is None

    async def test_read_packages_by_requirement_file_found(self, package_service, mock_db_manager):
        _, driver = mock_db_manager
        session_mock = AsyncMock()
        driver.session.return_value.__aenter__.return_value = session_mock

        result_mock = AsyncMock()
        record = {"requirement_files": {"fastapi": ">=0.100.0", "pydantic": "^2.0"}}
        result_mock.single.return_value = record
        session_mock.run.return_value = result_mock

        packages = await package_service.read_packages_by_requirement_file("file123")

        assert packages == {"fastapi": ">=0.100.0", "pydantic": "^2.0"}
        session_mock.run.assert_called_once()

    async def test_read_packages_by_requirement_file_not_found(self, package_service, mock_db_manager):
        _, driver = mock_db_manager
        session_mock = AsyncMock()
        driver.session.return_value.__aenter__.return_value = session_mock

        result_mock = AsyncMock()
        result_mock.single.return_value = None
        session_mock.run.return_value = result_mock

        packages = await package_service.read_packages_by_requirement_file("nonexistent")

        assert packages is None

    async def test_read_graph_for_package_ssc_info_operation_success(self, package_service, mock_db_manager):
        _, driver = mock_db_manager
        session_mock = AsyncMock()
        driver.session.return_value.__aenter__.return_value = session_mock

        graph_data = {
            "direct_dependencies": [
                {
                    "package_name": "pydantic",
                    "package_vendor": "n/a",
                    "package_constraints": "^2.0",
                    "versions": [{"name": "2.0.0", "mean": 5.5}]
                }
            ],
            "total_direct_dependencies": 1,
            "indirect_dependencies_by_depth": {
                "2": [{"package_name": "typing-extensions", "versions": []}]
            },
            "total_indirect_dependencies": 1
        }
        session_mock.execute_read.return_value = {"ssc_package_info": graph_data}

        result = await package_service.read_graph_for_package_ssc_info_operation(
            "PyPIPackage", "fastapi", 3
        )

        assert result == graph_data
        assert result["total_direct_dependencies"] == 1
        assert result["total_indirect_dependencies"] == 1

    async def test_read_graph_for_package_ssc_info_operation_not_found(self, package_service, mock_db_manager):
        _, driver = mock_db_manager
        session_mock = AsyncMock()
        driver.session.return_value.__aenter__.return_value = session_mock

        session_mock.execute_read.return_value = None

        result = await package_service.read_graph_for_package_ssc_info_operation(
            "PyPIPackage", "nonexistent", 3
        )

        assert result is None

    async def test_read_graph_memory_out_error(self, package_service, mock_db_manager):
        _, driver = mock_db_manager
        session_mock = AsyncMock()
        driver.session.return_value.__aenter__.return_value = session_mock

        error = _TestNeo4jError(
            message="Memory pool out of memory",
            code="Neo.TransientError.General.MemoryPoolOutOfMemoryError"
        )
        session_mock.execute_read.side_effect = error

        with pytest.raises(MemoryOutException):
            await package_service.read_graph_for_package_ssc_info_operation(
                "PyPIPackage", "fastapi", 10
            )

    async def test_read_graph_transaction_timeout_client(self, package_service, mock_db_manager):
        _, driver = mock_db_manager
        session_mock = AsyncMock()
        driver.session.return_value.__aenter__.return_value = session_mock

        error = _TestNeo4jError(
            message="Transaction timed out",
            code="Neo.ClientError.Transaction.TransactionTimedOutClientConfiguration"
        )
        session_mock.execute_read.side_effect = error

        with pytest.raises(MemoryOutException):
            await package_service.read_graph_for_package_ssc_info_operation(
                "PyPIPackage", "fastapi", 5
            )

    async def test_read_graph_transaction_timeout(self, package_service, mock_db_manager):
        _, driver = mock_db_manager
        session_mock = AsyncMock()
        driver.session.return_value.__aenter__.return_value = session_mock

        error = _TestNeo4jError(
            message="Transaction timed out",
            code="Neo.ClientError.Transaction.TransactionTimedOut"
        )
        session_mock.execute_read.side_effect = error

        with pytest.raises(MemoryOutException):
            await package_service.read_graph_for_package_ssc_info_operation(
                "PyPIPackage", "fastapi", 5
            )

    async def test_exists_package_true(self, package_service, mock_db_manager):
        _, driver = mock_db_manager
        session_mock = AsyncMock()
        driver.session.return_value.__aenter__.return_value = session_mock

        result_mock = AsyncMock()
        result_mock.single.return_value = {"exists": True}
        session_mock.run.return_value = result_mock

        exists = await package_service.exists_package("PyPIPackage", "fastapi")

        assert exists is True

    async def test_exists_package_false(self, package_service, mock_db_manager):
        _, driver = mock_db_manager
        session_mock = AsyncMock()
        driver.session.return_value.__aenter__.return_value = session_mock

        result_mock = AsyncMock()
        result_mock.single.return_value = {"exists": False}
        session_mock.run.return_value = result_mock

        exists = await package_service.exists_package("PyPIPackage", "nonexistent")

        assert exists is False

    async def test_exists_package_no_record(self, package_service, mock_db_manager):
        _, driver = mock_db_manager
        session_mock = AsyncMock()
        driver.session.return_value.__aenter__.return_value = session_mock

        result_mock = AsyncMock()
        result_mock.single.return_value = None
        session_mock.run.return_value = result_mock

        exists = await package_service.exists_package("PyPIPackage", "unknown")

        assert exists is False
