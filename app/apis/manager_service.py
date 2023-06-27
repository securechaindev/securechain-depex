from typing import Any

from .managers.pip_service import get_all_pip_versions, requires_pip_packages

from .managers.npm_service import get_all_npm_versions

from .managers.mvn_service import get_all_mvn_versions, requires_mvn_packages


async def get_all_versions(package_name: str, manager: str) -> list[dict[str, Any]]:
    match manager:
        case 'PIP':
            return await get_all_pip_versions(package_name)
        case 'NPM':
            return await get_all_npm_versions(package_name)
        case 'MVN':
            return await get_all_mvn_versions(package_name)
        case _:
            return await get_all_pip_versions(package_name)


async def requires_packages(package_name: str, version_dist: str, manager: str) -> dict[str, list[str] | str]:
    match manager:
        case 'PIP':
            return await requires_pip_packages(package_name, version_dist)
        case 'MVN':
            return await requires_mvn_packages(package_name, version_dist)
        case _:
            return await requires_pip_packages(package_name, version_dist)