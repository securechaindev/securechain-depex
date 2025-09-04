from typing import Any

from .dbs import get_graph_db_driver


async def read_versions_names_by_package(node_type: str, package_name: str) -> list[str]:
    query = f"""
    MATCH (p:{node_type}{{name:$package_name}})
    MATCH (p)-[r:HAVE]->(v: Version)
    RETURN collect(v.name)
    """
    async with get_graph_db_driver().session() as session:
        result = await session.run(query, package_name=package_name)
        record = await result.single()
    return record[0] if record else None


async def read_releases_by_serial_numbers(
    node_type: str,
    config: dict[str, int]
) -> list[dict[str, str | float | int]]:
    query = f"""
    MATCH (v:Version)<-[:HAVE]-(parent:{node_type})
    WHERE v.serial_number = $serial_number AND parent.name = $package
    RETURN v.name
    """
    sanitized_config: dict[str, str | float | int] = {}
    for var, value in config.items():
        async with get_graph_db_driver().session() as session:
            result = await session.run(query, package=var, serial_number=value)
            record = await result.single()
        if record:
            sanitized_config.update({var: record[0]})
        else:
            sanitized_config.update({var: value})
    return sanitized_config


async def read_serial_numbers_by_releases(
    node_type: str,
    config: dict[str, str]
) -> dict[str, int]:
    sanitized_config: dict[str, int] = {}
    query = f"""
    MATCH (v:Version)<-[:HAVE]-(parent:{node_type})
    WHERE v.name = $release AND parent.name = $package
    RETURN v.serial_number
    """
    for package, release in config.items():
        async with get_graph_db_driver().session() as session:
            result = await session.run(query, package=package, release=release)
            record = await result.single()
        if record:
            sanitized_config.update({package: record[0]})
    return sanitized_config


async def update_versions_serial_number(
    node_type: str,
    package_name: str,
    versions: list[dict[str, Any]],
) -> None:
    query = f"""
    MATCH (p:{node_type} {{name: $package_name}})-[:HAVE]->(v:Version)
    WITH v, $versions AS input_versions
    UNWIND input_versions AS version
    WITH v, version
    WHERE v.name = version.name
    SET v.serial_number = version.serial_number
    """
    async with get_graph_db_driver().session() as session:
        await session.run(
            query,
            package_name=package_name,
            versions=versions,
        )


async def count_number_of_versions_by_package(node_type: str, package_name: str) -> int:
    query = f"""
    MATCH (p:{node_type}{{name:$package_name}})
    MATCH (p)-[r:HAVE]->(v: Version)
    RETURN count(v)
    """
    async with get_graph_db_driver().session() as session:
        result = await session.run(query, package_name=package_name)
        record = await result.single()
    return record[0] if record else None
