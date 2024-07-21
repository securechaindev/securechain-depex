from datetime import datetime
from typing import Any

from .dbs.databases import get_graph_db_driver


async def create_repository(repository: dict[str, Any], package_manager: str) -> str:
    query = """
    match(u:User) where u._id = $user_id
    merge(r: Repository{
        owner: $owner,
        name: $name,
        moment: $moment,
        add_extras: $add_extras,
        is_complete: $is_complete
    })
    create (u)-[rel:OWN]->(r)
    return elementid(r) as id
    """
    driver = get_graph_db_driver(package_manager)
    async with driver.session() as session:
        result = await session.run(query, repository)
        record = await result.single()
    return record[0]


async def create_user_repository_rel(repository_id: str, user_id: str, package_manager: str) -> None:
    query = """
    match(u:User) where u._id = $user_id
    match(r:Repository) where elemtid(r) = $repository_id
    merge (u)-[rel:OWN]->(r)
    return elementid(r) as id
    """
    driver = get_graph_db_driver(package_manager)
    async with driver.session() as session:
        result = await session.run(query, repository_id, user_id)
        record = await result.single()
    return record[0]


async def read_repositories_update(owner: str, name: str) -> dict[str, datetime | bool]:
    query = """
    match(r: Repository{owner: $owner, name: $name}) return {moment: r.moment, is_complete: r.is_complete, id: elementid(r)}
    """
    for driver in get_graph_db_driver("ALL"):
        async with driver.session() as session:
            result = await session.run(query, owner=owner, name=name)
            record = await result.single()
            if record:
                break
    return record[0] if record else {"moment": None, "is_complete": True, "id": None}


async def read_repositories(owner: str, name: str) -> dict[str, str]:
    query = """
    match(r: Repository{owner: $owner, name: $name}) return elementid(r)
    """
    repository_ids: dict[str, str] = {}
    for package_manager in ("PIP", "MVN", "MVN"):
        driver = get_graph_db_driver(package_manager)
        async with driver.session() as session:
            result = await session.run(query, owner=owner, name=name)
            record = await result.single()
            repository_ids.update({package_manager: record[0] if record else None})
    return repository_ids


async def read_repository_by_id(
    repository_id: str, package_manager: str
) -> dict[str, str]:
    query = """
    match(r: Repository) where elementid(r)=$repository_id return {name: r.name, owner: r.owner}
    """
    driver = get_graph_db_driver(package_manager)
    async with driver.session() as session:
        result = await session.run(query, repository_id=repository_id)
        record = await result.single()
    return record[0] if record else None


async def read_graphs_by_owner_name_for_sigma(owner: str, name: str) -> dict[str, Any]:
    query = """
    match (r: Repository{owner: $owner, name: $name})
    call apoc.path.subgraphAll(r, {relationshipFilter: '>', limit: 20}) yield nodes, relationships
    unwind nodes as node
        with case labels(node)[0]
            when 'Version' then {
                id: elementid(node),
                label: node.name + '\n' + apoc.text.join(node.cves, ' ')
            }
            else {
                id: elementid(node),
                label: node.name
            }
        end as sigma_nodes, relationships
    unwind relationships as relationship
        with case type(relationship)
            when 'Requires' then {
                source: elementid(startnode(relationship)),
                target: elementid(endnode(relationship)),
                label: relationship.constraints
            }
            else {
                source: elementid(startnode(relationship)),
                target: elementid(endnode(relationship)),
                label: type(relationship)
            }
        end as sigma_relationships, sigma_nodes
    return {nodes: apoc.coll.toSet(collect(sigma_nodes)), relationships: apoc.coll.toSet(collect(sigma_relationships))}
    """
    graphs: dict[str, Any] = {}
    for package_manager in "PIP":
        driver = get_graph_db_driver(package_manager)
        async with driver.session() as session:
            result = await session.run(query, owner=owner, name=name)
            record = await result.single()
        graphs[package_manager] = record if record else None
    return graphs


