from datetime import datetime
from typing import Any

from app.database import DatabaseManager


class OperationService:
    def __init__(self, db: DatabaseManager):
        self._operation_result_collection = db.get_operation_result_collection()

    async def replace_operation_result(self, operation_result_id: str, result: dict[str, Any]) -> None:
        await self._operation_result_collection.replace_one(
            {"operation_result_id": operation_result_id},
            {"operation_result_id": operation_result_id, "result": result, "moment": datetime.now()},
            upsert=True,
        )

    async def read_operation_result(self, operation_result_id: str) -> dict[str, Any]:
        return await self._operation_result_collection.find_one({"operation_result_id": operation_result_id})
