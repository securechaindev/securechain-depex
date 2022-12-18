from app.services.version_service import read_version_by_release_and_package


async def config_sanitizer(config: dict[str, str]) -> dict[str, int]:
    sanitized_config: dict[str, int] = {}
    for package, release in config.items():
        version = await read_version_by_release_and_package(release, package)
        if version:
            sanitized_config[version['package']] = version['count']
    return sanitized_config