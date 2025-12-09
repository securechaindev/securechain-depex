from datetime import datetime
from typing import Any

from app.database import DatabaseManager


class SMTService:
    def __init__(self, db: DatabaseManager):
        self.smts_collection = db.get_smts_collection()

    async def replace_smt(self, smt_id: str, text: str) -> None:
        await self.smts_collection.replace_one(
            {"smt_id": smt_id},
            {"smt_id": smt_id, "text": text, "moment": datetime.now()},
            upsert=True,
        )

    async def read_smt(self, smt_id: str) -> dict[str, Any] | None:
        return await self.smts_collection.find_one({"smt_id": smt_id})
