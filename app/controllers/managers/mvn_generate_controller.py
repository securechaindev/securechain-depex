from datetime import datetime, timedelta
from typing import Any
from app.apis import (
    get_all_versions,
    requires_packages
)
from app.services import (
    read_cpe_matches_by_package_name,
    read_package_by_name,
    create_requirement_file,
    relate_package,
    update_package_moment,
    count_number_of_versions_by_package,
    read_versions_names_by_package,
    create_package_and_versions
)
from app.controllers.cve_controller import relate_cves


async def mvn_extract_graph(name: str, file: Any, repository_id: str) -> None:
    new_req_file_id = await create_requirement_file(
        {'name': name, 'manager': 'MVN'},
        repository_id,
        'MVN'
    )
    for dependencie, constraints in file['dependencies'].items():
        await mvn_exist_package(dependencie, constraints, new_req_file_id)


async def mvn_exist_package(package_name: str, constraints: str, requirement_file_id: str) -> None:
    package = await read_package_by_name(package_name, 'MVN')
    if package:
        if package['moment'] < datetime.now() - timedelta(days=10):
            await search_new_versions(package)
        await relate_package(package_name, constraints, requirement_file_id, 'MVN')
    else:
        await no_exist_package(package_name, constraints, requirement_file_id)


async def no_exist_package(package_name: str, constraints: list[str] | str, parent_id: str) -> None:
    all_versions = await get_all_versions(package_name, 'MVN')
    if all_versions:
        artifact_id = package_name.split(':')[1]
        cpe_matches = await read_cpe_matches_by_package_name(artifact_id)
        versions = [await relate_cves(version, cpe_matches, 'MVN', package_name, artifact_id) for version in all_versions]
        new_versions = await create_package_and_versions(
            {'name': package_name, 'moment': datetime.now()},
            versions,
            constraints,
            parent_id,
            'MVN'
        )
        for new_version in new_versions:
            await generate_packages(package_name, new_version)


async def generate_packages(parent_package_name: str, version: dict[str, Any]) -> None:
    require_packages = await requires_packages(parent_package_name, version['name'], 'MVN')
    if require_packages:
        for package_name, constraints in require_packages.items():
            package = await read_package_by_name(package_name, 'MVN')
            if package:
                if package['moment'] < datetime.now() - timedelta(days=10):
                    await search_new_versions(package)
                await relate_package(package_name, constraints, version['id'], 'MVN')
            else:
                await no_exist_package(package_name, constraints, version['id'])


async def search_new_versions(package: dict[str, Any]) -> None:
    no_existing_versions: list[dict[str, Any]] = []
    all_versions = await get_all_versions(package['name'], 'MVN')
    counter = await count_number_of_versions_by_package(package['name'], 'MVN')
    if counter < len(all_versions):
        cpe_matches = await read_cpe_matches_by_package_name(package['name'].split(':')[1])
        actual_versions = await read_versions_names_by_package(package['name'], 'MVN')
        for version in all_versions:
            if not version['release'] in actual_versions:
                version['count'] = counter
                new_version = await relate_cves(version, cpe_matches, 'MVN', package['name'])
                no_existing_versions.append(new_version)
                counter += 1
    await update_package_moment(package['name'], 'MVN')
    for version in no_existing_versions:
        await generate_packages(package['name'], version)