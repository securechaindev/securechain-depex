from datetime import datetime
from typing import Any

from .dbs.databases import get_graph_db_session


async def create_repository(repository: dict[str, Any], package_manager: str) -> str:
    query = """
    merge(r: Repository{
        owner: $owner,
        name: $name,
        moment: $moment,
        add_extras: $add_extras,
        is_complete: $is_complete
    })
    return elementid(r) as id
    """
    session = get_graph_db_session(package_manager)
    result = await session.run(query, repository)
    record = await result.single()
    return record[0]


async def read_repositories_moment(owner: str, name: str) -> dict[str, datetime | bool]:
    query = """
    match(r: Repository{owner: $owner, name: $name}) return {moment: r.moment, is_complete: r.is_complete}
    """
    session = get_graph_db_session("PIP")
    result = await session.run(query, owner=owner, name=name)
    record = await result.single()
    for session in get_graph_db_session("ALL"):
        result = await session.run(query, owner=owner, name=name)
        record = await result.single()
        if record:
            break
    return record[0] if record else {"moment": None, "is_complete": True}


async def read_repositories(owner: str, name: str) -> dict[str, str]:
    repository_ids: dict[str, str] = {}
    query = """
    match(r: Repository{owner: $owner, name: $name}) return elementid(r)
    """
    pip_session, npm_session, mvn_session = get_graph_db_session("ALL")
    pip_result = await pip_session.run(query, owner=owner, name=name)
    pip_record = await pip_result.single()
    repository_ids.update({"PIP": pip_record[0] if pip_record else None})
    npm_result = await npm_session.run(query, owner=owner, name=name)
    npm_record = await npm_result.single()
    repository_ids.update({"NPM": npm_record[0] if npm_record else None})
    mvn_result = await mvn_session.run(query, owner=owner, name=name)
    mvn_record = await mvn_result.single()
    repository_ids.update({"MVN": mvn_record[0] if mvn_record else None})
    return repository_ids


async def read_repository_by_id(
    repository_id: str, package_manager: str
) -> dict[str, str]:
    query = """
    match(r: Repository) where elementid(r)=$repository_id return {name: r.name, owner: r.owner}
    """
    session = get_graph_db_session(package_manager)
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
        session = get_graph_db_session(package_manager)
        result = await session.run(query, owner=owner, name=name)
        record = await result.single()
        graphs[package_manager] = record if record else None
    return graphs


async def read_graph_for_info_operation(
    requirement_file_id: str, package_manager: str, max_level: int
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
    session = get_graph_db_session(package_manager)
    result = await session.run(
        query,
        requirement_file_id=requirement_file_id,
        max_level=max_level * 2 if max_level != -1 else max_level,
    )
    record = await result.single()
    return record[0] if record else None


async def read_data_for_smt_transform(
    requirement_file_id: str, package_manager: str, max_level: int
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
    session = get_graph_db_session(package_manager)
    result = await session.run(
        query,
        requirement_file_id=requirement_file_id,
        max_level=max_level * 2 if max_level != -1 else max_level,
    )
    record = await result.single()
    return record[0] if record else None


async def update_repository_is_complete(
    repository_id: str, is_complete: bool, package_manager: str
) -> None:
    query = """
    match (r: Repository) where elementid(r) = $repository_id
    set r.is_complete = $is_complete
    """
    session = get_graph_db_session(package_manager)
    await session.run(query, repository_id=repository_id, is_complete=is_complete)


async def update_repository_moment(repository_id: str, package_manager: str) -> None:
    query = """
    match (r: Repository) where elementid(r) = $repository_id
    set r.moment = $moment
    """
    session = get_graph_db_session(package_manager)
    await session.run(query, repository_id=repository_id, moment=datetime.now())
