"""Unit tests for SMTService."""
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.smt_service import SMTService


class TestSMTService:
    """Test suite for SMTService."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock DatabaseManager."""
        db = MagicMock()
        collection = AsyncMock()
        db.get_smt_text_collection.return_value = collection
        return db, collection

    @pytest.mark.asyncio
    async def test_replace_smt_text(self, mock_db):
        """Test replacing SMT text."""
        db, collection = mock_db
        service = SMTService(db)

        smt_id = "smt-123"
        text_content = "(assert (> x 5))"

        await service.replace_smt_text(smt_id, text_content)

        # Verify replace_one was called
        collection.replace_one.assert_called_once()
        call_args = collection.replace_one.call_args

        # Check filter
        assert call_args[0][0] == {"smt_text_id": smt_id}

        # Check document
        doc = call_args[0][1]
        assert doc["smt_text_id"] == smt_id
        assert doc["text"] == text_content
        assert "moment" in doc
        assert isinstance(doc["moment"], datetime)

        # Check upsert
        assert call_args[1]["upsert"] is True

    @pytest.mark.asyncio
    async def test_replace_smt_text_empty(self, mock_db):
        """Test replacing with empty SMT text."""
        db, collection = mock_db
        service = SMTService(db)

        smt_id = "smt-empty"
        text_content = ""

        await service.replace_smt_text(smt_id, text_content)

        call_args = collection.replace_one.call_args
        doc = call_args[0][1]
        assert doc["text"] == ""

    @pytest.mark.asyncio
    async def test_replace_smt_text_complex_formula(self, mock_db):
        """Test replacing with complex SMT formula."""
        db, collection = mock_db
        service = SMTService(db)

        smt_id = "smt-complex"
        text_content = """(declare-const x Int)
(declare-const y Int)
(assert (> x 0))
(assert (< y 10))
(assert (= (+ x y) 15))
(check-sat)
(get-model)"""

        await service.replace_smt_text(smt_id, text_content)

        call_args = collection.replace_one.call_args
        doc = call_args[0][1]
        assert doc["text"] == text_content
        assert "(check-sat)" in doc["text"]

    @pytest.mark.asyncio
    async def test_read_smt_text(self, mock_db):
        """Test reading SMT text."""
        db, collection = mock_db
        service = SMTService(db)

        smt_id = "smt-read-123"
        expected_doc = {
            "smt_text_id": smt_id,
            "text": "(assert (= x 42))",
            "moment": datetime.now(),
        }

        collection.find_one.return_value = expected_doc

        result = await service.read_smt_text(smt_id)

        # Verify find_one was called
        collection.find_one.assert_called_once_with({"smt_text_id": smt_id})

        # Verify result
        assert result == expected_doc

    @pytest.mark.asyncio
    async def test_read_smt_text_not_found(self, mock_db):
        """Test reading non-existent SMT text."""
        db, collection = mock_db
        service = SMTService(db)

        smt_id = "non-existent-smt"
        collection.find_one.return_value = None

        result = await service.read_smt_text(smt_id)

        assert result is None
        collection.find_one.assert_called_once_with({"smt_text_id": smt_id})

    @pytest.mark.asyncio
    async def test_read_smt_text_with_metadata(self, mock_db):
        """Test reading SMT text with metadata."""
        db, collection = mock_db
        service = SMTService(db)

        smt_id = "smt-with-meta"
        expected_doc = {
            "smt_text_id": smt_id,
            "text": "(declare-const version String)",
            "moment": datetime(2025, 10, 27, 10, 30, 0),
            "solver": "z3",
            "status": "sat",
        }

        collection.find_one.return_value = expected_doc

        result = await service.read_smt_text(smt_id)

        assert result["text"] == "(declare-const version String)"
        assert result["solver"] == "z3"
        assert result["status"] == "sat"
