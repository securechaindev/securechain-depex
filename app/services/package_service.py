from datetime import datetime
from typing import Any

from .dbs import get_graph_db_driver


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
    ON CREATE SET p.vendor = $vendor, p.moment = $moment
    ON MATCH SET p.vendor = $vendor, p.moment = $moment
    {query_part3}
    WITH p AS package
    UNWIND $versions AS version
    CREATE(v:Version{{
        name: version.name,
        serial_number: version.serial_number,
        mean: version.mean,
        weighted_mean: version.weighted_mean,
        vulnerabilities: version.vulnerabilities
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
        vulnerabilities: version.vulnerabilities
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
