from datetime import datetime, timedelta

from typing import Any

from app.apis import get_all_versions

from app.services import (
    read_cpe_matches_by_package_name,
    read_package_by_name,
    create_requirement_file,
    relate_package,
    update_package_moment,
    count_number_of_versions_by_package,
    get_versions_names_by_package,
    create_package_and_versions
)

from app.controllers.cve_controller import relate_cves


async def npm_extract_graph(name: str, file: Any, repository_ids: dict[str, str]) -> None:
    repository_id = repository_ids['NPM']
    new_req_file_id = await create_requirement_file(
        {'name': name, 'manager': 'NPM'},
        repository_id,
        'NPM'
    )

    for dependencie, constraints in file['dependencies'].items():
        package = await read_package_by_name(dependencie, 'NPM')

        if package:
            if package['moment'] < datetime.now() - timedelta(days=10):
                await search_new_versions(package)

            await relate_package(
                dependencie,
                constraints,
                new_req_file_id,
                'NPM'
            )
        else:
            await no_exist_package(
                dependencie,
                constraints,
                new_req_file_id
            )


async def no_exist_package(package_name: str, constraints: list[str] | str, parent_id: str) -> None:
    all_versions, all_require_packages = await get_all_versions(package_name, 'NPM')

    if all_versions:
        cpe_matches = await read_cpe_matches_by_package_name(package_name)
        versions = [await relate_cves(version, cpe_matches, 'NPM', package_name) for version in all_versions]
        new_versions = await create_package_and_versions(
            {
                'name': package_name,
                'moment': datetime.now()
            },
            versions,
            constraints,
            parent_id,
            'NPM'
        )

        for new_version, require_packages in zip(new_versions, all_require_packages):
            await generate_packages(new_version, require_packages)


async def generate_packages(version: dict[str, Any], require_packages: Any) -> None:
    if require_packages:
        for package_name, constraints in require_packages.items():
            package_name = package_name.lower()
            package = await read_package_by_name(package_name, 'NPM')

            if package:
                if package['moment'] < datetime.now() - timedelta(days=10):
                    await search_new_versions(package)

                await relate_package(
                    package_name,
                    constraints,
                    version['id'],
                    'NPM'
                )
            else:
                await no_exist_package(
                    package_name,
                    constraints,
                    version['id']
                )


async def search_new_versions(package: dict[str, Any]) -> None:
    no_existing_versions: list[dict[str, Any]] = []
    all_versions = await get_all_versions(package['name'], 'NPM')
    counter = await count_number_of_versions_by_package(package['name'], 'NPM')

    if counter < len(all_versions):
        cpe_matches = await read_cpe_matches_by_package_name(package['name'])
        actual_versions = await get_versions_names_by_package(package['name'], 'NPM')

        for version in all_versions:
            if not version['release'] in actual_versions:
                version['count'] = counter
                new_version = await relate_cves(version, cpe_matches, 'NPM', package['name'])
                no_existing_versions.append(new_version)
                counter += 1

    await update_package_moment(package['name'], 'NPM')
    for version in no_existing_versions:
        await generate_packages(package['name'], version)