from datetime import datetime
from typing import Any

from .dbs.databases import get_graph_db_driver


async def create_requirement_file(requirement_file: dict[str, Any], repository_id: str) -> str:
    query = """
    match (r:Repository)
    where elementid(r) = $repository_id
    create(rf:RequirementFile {name:$name,manager:$manager,moment:$moment})
    create (r)-[rel:USE]->(rf)
    return elementid(rf) as id
    """
    async with get_graph_db_driver().session() as session:
        result = await session.run(query, requirement_file, repository_id=repository_id)
        record = await result.single()
    return record[0] if record else None


async def read_requirement_files_by_repository(repository_id: str) -> dict[str, str]:
    query = """
    match (r:Repository) where elementid(r) = $repository_id
    match (r)-[use_rel]->(requirement_file)
    return apoc.map.fromPairs(collect([requirement_file.name, elementid(requirement_file)]))
    """
    async with get_graph_db_driver().session() as session:
        result = await session.run(query, repository_id=repository_id)
        record = await result.single()
    return record[0] if record else None


async def update_requirement_rel_constraints(requirement_file_id: str, package_name: str, constraints: str) -> None:
    query = """
    match (rf:RequirementFile) where elementid(rf) = $requirement_file_id
    match (rf)-[requirement_rel]->(package)
    where package.name = $package_name
    set requirement_rel.constraints = $constraints
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
    match (rf: RequirementFile) where elementid(rf) = $requirement_file_id
    set rf.moment = $moment
    """
    async with get_graph_db_driver().session() as session:
        await session.run(
            query, requirement_file_id=requirement_file_id, moment=datetime.now()
    )


async def delete_requirement_file(repository_id: str, requirement_file_name: str) -> None:
    query = """
    match (r:Repository) where elementid(r) = $repository_id
    match (r)-[use_rel]->(requirement_file)-[requirement_rel]->(p)
    where requirement_file.name = $requirement_file_name
    delete requirement_rel, use_rel, requirement_file
    """
    async with get_graph_db_driver().session() as session:
        await session.run(
            query, repository_id=repository_id, requirement_file_name=requirement_file_name
        )


async def delete_requirement_file_rel(requirement_file_id: str, package_name: str) -> None:
    query = """
    match (rf:RequirementFile) where elementid(rf) = $requirement_file_id
    match (rf)-[requirement_rel]->(package)
    where package.name = $package_name
    delete requirement_rel
    """
    async with get_graph_db_driver().session() as session:
        await session.run(
            query, requirement_file_id=requirement_file_id, package_name=package_name
        )
