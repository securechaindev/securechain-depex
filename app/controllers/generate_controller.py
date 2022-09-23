from bson import ObjectId

from app.apis.pypi_service import requires_packages, get_all_versions

from app.controllers.version_controller import filter_versions_db

from app.services.package_edge_service import (
    create_package_edge,
    update_package_edge_versions
)
from app.services.package_service import (
    create_package,
    read_package_by_name,
    update_package_versions
)
from app.services.version_service import (
    create_version,
    read_version_by_release_and_date,
    update_version_package_edges
)


async def generate_packages(package_name: str, release: str) -> list[ObjectId]:
    require_packages = await requires_packages(package_name, release)
    package_edges = []

    if require_packages:

        for require_package in require_packages.items():
            package_name, constraints = require_package
            package_name = package_name.lower()

            package_edge = {'constraints': constraints}

            package = await read_package_by_name(package_name)
            
            if package is not None:

                package_edge_id = await exist_package(package, package_edge, 'pypi')

            else:

                package_edge_id = await no_exist_package(package_name, package_edge, 'pypi')

            package_edges.append(package_edge_id)

    return package_edges

async def exist_package(package: dict, package_edge: dict, db: str) -> ObjectId:
    package_edge['package'] = package['_id']

    package_edge['versions'] = await filter_versions_db(package_edge['constraints'], package['versions'])

    new_package_edge = await create_package_edge(package_edge, db)

    return new_package_edge['_id']

async def no_exist_package(package_name: str, package_edge: dict, db: str) -> ObjectId:
    package = {'name': package_name}

    new_package = await create_package(package)

    package_edge['package'] = new_package['_id']

    new_package_edge = await create_package_edge(package_edge, db)

    no_existing_versions = await generate_versions(new_package, new_package_edge, db)

    await relate_versions(no_existing_versions, new_package['name'])

    return new_package_edge['_id']

async def relate_versions(no_existing_versions: list, package_name: str) -> None:
    for version in no_existing_versions:

        version_package_edges = await generate_packages(package_name, version[1])

        await update_version_package_edges(version[0], version_package_edges)

async def generate_versions(package: dict, package_edge: dict, db: str) -> list:
    no_existing_versions: list = []
    package_versions = []

    all_versions = await get_all_versions(package['name'])

    for version in all_versions:

        existing_version = await read_version_by_release_and_date(version['release'], version['release_date'])

        if existing_version is not None:

            package_versions.append(existing_version['_id'])

        else:

            new_version = await create_version(version)

            new_version_id = new_version['_id']

            package_versions.append(new_version_id)

            no_existing_versions.append([new_version_id, new_version['release']])

    filtered_versions = await filter_versions_db(package_edge['constraints'], package_versions)

    await update_package_versions(package['_id'], package_versions)

    await update_package_edge_versions(package_edge['_id'], filtered_versions, db)

    return no_existing_versions