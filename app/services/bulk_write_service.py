from typing import Any

from .dbs.databases import get_collection


async def bulk_write_actions(
    actions: list[Any], collection_name: str, ordered: bool
) -> None:
    collection = get_collection(collection_name)
    await collection.bulk_write(actions, ordered=ordered)
