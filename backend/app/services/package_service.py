from datetime import datetime
from typing import Any

from .dbs.databases import get_graph_db_driver


async def create_package_and_versions(
    package: dict[str, Any],
    versions: list[dict[str, Any]],
    constraints: str | None = None,
    parent_id: str | None = None,
    parent_version_name: str | None = None,
) -> list[dict[str, str]]:
    query_part1 = (
        """
        match (parent:RequirementFile|Version)
        where elementid(parent) = $parent_id
        """
        if parent_id
        else ""
    )
    query_part3 = (
        f"create (parent)-[rel_p:Requires{{constraints:$constraints{", parent_version_name:$parent_version_name" if parent_version_name else ""}}}]->(p)"
        if parent_id
        else ""
    )
    query = f"""
    {query_part1}
    create(p:Package{{manager:$manager, group_id:$group_id, name:$name, moment:$moment}})
    {query_part3}
    with p as package
    unwind $versions as version
    create(v:Version{{
        name: version.name,
        release_date: version.release_date,
        count: version.count,
        cves: version.cves,
        mean: version.mean,
        weighted_mean: version.weighted_mean
    }})
    create (package)-[rel_v:Have]->(v)
    return collect({{name: v.name, id: elementid(v)}})
    """
    async with get_graph_db_driver().session() as session:
        result = await session.run(
            query,
            package,
            constraints=constraints,
            parent_id=parent_id,
            parent_version_name=parent_version_name,
            versions=versions,
        )
        record = await result.single()
    return record[0] if record else []


async def create_versions(
    package: dict[str, Any],
    versions: list[dict[str, Any]]
) -> dict[str, Any]:
    query = """
    match(p:Package{manager:$manager, group_id:$group_id, name:$name})
    with p as package
    unwind $versions as version
    create(v:Version{
        name: version.name,
        release_date: version.release_date,
        count: version.count,
        cves: version.cves,
        mean: version.mean,
        weighted_mean: version.weighted_mean
    })
    create (package)-[rel_v:Have]->(v)
    return collect({name: v.name, id: elementid(v)})
    """
    async with get_graph_db_driver().session() as session:
        result = await session.run(
            query,
            package,
            versions=versions,
        )
        record = await result.single()
    return record[0] if record else []


async def read_package_by_name(manager: str, group_id: str, name: str) -> dict[str, Any]:
    query = """
    match (p:Package)
    where p.manager = $manager and p.group_id = $group_id and p.name = $name
    return p{id: elementid(p), .*}
    """
    async with get_graph_db_driver().session() as session:
        result = await session.run(
            query,
            manager = manager,
            group_id=group_id,
            name=name
        )
        record = await result.single()
    return record[0] if record else None


async def read_packages_by_requirement_file(requirement_file_id: str) -> dict[str, str]:
    query = """
    match (rf:RequirementFile) where elementid(rf) = $requirement_file_id
    match (rf)-[requirement_rel]->(package)
    return apoc.map.fromPairs(collect([package.group_id + ':' + package.name, requirement_rel.constraints]))
    """
    async with get_graph_db_driver().session() as session:
        result = await session.run(query, requirement_file_id=requirement_file_id)
        record = await result.single()
    return record[0] if record else None


async def relate_packages(packages: list[dict[str, Any]]) -> None:
    query = """
    unwind $packages as package
    match (parent:RequirementFile|Version)
    where elementid(parent) = package.parent_id
    match (p: Package)
    where elementid(p) = package.id
    create (parent)-[:Requires{constraints: package.constraints, parent_version_name: package.parent_version_name}]->(p)
    """
    async with get_graph_db_driver().session() as session:
        await session.run(query, packages=packages)


async def update_package_moment(manager: str, group_id: str, name: str) -> None:
    query = """
    match (p:Package) where p.manager = $manager and p.group_id = $group_id and p.name = $name
    set p.moment = $moment
    """
    async with get_graph_db_driver().session() as session:
        await session.run(query, manager=manager, group_id=group_id, name=name, moment=datetime.now())
