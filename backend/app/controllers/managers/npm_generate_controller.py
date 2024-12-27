from datetime import datetime, timedelta
from typing import Any

from app.apis import get_all_versions
from app.controllers.cve_controller import attribute_cves
from app.services import (
    count_number_of_versions_by_package,
    create_package_and_versions,
    create_versions,
    create_requirement_file,
    read_cpe_product_by_package_name,
    read_package_by_name,
    read_versions_names_by_package,
    relate_packages,
    update_package_moment,
)

from app.logger import logger


async def npm_create_requirement_file(name: str, file: Any, repository_id: str) -> None:
    new_req_file_id = await create_requirement_file(
        {"name": name, "manager": "NPM", "moment": datetime.now()}, repository_id, "NPM"
    )
    await npm_generate_packages(file["dependencies"], new_req_file_id)


async def npm_generate_packages(
    dependencies: dict[str, str], parent_id: str, parent_version_name: str | None = None
) -> None:
    packages: list[dict[str, str]] = []
    for package_name, constraints in dependencies.items():
        package_name = package_name.lower()
        package = await read_package_by_name(package_name, "NPM")
        if package:
            package["parent_id"] = parent_id
            package["parent_version_name"] = parent_version_name
            package["constraints"] = constraints
            if package["moment"] < datetime.now() - timedelta(days=10):
                await npm_search_new_versions(package)
            packages.append(package)
        else:
            await npm_create_package(
                package_name, constraints, parent_id, parent_version_name
            )
    await relate_packages(packages, "NPM")


async def npm_create_package(
    package_name: str,
    constraints: str | None = None,
    parent_id: str | None = None,
    parent_version_name: str | None = None,
) -> None:
    all_versions, all_require_packages = await get_all_versions(
        "NPM", package_name=package_name
    )
    if all_versions:
        cpe_product = await read_cpe_product_by_package_name(package_name)
        versions = [
            await attribute_cves(version, cpe_product, "NPM")
            for version in all_versions
        ]
        new_versions = await create_package_and_versions(
            {"name": package_name, "moment": datetime.now()},
            versions,
            "NPM",
            constraints,
            parent_id,
            parent_version_name,
        )
        for require_packages, new_version in zip(all_require_packages, new_versions):
            await npm_generate_packages(
                require_packages, new_version["id"], package_name
            )


async def npm_search_new_versions(package: dict[str, Any]) -> None:
    all_versions, all_require_packages = await get_all_versions("NPM", package_name=package["name"])
    counter = await count_number_of_versions_by_package(package["name"], "NPM")
    if counter < len(all_versions):
        no_existing_versions: list[dict[str, Any]] = []
        all_require_packages = []
        cpe_product = await read_cpe_product_by_package_name(package["name"])
        actual_versions = await read_versions_names_by_package(package["name"], "NPM")
        for version, require_packages in zip(all_versions, all_require_packages):
            if version["name"] not in actual_versions:
                version["count"] = counter
                new_version = await attribute_cves(
                    version, cpe_product, "NPM"
                )
                no_existing_versions.append(new_version)
                all_require_packages.append(require_packages)
                counter += 1
        new_versions = await create_versions(
            package,
            no_existing_versions,
            "NPM",
        )
        for new_version, require_packages in zip(new_versions, all_require_packages):
            await npm_generate_packages(require_packages, new_version["id"], package["name"])
    await update_package_moment(package["name"], "NPM")
