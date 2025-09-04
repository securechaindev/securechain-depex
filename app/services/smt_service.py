from datetime import datetime
from typing import Any

from .dbs import get_collection


async def replace_smt_text(smt_text_id: str, text: str) -> None:
    smt_text_collection = get_collection("smt_text")
    await smt_text_collection.replace_one(
        {"smt_text_id": smt_text_id},
        {"smt_text_id": smt_text_id, "text": text, "moment": datetime.now()},
        upsert=True,
    )


async def read_smt_text(smt_text_id: str) -> dict[str, Any]:
    smt_text_collection = get_collection("smt_text")
    return await smt_text_collection.find_one({"smt_text_id": smt_text_id})
