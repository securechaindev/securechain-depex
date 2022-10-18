from datetime import datetime, timedelta

from bson import ObjectId

from app.apis.pypi_service import get_all_versions, requires_packages
from app.controllers.cve_controller import extract_cves
from app.services.package_edge_service import create_package_edge
from app.services.package_service import (create_package, read_package_by_name,
                                          update_package_moment,
                                          update_package_versions)
from app.services.requirement_file_service import \
    update_requirement_file_package_edges
from app.services.version_service import (create_version,
                                          read_version_by_release_and_package,
                                          read_versions_by_constraints,
                                          update_version_package_edges)


async def generate_package_edge(package: dict, constraints: list[list[str]], db: str, parent_id: ObjectId, parent_type: str) -> None:
    package_edge = {'constraints': constraints, 'package': package['_id']}

    package_edge['versions'] = await read_versions_by_constraints(constraints, package['_id'])

    new_package_edge = await create_package_edge(package_edge, db)

    match parent_type:
        case 'version':
            await update_version_package_edges(parent_id, new_package_edge['_id'])
        case 'req_file':
            await update_requirement_file_package_edges(parent_id, new_package_edge['_id'])

async def no_exist_package(package_name: str, constraints: list[list[str]], db: str, parent_id: ObjectId, parent_type: str) -> None:
    new_package = await create_package({'name': package_name, 'moment': datetime.now(), 'versions': []})

    no_existing_versions = await generate_versions(new_package)

    await generate_package_edge(new_package, constraints, db, parent_id, parent_type)

    await extract_cves(await read_package_by_name(new_package['name']))

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

                await generate_package_edge(package, constraints, 'pypi', version[0], 'version')

            else:

                await no_exist_package(package_name, constraints, 'pypi', version[0], 'version')

async def generate_versions(package: dict) -> list:
    no_existing_versions: list = []

    all_versions = await get_all_versions(package['name'])

    for version in all_versions:
        version['package'] = package['_id']

        new_version = await create_version(version)

        new_version_id = new_version['_id']

        await update_package_versions(package['_id'], new_version_id)

        no_existing_versions.append([new_version_id, new_version['release']])

    return no_existing_versions

async def search_new_versions(package: dict) -> None:
    no_existing_versions: list = []

    all_versions = await get_all_versions(package['name'])

    if len(package['versions']) < len(all_versions):
        for version in all_versions:
            if not await read_version_by_release_and_package(version['release'], package['_id']):
                version['package'] = package['_id']

                new_version = await create_version(version)

                new_version_id = new_version['_id']

                await update_package_versions(package['_id'], new_version_id)

                no_existing_versions.append([new_version_id, new_version['release']])

    await update_package_moment(package['_id'])
    for version in no_existing_versions:
        await generate_packages(package['name'], version)
