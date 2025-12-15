from json import dumps

from redis import Redis
from redis.exceptions import ResponseError

from app.schemas import PackageMessageSchema
from app.settings import settings


class RedisQueue:
    def __init__(self, host: str, port: int, db: int = 0):
        self.r = Redis(host=host, port=port, db=db, decode_responses=True)
        try:
            self.r.xgroup_create(settings.REDIS_STREAM, settings.REDIS_GROUP, id="0-0", mkstream=True)
        except ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise

    @classmethod
    def from_env(cls) -> RedisQueue:
        return cls(settings.REDIS_HOST, settings.REDIS_PORT, settings.REDIS_DB)

    async def add_package_message(self, message: PackageMessageSchema) -> str:
        message_dict = message.model_dump(mode="json")
        raw_json = dumps(message_dict)
        msg_id = await self.r.xadd(settings.REDIS_STREAM, {"data": raw_json})
        return msg_id

    def ack(self, msg_id: str) -> None:
        self.r.xack(settings.REDIS_STREAM, settings.REDIS_GROUP, msg_id)

    def dead_letter(self, msg_id: str, raw: str, error: str) -> None:
        self.r.xadd(f"{settings.REDIS_STREAM}-dlq", {"data": raw, "error": error})
        self.ack(msg_id)
