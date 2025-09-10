from datetime import datetime
from typing import Any

from neo4j import unit_of_work
from neo4j.exceptions import Neo4jError

from app.exceptions import MemoryOutException

from .dbs import get_graph_db_driver


@unit_of_work(timeout=3)
async def read_graph(tx, query, requirement_file_id, max_depth):
    result = await tx.run(
        query,
        requirement_file_id=requirement_file_id,
        max_depth=max_depth
    )
    return await result.single()


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
        result = await session.run(query, repository_id=repository_id, user_id=user_id)
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
    node_type: str,
    requirement_file_id: str,
    max_depth: int
) -> dict[str, Any]:
    query = f"""
    MATCH (rf:RequirementFile)
    WHERE elementid(rf) = $requirement_file_id
    CALL apoc.path.expandConfig(
        rf,
        {{
            relationshipFilter: 'REQUIRE>|HAVE>',
            labelFilter: 'Version|{node_type}',
            maxLevel: $max_depth,
            bfs: true,
            uniqueness: 'NODE_GLOBAL'
        }}
    ) YIELD path
    WITH
        last(nodes(path)) AS pkg,
        (length(path) - 1) / 2 AS depth,
        last(relationships(path)) AS rel
    WHERE '{node_type}' IN labels(pkg) AND type(rel) = 'REQUIRE'
    OPTIONAL MATCH (pkg:{node_type})-[:HAVE]->(v:Version)
    WITH
        pkg,
        depth,
        collect(DISTINCT {{
            name: v.name,
            mean: v.mean,
            serial_number: v.serial_number,
            weighted_mean: v.weighted_mean,
            vulnerability_count: v.vulnerabilities
        }}) AS versions,
        rel.constraints AS constraints
    WITH {{
        package_name: pkg.name,
        package_vendor: pkg.vendor,
        package_constraints: constraints,
        versions: versions
        }} AS enriched_pkg,
        depth
    WITH
        collect(CASE WHEN depth = 0 THEN enriched_pkg END) AS direct_deps,
        collect(CASE WHEN depth > 1 THEN {{node: enriched_pkg, depth: depth}} END) AS indirect_info
    WITH
        direct_deps,
        indirect_info,
        reduce(
            map = {{}},
            entry IN indirect_info |
            apoc.map.setKey(
            map,
            toString(entry.depth),
            coalesce(map[toString(entry.depth)], []) + entry.node
            )
        ) AS indirect_by_depth
    RETURN {{
        direct_dependencies: direct_deps,
        total_direct_dependencies: size(direct_deps),
        indirect_dependencies_by_depth: apoc.map.removeKey(indirect_by_depth, null),
        total_indirect_dependencies: size(indirect_info)
    }}
    """
    try:
        async with get_graph_db_driver().session() as session:
            record = await session.execute_read(
                read_graph,
                query,
                requirement_file_id,
                max_depth
            )
            return record[0] if record else None
    except Neo4jError as err:
        code = getattr(err, "code", "") or ""
        if (
            code == "Neo.TransientError.General.MemoryPoolOutOfMemoryError"
            or code == "Neo.ClientError.Transaction.TransactionTimedOutClientConfiguration"
            or code == "Neo.ClientError.Transaction.TransactionTimedOut"
        ):
            raise MemoryOutException() from err


async def read_data_for_smt_transform(
    requirement_file_id: str,
    max_depth: int
) -> dict[str, Any]:
    query = """
    MATCH (rf:RequirementFile)
    WHERE elementid(rf) = $requirement_file_id
    CALL apoc.path.subgraphAll(rf, {relationshipFilter: '>', maxLevel: $max_depth})
    YIELD relationships
    WITH rf,
        [rel IN relationships WHERE type(rel) = 'REQUIRE' |
            {
            parent_serial_number: startNode(rel).serial_number,
            package: endNode(rel).name,
            constraints: rel.constraints,
            parent_version_name: rel.parent_version_name,
            type: CASE WHEN rel.parent_version_name IS NULL THEN 'direct' ELSE 'indirect' END
            }
        ] AS require,
        [rel IN relationships WHERE type(rel) = 'HAVE' |
            {
            package: startNode(rel).name,
            name: endNode(rel).name,
            serial_number: endNode(rel).serial_number,
            mean: endNode(rel).mean,
            weighted_mean: endNode(rel).weighted_mean
            }
        ] AS have
    RETURN {
        name: rf.name,
        moment: rf.moment,
        require: apoc.map.groupByMulti(apoc.coll.sortMaps(require, 'parent_serial_number'), 'type'),
        have: apoc.map.groupByMulti(apoc.coll.sortMaps(have, 'serial_number'), 'package')
    }
    """
    try:
        async with get_graph_db_driver().session() as session:
            record = await session.execute_read(
                read_graph,
                query,
                requirement_file_id,
                max_depth
            )
            return record[0] if record else None
    except Neo4jError as err:
        code = getattr(err, "code", "") or ""
        if (
            code == "Neo.TransientError.General.MemoryPoolOutOfMemoryError"
            or code == "Neo.ClientError.Transaction.TransactionTimedOutClientConfiguration"
            or code == "Neo.ClientError.Transaction.TransactionTimedOut"
        ):
            raise MemoryOutException() from err


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
