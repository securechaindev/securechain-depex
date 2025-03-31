from datetime import datetime, timedelta
from typing import Any

from app.apis import get_nuget_versions
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


async def nuget_create_requirement_file(name: str, file: Any, repository_id: str) -> None:
    new_req_file_id = await create_requirement_file(
        {"name": name, "manager": "nuget", "moment": datetime.now()}, repository_id
    )
    await nuget_generate_packages(file["dependencies"], new_req_file_id)


async def nuget_generate_packages(
    dependencies: dict[str, str],
    parent_id: str,
    parent_version_name: str | None = None
) -> None:
    known_packages = []
    for name, constraints in dependencies.items():
        name = name.lower()
        package = await read_package_by_name("NuGetPackage", name)
        if package:
            package["parent_id"] = parent_id
            package["parent_version_name"] = parent_version_name
            package["constraints"] = constraints
            if package["moment"] < datetime.now() - timedelta(days=10):
                await nuget_search_new_versions(package)
            known_packages.append(package)
        else:
            await nuget_create_package(
                name, constraints, parent_id, parent_version_name
            )
    await relate_packages("NuGetPackage", known_packages)


async def nuget_create_package(
    name: str,
    constraints: str | None = None,
    parent_id: str | None = None,
    parent_version_name: str | None = None,
) -> None:
    all_versions, all_require_packages = await get_nuget_versions(name)
    if all_versions:
        versions = [
            await attribute_vulnerabilities(name, version)
            for version in all_versions
        ]
        new_versions = await create_package_and_versions(
            {"name": name, "vendor": "n/a", "moment": datetime.now()},
            versions,
            "NuGetPackage",
            constraints,
            parent_id,
            parent_version_name,
        )
        for require_packages, new_version in zip(all_require_packages, new_versions):
            await nuget_generate_packages(require_packages, new_version["id"], name)


async def nuget_search_new_versions(package: dict[str, Any]) -> None:
    all_versions, all_require_packages = await get_nuget_versions(package["name"])
    counter = await count_number_of_versions_by_package("NuGetPackage", package["name"])
    if counter < len(all_versions):
        no_existing_versions: list[dict[str, Any]] = []
        filtered_require_packages = []
        actual_versions = await read_versions_names_by_package("NuGetPackage", package["name"])
        for version, require_packages in zip(all_versions, all_require_packages):
            if version["name"] not in actual_versions:
                version["count"] = counter
                no_existing_versions.append(version)
                filtered_require_packages.append(require_packages)
                counter += 1
        no_existing_attributed_versions = [
            await attribute_vulnerabilities(package["name"], version)
            for version in no_existing_versions
        ]
        new_versions = await create_versions(package, "NuGetPackage", no_existing_attributed_versions)
        for new_version, require_packages in zip(new_versions, all_require_packages):
            await nuget_generate_packages(require_packages, new_version["id"], package["name"])
    await update_package_moment("NuGetPackage", package["name"])
