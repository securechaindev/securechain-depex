from datetime import datetime, timedelta
from typing import Any

from app.apis import get_all_versions, requires_packages
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


async def maven_create_requirement_file(name: str, file: Any, repository_id: str) -> None:
    new_req_file_id = await create_requirement_file(
        {"name": name, "manager": "maven", "moment": datetime.now()}, repository_id
    )
    await maven_generate_packages(file["dependencies"], new_req_file_id)


async def maven_generate_packages(
    dependencies: dict[str, str], parent_id: str, parent_version_name: str | None = None
) -> None:
    packages: list[dict[str, str]] = []
    for dependency, constraints in dependencies.items():
        group_id, artifact_id = dependency
        package = await read_package_by_name("maven", group_id, artifact_id)
        if package:
            package["parent_id"] = parent_id
            package["parent_version_name"] = parent_version_name
            package["constraints"] = constraints
            if package["moment"] < datetime.now() - timedelta(days=10):
                await maven_search_new_versions(package)
            packages.append(package)
        else:
            await maven_create_package(
                group_id, artifact_id, constraints, parent_id, parent_version_name
            )
    await relate_packages(packages)


async def maven_create_package(
    group_id: str,
    artifact_id: str,
    constraints: str | None = None,
    parent_id: str | None = None,
    parent_version_name: str | None = None,
) -> None:
    all_versions = await get_all_versions(
        "maven", package_artifact_id=artifact_id, package_group_id=group_id
    )
    if all_versions:
        cpe_product = await read_cpe_product_by_package_name(artifact_id)
        versions = [
            await attribute_cves(version, cpe_product, "maven")
            for version in all_versions
        ]
        new_versions = await create_package_and_versions(
            {"manager": "maven", "group_id": group_id, "name": artifact_id, "moment": datetime.now()},
            versions,
            constraints,
            parent_id,
            parent_version_name,
        )
        for new_version in new_versions:
            await maven_extract_packages(group_id, artifact_id, new_version)


async def maven_extract_packages(
    parent_group_id: str, parent_artifact_id: str, version: dict[str, Any]
) -> None:
    require_packages = await requires_packages(
        version["name"],
        "maven",
        package_group_id=parent_group_id,
        package_artifact_id=parent_artifact_id,
    )
    await maven_generate_packages(require_packages, version["id"], parent_artifact_id)


async def maven_search_new_versions(package: dict[str, Any]) -> None:
    all_versions = await get_all_versions(
        "maven", package_artifact_id=package["name"], package_group_id=package["group_id"]
    )
    counter = await count_number_of_versions_by_package("maven", package["group_id"], package["name"])
    if counter < len(all_versions):
        no_existing_versions: list[dict[str, Any]] = []
        cpe_product = await read_cpe_product_by_package_name(package["name"])
        actual_versions = await read_versions_names_by_package("maven", package["group_id"], package["name"])
        for version in all_versions:
            if version["name"] not in actual_versions:
                version["count"] = counter
                new_version = await attribute_cves(
                    version, cpe_product, "maven"
                )
                no_existing_versions.append(new_version)
                counter += 1
        new_versions = await create_versions(
            package,
            no_existing_versions,
        )
        for new_version in new_versions:
            await maven_extract_packages(package["name"], new_version)
    await update_package_moment("maven", package["group_id"], package["name"])
