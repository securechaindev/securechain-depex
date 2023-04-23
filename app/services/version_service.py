from typing import Any

from app.utils import mean, weighted_mean

from .dbs.databases import session


async def create_version(version: dict[str, Any], package_name: str) -> dict[str, Any]:
    query = """
    match (p: Package)
    where p.name = $package_name
    create(v: Version{
        name: $name,
        release_date: $release_date,
        count: $count,
        cves: [],
        mean: 0,
        weighted_mean: 0
    })
    create (p)-[rel: HAVE]->(v)
    return v{.*, id: elementid(v)}
    """
    result = await session.run(query, version, package_name=package_name)
    record = await result.single()
    return record[0] if record else None


async def count_number_of_versions_by_package(package_name: str) -> int:
    query = '''
    match (p: Package) where p.name = $package_name
    match (p)-[r: HAVE]->(v: Version)
    return count(v)
    '''
    result = await session.run(query, package_name=package_name)
    record = await result.single()
    return record[0] if record else None


async def get_versions_names_by_package(package_name: str) -> list[str]:
    query = """
    match (p: Package) where p.name = $package_name
    match (p)-[r: HAVE]->(v: Version)
    return collect(v.name)
    """
    result = await session.run(query, package_name=package_name)
    record = await result.single()
    return record[0] if record else None


async def get_releases_by_counts(
    configs: list[dict[str, int]]
) -> list[dict[str, str | float | int]]:
    sanitized_configs: list[dict[str, str | float | int]] = []
    query = """
    MATCH (v:Version)<-[:HAVE]-(parent:Package)
    WHERE v.count = $count and parent.name = $package
    RETURN v.name
    """

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


async def get_counts_by_releases(
    config: dict[str, str]
) -> dict[str, int]:
    sanitized_config: dict[str, int] = {}
    query = """
    MATCH (v:Version)<-[:HAVE]-(parent:Package)
    WHERE v.name = $release and parent.name = $package
    RETURN v.count
    """

    for package, release in config.items():
        result = await session.run(query, package=package, release=release)
        record = await result.single()
        if record:
            sanitized_config.update({package: record[0]})
    return sanitized_config


async def add_impacts_and_cves(impacts: list[float], cves: list[str], version_id: str) -> None:
    query = """
    match (v: Version)
    where elementid(v) = $version_id
    set v.cves = $cves, v.mean = $mean, v.weighted_mean = $weighted_mean
    """
    await session.run(
        query,
        version_id=version_id,
        cves=cves,
        mean=await mean(impacts),
        weighted_mean=await weighted_mean(impacts)
    )