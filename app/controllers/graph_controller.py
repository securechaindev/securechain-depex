from bson import ObjectId

from fastapi import APIRouter, Body, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from app.models.graph_model import GraphModel

from app.services.graph_service import add_graph
from app.services.package_service import add_package, get_package_by_name, update_package_versions
from app.services.version_service import add_version, get_version_by_release_and_date, get_version_by_id
from app.services.package_edge_service import add_package_edge, update_package_edge_versions

from app.utils.json_encoder import JSONEncoder
from app.utils.ctc_parser import parse_constraints
from app.utils.filter import filter_versions

from app.managers.pypi import requires_dist, requires_packages, get_all_versions

from pkg_resources import parse_version
from app.utils.operators import ops


router = APIRouter()

@router.post('/graph', response_description='Init graph', response_model = GraphModel)
async def init_graph(graph: GraphModel = Body(...)):
    graph_json = jsonable_encoder(graph)

    new_graph = await add_graph(graph_json)

    req_dist = requires_dist(graph_json['name'])

    for dist in req_dist.items():
        dist, _ = dist
        dist = dist.lower()

        package = await get_package_by_name(dist)
        exist = package is not None

        if exist:
            continue

        package = {
            'name': dist
        }

        package_versions = []

        new_package = await add_package(package)
        
        all_versions = get_all_versions(dist)

        for version in all_versions:

            existing_version = await get_version_by_release_and_date(version['release'], version['release_date'])
            exist_version = existing_version is not None

            if exist_version:

                package_versions.append(existing_version['_id'])

            else:

                version = await generate_packages(package['name'], version)

                new_version = await add_version(version)
        
                package_versions.append(new_version['_id'])
        
        await update_package_versions(new_package['_id'], package_versions)

    return JSONResponse(status_code = status.HTTP_201_CREATED, content = JSONEncoder().encode(new_graph))

async def generate_packages(package_name: str, parent_version: dict):
    require_packages = requires_packages(package_name, parent_version['release'])

    if require_packages:

        parent_version['package_edges'] = []

        for require_package in require_packages.items():
            package_edge: dict = {'versions': []}

            name, raw_constraints = require_package

            name = name.lower()
            constraints = parse_constraints(raw_constraints)

            package_edge['constraints'] = constraints

            package = await get_package_by_name(name)
            exist = package is not None

            if exist:
                package_edge['package'] = package['_id']

                if 'Any' in package_edge['constraints']:

                    package_edge['versions'] = package['versions']

                else:

                    package_edge = await filter_versions_db(package_edge, package['versions'])

                new_package_edge = await add_package_edge(package_edge)

                parent_version['package_edges'].append(new_package_edge['_id'])

                continue

            package = {
                'name': name
            }

            new_package = await add_package(package)

            package_edge['package'] = new_package['_id']

            new_package_edge = await add_package_edge(package_edge)

            package_edge_id = new_package_edge['_id']

            parent_version['package_edges'].append(package_edge_id)

            await generate_versions(new_package, package_edge_id, constraints)
            
    return parent_version

async def generate_versions(new_package: dict, package_edge_id: ObjectId, constraints: list):
    package_versions = []
    package_edge_versions = []
    package_name = new_package['name']
    package_id = new_package['_id']

    all_versions = get_all_versions(package_name)
    filtered_versions = filter_versions(all_versions, constraints)

    for version in all_versions:

        existing_version = await get_version_by_release_and_date(version['release'], version['release_date'])
        exist_version = existing_version is not None

        if exist_version:

            version_id = existing_version['_id']
            package_versions.append(version_id)

        else:

            version = await generate_packages(package_name, version)

            new_version = await add_version(version)

            version_id = new_version['_id']
            package_versions.append(version_id)

        if version in filtered_versions:

            package_edge_versions.append(version_id)
            
    await update_package_versions(package_id, package_versions)
    await update_package_edge_versions(package_edge_id, package_edge_versions)

async def filter_versions_db(package_edge: dict, versions: list):
    for version_id in versions:

        version = await get_version_by_id(version_id)

        for constraint in package_edge['constraints']:

            op, release_ctc = constraint.split(' ')

            if ops[op](parse_version(version['release']), parse_version(release_ctc)):

                package_edge['versions'].append(version_id)

    return package_edge