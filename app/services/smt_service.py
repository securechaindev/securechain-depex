from datetime import datetime
from typing import Any

from .dbs.databases import get_collection


async def replace_smt_text(smt_id: str, text: str) -> None:
    smt_text_collection = get_collection("smt_text")
    await smt_text_collection.replace_one(
        {"smt_id": smt_id},
        {"smt_id": smt_id, "text": text, "moment": datetime.now()},
        upsert=True,
    )


async def read_smt_text(smt_id: str) -> dict[str, Any]:
    smt_text_collection = get_collection("smt_text")
    return await smt_text_collection.find_one({"smt_id": smt_id})
