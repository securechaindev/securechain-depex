from datetime import datetime
from typing import Any

from .dbs import get_collection


async def replace_operation_result(operation_result_id: str, result: dict[str, Any]) -> None:
    operation_result_collection = get_collection("operation_result")
    await operation_result_collection.replace_one(
        {"operation_result_id": operation_result_id},
        {"operation_result_id": operation_result_id, "result": result, "moment": datetime.now()},
        upsert=True,
    )


async def read_operation_result(operation_result_id: str) -> dict[str, Any]:
    operation_result_collection = get_collection("operation_result")
    return await operation_result_collection.find_one({"operation_result_id": operation_result_id})
