"""Unit tests for OperationService."""
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.operation_service import OperationService


class TestOperationService:
    """Test suite for OperationService."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock DatabaseManager."""
        db = MagicMock()
        collection = AsyncMock()
        db.get_operation_result_collection.return_value = collection
        return db, collection

    @pytest.mark.asyncio
    async def test_replace_operation_result(self, mock_db):
        """Test replacing an operation result."""
        db, collection = mock_db
        service = OperationService(db)

        operation_id = "test-op-123"
        result_data = {"status": "success", "data": {"count": 42}}

        await service.replace_operation_result(operation_id, result_data)

        # Verify replace_one was called with correct parameters
        collection.replace_one.assert_called_once()
        call_args = collection.replace_one.call_args

        # Check filter
        assert call_args[0][0] == {"operation_result_id": operation_id}

        # Check document structure
        doc = call_args[0][1]
        assert doc["operation_result_id"] == operation_id
        assert doc["result"] == result_data
        assert "moment" in doc
        assert isinstance(doc["moment"], datetime)

        # Check upsert flag
        assert call_args[1]["upsert"] is True

    @pytest.mark.asyncio
    async def test_replace_operation_result_empty_data(self, mock_db):
        """Test replacing an operation result with empty data."""
        db, collection = mock_db
        service = OperationService(db)

        operation_id = "test-op-456"
        result_data = {}

        await service.replace_operation_result(operation_id, result_data)

        collection.replace_one.assert_called_once()
        call_args = collection.replace_one.call_args
        doc = call_args[0][1]
        assert doc["result"] == {}

    @pytest.mark.asyncio
    async def test_replace_operation_result_complex_data(self, mock_db):
        """Test replacing an operation result with complex nested data."""
        db, collection = mock_db
        service = OperationService(db)

        operation_id = "test-op-789"
        result_data = {
            "status": "completed",
            "metrics": {
                "duration": 123.45,
                "items_processed": 1000,
            },
            "errors": [],
            "warnings": ["deprecated_api"],
        }

        await service.replace_operation_result(operation_id, result_data)

        call_args = collection.replace_one.call_args
        doc = call_args[0][1]
        assert doc["result"] == result_data
        assert doc["result"]["metrics"]["duration"] == 123.45

    @pytest.mark.asyncio
    async def test_read_operation_result(self, mock_db):
        """Test reading an operation result."""
        db, collection = mock_db
        service = OperationService(db)

        operation_id = "test-op-read-123"
        expected_result = {
            "operation_result_id": operation_id,
            "result": {"status": "success"},
            "moment": datetime.now(),
        }

        collection.find_one.return_value = expected_result

        result = await service.read_operation_result(operation_id)

        # Verify find_one was called with correct filter
        collection.find_one.assert_called_once_with(
            {"operation_result_id": operation_id}
        )

        # Verify result matches
        assert result == expected_result

    @pytest.mark.asyncio
    async def test_read_operation_result_not_found(self, mock_db):
        """Test reading a non-existent operation result."""
        db, collection = mock_db
        service = OperationService(db)

        operation_id = "non-existent-op"
        collection.find_one.return_value = None

        result = await service.read_operation_result(operation_id)

        assert result is None
        collection.find_one.assert_called_once_with(
            {"operation_result_id": operation_id}
        )

    @pytest.mark.asyncio
    async def test_read_operation_result_with_data(self, mock_db):
        """Test reading an operation result with actual data."""
        db, collection = mock_db
        service = OperationService(db)

        operation_id = "test-op-with-data"
        expected_result = {
            "operation_result_id": operation_id,
            "result": {
                "packages": ["fastapi", "uvicorn", "pydantic"],
                "count": 3,
            },
            "moment": datetime(2025, 10, 27, 12, 0, 0),
        }

        collection.find_one.return_value = expected_result

        result = await service.read_operation_result(operation_id)

        assert result["result"]["packages"] == ["fastapi", "uvicorn", "pydantic"]
        assert result["result"]["count"] == 3
