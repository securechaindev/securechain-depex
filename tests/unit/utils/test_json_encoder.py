from datetime import datetime

import pytest
from bson import ObjectId
from neo4j.time import DateTime

from app.utils.json_encoder import JSONEncoder


class TestJSONEncoder:

    @pytest.fixture
    def encoder(self):
        return JSONEncoder()

    def test_encode_simple_dict(self, encoder):
        data = {"name": "test", "value": 42}
        result = encoder.encode(data)

        assert result == data
        assert isinstance(result, dict)

    def test_encode_with_objectid(self, encoder):
        obj_id = ObjectId()
        data = {"_id": obj_id, "name": "test"}

        result = encoder.encode(data)

        assert isinstance(result["_id"], str)
        assert result["_id"] == str(obj_id)
        assert result["name"] == "test"

    def test_encode_with_datetime(self, encoder):
        now = datetime(2025, 10, 27, 12, 30, 45)
        data = {"timestamp": now, "event": "test"}

        result = encoder.encode(data)

        assert isinstance(result["timestamp"], str)
        assert "2025-10-27" in result["timestamp"]
        assert result["event"] == "test"

    def test_encode_with_neo4j_datetime(self, encoder):
        neo_dt = DateTime(2025, 10, 27, 12, 30, 45)
        data = {"created": neo_dt, "type": "node"}

        result = encoder.encode(data)

        assert isinstance(result["created"], str)
        assert result["type"] == "node"

    def test_encode_nested_dict(self, encoder):
        obj_id = ObjectId()
        data = {
            "user": {
                "_id": obj_id,
                "name": "John",
                "created": datetime(2025, 1, 1),
            },
            "active": True,
        }

        result = encoder.encode(data)

        assert isinstance(result["user"]["_id"], str)
        assert isinstance(result["user"]["created"], str)
        assert result["user"]["name"] == "John"
        assert result["active"] is True

    def test_encode_list_with_objectids(self, encoder):
        obj_ids = [ObjectId(), ObjectId(), ObjectId()]
        data = {"ids": obj_ids, "count": 3}

        result = encoder.encode(data)

        assert isinstance(result["ids"], list)
        assert len(result["ids"]) == 3
        for item in result["ids"]:
            assert isinstance(item, str)

    def test_encode_mixed_types(self, encoder):
        data = {
            "string": "value",
            "number": 42,
            "float": 3.14,
            "boolean": True,
            "null": None,
            "list": [1, 2, 3],
            "nested": {"key": "value"},
        }

        result = encoder.encode(data)

        assert result == data

    def test_encode_empty_dict(self, encoder):
        data = {}
        result = encoder.encode(data)

        assert result == {}

    def test_default_with_objectid(self, encoder):
        obj_id = ObjectId()
        result = encoder.default(obj_id)

        assert isinstance(result, str)
        assert result == str(obj_id)

    def test_default_with_datetime(self, encoder):
        dt = datetime(2025, 10, 27)
        result = encoder.default(dt)

        assert isinstance(result, str)
        assert "2025-10-27" in result

    def test_default_with_neo4j_datetime(self, encoder):
        neo_dt = DateTime(2025, 10, 27)
        result = encoder.default(neo_dt)

        assert isinstance(result, str)

    def test_default_with_unsupported_type(self, encoder):

        class CustomClass:
            pass

        obj = CustomClass()

        with pytest.raises(TypeError) as exc_info:
            encoder.default(obj)

        assert "CustomClass" in str(exc_info.value)
        assert "not JSON serializable" in str(exc_info.value)

    def test_encode_complex_structure(self, encoder):
        data = {
            "packages": [
                {
                    "_id": ObjectId(),
                    "name": "fastapi",
                    "created": datetime(2024, 1, 1),
                    "versions": ["0.100.0", "0.101.0"],
                },
                {
                    "_id": ObjectId(),
                    "name": "pydantic",
                    "created": datetime(2024, 2, 1),
                    "versions": ["2.0.0", "2.1.0"],
                },
            ],
            "total": 2,
            "timestamp": datetime.now(),
        }

        result = encoder.encode(data)

        assert len(result["packages"]) == 2
        assert isinstance(result["packages"][0]["_id"], str)
        assert isinstance(result["packages"][0]["created"], str)
        assert isinstance(result["timestamp"], str)
        assert result["total"] == 2
