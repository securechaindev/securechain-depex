from datetime import datetime
from typing import Any

from neo4j import unit_of_work
from neo4j.exceptions import Neo4jError

from app.exceptions import MemoryOutException

from .dbs import get_graph_db_driver


@unit_of_work(timeout=3)
async def read_graph_package(tx, query, package_name, max_depth):
    result = await tx.run(
        query,
        package_name=package_name,
        max_depth=max_depth
    )
    return await result.single()


async def create_package_and_versions(
    node_type: str,
    package: dict[str, Any],
    versions: list[dict[str, Any]],
    constraints: str | None = None,
    parent_id: str | None = None,
    parent_version_name: str | None = None,
) -> list[dict[str, str]]:
    query_part1 = ""
    query_part3 = ""
    if parent_id:
        query_part1 = (
            """
            MATCH (parent:RequirementFile|Version)
            WHERE elementid(parent) = $parent_id
            """
        )
        query_part3 = (
            f"CREATE (parent)-[rel_p:REQUIRE{{constraints:$constraints{", parent_version_name:$parent_version_name" if parent_version_name else ""}}}]->(p)"
        )
    query = f"""
    {query_part1}
    MERGE(p:{node_type}{{{"group_id:$group_id, artifact_id:$artifact_id," if node_type == "MavenPackage" else ""}name:$name}})
    ON CREATE SET p.vendor = $vendor, p.moment = $moment, p.repository_url = $repository_url
    ON MATCH SET p.moment = $moment
    {query_part3}
    WITH p AS package
    UNWIND $versions AS version
    CREATE(v:Version{{
        name: version.name,
        serial_number: version.serial_number,
        mean: version.mean,
        weighted_mean: version.weighted_mean,
        vulnerabilities: version.vulnerabilities,
        release_date: version.release_date
    }})
    CREATE (package)-[rel_v:HAVE]->(v)
    RETURN collect({{name: v.name, id: elementid(v)}})
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
    node_type: str,
    package_name: str,
    versions: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    query = f"""
    MATCH(p:{node_type}{{name:$package_name}})
    WITH p AS package
    UNWIND $versions AS version
    CREATE(v:Version{{
        name: version.name,
        serial_number: version.serial_number,
        mean: version.mean,
        weighted_mean: version.weighted_mean,
        vulnerabilities: version.vulnerabilities,
        release_date: version.release_date
    }})
    CREATE (package)-[rel_v:HAVE]->(v)
    RETURN collect({{name: v.name, id: elementid(v)}})
    """
    async with get_graph_db_driver().session() as session:
        result = await session.run(
            query,
            package_name=package_name,
            versions=versions,
        )
        record = await result.single()
    return record[0] if record else []


async def read_package_by_name(node_type: str, package_name: str) -> dict[str, Any]:
    query = f"""
    MATCH(p:{node_type}{{name:$package_name}})
    RETURN p{{id: elementid(p), .*}}
    """
    async with get_graph_db_driver().session() as session:
        result = await session.run(
            query,
            package_name=package_name
        )
        record = await result.single()
    return record[0] if record else None


async def read_package_status_by_name(node_type: str, package_name: str) -> dict[str, Any]:
    query = f"""
    MATCH(p:{node_type}{{name:$package_name}})-[:HAVE]->(v:Version)
    WITH p, collect(v{{.*}}) AS versions
    RETURN p{{.*, versions: versions}}
    """
    async with get_graph_db_driver().session() as session:
        result = await session.run(
            query,
            package_name=package_name
        )
        record = await result.single()
    return record[0] if record else None


async def read_version_status_by_package_and_name(node_type: str, package_name: str, version_name: str) -> dict[str, Any]:
    query = f"""
    MATCH(p:{node_type}{{name:$package_name}})-[:HAVE]->(v:Version{{name:$version_name}})
    RETURN v{{id: elementid(v), .*}}
    """
    async with get_graph_db_driver().session() as session:
        result = await session.run(
            query,
            package_name=package_name,
            version_name=version_name
        )
        record = await result.single()
    return record[0] if record else None


async def read_packages_by_requirement_file(requirement_file_id: str) -> dict[str, str]:
    query = """
    MATCH (rf:RequirementFile) WHERE elementid(rf) = $requirement_file_id
    MATCH (rf)-[requirement_rel]->(package)
    RETURN apoc.map.fromPairs(collect([package.name, requirement_rel.constraints]))
    """
    async with get_graph_db_driver().session() as session:
        result = await session.run(query, requirement_file_id=requirement_file_id)
        record = await result.single()
    return record[0] if record else None


async def read_graph_for_package_ssc_info_operation(
    node_type: str,
    package_name: str,
    max_depth: int
) -> dict[str, Any]:
    query = f"""
    MATCH (p:{node_type}{{name:$package_name}})
    CALL apoc.path.expandConfig(
        p,
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
        length(path) / 2 AS depth,
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
        collect(CASE WHEN depth = 1 THEN enriched_pkg END) AS direct_deps,
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
                read_graph_package,
                query,
                package_name,
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


async def relate_packages(node_type: str, packages: list[dict[str, Any]]) -> None:
    query = f"""
    UNWIND $packages AS package
    MATCH (parent:RequirementFile|Version)
    WHERE elementid(parent) = package.parent_id
    MATCH (p: {node_type})
    WHERE elementid(p) = package.id
    CREATE (parent)-[:REQUIRE{{constraints: package.constraints, parent_version_name: package.parent_version_name}}]->(p)
    """
    async with get_graph_db_driver().session() as session:
        await session.run(query, packages=packages)


async def update_package_moment(node_type: str, package_name: str) -> None:
    query = f"""
    MATCH(p:{node_type}{{name:$package_name}})
    SET p.moment = $moment
    """
    async with get_graph_db_driver().session() as session:
        await session.run(query, package_name=package_name, moment=datetime.now())


async def exists_package(node_type: str, package_name: str) -> bool:
    query = f"""
    MATCH(p:{node_type}{{name:$package_name}})
    RETURN count(p) > 0
    """
    async with get_graph_db_driver().session() as session:
        result = await session.run(query, package_name=package_name)
        record = await result.single()
    return record[0] if record else False


async def exists_version(node_type: str, package_name: str, version_name: str) -> bool:
    query = f"""
    MATCH(p:{node_type}{{name:$package_name}})-[:HAVE]->(v:Version{{name:$version_name}})
    RETURN count(v) > 0
    """
    async with get_graph_db_driver().session() as session:
        result = await session.run(query, package_name=package_name, version_name=version_name)
        record = await result.single()
    return record[0] if record else False
