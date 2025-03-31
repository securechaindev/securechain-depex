from datetime import datetime, timedelta
from typing import Any

from app.apis import get_maven_requires, get_maven_versions
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


async def maven_create_requirement_file(name: str, file: Any, repository_id: str) -> None:
    new_req_file_id = await create_requirement_file(
        {"name": name, "manager": "maven", "moment": datetime.now()}, repository_id
    )
    await maven_generate_packages(file["dependencies"], new_req_file_id)


async def maven_generate_packages(
    dependencies: dict[str, str],
    parent_id: str,
    parent_version_name: str | None = None
) -> None:
    known_packages = []
    for dependency, constraints in dependencies.items():
        group_id, artifact_id = dependency
        package = await read_package_by_name("MavenPackage", f"{group_id}:{artifact_id}")
        if package:
            package["parent_id"] = parent_id
            package["parent_version_name"] = parent_version_name
            package["constraints"] = constraints
            if package["moment"] < datetime.now() - timedelta(days=10):
                await maven_search_new_versions(package)
            known_packages.append(package)
        else:
            await maven_create_package(group_id, artifact_id, constraints, parent_id, parent_version_name)
    await relate_packages("MavenPackage", known_packages)


async def maven_create_package(
    group_id: str,
    artifact_id: str,
    constraints: str | None = None,
    parent_id: str | None = None,
    parent_version_name: str | None = None,
) -> None:
    all_versions = await get_maven_versions(
        group_id, artifact_id
    )
    if all_versions:
        versions = [
            await attribute_vulnerabilities(f"{group_id}:{artifact_id}", version)
            for version in all_versions
        ]
        new_versions = await create_package_and_versions(
            {"group_id": group_id, "artifact_id": artifact_id, "name": f"{group_id}:{artifact_id}", "vendor": "n/a", "moment": datetime.now()},
            versions,
            "MavenPackage",
            constraints,
            parent_id,
            parent_version_name,
        )
        for new_version in new_versions:
            await maven_extract_packages(group_id, artifact_id, new_version)


async def maven_extract_packages(
    parent_group_id: str,
    parent_artifact_id: str,
    version: dict[str, Any]
) -> None:
    require_packages = await get_maven_requires(
        version["name"],
        parent_group_id,
        parent_artifact_id,
    )
    await maven_generate_packages(require_packages, version["id"], parent_artifact_id)


async def maven_search_new_versions(package: dict[str, Any]) -> None:
    all_versions = await get_maven_versions(package["group_id"], package["artifact_id"])
    counter = await count_number_of_versions_by_package("MavenPackage", package["name"])
    if counter < len(all_versions):
        no_existing_versions: list[dict[str, Any]] = []
        actual_versions = await read_versions_names_by_package("MavenPackage", package["name"])
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
            "MavenPackage",
            no_existing_attributed_versions,
        )
        for new_version, in new_versions:
            await maven_extract_packages(package["group_id"], package["artifact_id"], new_version)
    await update_package_moment("MavenPackage", package["name"])
