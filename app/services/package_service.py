from typing import Any

from datetime import datetime

from .dbs.databases import get_graph_db_session


async def create_package_and_versions(package: dict[str, Any], versions: list[dict[str, Any]], constraints: list[str] | str, parent_id: str, package_manager: str) -> list[dict[str, str]]:
    query = '''
    match (parent:RequirementFile|Version)
    where elementid(parent) = $parent_id
    create(p:Package{name:$name,moment:$moment})
    create (parent)-[rel_p:Requires{constraints:$constraints}]->(p)
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
    '''
    session = get_graph_db_session(package_manager)
    result = await session.run(query, package, constraints=constraints, parent_id=parent_id, versions=versions)
    record = await result.single()
    return record[0] if record else None


async def read_package_by_name(package_name: str, package_manager: str) -> dict[str, Any]:
    query = '''
    match (p:Package)
    where p.name = $package_name
    return p{.*}
    '''
    session = get_graph_db_session(package_manager)
    result = await session.run(query, package_name=package_name)
    record = await result.single()
    return record[0] if record else None


async def relate_package(package_name: str, constraints: list[str] | str, parent_id: str, package_manager: str) -> None:
    query = '''
    match 
        (p:Package),
        (parent:RequirementFile|Version)
    where p.name = $package_name and elementid(parent) = $parent_id
    create (parent)-[rel:Requires{constraints: $constraints}]->(p)
    '''
    session = get_graph_db_session(package_manager)
    await session.run(query, package_name=package_name, constraints=constraints, parent_id=parent_id)


async def update_package_moment(package_name: str, package_manager: str) -> None:
    query = '''
    match (p:Package) where p.name = $package_name
    set p.moment = $moment
    '''
    session = get_graph_db_session(package_manager)
    await session.run(query, package_name=package_name, moment=datetime.now())