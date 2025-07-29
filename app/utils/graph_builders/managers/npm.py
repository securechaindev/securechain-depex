from datetime import datetime, timedelta
from typing import Any

from app.apis import get_npm_versions
from app.services import (
    count_number_of_versions_by_package,
    create_package_and_versions,
    create_requirement_file,
    create_versions,
    read_package_by_name,
    read_versions_names_by_package,
    relate_packages,
    update_package_moment,
    update_versions_serial_number,
)

from .vulnerabilities import attribute_vulnerabilities


async def npm_create_requirement_file(requirement_file_name: str, file: Any, repository_id: str) -> None:
    new_req_file_id = await create_requirement_file(
        {"name": requirement_file_name, "manager": file["manager"], "moment": datetime.now()}, repository_id
    )
    await npm_generate_packages(file["requirement"], new_req_file_id)


async def npm_generate_packages(
    requirement: dict[str, str],
    parent_id: str,
    parent_version_name: str | None = None
) -> None:
    known_packages = []
    for package_name, constraints in requirement.items():
        package_name = package_name.lower()
        package = await read_package_by_name("NPMPackage", package_name)
        if package:
            package["parent_id"] = parent_id
            package["parent_version_name"] = parent_version_name
            package["constraints"] = constraints
            if package["moment"] < datetime.now() - timedelta(days=10):
                await npm_search_new_versions(package)
            known_packages.append(package)
        else:
            await npm_create_package(
                package_name, constraints, parent_id, parent_version_name
            )
    await relate_packages("NPMPackage", known_packages)


async def npm_create_package(
    package_name: str,
    constraints: str | None = None,
    parent_id: str | None = None,
    parent_version_name: str | None = None
) -> None:
    versions, requirements = await get_npm_versions(package_name)
    if versions:
        attributed_versions = [
            await attribute_vulnerabilities(package_name, version)
            for version in versions
        ]
        vendor = package_name.split("/")[0] if "@" in package_name else "n/a"
        created_versions = await create_package_and_versions(
            "NPMPackage",
            {"name": package_name, "vendor": vendor, "moment": datetime.now()},
            attributed_versions,
            constraints,
            parent_id,
            parent_version_name,
        )
        for requirement, created_version in zip(requirements, created_versions):
            await npm_generate_packages(requirement, created_version["id"], package_name)


async def npm_search_new_versions(package: dict[str, Any]) -> None:
    versions, requirements = await get_npm_versions(package["name"])
    count = await count_number_of_versions_by_package("NPMPackage", package["name"])
    if count < len(versions):
        new_attributed_versions: list[dict[str, Any]] = []
        new_requirements = []
        actual_versions = await read_versions_names_by_package("NPMPackage", package["name"])
        for index, (version, requirement) in enumerate(zip(versions, requirements)):
            if version["name"] not in actual_versions:
                new_attributed_versions.append(
                    await attribute_vulnerabilities(package["name"], version)
                )
                del versions[index]
                new_requirements.append(requirement)
        created_versions = await create_versions(
            "NPMPackage",
            package["name"],
            new_attributed_versions
        )
        await update_versions_serial_number("NPMPackage", package["name"], versions)
        for version, requirement in zip(created_versions, new_requirements):
            await npm_generate_packages(requirement, version["id"], package["name"])
    await update_package_moment("NPMPackage", package["name"])
