from typing import Any

from .managers.mvn_service import get_all_mvn_versions, requires_mvn_packages
from .managers.npm_service import get_all_npm_versions
from .managers.pip_service import get_all_pip_versions, requires_pip_packages


async def get_all_versions(
    manager: str,
    package_name: str | None = None,
    package_artifact_id: str | None = None,
    package_group_id: str | None = None,
) -> list[dict[str, Any]]:
    match manager:
        case "PIP":
            return await get_all_pip_versions(package_name)
        case "NPM":
            return await get_all_npm_versions(package_name)
        case "MVN":
            return await get_all_mvn_versions(package_artifact_id, package_group_id)


async def requires_packages(
    version_dist: str,
    manager: str,
    package_name: str | None = None,
    package_artifact_id: str | None = None,
    package_group_id: str | None = None,
) -> dict[str, list[str] | str]:
    match manager:
        case "PIP":
            return await requires_pip_packages(package_name, version_dist)
        case "MVN":
            return await requires_mvn_packages(
                package_artifact_id, package_group_id, version_dist
            )
