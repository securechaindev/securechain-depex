from typing import Any

from .dbs.databases import session


async def create_requirement_file(requirement_file: dict[str, Any], owner: str, name: str) -> str:
    query = """
    match (r:Repository)
    where r.owner = $owner and r.name = $reponame
    create(rf:RequirementFile {name:$name,manager:$manager})
    create (r)-[rel:USE]->(rf)
    return elementid(rf) as id
    """
    result = await session.run(query, requirement_file, owner=owner, reponame=name)
    record = await result.single()
    return record[0] if record else None