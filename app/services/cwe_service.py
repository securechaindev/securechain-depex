from typing import Any

from .dbs.databases import get_collection


async def read_cwes_by_cve_id(cve: str) -> list[dict[str, Any]]:
    cwes_collection = get_collection("cwes")
    pipeline: Any = [
        {"$project": {
            "_id": 0,
            "@ID": 1,
            "Description": 1,
            "Extended_Description": 1,
            "Background_Details": 1,
            "Common_Consequences": 1,
            "Detection_Methods": 1,
            "Potential_Mitigations": 1,
            "Demonstrative_Examples": 1,
            "cvelist": 1
        }},
        {"$match": {"cvelist": {"$in": [cve]}}},
    ]
    try:
        return [
            cwe async for cwe in cwes_collection.aggregate(pipeline)
        ]
    except Exception as _:
        return []
