from .dbs.databases import get_graph_db_driver


async def read_versions_names_by_package(node_type: str, package_name: str) -> list[str]:
    query = f"""
    MATCH (p:{node_type}{{name:$package_name}})
    MATCH (p)-[r:Have]->(v: Version)
    RETURN collect(v.name)
    """
    async with get_graph_db_driver().session() as session:
        result = await session.run(query, package_name=package_name)
        record = await result.single()
    return record[0] if record else None


async def read_releases_by_serial_numbers(
    node_type: str,
    configs: list[dict[str, int]]
) -> list[dict[str, str | float | int]]:
    sanitized_configs: list[dict[str, str | float | int]] = []
    query = f"""
    MATCH (v:Version)<-[:Have]-(parent:{node_type})
    WHERE v.serial_number = $serial_number AND parent.name = $package
    RETURN v.name
    """
    for config in configs:
        sanitized_config: dict[str, str | float | int] = {}
        for var, value in config.items():
            async with get_graph_db_driver().session() as session:
                result = await session.run(query, package=var, serial_number=value)
                record = await result.single()
            if record:
                sanitized_config.update({var: record[0]})
            else:
                sanitized_config.update({var: value})
        sanitized_configs.append(sanitized_config)
    return sanitized_configs


async def read_serial_numbers_by_releases(
    node_type: str,
    config: dict[str, str]
) -> dict[str, int]:
    sanitized_config: dict[str, int] = {}
    query = f"""
    MATCH (v:Version)<-[:Have]-(parent:{node_type})
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


async def count_number_of_versions_by_package(node_type: str, package_name: str) -> int:
    query = f"""
    MATCH (p:{node_type}{{name:$package_name}})
    MATCH (p)-[r:Have]->(v: Version)
    RETURN count(v)
    """
    async with get_graph_db_driver().session() as session:
        result = await session.run(query, package_name=package_name)
        record = await result.single()
    return record[0] if record else None
