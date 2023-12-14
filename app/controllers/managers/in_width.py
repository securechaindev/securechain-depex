from datetime import datetime, timedelta
from typing import Any

from app.apis import get_all_versions, requires_packages
from app.controllers.cve_controller import relate_cves
from app.services import (
    count_number_of_versions_by_package,
    create_package_and_versions_with_parent,
    create_requirement_file,
    read_cpe_product_by_package_name,
    read_package_by_name,
    read_versions_names_by_package,
    relate_package,
    relate_packages,
    update_package_moment
)

new_req_file_id = ""

async def mvn_extract_graph(name: str, file: Any, repository_id: str) -> None:
    global new_req_file_id
    new_req_file_id = await create_requirement_file(
        {"name": name, "manager": "MVN"}, repository_id, "MVN"
    )
    for dependency, constraints in file["dependencies"].items():
        await mvn_extract_package(dependency, constraints, new_req_file_id)


async def mvn_extract_package(
    dependency: str, constraints: str, requirement_file_id: str
) -> None:
    group_id, artifact_id = dependency
    package = await read_package_by_name(artifact_id, "MVN")
    if package:
        if package["moment"] < datetime.now() - timedelta(days=10):
            await search_new_versions(package)
        await relate_package(artifact_id, constraints, requirement_file_id, "MVN")
    else:
        await generate_packages([{"group_id": group_id, "artifact_id": artifact_id, "constraints": constraints, "parent_id": requirement_file_id}])


async def generate_packages(
    packages: dict[str, str]
) -> None:
    existing_packages: dict[tuple(str, str), list[str]] = []
    new_versions: list[dict[str, str]] = []
    for package in packages:
        existing_package = await read_package_by_name(package["artifact_id"], "MVN")
        if existing_package:
            if existing_package["moment"] < datetime.now() - timedelta(days=10):
                await search_new_versions(existing_package)
            existing_packages.setdefault({"package_name": package["artifact_id"], "constraints": package["constraints"]}, []).append(package["parent_id"])
        else:
            all_versions = await get_all_versions(
                "MVN", package_artifact_id=package["artifact_id"], package_group_id=package["group_id"]
            )
            if all_versions:
                cpe_product = await read_cpe_product_by_package_name(package["artifact_id"])
                versions = [
                    await relate_cves(version, cpe_product, "MVN") for version in all_versions
                ]
                new_versions.append(await create_package_and_versions_with_parent(
                    {"name": package["artifact_id"], "group_id": package["group_id"], "moment": datetime.now()},
                    versions,
                    package["constraints"],
                    package["parent_id"],
                    "MVN",
                ))
    await relate_packages(existing_packages, "MVN")
    await extract_packages(new_versions)


async def extract_packages(
    versions: list[dict[str, str]]
) -> None:
    no_existing_packages: list[dict[str, str]] = []
    for version in versions:
        require_packages = await requires_packages(
            version["name"],
            "MVN",
            package_group_id=version["parent_group_id"],
            package_artifact_id=version["parent_artifact_id"],
        )
        if require_packages:
            for group_artifact, constraints in require_packages.items():
                group_id, artifact_id = group_artifact
                no_existing_packages.append({"group_id": group_id, "artifact_id": artifact_id, "constraints": constraints, "parent_id": version["id"]})
    await generate_packages(no_existing_packages)


async def search_new_versions(package: dict[str, Any]) -> None:
    no_existing_versions: list[dict[str, Any]] = []
    all_versions = await get_all_versions(
        "MVN", package_artifact_id=package["name"], package_group_id=package["group_id"]
    )
    counter = await count_number_of_versions_by_package(package["name"], "MVN")
    if counter < len(all_versions):
        cpe_matches = await read_cpe_product_by_package_name(package["name"])
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
