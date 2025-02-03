from typing import Any

from .managers import (
    get_cargo_requires,
    get_cargo_versions,
    get_maven_requires,
    get_maven_versions,
    get_npm_versions,
    get_nuget_versions,
    get_pypi_requires,
    get_pypi_versions,
)


async def get_versions(
    manager: str,
    name: str | None = None,
    artifact_id: str | None = None,
    group_id: str | None = None,
) -> list[dict[str, Any]]:
    match manager:
        case "cargo":
            return await get_cargo_versions(name)
        case "nuget":
            return await get_nuget_versions(name)
        case "pypi":
            return await get_pypi_versions(name)
        case "npm":
            return await get_npm_versions(name)
        case "maven":
            return await get_maven_versions(group_id, artifact_id)


async def get_requires(
    version: str,
    manager: str,
    name: str | None = None,
    artifact_id: str | None = None,
    group_id: str | None = None,
) -> dict[str, list[str] | str]:
    match manager:
        case "cargo":
            return await get_cargo_requires(name, version)
        case "pypi":
            return await get_pypi_requires(name, version)
        case "maven":
            return await get_maven_requires(
                group_id, artifact_id, version
            )
