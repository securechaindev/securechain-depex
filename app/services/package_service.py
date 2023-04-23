from typing import Any

from datetime import datetime

from .dbs.databases import session


async def create_package(
    package: dict[str, Any],
    constraints: list[str] | str,
    parent_id: str
) -> str:
    query = """
    match (parent:RequirementFile|Version)
    where elementid(parent) = $parent_id
    create(p:Package{name:$name,moment:$moment})
    create (parent)-[rel:REQUIRES{constraints:$constraints}]->(p)
    return p.name as name
    """
    result = await session.run(query, package, constraints=constraints, parent_id=parent_id)
    record = await result.single()
    return record[0] if record else None


async def read_package_by_name(package_name: str) -> dict[str, Any]:
    query = """
    match (p: Package)
    where p.name = $package_name
    return p{.*}
    """
    result = await session.run(query, package_name=package_name)
    record = await result.single()
    return record[0] if record else None


async def relate_package(package_name: str, constraints: list[str] | str, parent_id: str) -> None:
    query = """
    match 
        (p: Package),
        (parent: RequirementFile|Version)
    where p.name = $package_name and elementid(parent) = $parent_id
    create (parent)-[rel: REQUIRES {constraints: $constraints}]->(p)
    """
    await session.run(
        query,
        package_name=package_name,
        constraints=constraints,
        parent_id=parent_id
    )


async def update_package_moment(package_name: str) -> None:
    query = '''
    match (p: Package) where p.name = $package_name
    set p.moment = $moment
    '''
    await session.run(query, package_name=package_name, moment=datetime.now())