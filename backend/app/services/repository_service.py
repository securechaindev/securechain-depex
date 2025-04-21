from datetime import datetime
from typing import Any

from .dbs.databases import get_graph_db_driver


async def create_repository(repository: dict[str, Any]) -> str:
    query = """
    MATCH(u:User) WHERE u._id = $user_id
    MERGE(r: Repository{
        owner: $owner,
        name: $name,
        moment: $moment,
        add_extras: $add_extras,
        is_complete: $is_complete
    })
    CREATE (u)-[rel:OWN]->(r)
    RETURN elementid(r) AS id
    """
    async with get_graph_db_driver().session() as session:
        result = await session.run(query, repository)
        record = await result.single()
    return record[0] if record else None


async def create_user_repository_rel(repository_id: str, user_id: str) -> None:
    query = """
    MATCH(u:User) WHERE u._id = $user_id
    MATCH(r:Repository) WHERE elementid(r) = $repository_id
    MERGE (u)-[rel:OWN]->(r)
    RETURN elementid(r) AS id
    """
    async with get_graph_db_driver().session() as session:
        result = await session.run(query, repository_id, user_id)
        record = await result.single()
    return record[0]


async def read_repositories_update(owner: str, name: str) -> dict[str, datetime | bool]:
    query = """
    MATCH(r: Repository{owner: $owner, name: $name})
    RETURN {moment: r.moment, is_complete: r.is_complete, id: elementid(r)}
    """
    async with get_graph_db_driver().session() as session:
        result = await session.run(query, owner=owner, name=name)
        record = await result.single()
    return record[0] if record else {"moment": None, "is_complete": True, "id": None}


async def read_repositories(owner: str, name: str) -> str:
    query = """
    MATCH(r: Repository{owner: $owner, name: $name})
    RETURN elementid(r)
    """
    async with get_graph_db_driver().session() as session:
        result = await session.run(query, owner=owner, name=name)
        record = await result.single()
    return record[0] if record else None


async def read_repository_by_id(repository_id: str) -> dict[str, str]:
    query = """
    MATCH(r: Repository) WHERE elementid(r)=$repository_id
    RETURN {name: r.name, owner: r.owner}
    """
    async with get_graph_db_driver().session() as session:
        result = await session.run(query, repository_id=repository_id)
        record = await result.single()
    return record[0] if record else None


async def read_graph_for_info_operation(
    file_info_request: dict[str, Any]
) -> dict[str, Any]:
    query = """
    MATCH(rf: RequirementFile) WHERE elementid(rf) = $requirement_file_id
    CALL apoc.path.subgraphAll(rf, {relationshipFilter: '>', maxLevel: $max_level}) YIELD nodes, relationships
    WITH nodes, relationships
    UNWIND nodes AS node
    WITH CASE WHEN labels(node)[0] ENDS WITH 'Package' THEN node END AS deps,
    CASE WHEN labels(node)[0] = 'Version' THEN node.vulnerabilities END AS vulnerabilities, relationships
    WITH collect(deps) AS deps, apoc.coll.flatten(collect(vulnerabilities)) AS vulnerabilities, relationships
    UNWIND relationships AS relationship
    WITH CASE WHEN type(relationship) = 'Requires' THEN relationship END AS rels, deps, vulnerabilities
    WITH deps, vulnerabilities, collect(rels) AS rels
    RETURN {dependencies: size(deps), edges: size(rels), vulnerabilities: apoc.coll.toSet(vulnerabilities)}
    """
    async with get_graph_db_driver().session() as session:
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
    MATCH (rf: RequirementFile) WHERE elementid(rf) = $requirement_file_id
    CALL apoc.path.subgraphAll(rf, {relationshipFilter: '>', maxLevel: $max_level}) YIELD relationships
    UNWIND relationships AS relationship
        WITH CASE type(relationship)
            WHEN 'Requires' THEN {
                parent_count: startnode(relationship).count,
                dependency: endnode(relationship).name,
                constraints: relationship.constraints,
                parent_version_name: relationship.parent_version_name,
                type: CASE WHEN relationship.parent_version_name is null THEN "direct" ELSE "indirect" END
            } END AS requires,
        CASE type(relationship)
            WHEN 'Have' THEN {
                    dependency: startnode(relationship).name,
                    release: endnode(relationship).name,
                    count: endnode(relationship).count,
                    mean: endnode(relationship).mean,
                    weighted_mean: endnode(relationship).weighted_mean

            } END AS have, rf
    RETURN {
        name: collect(rf.name)[0],
        moment: collect(rf.moment)[0],
        requires: apoc.map.groupByMulti(apoc.coll.sortMaps(collect(requires), "parent_count"), "type"),
        have: apoc.map.groupByMulti(apoc.coll.sortMaps(collect(have), "count"), "dependency")
    }
    """
    async with get_graph_db_driver().session() as session:
        result = await session.run(
            query,
            operation_request,
        )
        record = await result.single()
    return record[0] if record else None


async def read_repositories_by_user_id(user_id: str) -> dict[str, Any]:
    query = """
    MATCH (u:User)-[]->(r:Repository)-[rel:USE]->(rf:RequirementFile)
    WHERE u._id = $user_id
    WITH r, collect({name: rf.name, manager: rf.manager, requirement_file_id: elementid(rf)}) as requirement_files
    RETURN collect({
        owner: r.owner,
        name: r.name,
        is_complete: r.is_complete,
        requirement_files: requirement_files
    })
    """
    repositories = []
    async with get_graph_db_driver().session() as session:
        result = await session.run(query, user_id=user_id)
        record = await result.single()
        repositories.extend(record[0] if record else [])
    return repositories


async def update_repository_is_complete(repository_id: str, is_complete: bool) -> None:
    query = """
    MATCH (r:Repository) WHERE elementid(r) = $repository_id
    SET r.is_complete = $is_complete
    """
    async with get_graph_db_driver().session() as session:
        await session.run(query, repository_id=repository_id, is_complete=is_complete)


async def update_repository_moment(repository_id: str) -> None:
    query = """
    MATCH (r:Repository) WHERE elementid(r) = $repository_id
    SET r.moment = $moment
    """
    async with get_graph_db_driver().session() as session:
        await session.run(query, repository_id=repository_id, moment=datetime.now())


async def update_repository_users(repository_id: str, user_id: str) -> None:
    query = """
    MATCH (r:Repository)
    WHERE elementid(r) = $repository_id AND NOT $user_id IN r.users
    SET r.users = r.users + [$user_id]
    """
    async with get_graph_db_driver().session() as session:
        await session.run(query, repository_id=repository_id, user_id=user_id)
