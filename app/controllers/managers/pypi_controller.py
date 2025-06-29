from datetime import datetime, timedelta
from typing import Any

from app.apis import get_pypi_requires, get_pypi_versions
from app.controllers.vulnerability_controller import attribute_vulnerabilities
from app.services import (
    count_number_of_versions_by_package,
    create_package_and_versions,
    create_requirement_file,
    create_versions,
    read_package_by_name,
    read_versions_names_by_package,
    relate_packages,
    update_package_moment,
)


async def pypi_create_requirement_file(name: str, file: Any, repository_id: str) -> None:
    new_req_file_id = await create_requirement_file(
        {"name": name, "manager": file["manager"], "moment": datetime.now()}, repository_id
    )
    await pypi_generate_packages(file["dependencies"], new_req_file_id)


async def pypi_generate_packages(
    dependencies: dict[str, str],
    parent_id: str,
    parent_version_name: str | None = None
) -> None:
    known_packages = []
    for name, constraints in dependencies.items():
        package = await read_package_by_name("PyPIPackage", name)
        if package:
            package["parent_id"] = parent_id
            package["parent_version_name"] = parent_version_name
            package["constraints"] = constraints
            if package["moment"] < datetime.now() - timedelta(days=10):
                await pypi_search_new_versions(package)
            known_packages.append(package)
        else:
            await pypi_create_package(name, constraints, parent_id, parent_version_name)
    await relate_packages("PyPIPackage", known_packages)


async def pypi_create_package(
    name: str,
    constraints: str | None = None,
    parent_id: str | None = None,
    parent_version_name: str | None = None,
) -> None:
    all_versions = await get_pypi_versions(name)
    if all_versions:
        versions = [
            await attribute_vulnerabilities(name, version)
            for version in all_versions
        ]
        new_versions = await create_package_and_versions(
            {"name": name, "vendor": "n/a", "moment": datetime.now()},
            versions,
            "PyPIPackage",
            constraints,
            parent_id,
            parent_version_name
        )
        for new_version in new_versions:
            await pypi_extract_packages(name, new_version)


async def pypi_extract_packages(
    parent_package_name: str,
    version: dict[str, Any]
) -> None:
    require_packages = await get_pypi_requires(
        version["name"], parent_package_name
    )
    await pypi_generate_packages(require_packages, version["id"], parent_package_name)


async def pypi_search_new_versions(package: dict[str, Any]) -> None:
    all_versions = await get_pypi_versions(package["name"])
    counter = await count_number_of_versions_by_package("PyPIPackage", package["name"])
    if counter < len(all_versions):
        new_versions: list[dict[str, Any]] = []
        actual_versions = await read_versions_names_by_package("PyPIPackage", package["name"])
        for version in all_versions:
            if version["name"] not in actual_versions:
                version["count"] = counter
                new_version = await attribute_vulnerabilities(package["name"], version)
                new_versions.append(new_version)
                counter += 1
        created_versions = await create_versions(
            package,
            "PyPIPackage",
            new_versions,
        )
        for version in created_versions:
            await pypi_extract_packages(package["name"], version)
    await update_package_moment("PyPIPackage", package["name"])
