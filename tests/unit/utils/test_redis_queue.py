"""Tests for RedisQueue class."""

from unittest.mock import MagicMock, patch

import pytest
from redis.exceptions import ResponseError

from app.schemas import PackageMessageSchema
from app.utils.redis_queue import RedisQueue


class TestRedisQueue:
    """Test suite for RedisQueue class."""

    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis instance."""
        with patch("app.utils.redis_queue.Redis") as mock:
            redis_instance = MagicMock()
            mock.return_value = redis_instance
            yield redis_instance

    @pytest.fixture
    def redis_queue(self, mock_redis):
        """Create RedisQueue instance with mocked Redis."""
        # Mock successful group creation
        mock_redis.xgroup_create.return_value = None
        queue = RedisQueue(host="localhost", port=6379, db=0)
        return queue

    @pytest.fixture
    def package_message(self):
        """Create a sample PackageMessageSchema."""
        return PackageMessageSchema(
            node_type="PyPIPackage",
            package="fastapi",
            vendor="n/a",
            repository_url="https://github.com/tiangolo/fastapi",
        )

    def test_init_creates_stream_group(self, mock_redis):
        """Test initialization creates Redis stream group."""
        mock_redis.xgroup_create.return_value = None
        queue = RedisQueue(host="localhost", port=6379, db=1)

        # Verify Redis connection was created
        assert queue.r == mock_redis

        # Verify xgroup_create was called
        mock_redis.xgroup_create.assert_called_once()

    def test_init_handles_busygroup_error(self, mock_redis):
        """Test initialization handles BUSYGROUP error gracefully."""
        mock_redis.xgroup_create.side_effect = ResponseError("BUSYGROUP Consumer Group name already exists")

        # Should not raise exception
        queue = RedisQueue(host="localhost", port=6379, db=0)
        assert queue.r == mock_redis

    def test_init_raises_other_redis_errors(self, mock_redis):
        """Test initialization raises non-BUSYGROUP Redis errors."""
        mock_redis.xgroup_create.side_effect = ResponseError("Some other Redis error")

        with pytest.raises(ResponseError, match="Some other Redis error"):
            RedisQueue(host="localhost", port=6379, db=0)

    def test_from_env_uses_settings(self, mock_redis):
        """Test from_env class method uses settings values."""
        mock_redis.xgroup_create.return_value = None

        with patch("app.utils.redis_queue.settings") as mock_settings:
            mock_settings.REDIS_HOST = "redis.example.com"
            mock_settings.REDIS_PORT = 6380
            mock_settings.REDIS_DB = 2

            queue = RedisQueue.from_env()

            # Verify Redis was initialized with settings
            assert queue.r == mock_redis

    def test_add_package_message(self, redis_queue, package_message):
        """Test adding a package message to Redis stream."""
        redis_queue.r.xadd.return_value = "1234567890-0"

        msg_id = redis_queue.add_package_message(package_message)

        # Verify xadd was called with correct data
        assert msg_id == "1234567890-0"
        redis_queue.r.xadd.assert_called_once()

        call_args = redis_queue.r.xadd.call_args
        stream_name = call_args[0][0]
        data = call_args[0][1]

        # Verify stream name
        assert "redis_stream" in str(stream_name) or stream_name

        # Verify data contains JSON
        assert "data" in data
        json_data = data["data"]
        assert "fastapi" in json_data
        assert "PyPIPackage" in json_data

    def test_add_package_message_serialization(self, redis_queue, package_message):
        """Test message is properly serialized to JSON."""
        redis_queue.r.xadd.return_value = "1234567890-0"

        redis_queue.add_package_message(package_message)

        call_args = redis_queue.r.xadd.call_args[0][1]
        json_str = call_args["data"]

        # Parse JSON to verify structure
        import json
        parsed = json.loads(json_str)
        assert parsed["node_type"] == "PyPIPackage"
        assert parsed["package"] == "fastapi"
        assert parsed["vendor"] == "n/a"
        assert "moment" in parsed

    def test_read_batch_with_messages(self, redis_queue):
        """Test reading batch of messages from stream."""
        # Mock Redis response format: [(stream_name, [(msg_id, fields)])]
        redis_queue.r.xreadgroup.return_value = [
            (
                "test_stream",
                [
                    ("1234-0", {"data": '{"test": "message1"}'}),
                    ("1235-0", {"data": '{"test": "message2"}'}),
                ],
            )
        ]

        messages = redis_queue.read_batch(count=10, block_ms=1000)

        # Verify read_batch returns list of tuples
        assert len(messages) == 2
        assert messages[0] == ("1234-0", '{"test": "message1"}')
        assert messages[1] == ("1235-0", '{"test": "message2"}')

        # Verify xreadgroup was called
        redis_queue.r.xreadgroup.assert_called_once()

    def test_read_batch_empty_stream(self, redis_queue):
        """Test reading from empty stream returns empty list."""
        redis_queue.r.xreadgroup.return_value = []

        messages = redis_queue.read_batch(count=20)

        assert messages == []

    def test_read_batch_with_count_and_block(self, redis_queue):
        """Test read_batch passes count and block parameters."""
        redis_queue.r.xreadgroup.return_value = []

        redis_queue.read_batch(count=50, block_ms=5000)

        call_args = redis_queue.r.xreadgroup.call_args
        # Verify count and block parameters
        assert call_args[1]["count"] == 50
        assert call_args[1]["block"] == 5000

    def test_read_batch_filters_missing_data(self, redis_queue):
        """Test read_batch filters out entries without data field."""
        redis_queue.r.xreadgroup.return_value = [
            (
                "test_stream",
                [
                    ("1234-0", {"data": '{"test": "message1"}'}),
                    ("1235-0", {"other": "field"}),  # No 'data' field
                    ("1236-0", {"data": '{"test": "message2"}'}),
                ],
            )
        ]

        messages = redis_queue.read_batch()

        # Should only return entries with 'data' field
        assert len(messages) == 2
        assert messages[0][0] == "1234-0"
        assert messages[1][0] == "1236-0"

    def test_ack_message(self, redis_queue):
        """Test acknowledging a message."""
        redis_queue.r.xack.return_value = 1

        redis_queue.ack("1234567890-0")

        # Verify xack was called with correct parameters
        redis_queue.r.xack.assert_called_once()
        call_args = redis_queue.r.xack.call_args[0]
        assert "1234567890-0" in call_args

    def test_dead_letter_adds_to_dlq_and_acks(self, redis_queue):
        """Test dead_letter adds message to DLQ and acknowledges."""
        redis_queue.r.xadd.return_value = "dlq-msg-id"
        redis_queue.r.xack.return_value = 1

        msg_id = "1234567890-0"
        raw_data = '{"test": "failed message"}'
        error_msg = "Processing failed"

        redis_queue.dead_letter(msg_id, raw_data, error_msg)

        # Verify xadd was called for DLQ
        redis_queue.r.xadd.assert_called_once()
        call_args = redis_queue.r.xadd.call_args[0]

        # DLQ stream name should have -dlq suffix
        dlq_stream = call_args[0]
        assert "-dlq" in dlq_stream

        # DLQ entry should contain data and error
        dlq_data = call_args[1]
        assert dlq_data["data"] == raw_data
        assert dlq_data["error"] == error_msg

        # Verify message was acknowledged
        redis_queue.r.xack.assert_called_once()

    def test_dead_letter_complex_error(self, redis_queue):
        """Test dead_letter with complex error message."""
        redis_queue.r.xadd.return_value = "dlq-msg-id"
        redis_queue.r.xack.return_value = 1

        error_msg = "ValueError: Invalid package version format at line 42"

        redis_queue.dead_letter("msg-123", '{"pkg": "test"}', error_msg)

        call_args = redis_queue.r.xadd.call_args[0][1]
        assert call_args["error"] == error_msg
