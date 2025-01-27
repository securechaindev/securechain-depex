from .dbs.databases import get_graph_db_driver


async def read_cve_ids_by_version_and_package(version: str, package_name: str) -> list[str]:
    query = """
    match (p: Package) where p.name = $package_name
    match (p)-[r:Have]->(v: Version) where v.name = $version
    return v.cves
    """
    async with get_graph_db_driver().session() as session:
        result = await session.run(query, version=version, package_name=package_name)
        record = await result.single()
    return record[0] if record else []


async def read_versions_names_by_package(manager: str, group_id: str, name: str) -> list[str]:
    query = """
    match (p: Package) where p.manager = $manager and p.group_id = $group_id and p.name = $name
    match (p)-[r:Have]->(v: Version)
    return collect(v.name)
    """
    async with get_graph_db_driver().session() as session:
        result = await session.run(query, manager=manager, group_id=group_id, name=name)
        record = await result.single()
    return record[0] if record else None


async def read_releases_by_counts(configs: list[dict[str, int]]) -> list[dict[str, str | float | int]]:
    sanitized_configs: list[dict[str, str | float | int]] = []
    query = """
    MATCH (v:Version)<-[:Have]-(parent:Package)
    WHERE v.count = $count and parent.name = $package
    RETURN v.name
    """
    for config in configs:
        sanitized_config: dict[str, str | float | int] = {}
        for var, value in config.items():
            async with get_graph_db_driver().session() as session:
                result = await session.run(query, package=var, count=value)
                record = await result.single()
            if record:
                sanitized_config.update({var: record[0]})
            else:
                sanitized_config.update({var: value})
        sanitized_configs.append(sanitized_config)
    return sanitized_configs


async def read_counts_by_releases(config: dict[str, str]) -> dict[str, int]:
    sanitized_config: dict[str, int] = {}
    query = """
    MATCH (v:Version)<-[:Have]-(parent:Package)
    WHERE v.name = $release and parent.name = $package
    RETURN v.count
    """
    for package, release in config.items():
        async with get_graph_db_driver().session() as session:
            result = await session.run(query, package=package, release=release)
            record = await result.single()
        if record:
            sanitized_config.update({package: record[0]})
    return sanitized_config


async def count_number_of_versions_by_package(manager: str, group_id: str, name: str) -> int:
    query = """
    match (p: Package) where p.manager = $manager and p.group_id = $group_id and p.name = $name
    match (p)-[r:Have]->(v: Version)
    return count(v)
    """
    async with get_graph_db_driver().session() as session:
        result = await session.run(query, manager=manager, group_id=group_id, name=name)
        record = await result.single()
    return record[0] if record else None
