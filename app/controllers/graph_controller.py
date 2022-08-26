from fastapi import APIRouter, Body, status, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from app.apis.pypi_service import requires_dist, get_all_versions

from app.controllers.generate_controller import generate_packages

from app.models.graph_model import GraphModel

from app.services.graph_service import add_graph
from app.services.package_service import add_package, get_package_by_name, update_package_versions
from app.services.version_service import add_version, get_version_by_release_and_date, update_version_package_edges

from app.utils.json_encoder import JSONEncoder


router = APIRouter()

@router.post('/graph', response_description='Init graph', response_model = GraphModel)
async def init_graph(background_tasks: BackgroundTasks, graph: GraphModel = Body(...)):
    graph_json = jsonable_encoder(graph)

    new_graph = await add_graph(graph_json)

    background_tasks.add_task(background_generate, graph_json['name'])

    return JSONResponse(status_code = status.HTTP_201_CREATED, content = JSONEncoder().encode(new_graph))

async def background_generate(graph_name):

    req_dist = requires_dist(graph_name)

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

                new_version = await add_version(version)

                new_version_id = new_version['_id']

                package_versions.append(new_version_id)


                version_package_edges = await generate_packages(package['name'], new_version['release'])

                await update_version_package_edges(new_version_id, version_package_edges)
        
        
        await update_package_versions(new_package['_id'], package_versions)