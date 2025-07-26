from datetime import datetime
from typing import Any

from .dbs.databases import get_graph_db_driver


async def create_requirement_file(requirement_file: dict[str, Any], repository_id: str) -> str:
    query = """
    MATCH (r:Repository)
    WHERE elementid(r) = $repository_id
    CREATE (rf:RequirementFile {name:$name,manager:$manager,moment:$moment})
    CREATE (r)-[rel:USE]->(rf)
    RETURN elementid(rf) AS id
    """
    async with get_graph_db_driver().session() as session:
        result = await session.run(query, requirement_file, repository_id=repository_id)
        record = await result.single()
    return record[0] if record else None


async def read_requirement_files_by_repository(repository_id: str) -> dict[str, str]:
    query = """
    MATCH (r:Repository)
    WHERE elementid(r) = $repository_id
    MATCH (r)-[use_rel]->(requirement_file)
    RETURN apoc.map.fromPairs(collect([requirement_file.name, elementid(requirement_file)]))
    """
    async with get_graph_db_driver().session() as session:
        result = await session.run(query, repository_id=repository_id)
        record = await result.single()
    return record[0] if record else None


async def read_requirement_file_moment(requirement_file_id: str) -> datetime:
    query = """
    MATCH (rf:RequirementFile)
    WHERE elementid(rf) = $requirement_file_id
    RETURN rf.moment AS moment
    """
    async with get_graph_db_driver().session() as session:
        result = await session.run(query, requirement_file_id=requirement_file_id)
        record = await result.single()
    return record[0] if record else None


async def update_requirement_rel_constraints(requirement_file_id: str, package_name: str, constraints: str) -> None:
    query = """
    MATCH (rf:RequirementFile)
    WHERE elementid(rf) = $requirement_file_id
    MATCH (rf)-[requirement_rel]->(package)
    WHERE package.name = $package_name
    SET requirement_rel.constraints = $constraints
    """
    async with get_graph_db_driver().session() as session:
        await session.run(
            query,
            requirement_file_id=requirement_file_id,
            package_name=package_name,
            constraints=constraints,
        )


async def update_requirement_file_moment(requirement_file_id: str) -> None:
    query = """
    MATCH (rf: RequirementFile)
    WHERE elementid(rf) = $requirement_file_id
    SET rf.moment = $moment
    """
    async with get_graph_db_driver().session() as session:
        await session.run(
            query, requirement_file_id=requirement_file_id, moment=datetime.now()
    )


async def delete_requirement_file(repository_id: str, requirement_file_name: str) -> None:
    query = """
    MATCH (r:Repository)
    WHERE elementid(r) = $repository_id
    MATCH (r)-[use_rel]->(requirement_file)-[requirement_rel]->(p)
    WHERE requirement_file.name = $requirement_file_name
    DELETE requirement_rel, use_rel, requirement_file
    """
    async with get_graph_db_driver().session() as session:
        await session.run(
            query, repository_id=repository_id, requirement_file_name=requirement_file_name
        )


async def delete_requirement_file_rel(requirement_file_id: str, package_name: str) -> None:
    query = """
    MATCH (rf:RequirementFile)
    WHERE elementid(rf) = $requirement_file_id
    MATCH (rf)-[requirement_rel]->(package)
    WHERE package.name = $package_name
    DELETE requirement_rel
    """
    async with get_graph_db_driver().session() as session:
        await session.run(
            query, requirement_file_id=requirement_file_id, package_name=package_name
        )
