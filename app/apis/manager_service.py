from typing import Any

from .managers.pypi_service import get_all_pypi_versions, requires_pypi_packages

from .managers.npm_service import get_all_npm_versions


async def get_all_versions(package_name: str, manager: str) -> list[dict[str, Any]]:
    match manager:
        case 'PIP':
            return await get_all_pypi_versions(package_name)
        case 'NPM':
            return await get_all_npm_versions(package_name)
        case _:
            return await get_all_pypi_versions(package_name)


async def requires_packages(package_name: str, version_dist: str, manager: str) -> list[str] | str:
    match manager:
        case 'PIP':
            return await requires_pypi_packages(package_name, version_dist)
        case _:
            return await requires_pypi_packages(package_name, version_dist)