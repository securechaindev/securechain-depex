"""Tests for RequirementFileService."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from neo4j.exceptions import Neo4jError

from app.exceptions import MemoryOutException
from app.services.requirement_file_service import RequirementFileService


class _TestNeo4jError(Neo4jError):
    """Custom Neo4jError for testing with code support."""
    def __init__(self, message: str, code: str):
        super().__init__(message)
        self._code = code

    @property
    def code(self):
        return self._code


class TestRequirementFileService:
    """Test suite for RequirementFileService class."""

    @pytest.fixture
    def mock_db_manager(self):
        """Create a mock DatabaseManager."""
        db_manager = MagicMock()
        driver = MagicMock()
        db_manager.get_neo4j_driver.return_value = driver
        return db_manager, driver

    @pytest.fixture
    def req_file_service(self, mock_db_manager):
        """Create RequirementFileService instance with mocked database."""
        db_manager, _ = mock_db_manager
        return RequirementFileService(db_manager)

    async def test_create_requirement_file_success(self, req_file_service, mock_db_manager):
        """Test creating a requirement file successfully."""
        _, driver = mock_db_manager
        session_mock = AsyncMock()
        driver.session.return_value.__aenter__.return_value = session_mock

        result_mock = AsyncMock()
        result_mock.single.return_value = {"id": "rf123"}
        session_mock.run.return_value = result_mock

        requirement_file = {
            "name": "requirements.txt",
            "manager": "pypi",
            "moment": datetime.now()
        }

        rf_id = await req_file_service.create_requirement_file(requirement_file, "repo123")

        assert rf_id == "rf123"
        session_mock.run.assert_called_once()

    async def test_create_requirement_file_no_record(self, req_file_service, mock_db_manager):
        """Test create_requirement_file returns None when no record created."""
        _, driver = mock_db_manager
        session_mock = AsyncMock()
        driver.session.return_value.__aenter__.return_value = session_mock

        result_mock = AsyncMock()
        result_mock.single.return_value = None
        session_mock.run.return_value = result_mock

        requirement_file = {
            "name": "requirements.txt",
            "manager": "pypi",
            "moment": datetime.now()
        }

        rf_id = await req_file_service.create_requirement_file(requirement_file, "nonexistent")

        assert rf_id is None

    async def test_read_requirement_files_by_repository_found(self, req_file_service, mock_db_manager):
        """Test reading requirement files when they exist."""
        _, driver = mock_db_manager
        session_mock = AsyncMock()
        driver.session.return_value.__aenter__.return_value = session_mock

        result_mock = AsyncMock()
        result_mock.single.return_value = [
            {"requirements.txt": "rf123", "package.json": "rf456"}
        ]
        session_mock.run.return_value = result_mock

        files = await req_file_service.read_requirement_files_by_repository("repo123")

        assert files == {"requirements.txt": "rf123", "package.json": "rf456"}

    async def test_read_requirement_files_by_repository_not_found(self, req_file_service, mock_db_manager):
        """Test reading requirement files when repository doesn't exist."""
        _, driver = mock_db_manager
        session_mock = AsyncMock()
        driver.session.return_value.__aenter__.return_value = session_mock

        result_mock = AsyncMock()
        result_mock.single.return_value = None
        session_mock.run.return_value = result_mock

        files = await req_file_service.read_requirement_files_by_repository("nonexistent")

        assert files is None

    async def test_read_requirement_file_moment_found(self, req_file_service, mock_db_manager):
        """Test reading requirement file moment when it exists."""
        _, driver = mock_db_manager
        session_mock = AsyncMock()
        driver.session.return_value.__aenter__.return_value = session_mock

        moment = datetime.now()
        result_mock = AsyncMock()
        result_mock.single.return_value = [moment]
        session_mock.run.return_value = result_mock

        result = await req_file_service.read_requirement_file_moment("rf123")

        assert result == moment

    async def test_read_requirement_file_moment_not_found(self, req_file_service, mock_db_manager):
        """Test reading moment when requirement file doesn't exist."""
        _, driver = mock_db_manager
        session_mock = AsyncMock()
        driver.session.return_value.__aenter__.return_value = session_mock

        result_mock = AsyncMock()
        result_mock.single.return_value = None
        session_mock.run.return_value = result_mock

        result = await req_file_service.read_requirement_file_moment("nonexistent")

        assert result is None

    async def test_read_data_for_smt_transform_success(self, req_file_service, mock_db_manager):
        """Test reading data for SMT transform."""
        _, driver = mock_db_manager
        session_mock = AsyncMock()
        driver.session.return_value.__aenter__.return_value = session_mock

        smt_data = {
            "name": "requirements.txt",
            "moment": datetime.now(),
            "require": {
                "direct": [{"package": "fastapi", "constraints": ">=0.100.0"}],
                "indirect": []
            },
            "have": {
                "fastapi": [{"name": "0.100.0", "serial_number": 100}]
            }
        }
        session_mock.execute_read.return_value = [smt_data]

        result = await req_file_service.read_data_for_smt_transform("rf123", 3)

        assert result == smt_data
        assert "require" in result
        assert "have" in result

    async def test_read_data_for_smt_transform_memory_error(self, req_file_service, mock_db_manager):
        """Test read_data_for_smt_transform raises MemoryOutException on memory error."""
        _, driver = mock_db_manager
        session_mock = AsyncMock()
        driver.session.return_value.__aenter__.return_value = session_mock

        error = _TestNeo4jError(
            message="Memory pool out of memory",
            code="Neo.TransientError.General.MemoryPoolOutOfMemoryError"
        )
        session_mock.execute_read.side_effect = error

        with pytest.raises(MemoryOutException):
            await req_file_service.read_data_for_smt_transform("rf123", 10)

    async def test_read_graph_for_req_file_info_operation_success(self, req_file_service, mock_db_manager):
        """Test reading graph for requirement file info operation."""
        _, driver = mock_db_manager
        session_mock = AsyncMock()
        driver.session.return_value.__aenter__.return_value = session_mock

        graph_data = {
            "direct_dependencies": [
                {
                    "package_name": "fastapi",
                    "package_vendor": "n/a",
                    "package_constraints": ">=0.100.0",
                    "versions": [{"name": "0.100.0", "mean": 5.5}]
                }
            ],
            "total_direct_dependencies": 1,
            "indirect_dependencies_by_depth": {},
            "total_indirect_dependencies": 0
        }
        session_mock.execute_read.return_value = [graph_data]

        result = await req_file_service.read_graph_for_req_file_info_operation(
            "PyPIPackage", "rf123", 3
        )

        assert result == graph_data
        assert result["total_direct_dependencies"] == 1

    async def test_read_graph_for_req_file_info_operation_timeout(self, req_file_service, mock_db_manager):
        """Test read_graph raises MemoryOutException on timeout."""
        _, driver = mock_db_manager
        session_mock = AsyncMock()
        driver.session.return_value.__aenter__.return_value = session_mock

        error = _TestNeo4jError(
            message="Transaction timed out",
            code="Neo.ClientError.Transaction.TransactionTimedOut"
        )
        session_mock.execute_read.side_effect = error

        with pytest.raises(MemoryOutException):
            await req_file_service.read_graph_for_req_file_info_operation(
                "PyPIPackage", "rf123", 5
            )

    async def test_update_requirement_rel_constraints(self, req_file_service, mock_db_manager):
        """Test updating requirement relationship constraints."""
        _, driver = mock_db_manager
        session_mock = AsyncMock()
        driver.session.return_value.__aenter__.return_value = session_mock

        await req_file_service.update_requirement_rel_constraints("rf123", "fastapi", ">=0.110.0")

        session_mock.run.assert_called_once()
        call_args = session_mock.run.call_args
        assert call_args[1]["constraints"] == ">=0.110.0"

    async def test_update_requirement_file_moment(self, req_file_service, mock_db_manager):
        """Test updating requirement file moment."""
        _, driver = mock_db_manager
        session_mock = AsyncMock()
        driver.session.return_value.__aenter__.return_value = session_mock

        await req_file_service.update_requirement_file_moment("rf123")

        session_mock.run.assert_called_once()
        call_args = session_mock.run.call_args
        assert "moment" in call_args[1]
        assert isinstance(call_args[1]["moment"], datetime)

    async def test_delete_requirement_file(self, req_file_service, mock_db_manager):
        """Test deleting a requirement file."""
        _, driver = mock_db_manager
        session_mock = AsyncMock()
        driver.session.return_value.__aenter__.return_value = session_mock

        await req_file_service.delete_requirement_file("repo123", "requirements.txt")

        session_mock.run.assert_called_once()
        call_args = session_mock.run.call_args
        assert call_args[1]["requirement_file_name"] == "requirements.txt"

    async def test_delete_requirement_file_rel(self, req_file_service, mock_db_manager):
        """Test deleting a requirement file relationship."""
        _, driver = mock_db_manager
        session_mock = AsyncMock()
        driver.session.return_value.__aenter__.return_value = session_mock

        await req_file_service.delete_requirement_file_rel("rf123", "fastapi")

        session_mock.run.assert_called_once()
        call_args = session_mock.run.call_args
        assert call_args[1]["package_name"] == "fastapi"
