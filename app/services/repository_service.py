from typing import Any

from fastapi import HTTPException

from .dbs.databases import session


async def create_repository(repository: dict[str, Any]) -> str:
    query = """
    create(r: Repository{
        owner: $owner,
        name: $name,
        add_extras: $add_extras,
        is_complete: $is_complete
    })
    return elementid(r) as id
    """
    result = await session.run(query, repository)
    record = await result.single()
    return record[0] if record else None


async def read_graph_by_repository_id(
    requirement_file_id: str
) -> dict[str, Any]:
    query = """
    match (rf: RequirementFile) where elementid(rf) = $requirement_file_id
    call apoc.path.subgraphAll(rf, {relationshipFilter: '>'}) yield nodes, relationships
    return nodes, relationships
    """
    result = await session.run(query, requirement_file_id=requirement_file_id)
    record = await result.single()
    if record:
        return record[0]
    raise HTTPException(status_code=404, detail=[f'Graph with id {requirement_file_id} not found'])


async def read_data_for_smt_transform(requirement_file_id: str) -> dict[str, Any]:
    query = """
    match (rf: RequirementFile) where elementid(rf) = $requirement_file_id
    call apoc.path.subgraphAll(rf, {relationshipFilter: '>'}) yield relationships
    unwind relationships as relationship
    with case type(relationship)
    when 'REQUIRES'  then {
        parent_type: labels(startnode(relationship))[0],
        parent_id: elementid(startnode(relationship)),
        parent_name: startnode(relationship).name,
        parent_count: startnode(relationship).count,
        dependency: endnode(relationship).name,
        constraints: relationship.constraints
    }
    end as requires,
    case type(relationship)
    when 'HAVE' then {
        dependency: startnode(relationship).name,
        id: elementid(endnode(relationship)),
        release: endnode(relationship).name,
        count: endnode(relationship).count,
        mean: endnode(relationship).mean,
        weighted_mean: endnode(relationship).weighted_mean
    }
    end as have
    return {requires: collect(requires), have: collect(have)}
    """
    result = await session.run(query, requirement_file_id=requirement_file_id)
    record = await result.single()
    return record[0] if record else None


async def update_repository_is_completed(repository_id: str) -> None:
    query = '''
    match (r: Repository) where elementid(r) = $repository_id
    set r.is_complete = true
    '''
    await session.run(query, repository_id=repository_id)