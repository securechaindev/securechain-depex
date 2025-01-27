from datetime import datetime, timedelta
from typing import Any

from app.apis import get_all_versions
from app.controllers.cve_controller import attribute_cves
from app.services import (
    count_number_of_versions_by_package,
    create_package_and_versions,
    create_requirement_file,
    create_versions,
    read_cpe_product_by_package_name,
    read_package_by_name,
    read_versions_names_by_package,
    relate_packages,
    update_package_moment,
)


async def npm_create_requirement_file(name: str, file: Any, repository_id: str) -> None:
    new_req_file_id = await create_requirement_file(
        {"name": name, "manager": "npm", "moment": datetime.now()}, repository_id
    )
    await npm_generate_packages(file["dependencies"], new_req_file_id)


async def npm_generate_packages(
    dependencies: dict[str, str], parent_id: str, parent_version_name: str | None = None
) -> None:
    packages: list[dict[str, str]] = []
    for name, constraints in dependencies.items():
        name = name.lower()
        package = await read_package_by_name("npm", "none", name)
        if package:
            package["parent_id"] = parent_id
            package["parent_version_name"] = parent_version_name
            package["constraints"] = constraints
            if package["moment"] < datetime.now() - timedelta(days=10):
                await npm_search_new_versions(package)
            packages.append(package)
        else:
            await npm_create_package(
                name, constraints, parent_id, parent_version_name
            )
    await relate_packages(packages)


async def npm_create_package(
    package_name: str,
    constraints: str | None = None,
    parent_id: str | None = None,
    parent_version_name: str | None = None,
) -> None:
    all_versions, all_require_packages = await get_all_versions(
        "npm", package_name=package_name
    )
    if all_versions:
        cpe_product = await read_cpe_product_by_package_name(package_name)
        versions = [
            await attribute_cves(version, cpe_product, "npm")
            for version in all_versions
        ]
        new_versions = await create_package_and_versions(
            {"manager": "npm", "group_id": "none", "name": package_name, "moment": datetime.now()},
            versions,
            constraints,
            parent_id,
            parent_version_name,
        )
        for require_packages, new_version in zip(all_require_packages, new_versions):
            await npm_generate_packages(
                require_packages, new_version["id"], package_name
            )


async def npm_search_new_versions(package: dict[str, Any]) -> None:
    all_versions, all_require_packages = await get_all_versions("npm", package_name=package["name"])
    counter = await count_number_of_versions_by_package("npm", "none", package["name"])
    if counter < len(all_versions):
        no_existing_versions: list[dict[str, Any]] = []
        all_require_packages = []
        cpe_product = await read_cpe_product_by_package_name(package["name"])
        actual_versions = await read_versions_names_by_package("npm", "none", package["name"])
        for version, require_packages in zip(all_versions, all_require_packages):
            if version["name"] not in actual_versions:
                version["count"] = counter
                new_version = await attribute_cves(
                    version, cpe_product, "npm"
                )
                no_existing_versions.append(new_version)
                all_require_packages.append(require_packages)
                counter += 1
        new_versions = await create_versions(
            package,
            no_existing_versions,
        )
        for new_version, require_packages in zip(new_versions, all_require_packages):
            await npm_generate_packages(require_packages, new_version["id"], package["name"])
    await update_package_moment("npm", "none", package["name"])
