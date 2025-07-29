from datetime import datetime, timedelta
from typing import Any

from app.apis import get_cargo_requirement, get_cargo_versions
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


async def cargo_create_requirement_file(requirement_file_name: str, file: Any, repository_id: str) -> None:
    new_req_file_id = await create_requirement_file(
        {"name": requirement_file_name, "manager": file["manager"], "moment": datetime.now()}, repository_id
    )
    await cargo_generate_packages(file["requirement"], new_req_file_id)


async def cargo_generate_packages(
    requirement: dict[str, str],
    parent_id: str,
    parent_version_name: str | None = None
) -> None:
    known_packages = []
    for package_name, constraints in requirement.items():
        package = await read_package_by_name("CargoPackage", package_name)
        if package:
            package["parent_id"] = parent_id
            package["parent_version_name"] = parent_version_name
            package["constraints"] = constraints
            if package["moment"] < datetime.now() - timedelta(days=10):
                await cargo_search_new_versions(package)
            known_packages.append(package)
        else:
            await cargo_create_package(package_name, constraints, parent_id, parent_version_name)
    await relate_packages("CargoPackage", known_packages)


async def cargo_create_package(
    package_name: str,
    constraints: str | None = None,
    parent_id: str | None = None,
    parent_version_name: str | None = None,
) -> None:
    versions = await get_cargo_versions(package_name)
    if versions:
        attributed_versions = [
            await attribute_vulnerabilities(package_name, version)
            for version in versions
        ]
        created_versions = await create_package_and_versions(
            "CargoPackage",
            {"name": package_name, "vendor": "n/a", "moment": datetime.now()},
            attributed_versions,
            constraints,
            parent_id,
            parent_version_name,
        )
        for created_version in created_versions:
            await cargo_extract_packages(package_name, created_version)


async def cargo_extract_packages(
    parent_package_name: str,
    version: dict[str, Any]
) -> None:
    requirement = await get_cargo_requirement(
        parent_package_name, version["name"]
    )
    await cargo_generate_packages(requirement, version["id"], parent_package_name)


async def cargo_search_new_versions(package: dict[str, Any]) -> None:
    versions = await get_cargo_versions(package["name"])
    count = await count_number_of_versions_by_package("CargoPackage", package["name"])
    if count < len(versions):
        new_attributed_versions: list[dict[str, Any]] = []
        actual_versions = await read_versions_names_by_package("CargoPackage", package["name"])
        for index, version in enumerate(versions):
            if version["name"] not in actual_versions:
                new_attributed_versions.append(
                    await attribute_vulnerabilities(package["name"], version)
                )
                del versions[index]
        created_versions = await create_versions(
            "CargoPackage",
            package["name"],
            new_attributed_versions,
        )
        await update_versions_serial_number("CargoPackage", package["name"], versions)
        for version in created_versions:
            await cargo_extract_packages(package["name"], version)
    await update_package_moment("CargoPackage", package["name"])
