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


async def pip_extract_graph(name: str, file: Any, repository_id: str) -> None:
    new_req_file_id = await create_requirement_file(
        {'name': name, 'manager': 'PIP'},
        repository_id,
        'PIP'
    )
    for dependencie, constraints in file['dependencies'].items():
        await pip_exist_package(dependencie, constraints, new_req_file_id)


async def pip_exist_package(package_name: str, constraints: str, requirement_file_id: str) -> None:
    package = await read_package_by_name(package_name, 'PIP')
    if package:
        if package['moment'] < datetime.now() - timedelta(days=10):
            await search_new_versions(package)
        await relate_package(package_name, constraints, requirement_file_id, 'PIP')
    else:
        await no_exist_package(package_name, constraints, requirement_file_id)


async def no_exist_package(package_name: str, constraints: list[str] | str, parent_id: str) -> None:
    all_versions = await get_all_versions(package_name, 'PIP')
    if all_versions:
        cpe_matches = await read_cpe_matches_by_package_name(package_name)
        versions = [await relate_cves(version, cpe_matches, 'PIP', package_name) for version in all_versions]
        new_versions = await create_package_and_versions(
            {'name': package_name, 'moment': datetime.now()},
            versions,
            constraints,
            parent_id,
            'PIP'
        )
        for new_version in new_versions:
            await generate_packages(package_name, new_version)


async def generate_packages(parent_package_name: str, version: dict[str, Any]) -> None:
    require_packages = await requires_packages(parent_package_name, version['name'], 'PIP')
    if require_packages:
        for package_name, constraints in require_packages.items():
            package_name = package_name.lower()
            package = await read_package_by_name(package_name, 'PIP')
            if package:
                if package['moment'] < datetime.now() - timedelta(days=10):
                    await search_new_versions(package)
                await relate_package(package_name, constraints, version['id'], 'PIP')
            else:
                await no_exist_package(package_name, constraints, version['id'])


async def search_new_versions(package: dict[str, Any]) -> None:
    no_existing_versions: list[dict[str, Any]] = []
    all_versions = await get_all_versions(package['name'], 'PIP')
    counter = await count_number_of_versions_by_package(package['name'], 'PIP')
    if counter < len(all_versions):
        cpe_matches = await read_cpe_matches_by_package_name(package['name'])
        actual_versions = await read_versions_names_by_package(package['name'], 'PIP')
        for version in all_versions:
            if not version['release'] in actual_versions:
                version['count'] = counter
                new_version = await relate_cves(version, cpe_matches, 'PIP', package['name'])
                no_existing_versions.append(new_version)
                counter += 1
    await update_package_moment(package['name'], 'PIP')
    for version in no_existing_versions:
        await generate_packages(package['name'], version)