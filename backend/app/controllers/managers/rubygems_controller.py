from datetime import datetime, timedelta
from typing import Any

from app.apis import get_rubygems_requires, get_rubygems_versions
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


async def rubygems_create_requirement_file(name: str, file: Any, repository_id: str) -> None:
    new_req_file_id = await create_requirement_file(
        {"name": name, "manager": "rubygems", "moment": datetime.now()}, repository_id
    )
    await rubygems_generate_packages(file["dependencies"], new_req_file_id)


async def rubygems_generate_packages(
    dependencies: dict[str, str],
    parent_id: str,
    parent_version_name: str | None = None
) -> None:
    known_packages = []
    for name, constraints in dependencies.items():
        package = await read_package_by_name("RubyGemsPackage", name)
        if package:
            package["parent_id"] = parent_id
            package["parent_version_name"] = parent_version_name
            package["constraints"] = constraints
            if package["moment"] < datetime.now() - timedelta(days=10):
                await rubygems_search_new_versions(package)
            known_packages.append(package)
        else:
            await rubygems_create_package(name, constraints, parent_id, parent_version_name)
    await relate_packages("RubyGemsPackage", known_packages)


async def rubygems_create_package(
    name: str,
    constraints: str | None = None,
    parent_id: str | None = None,
    parent_version_name: str | None = None,
) -> None:
    all_versions = await get_rubygems_versions(name)
    if all_versions:
        versions = [
            await attribute_vulnerabilities(name, version)
            for version in all_versions
        ]
        new_versions = await create_package_and_versions(
            {"name": name, "vendor": "n/a", "moment": datetime.now()},
            versions,
            "RubyGemsPackage",
            constraints,
            parent_id,
            parent_version_name,
        )
        for new_version in new_versions:
            await rubygems_extract_packages(name, new_version)


async def rubygems_extract_packages(
    parent_package_name: str,
    version: dict[str, Any]
) -> None:
    require_packages = await get_rubygems_requires(
        version["name"], parent_package_name
    )
    await rubygems_generate_packages(require_packages, version["id"], parent_package_name)


async def rubygems_search_new_versions(package: dict[str, Any]) -> None:
    all_versions = await get_rubygems_versions(package["name"])
    counter = await count_number_of_versions_by_package("RubyGemsPackage", package["name"])
    if counter < len(all_versions):
        no_existing_versions: list[dict[str, Any]] = []
        actual_versions = await read_versions_names_by_package("RubyGemsPackage", package["name"])
        for version in all_versions:
            if version["name"] not in actual_versions:
                version["count"] = counter
                no_existing_versions.append(version)
                counter += 1
        no_existing_attributed_versions = [
            await attribute_vulnerabilities(package["name"], version)
            for version in no_existing_versions
        ]
        new_versions = await create_versions(
            package,
            "RubyGemsPackage",
            no_existing_attributed_versions,
        )
        for new_version, in new_versions:
            await rubygems_extract_packages(package["name"], new_version)
    await update_package_moment("RubyGemsPackage", package["name"])
