from bson.objectid import ObjectId

from app.services.db.database import package_collection


async def add_package(package_data: dict) -> dict:
    package = await package_collection.insert_one(package_data)
    new_package = await package_collection.find_one({"_id": package.inserted_id})
    return new_package