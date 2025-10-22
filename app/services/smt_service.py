from datetime import datetime
from typing import Any

from app.database import DatabaseManager


class SMTService:
    def __init__(self, db: DatabaseManager):
        self._smt_text_collection = db.get_smt_text_collection()

    async def replace_smt_text(self, smt_text_id: str, text: str) -> None:
        await self._smt_text_collection.replace_one(
            {"smt_text_id": smt_text_id},
            {"smt_text_id": smt_text_id, "text": text, "moment": datetime.now()},
            upsert=True,
        )

    async def read_smt_text(self, smt_text_id: str) -> dict[str, Any]:
        return await self._smt_text_collection.find_one({"smt_text_id": smt_text_id})
