from datetime import datetime, timedelta
from typing import Any

from app.apis import get_all_versions, requires_packages
from app.controllers.cve_controller import relate_cves
from app.services import (
    count_number_of_versions_by_package,
    create_package_and_versions_with_parent,
    create_requirement_file,
    read_cpe_matches_by_package_name,
    read_package_by_name,
    read_versions_names_by_package,
    relate_package,
    update_package_moment,
)


async def mvn_extract_graph(name: str, file: Any, repository_id: str) -> None:
    new_req_file_id = await create_requirement_file(
        {"name": name, "manager": "MVN"}, repository_id, "MVN"
    )
    for dependency, constraints in file["dependencies"].items():
        await mvn_extract_package(dependency, constraints, new_req_file_id)


async def mvn_extract_package(
    dependency: str, constraints: str, requirement_file_id: str
) -> None:
    group_id, artifact_id = dependency.split(":")
    package = await read_package_by_name(artifact_id, "MVN")
    if package:
        if package["moment"] < datetime.now() - timedelta(days=10):
            await search_new_versions(package)
        await relate_package(artifact_id, constraints, requirement_file_id, "MVN")
    else:
        await no_exist_package(group_id, artifact_id, constraints, requirement_file_id)


async def no_exist_package(
    group_id: str, artifact_id: str, constraints: list[str] | str, parent_id: str
) -> None:
    all_versions = await get_all_versions(
        "MVN", package_artifact_id=artifact_id, package_group_id=group_id
    )
    if all_versions:
        cpe_matches = await read_cpe_matches_by_package_name(artifact_id)
        versions = [
            await relate_cves(version, cpe_matches, "MVN", artifact_id)
            for version in all_versions
        ]
        new_versions = await create_package_and_versions_with_parent(
            {"name": artifact_id, "group_id": group_id, "moment": datetime.now()},
            versions,
            constraints,
            parent_id,
            "MVN",
        )
        for new_version in new_versions:
            await generate_packages(group_id, artifact_id, new_version)


async def generate_packages(
    parent_group_id: str, parent_artifact_id: str, version: dict[str, Any]
) -> None:
    require_packages = await requires_packages(
        version["name"],
        "MVN",
        package_group_id=parent_group_id,
        package_artifact_id=parent_artifact_id,
    )
    if require_packages:
        for group_artifact, constraints in require_packages.items():
            group_id, artifact_id = group_artifact
            package = await read_package_by_name(artifact_id, "MVN")
            if package:
                if package["moment"] < datetime.now() - timedelta(days=10):
                    await search_new_versions(package)
                await relate_package(artifact_id, constraints, version["id"], "MVN")
            else:
                await no_exist_package(
                    group_id, artifact_id, constraints, version["id"]
                )


async def search_new_versions(package: dict[str, Any]) -> None:
    no_existing_versions: list[dict[str, Any]] = []
    all_versions = await get_all_versions(
        "MVN", package_artifact_id=package["name"], package_group_id=package["group_id"]
    )
    counter = await count_number_of_versions_by_package(package["name"], "MVN")
    if counter < len(all_versions):
        cpe_matches = await read_cpe_matches_by_package_name(package["name"])
        actual_versions = await read_versions_names_by_package(package["name"], "MVN")
        for version in all_versions:
            if version["release"] not in actual_versions:
                version["count"] = counter
                new_version = await relate_cves(
                    version, cpe_matches, "MVN", package["name"]
                )
                no_existing_versions.append(new_version)
                counter += 1
    await update_package_moment(package["name"], "MVN")
    for version in no_existing_versions:
        await generate_packages(package["name"], version)
