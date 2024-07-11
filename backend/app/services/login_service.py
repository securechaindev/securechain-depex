from typing import Any

from .dbs.databases import get_collection


async def create_user(user: dict[str, str]) -> None:
    users_collection = get_collection("users")
    await users_collection.insert_one(user)


async def create_jwt_token(token: dict[str, Any]) -> None:
    jwt_tokens_collection = get_collection("jwt_tokens")
    await jwt_tokens_collection.insert_one(token)


async def read_user_by_email(email: str) -> dict[str, str]:
    users_collection = get_collection("users")
    return await users_collection.find_one({"email": email})


async def update_user_password(user: dict[str, Any]) -> None:
    users_collection = get_collection("users")
    return await users_collection.update_one({"email": user["email"]}, {"$set": {"password": user["password"]}})
