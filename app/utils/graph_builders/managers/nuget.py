from datetime import datetime, timedelta
from typing import Any

from app.apis import get_nuget_versions
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
from app.utils.others import version_to_serial_number

from .vulnerabilities import attribute_vulnerabilities


async def nuget_create_requirement_file(requirement_file_name: str, file: Any, repository_id: str) -> None:
    new_req_file_id = await create_requirement_file(
        {"name": requirement_file_name, "manager": file["manager"], "moment": datetime.now()}, repository_id
    )
    await nuget_generate_packages(file["requirement"], new_req_file_id)


async def nuget_generate_packages(
    requirement: dict[str, str],
    parent_id: str,
    parent_version_name: str | None = None
) -> None:
    known_packages = []
    for package_name, constraints in requirement.items():
        package_name = package_name.lower()
        package = await read_package_by_name("NuGetPackage", package_name)
        if package:
            package["parent_id"] = parent_id
            package["parent_version_name"] = parent_version_name
            package["constraints"] = constraints
            if package["moment"] < datetime.now() - timedelta(days=10):
                await nuget_search_new_versions(package)
            known_packages.append(package)
        else:
            await nuget_create_package(
                package_name, constraints, parent_id, parent_version_name
            )
    await relate_packages("NuGetPackage", known_packages)


async def nuget_create_package(
    package_name: str,
    constraints: str | None = None,
    parent_id: str | None = None,
    parent_version_name: str | None = None,
) -> None:
    versions, requirements = await get_nuget_versions(package_name)
    if versions:
        attributed_versions = [
            await attribute_vulnerabilities(package_name, version)
            for version in versions
        ]
        created_versions = await create_package_and_versions(
            "NuGetPackage",
            {"name": package_name, "vendor": "n/a", "moment": datetime.now()},
            attributed_versions,
            constraints,
            parent_id,
            parent_version_name,
        )
        for requirement, created_version in zip(requirements, created_versions):
            await nuget_generate_packages(requirement, created_version["id"], package_name)


async def nuget_search_new_versions(package: dict[str, Any]) -> None:
    versions, requirements = await get_nuget_versions(package["name"])
    count = await count_number_of_versions_by_package("NuGetPackage", package["name"])
    if count < len(versions):
        attributed_versions: list[dict[str, Any]] = []
        new_requirements = []
        actual_versions = await read_versions_names_by_package("NuGetPackage", package["name"])
        for version, requirement in zip(versions, requirements):
            if version["name"] not in actual_versions:
                version["serial_number"] = await version_to_serial_number(version["name"])
                attributed_versions.append(
                    await attribute_vulnerabilities(package["name"], version)
                )
                new_requirements.append(requirement)
        created_versions = await create_versions(
            "NuGetPackage",
            package["name"],
            attributed_versions
        )
        for version, requirement in zip(created_versions, new_requirements):
            await nuget_generate_packages(requirement, version["id"], package["name"])
    await update_package_moment("NuGetPackage", package["name"])
