from typing import Any
from datetime import datetime
from fastapi import HTTPException
from .dbs.databases import get_graph_db_session


async def create_repositories(repository: dict[str, Any]) -> dict[str, str]:
    repository_ids: dict[str, str] = {}
    query = '''
    create(r: Repository{
        owner: $owner,
        name: $name,
        add_extras: $add_extras,
        is_complete: $is_complete
    })
    return elementid(r) as id
    '''
    pip_session, npm_session, mvn_session = get_graph_db_session('ALL')
    pip_result = await pip_session.run(query, repository)
    pip_record = await pip_result.single()
    repository_ids.update({'PIP': pip_record[0]})
    npm_result = await npm_session.run(query, repository)
    npm_record = await npm_result.single()
    repository_ids.update({'NPM': npm_record[0]})
    mvn_result = await mvn_session.run(query, repository)
    mvn_record = await mvn_result.single()
    repository_ids.update({'MVN': mvn_record[0]})
    return repository_ids


async def create_repository(repository: dict[str, Any], package_manager: str) -> dict[str, str]:
    query = '''
    merge(r: Repository{
        owner: $owner,
        name: $name,
        moment: $moment,
        add_extras: $add_extras,
        is_complete: $is_complete
    })
    return elementid(r) as id
    '''
    session = get_graph_db_session(package_manager)
    result = await session.run(query, repository)
    record = await result.single()
    return record[0]


async def read_repositories_moment(owner: str, name: str) -> datetime:
    query = '''
    match(r: Repository{owner: $owner, name: $name}) return r.moment
    '''
    for session in get_graph_db_session('ALL'):
        result = await session.run(query, owner=owner, name=name)
        record = await result.single()
        if record:
            break
    return record[0] if record else None


async def read_repositories(owner: str, name: str) -> dict[str, str]:
    repository_ids: dict[str, str] = {}
    query = '''
    match(r: Repository{owner: $owner, name: $name}) return elementid(r)
    '''
    pip_session, npm_session, mvn_session = get_graph_db_session('ALL')
    pip_result = await pip_session.run(query, owner=owner, name=name)
    pip_record = await pip_result.single()
    repository_ids.update({'PIP': pip_record[0] if pip_record else None})
    npm_result = await npm_session.run(query, owner=owner, name=name)
    npm_record = await npm_result.single()
    repository_ids.update({'NPM': npm_record[0] if npm_record else None})
    mvn_result = await mvn_session.run(query, owner=owner, name=name)
    mvn_record = await mvn_result.single()
    repository_ids.update({'MVN': mvn_record[0] if mvn_record else None})
    return repository_ids


async def read_repository_by_id(repository_id: str, package_manager: str) -> dict[str, str]:
    query = '''
    match(r: Repository) where elementid(r)=$repository_id return {name: r.name, owner: r.owner}
    '''
    session = get_graph_db_session(package_manager)
    result = await session.run(query, repository_id=repository_id)
    record = await result.single()
    return record[0] if record else None


async def read_repository_by_owner_name(owner: str, name: str, package_manager: str) -> dict[str, Any]:
    query = '''
    match(r: Repository{owner: $owner, name: $name}) return elementid(r)
    '''
    session = get_graph_db_session(package_manager)
    result = await session.run(query, owner=owner, name=name)
    record = await result.single()
    return record[0] if record else None


async def read_repository_files(repository_id: str, package_manager: str) -> list[dict[str, Any]]:
    query = '''
    match(r: Repository)-[*1]->(s:RequirementFile) where elementid(r) = $repository_id return s{.*}
    '''
    session = get_graph_db_session(package_manager)
    result = await session.run(query, repository_id=repository_id)
    record = await result.single()
    return record[0] if record else None


async def read_graph_by_repository_id(requirement_file_id: str, package_manager: str) -> dict[str, Any]:
    query = '''
    match (rf: RequirementFile) where elementid(rf) = $requirement_file_id
    call apoc.path.subgraphAll(rf, {relationshipFilter: '>'}) yield nodes, relationships
    return nodes, relationships
    '''
    session = get_graph_db_session(package_manager)
    result = await session.run(query, requirement_file_id=requirement_file_id)
    record = await result.single()
    if record:
        return record[0]
    raise HTTPException(status_code=404, detail=[f'Graph with id {requirement_file_id} not found'])


async def read_info(requirement_file_id: str, package_manager: str) -> dict[str, Any]:
    query = '''
    match (rf: RequirementFile) where elementid(rf) = $requirement_file_id
    call apoc.path.subgraphAll(rf, {relationshipFilter: '>'}) yield nodes, relationships
    with nodes, relationships
    unwind nodes as node
    with case when labels(node)[0] = 'Package' then node end as deps,
    case when labels(node)[0] = 'Version' then node.cves end as cves, relationships
    with collect(deps) as deps, apoc.coll.flatten(collect(cves)) as cves, relationships
    unwind relationships as relationship
    with case when type(relationship) = 'REQUIRES' then relationship end as rels, deps, cves
    with deps, cves, collect(rels) as rels
    return {dependencies: size(deps), edges: size(rels), cves: apoc.coll.toSet(cves)}
    '''
    session = get_graph_db_session(package_manager)
    result = await session.run(query, requirement_file_id=requirement_file_id)
    record = await result.single()
    return record[0] if record else None


async def read_data_for_smt_transform(requirement_file_id: str, package_manager: str, max_level: int) -> dict[str, Any]:
    query = '''
    match (rf: RequirementFile) where elementid(rf) = $requirement_file_id
    call apoc.path.subgraphAll(rf, {relationshipFilter: '>', maxLevel: $max_level}) yield relationships
    unwind relationships as relationship
    with case type(relationship)
    when 'Requires' then {
        parent_type: labels(startnode(relationship))[0],
        parent_id: elementid(startnode(relationship)),
        parent_name: startnode(relationship).name,
        parent_count: startnode(relationship).count,
        dependency: endnode(relationship).name,
        constraints: relationship.constraints
    }
    end as requires,
    case type(relationship)
    when 'Have' then {
        dependency: startnode(relationship).name,
        id: elementid(endnode(relationship)),
        release: endnode(relationship).name,
        count: endnode(relationship).count,
        mean: endnode(relationship).mean,
        weighted_mean: endnode(relationship).weighted_mean
    }
    end as have
    return {requires: collect(requires), have: collect(have)}
    '''
    session = get_graph_db_session(package_manager)
    result = await session.run(query, requirement_file_id=requirement_file_id, max_level=max_level*2)
    record = await result.single()
    return record[0] if record else None


async def update_repository_is_completed(repository_id: str, package_manager: str) -> None:
    query = '''
    match (r: Repository) where elementid(r) = $repository_id
    set r.is_complete = true
    '''
    session = get_graph_db_session(package_manager)
    await session.run(query, repository_id=repository_id)