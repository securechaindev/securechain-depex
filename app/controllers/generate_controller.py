from bson import ObjectId

from app.apis.pypi_service import requires_packages, get_all_versions

from app.controllers.version_controller import filter_versions_db

from app.services.package_edge_service import add_package_edge, update_package_edge_versions
from app.services.package_service import add_package, get_package_by_name, update_package_versions
from app.services.version_service import add_version, get_version_by_release_and_date, update_version_package_edges


async def generate_packages(package_name: str, release: dict) -> list[ObjectId]:
    require_packages = requires_packages(package_name, release)
    package_edges = []

    if require_packages:

        for require_package in require_packages.items():
            package_edge: dict = {}

            name, constraints = require_package
            name = name.lower()

            package_edge['constraints'] = constraints

            package = await get_package_by_name(name)
            
            if package is not None:

                package_edge_id = await exist_package(package_edge, package)

            else:

                package_edge_id = await no_exist_package(name, package_edge, constraints)

            package_edges.append(package_edge_id)

    return package_edges


async def exist_package(package_edge: dict, package: dict) -> ObjectId:
    package_edge['package'] = package['_id']

    filtered_versions = await filter_versions_db(package_edge['constraints'], package['versions'])

    package_edge['versions'] = filtered_versions

    new_package_edge = await add_package_edge(package_edge)

    return new_package_edge['_id']

async def no_exist_package(name: str, package_edge: dict, constraints: list[list[str]]) -> ObjectId:
    package = {
        'name': name
    }

    new_package = await add_package(package)

    package_edge['package'] = new_package['_id']

    new_package_edge = await add_package_edge(package_edge)

    package_edge_id = new_package_edge['_id']

    no_existing_versions = await generate_versions(new_package, package_edge_id, constraints)

    for version in no_existing_versions:

        version_package_edges = await generate_packages(new_package['name'], version[1])

        await update_version_package_edges(version[0], version_package_edges)

    return package_edge_id

async def generate_versions(package: dict, package_edge_id: ObjectId, constraints: list) -> None:
    package_versions = []
    no_existing_versions = []
    package_name = package['name']
    package_id = package['_id']

    all_versions = get_all_versions(package_name)

    for version in all_versions:

        existing_version = await get_version_by_release_and_date(version['release'], version['release_date'])

        if existing_version is not None:

            package_versions.append(existing_version['_id'])

        else:

            new_version = await add_version(version)

            new_version_id = new_version['_id']

            package_versions.append(new_version_id)

            no_existing_versions.append([new_version_id, new_version['release']])

    filtered_versions = await filter_versions_db(constraints, package_versions)

    await update_package_versions(package_id, package_versions)

    await update_package_edge_versions(package_edge_id, filtered_versions)

    return no_existing_versions