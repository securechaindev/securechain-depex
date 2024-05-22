from .dbs.databases import get_graph_db_session


async def read_cve_ids_by_version_and_package(
    version: str, package_name: str, package_manager: str
) -> list[str]:
    query = """
    match (p: Package) where p.name = $package_name
    match (p)-[r:Have]->(v: Version) where v.name = $version
    return v.cves
    """
    session = get_graph_db_session(package_manager)
    result = await session.run(query, version=version, package_name=package_name)
    record = await result.single()
    return record[0] if record else []


async def read_versions_names_by_package(
    package_name: str, package_manager: str
) -> list[str]:
    query = """
    match (p: Package) where p.name = $package_name
    match (p)-[r:Have]->(v: Version)
    return collect(v.name)
    """
    session = get_graph_db_session(package_manager)
    result = await session.run(query, package_name=package_name)
    record = await result.single()
    return record[0] if record else None


async def read_releases_by_counts(
    configs: list[dict[str, int]], package_manager: str
) -> list[dict[str, str | float | int]]:
    sanitized_configs: list[dict[str, str | float | int]] = []
    query = """
    MATCH (v:Version)<-[:Have]-(parent:Package)
    WHERE v.count = $count and parent.name = $package
    RETURN v.name
    """
    session = get_graph_db_session(package_manager)
    for config in configs:
        sanitized_config: dict[str, str | float | int] = {}
        for var, value in config.items():
            result = await session.run(query, package=var, count=value)
            record = await result.single()
            if record:
                sanitized_config.update({var: record[0]})
            else:
                sanitized_config.update({var: value})
        sanitized_configs.append(sanitized_config)
    return sanitized_configs


async def read_counts_by_releases(
    config: dict[str, str], package_manager: str
) -> dict[str, int]:
    sanitized_config: dict[str, int] = {}
    query = """
    MATCH (v:Version)<-[:Have]-(parent:Package)
    WHERE v.name = $release and parent.name = $package
    RETURN v.count
    """
    session = get_graph_db_session(package_manager)
    for package, release in config.items():
        result = await session.run(query, package=package, release=release)
        record = await result.single()
        if record:
            sanitized_config.update({package: record[0]})
    return sanitized_config


async def count_number_of_versions_by_package(
    package_name: str, package_manager: str
) -> int:
    query = """
    match (p: Package) where p.name = $package_name
    match (p)-[r:Have]->(v: Version)
    return count(v)
    """
    session = get_graph_db_session(package_manager)
    result = await session.run(query, package_name=package_name)
    record = await result.single()
    return record[0] if record else None
