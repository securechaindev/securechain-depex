from datetime import datetime
from typing import Any

from .dbs.databases import get_graph_db_driver


async def create_package_and_versions(
    package: dict[str, Any],
    versions: list[dict[str, Any]],
    package_manager: str,
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
    query_part2 = f"{{{"group_id:$group_id, " if package_manager == "MVN" else ""}name:$name, moment:$moment}}"
    query_part3 = (
        f"create (parent)-[rel_p:Requires{{constraints:$constraints{", parent_version_name:$parent_version_name" if parent_version_name else ""}}}]->(p)"
        if parent_id
        else ""
    )
    query = f"""
    {query_part1}
    create(p:Package{query_part2})
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
    driver = get_graph_db_driver(package_manager)
    async with driver.session() as session:
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
    versions: list[dict[str, Any]],
    package_manager: str
) -> dict[str, Any]:
    query_part = f"{{{"group_id:$group_id, " if package_manager == "MVN" else ""}name:$name}}"
    query = f"""
    match(p:Package{query_part})
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
    driver = get_graph_db_driver(package_manager)
    async with driver.session() as session:
        result = await session.run(
            query,
            package,
            versions=versions,
        )
        record = await result.single()
    return record[0] if record else []


# TODO: Añadir el group id para busquedas en maven más eficientes con el indice compuesto
async def read_package_by_name(
    package_name: str, package_manager: str
) -> dict[str, Any]:
    query = """
    match (p:Package)
    where p.name = $package_name
    return p{id: elementid(p), .*}
    """
    driver = get_graph_db_driver(package_manager)
    async with driver.session() as session:
        result = await session.run(query, package_name=package_name)
        record = await result.single()
    return record[0] if record else None


async def read_packages_by_requirement_file(
    requirement_file_id: str, package_manager: str
) -> dict[str, str]:
    query_part = "package.group_id + ':' + " if package_manager == "MVN" else ""
    query = f"""
    match (rf:RequirementFile) where elementid(rf) = $requirement_file_id
    match (rf)-[requirement_rel]->(package)
    return apoc.map.fromPairs(collect([{query_part}package.name, requirement_rel.constraints]))
    """
    driver = get_graph_db_driver(package_manager)
    async with driver.session() as session:
        result = await session.run(query, requirement_file_id=requirement_file_id)
        record = await result.single()
    return record[0] if record else None


async def relate_packages(packages: list[dict[str, Any]], package_manager: str) -> None:
    query = """
    unwind $packages as package
    match (parent:RequirementFile|Version)
    where elementid(parent) = package.parent_id
    match (p: Package)
    where elementid(p) = package.id
    create (parent)-[:Requires{constraints: package.constraints, parent_version_name: package.parent_version_name}]->(p)
    """
    driver = get_graph_db_driver(package_manager)
    async with driver.session() as session:
        await session.run(query, packages=packages)


async def update_package_moment(package_name: str, package_manager: str) -> None:
    query = """
    match (p:Package) where p.name = $package_name
    set p.moment = $moment
    """
    driver = get_graph_db_driver(package_manager)
    async with driver.session() as session:
        await session.run(query, package_name=package_name, moment=datetime.now())
