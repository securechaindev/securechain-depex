from typing import Any

from .managers.maven_service import get_all_maven_versions, requires_maven_packages
from .managers.npm_service import get_all_npm_versions
from .managers.nuget_service import get_all_nuget_versions
from .managers.pypi_service import get_all_pypi_versions, requires_pypi_packages


async def get_all_versions(
    manager: str,
    package_name: str | None = None,
    package_artifact_id: str | None = None,
    package_group_id: str | None = None,
) -> list[dict[str, Any]]:
    match manager:
        case "nuget":
            return await get_all_nuget_versions(package_name)
        case "pypi":
            return await get_all_pypi_versions(package_name)
        case "npm":
            return await get_all_npm_versions(package_name)
        case "maven":
            return await get_all_maven_versions(package_artifact_id, package_group_id)


async def requires_packages(
    version_dist: str,
    manager: str,
    package_name: str | None = None,
    package_artifact_id: str | None = None,
    package_group_id: str | None = None,
) -> dict[str, list[str] | str]:
    match manager:
        case "pypi":
            return await requires_pypi_packages(package_name, version_dist)
        case "maven":
            return await requires_maven_packages(
                package_artifact_id, package_group_id, version_dist
            )
