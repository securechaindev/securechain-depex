from datetime import datetime, timedelta

from typing import Any

from app.apis import (
    get_all_versions,
    requires_packages,
    get_repo_data
)
from app.services import (
    read_cpe_matches_by_package_name
)

from app.services import (
    create_package,
    read_package_by_name,
    create_version,
    create_requirement_file,
    relate_package,
    update_package_moment,
    count_number_of_versions_by_package,
    get_versions_names_by_package
)

from .cve_controller import relate_cves


async def extract_graph(repository: dict[str, Any]) -> None:
    files = await get_repo_data(repository['owner'], repository['name'])

    for name, file in files.items():
        if file['manager'] != 'PIP':
            continue

        req_file = {'name': name, 'manager': file['manager']}

        new_req_file_id = await create_requirement_file(
            req_file, repository['owner'],
            repository['name']
        )

        for dependencie, constraints in file['dependencies'].items():

            package = await read_package_by_name(dependencie)

            if package:

                if package['moment'] < datetime.now() - timedelta(days=10):
                    await search_new_versions(package)

                await relate_package(
                    dependencie,
                    constraints,
                    new_req_file_id
                )

            else:

                await no_exist_package(
                    dependencie,
                    constraints,
                    new_req_file_id
                )


async def no_exist_package(
    package_name: str,
    constraints: list[str] | str,
    parent_id: str
) -> None:
    new_package_name = await create_package(
        {
            'name': package_name,
            'moment': datetime.now()
        },
        constraints,
        parent_id
    )

    no_existing_versions = await generate_versions(new_package_name)

    for version in no_existing_versions:

        await generate_packages(package_name, version)


async def generate_versions(package_name: str) -> list[dict[str, Any]]:
    no_existing_versions: list[dict[str, Any]] = []
    cpe_matches = await read_cpe_matches_by_package_name(package_name)

    all_versions = await get_all_versions(package_name)

    counter = 0
    for version in all_versions:
        version['count'] = counter
        new_version = await create_version(version, package_name)
        await relate_cves(new_version, cpe_matches)
        counter += 1

        no_existing_versions.append(new_version)

    return no_existing_versions


async def generate_packages(parent_package_name: str, version: dict[str, Any]) -> None:
    require_packages = await requires_packages(parent_package_name, version['name'])

    if require_packages:

        for package_name, constraints in require_packages.items():
            package_name = package_name.lower()

            package = await read_package_by_name(package_name)

            if package:

                if package['moment'] < datetime.now() - timedelta(days=10):
                    await search_new_versions(package)

                await relate_package(
                    package_name,
                    constraints,
                    version['id']
                )

            else:

                await no_exist_package(
                    package_name,
                    constraints,
                    version['id']
                )


async def search_new_versions(package: dict[str, Any]) -> None:
    no_existing_versions: list[dict[str, Any]] = []
    all_versions = await get_all_versions(package['name'])
    counter = await count_number_of_versions_by_package(package['name'])

    if counter < len(all_versions):
        cpe_matches = await read_cpe_matches_by_package_name(package['name'])
        actual_versions = await get_versions_names_by_package(package['name'])

        for version in all_versions:
            if not version['release'] in actual_versions:
                version['count'] = counter
                new_version = await create_version(version, package['name'])
                await relate_cves(new_version, cpe_matches)
                no_existing_versions.append(new_version)
                counter += 1

    await update_package_moment(package['name'])
    for version in no_existing_versions:
        await generate_packages(package['name'], version)