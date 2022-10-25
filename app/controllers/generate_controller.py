from datetime import datetime, timedelta

from bson import ObjectId

from app.apis.pypi_service import get_all_versions, requires_packages
from app.controllers.cve_controller import relate_cves
from app.services.package_edge_service import create_package_edge
from app.services.package_service import (create_package, read_package_by_name,
                                          update_package_moment,
                                          update_package_versions)
from app.services.version_service import (create_version,
                                          read_version_by_release_and_package,
                                          read_versions_by_constraints)


async def generate_package_edge(package: dict, constraints: list[list[str]], db: str, parent_id: ObjectId) -> None:
    package_edge = {
            'constraints': constraints,
            'versions': await read_versions_by_constraints(constraints, package['_id']),
            'parent': parent_id,
            'child': package['_id']
        }

    await create_package_edge(package_edge, db)

async def no_exist_package(package_name: str, constraints: list[list[str]], db: str, parent_id: ObjectId) -> None:
    new_package = await create_package({'name': package_name, 'moment': datetime.now(), 'versions': []})

    no_existing_versions = await generate_versions(new_package)

    await generate_package_edge(new_package, constraints, db, parent_id)

    await relate_cves(await read_package_by_name(new_package['name']))

    for version in no_existing_versions:

        await generate_packages(package_name, version)

async def generate_packages(package_name: str, version: list) -> None:
    require_packages = await requires_packages(package_name, version[1])

    if require_packages:

        for require_package in require_packages.items():
            package_name, constraints = require_package
            package_name = package_name.lower()

            package = await read_package_by_name(package_name)
            
            if package is not None:

                now = datetime.now()
                if package['moment'] < now - timedelta(days = 10):
                    await search_new_versions(package)

                await generate_package_edge(package, constraints, 'pypi', version[0])

            else:

                await no_exist_package(package_name, constraints, 'pypi', version[0])

async def generate_versions(package: dict) -> list:
    no_existing_versions: list = []

    all_versions = await get_all_versions(package['name'])

    counter = 0
    for version in all_versions:
        version['package'] = package['_id']
        version['count'] = counter

        new_version = await create_version(version)

        new_version_id = new_version['_id']

        await update_package_versions(package['_id'], new_version_id)

        no_existing_versions.append([new_version_id, new_version['release']])

        counter += 1

    return no_existing_versions

async def search_new_versions(package: dict) -> None:
    no_existing_versions: list = []

    all_versions = await get_all_versions(package['name'])

    if len(package['versions']) < len(all_versions):
        counter = len(package['versions']) + 1
        for version in all_versions:
            if not await read_version_by_release_and_package(version['release'], package['_id']):
                version['package'] = package['_id']
                version['count'] = counter

                new_version = await create_version(version)

                new_version_id = new_version['_id']

                await update_package_versions(package['_id'], new_version_id)

                no_existing_versions.append([new_version_id, new_version['release']])

                counter += 1

    await update_package_moment(package['_id'])
    for version in no_existing_versions:
        await generate_packages(package['name'], version)
