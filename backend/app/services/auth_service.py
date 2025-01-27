from typing import Any

from .dbs.databases import get_collection, get_graph_db_driver


async def create_user(user: dict[str, str]) -> None:
    query = """
    create(u: User{
        _id: $user_id
    })
    """
    users_collection = get_collection("users")
    result = await users_collection.insert_one(user)
    user_id = str(result.inserted_id)
    async with get_graph_db_driver().session() as session:
        result = await session.run(query, user_id=user_id)


async def read_user_by_email(email: str) -> dict[str, str]:
    users_collection = get_collection("users")
    return await users_collection.find_one({"email": email})


async def update_user_password(user: dict[str, Any]) -> None:
    users_collection = get_collection("users")
    return await users_collection.update_one({"email": user["email"]}, {"$set": {"password": user["password"]}})