async def read_graph_for_info_operation(
    file_info_request: dict[str, Any]
) -> dict[str, Any]:
    query = """
    match (rf: RequirementFile) where elementid(rf) = $requirement_file_id
    call apoc.path.subgraphAll(rf, {relationshipFilter: '>', maxLevel: $max_level}) yield nodes, relationships
    with nodes, relationships
    unwind nodes as node
    with case when labels(node)[0] = 'Package' then node end as deps,
    case when labels(node)[0] = 'Version' then node.cves end as cves, relationships
    with collect(deps) as deps, apoc.coll.flatten(collect(cves)) as cves, relationships
    unwind relationships as relationship
    with case when type(relationship) = 'Requires' then relationship end as rels, deps, cves
    with deps, cves, collect(rels) as rels
    return {dependencies: size(deps), edges: size(rels), cves: apoc.coll.toSet(cves)}
    """
    driver = get_graph_db_driver(file_info_request["package_manager"])
    async with driver.session() as session:
        result = await session.run(
            query,
            file_info_request
        )
        record = await result.single()
    return record[0] if record else None


async def read_data_for_smt_transform(
    operation_request: dict[str, Any]
) -> dict[str, Any]:
    query = """
    match (rf: RequirementFile) where elementid(rf) = $requirement_file_id
    call apoc.path.subgraphAll(rf, {relationshipFilter: '>', maxLevel: $max_level}) yield relationships
    unwind relationships as relationship
        with case type(relationship)
            when 'Requires' then {
                parent_count: startnode(relationship).count,
                dependency: endnode(relationship).name,
                constraints: relationship.constraints,
                parent_version_name: relationship.parent_version_name
            } end as requires,
        case type(relationship)
            when 'Have' then {
                    dependency: startnode(relationship).name,
                    release: endnode(relationship).name,
                    count: endnode(relationship).count,
                    mean: endnode(relationship).mean,
                    weighted_mean: endnode(relationship).weighted_mean

            } end as have, rf
    return {name: collect(rf.name)[0], moment: collect(rf.moment)[0], requires: apoc.coll.sortMaps(collect(requires), "parent_count"), have: apoc.map.groupByMulti(apoc.coll.sortMaps(collect(have), "count"), "dependency")}
    """
    driver = get_graph_db_driver(operation_request["package_manager"])
    async with driver.session() as session:
        result = await session.run(
            query,
            operation_request,
        )
        record = await result.single()
    return record[0] if record else None


async def read_repositories_by_user_id(user_id: str) -> dict[str, Any]:
    query = """
    match (u:User)-[]->(r:Repository)-[rel:USE]->(rf:RequirementFile)
    where u._id = $user_id
    with r, collect({name: rf.name, manager: rf.manager, requirement_file_id: elementid(rf)}) as requirement_files
    return collect({
        owner: r.owner,
        name: r.name,
        is_complete: r.is_complete,
        requirement_files: requirement_files
    })
    """
    repositories = []
    for driver in get_graph_db_driver("ALL"):
        async with driver.session() as session:
            result = await session.run(query, user_id=user_id)
            record = await result.single()
            repositories.extend(record[0] if record else [])
    return repositories


async def update_repository_is_complete(
    repository_id: str, is_complete: bool, package_manager: str
) -> None:
    query = """
    match (r:Repository) where elementid(r) = $repository_id
    set r.is_complete = $is_complete
    """
    driver = get_graph_db_driver(package_manager)
    async with driver.session() as session:
        await session.run(query, repository_id=repository_id, is_complete=is_complete)


async def update_repository_moment(repository_id: str, package_manager: str) -> None:
    query = """
    match (r:Repository) where elementid(r) = $repository_id
    set r.moment = $moment
    """
    driver = get_graph_db_driver(package_manager)
    async with driver.session() as session:
        await session.run(query, repository_id=repository_id, moment=datetime.now())


async def update_repository_users(repository_id: str, user_id: str) -> None:
    query = """
    match (r:Repository)
    where elementid(r) = $repository_id and not $user_id in r.users
    set r.users = r.users + [$user_id]
    """
    for driver in get_graph_db_driver("ALL"):
        async with driver.session() as session:
            await session.run(query, repository_id=repository_id, user_id=user_id)
