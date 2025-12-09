
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from redis.exceptions import ResponseError

from app.schemas import PackageMessageSchema
from app.utils.redis_queue import RedisQueue


class TestRedisQueue:

    @pytest.fixture
    def mock_redis(self):
        with patch("app.utils.redis_queue.Redis") as mock:
            redis_instance = MagicMock()
            mock.return_value = redis_instance
            yield redis_instance

    @pytest.fixture
    def redis_queue(self, mock_redis):
        mock_redis.xgroup_create.return_value = None
        queue = RedisQueue(host="localhost", port=6379, db=0)
        return queue

    @pytest.fixture
    def package_message(self):
        return PackageMessageSchema(
            node_type="PyPIPackage",
            package="fastapi",
            vendor="n/a",
            repository_url="https://github.com/tiangolo/fastapi",
        )

    def test_init_creates_stream_group(self, mock_redis):
        mock_redis.xgroup_create.return_value = None
        queue = RedisQueue(host="localhost", port=6379, db=1)

        assert queue.r == mock_redis

        mock_redis.xgroup_create.assert_called_once()

    def test_init_handles_busygroup_error(self, mock_redis):
        mock_redis.xgroup_create.side_effect = ResponseError("BUSYGROUP Consumer Group name already exists")

        queue = RedisQueue(host="localhost", port=6379, db=0)
        assert queue.r == mock_redis

    def test_init_raises_other_redis_errors(self, mock_redis):
        mock_redis.xgroup_create.side_effect = ResponseError("Some other Redis error")

        with pytest.raises(ResponseError, match="Some other Redis error"):
            RedisQueue(host="localhost", port=6379, db=0)

    def test_from_env_uses_settings(self, mock_redis):
        mock_redis.xgroup_create.return_value = None

        with patch("app.utils.redis_queue.settings") as mock_settings:
            mock_settings.REDIS_HOST = "redis.example.com"
            mock_settings.REDIS_PORT = 6380
            mock_settings.REDIS_DB = 2

            queue = RedisQueue.from_env()

            assert queue.r == mock_redis

    @pytest.mark.asyncio
    async def test_add_package_message(self, redis_queue, package_message):
        redis_queue.r.xadd = AsyncMock(return_value="1234567890-0")

        msg_id = await redis_queue.add_package_message(package_message)

        assert msg_id == "1234567890-0"
        redis_queue.r.xadd.assert_called_once()

        call_args = redis_queue.r.xadd.call_args
        stream_name = call_args[0][0]
        data = call_args[0][1]

        assert "redis_stream" in str(stream_name) or stream_name

        assert "data" in data
        json_data = data["data"]
        assert "fastapi" in json_data
        assert "PyPIPackage" in json_data

    @pytest.mark.asyncio
    async def test_add_package_message_serialization(self, redis_queue, package_message):
        redis_queue.r.xadd = AsyncMock(return_value="1234567890-0")

        await redis_queue.add_package_message(package_message)

        call_args = redis_queue.r.xadd.call_args[0][1]
        json_str = call_args["data"]

        import json
        parsed = json.loads(json_str)
        assert parsed["node_type"] == "PyPIPackage"
        assert parsed["package"] == "fastapi"
        assert parsed["vendor"] == "n/a"
        assert "moment" in parsed

    @pytest.mark.asyncio
    async def test_read_batch_with_messages(self, redis_queue):
        redis_queue.r.xreadgroup = AsyncMock(return_value=[
            (
                "test_stream",
                [
                    ("1234-0", {"data": '{"test": "message1"}'}),
                    ("1235-0", {"data": '{"test": "message2"}'}),
                ],
            )
        ])

        messages = await redis_queue.read_batch(count=10, block_ms=1000)

        assert len(messages) == 2
        assert messages[0] == ("1234-0", '{"test": "message1"}')
        assert messages[1] == ("1235-0", '{"test": "message2"}')

        redis_queue.r.xreadgroup.assert_called_once()

    @pytest.mark.asyncio
    async def test_read_batch_empty_stream(self, redis_queue):
        redis_queue.r.xreadgroup = AsyncMock(return_value=[])

        messages = await redis_queue.read_batch(count=20)

        assert messages == []

    @pytest.mark.asyncio
    async def test_read_batch_with_count_and_block(self, redis_queue):
        redis_queue.r.xreadgroup = AsyncMock(return_value=[])

        await redis_queue.read_batch(count=50, block_ms=5000)

        call_args = redis_queue.r.xreadgroup.call_args
        assert call_args[1]["count"] == 50
        assert call_args[1]["block"] == 5000

    @pytest.mark.asyncio
    async def test_read_batch_filters_missing_data(self, redis_queue):
        redis_queue.r.xreadgroup = AsyncMock(return_value=[
            (
                "test_stream",
                [
                    ("1234-0", {"data": '{"test": "message1"}'}),
                    ("1235-0", {"other": "field"}),
                    ("1236-0", {"data": '{"test": "message2"}'}),
                ],
            )
        ])

        messages = await redis_queue.read_batch()

        assert len(messages) == 2
        assert messages[0][0] == "1234-0"
        assert messages[1][0] == "1236-0"

    def test_ack_message(self, redis_queue):
        redis_queue.r.xack.return_value = 1

        redis_queue.ack("1234567890-0")

        redis_queue.r.xack.assert_called_once()
        call_args = redis_queue.r.xack.call_args[0]
        assert "1234567890-0" in call_args

    def test_dead_letter_adds_to_dlq_and_acks(self, redis_queue):
        redis_queue.r.xadd.return_value = "dlq-msg-id"
        redis_queue.r.xack.return_value = 1

        msg_id = "1234567890-0"
        raw_data = '{"test": "failed message"}'
        error_msg = "Processing failed"

        redis_queue.dead_letter(msg_id, raw_data, error_msg)

        redis_queue.r.xadd.assert_called_once()
        call_args = redis_queue.r.xadd.call_args[0]

        dlq_stream = call_args[0]
        assert "-dlq" in dlq_stream

        dlq_data = call_args[1]
        assert dlq_data["data"] == raw_data
        assert dlq_data["error"] == error_msg

        redis_queue.r.xack.assert_called_once()

    def test_dead_letter_complex_error(self, redis_queue):
        redis_queue.r.xadd.return_value = "dlq-msg-id"
        redis_queue.r.xack.return_value = 1

        error_msg = "ValueError: Invalid package version format at line 42"

        redis_queue.dead_letter("msg-123", '{"pkg": "test"}', error_msg)

        call_args = redis_queue.r.xadd.call_args[0][1]
        assert call_args["error"] == error_msg
