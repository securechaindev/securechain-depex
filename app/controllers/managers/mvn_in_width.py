from datetime import datetime, timedelta
from typing import Any

from app.apis import get_all_versions, requires_packages
from app.controllers.cve_controller import attribute_cves
from app.services import (
    count_number_of_versions_by_package,
    create_package_and_versions,
    create_requirement_file,
    read_cpe_product_by_package_name,
    read_package_by_name,
    read_versions_names_by_package,
    relate_packages,
    update_package_moment,
    parent_depth
)

new_req_file_id = ""

async def mvn_create_requirement_file(name: str, file: Any, repository_id: str) -> None:
    global new_req_file_id
    new_req_file_id = await create_requirement_file(
        {"name": name, "manager": "MVN"}, repository_id, "MVN"
    )
    versions = await mvn_generate_packages(file["dependencies"], new_req_file_id)
    await mvn_generate_versions1(versions)


async def mvn_generate_versions1(versions_: list[dict[str, str]]) -> None:
    new_versions: list[dict[str, str]] = []
    for version_ in versions_:
        versions, parent_artifact_id, parent_group_id = version_
        for version in versions:
            result = await extract_packages(version, parent_artifact_id, parent_group_id)
            if result:
                dependencies, version_id = result
            else:
                continue
            new_versions.extend(await mvn_generate_packages(dependencies, version_id))
    await mvn_generate_versions2(new_versions)

async def mvn_generate_versions2(versions_: list[dict[str, str]]) -> None:
    new_versions: list[dict[str, str]] = []
    for version_ in versions_:
        versions, parent_artifact_id, parent_group_id = version_
        for version in versions:
            result = await extract_packages(version, parent_artifact_id, parent_group_id)
            if result:
                dependencies, version_id = result
            else:
                continue
            new_versions.extend(await mvn_generate_packages(dependencies, version_id))
    await mvn_generate_versions1(new_versions)


async def mvn_generate_packages(
    dependencies: dict[str, str],
    parent_id: str,
    parent_version_name: str | None = None
) -> list[dict[str, str]]:
    existing_packages: list[dict(str, str)] = []
    new_versions: list[dict[str, str]] = []
    for dependency, constraints in dependencies.items():
        group_id, artifact_id = dependency
        package = await read_package_by_name(artifact_id, "MVN")
        if package:
            # if package["moment"] < datetime.now() - timedelta(days=10):
            #     await search_new_versions(package)
            package["parent_id"] = parent_id
            package["parent_version_name"] = parent_version_name
            package["constraints"] = constraints
            existing_packages.append(package)
        else:
            all_versions = await get_all_versions(
                "MVN", package_artifact_id=artifact_id, package_group_id=group_id
            )
            if all_versions:
                cpe_product = await read_cpe_product_by_package_name(artifact_id)
                versions = [
                    await attribute_cves(version, cpe_product, "MVN") for version in all_versions
                ]
                new_versions.append([await create_package_and_versions(
                    {"name": artifact_id, "group_id": group_id, "moment": datetime.now()},
                    versions,
                    "MVN",
                    constraints,
                    parent_id,
                    artifact_id
                ), artifact_id, group_id])
    await relate_packages(existing_packages, "MVN")
    return new_versions


async def extract_packages(
    version: dict[str, str],
    parent_artifact_id: str,
    parent_group_id: str
) -> None:
    require_packages = await requires_packages(
        version["name"],
        "MVN",
        package_group_id=parent_group_id,
        package_artifact_id=parent_artifact_id,
    )
    return require_packages, version["id"]


# async def search_new_versions(package: dict[str, Any]) -> None:
#     no_existing_versions: list[dict[str, Any]] = []
#     all_versions = await get_all_versions(
#         "MVN", package_artifact_id=package["name"], package_group_id=package["group_id"]
#     )
#     counter = await count_number_of_versions_by_package(package["name"], "MVN")
#     if counter < len(all_versions):
#         cpe_matches = await read_cpe_product_by_package_name(package["name"])
#         actual_versions = await read_versions_names_by_package(package["name"], "MVN")
#         for version in all_versions:
#             if version["release"] not in actual_versions:
#                 version["count"] = counter
#                 new_version = await attribute_cves(
#                     version, cpe_matches, "MVN", package["name"]
#                 )
#                 no_existing_versions.append(new_version)
#                 counter += 1
#     await update_package_moment(package["name"], "MVN")
#     for version in no_existing_versions:
#         await extract_packages(package["name"], version)
