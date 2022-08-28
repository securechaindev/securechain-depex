from fastapi import APIRouter, Body, status, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from app.apis.pypi_service import get_all_versions
from app.apis.git_service import get_repo_data

from app.controllers.generate_controller import generate_packages, generate_versions
from app.controllers.version_controller import filter_versions_db

from app.models.graph_model import GraphModel

from app.services.graph_service import add_graph, update_graph_requirement_files
from app.services.package_service import add_package, get_package_by_name, update_package_versions
from app.services.package_edge_service import add_package_edge
from app.services.requirement_file_service import add_requirement_file, update_requirement_file
from app.services.version_service import add_version, get_version_by_release_and_date, update_version_package_edges

from app.utils.json_encoder import JSONEncoder


router = APIRouter()

@router.post('/graph', response_description='Init graph', response_model = GraphModel)
async def init_graph(background_tasks: BackgroundTasks, graph: GraphModel = Body(...)):
    graph_json = jsonable_encoder(graph)

    new_graph = await add_graph(graph_json)

    # background_tasks.add_task(generate_graph, new_graph)

    await generate_graph(new_graph)

    return JSONResponse(status_code = status.HTTP_201_CREATED, content = JSONEncoder().encode(new_graph))

# Implementar las llamadas de requests de forma asíncrona
async def generate_graph(graph):
    files = await get_repo_data(graph['owner'], graph['name'], graph['manager'])

    requirement_files = []

    for file in files:

        package_edges = []

        req_file = {
            'name': file
        }

        new_req_file = await add_requirement_file(req_file)

        requirement_files.append(new_req_file['_id'])

        for dependencie in files[file]:

            package_edge = {}

            package_name = dependencie[0]

            constraints = dependencie[1]

            package_edge['constraints'] = constraints

            package = await get_package_by_name(package_name)

            if package is not None:

                package_edge['package'] = package['_id']

                package_edge['versions'] = await filter_versions_db(constraints, package['versions'])

                new_package_edge = await add_package_edge(package_edge)

            else:

                package = {
                    'name': package_name,
                }

                new_package = await add_package(package)

                package_edge['package'] = new_package['_id']

                new_package_edge = await add_package_edge(package_edge)

                no_existing_versions = await generate_versions(new_package, new_package_edge['_id'], constraints)

                for version in no_existing_versions:

                    version_package_edges = await generate_packages(new_package['name'], version[1])

                    await update_version_package_edges(version[0], version_package_edges)

            package_edges.append(new_package_edge['_id'])

        await update_requirement_file(new_req_file['_id'], package_edges)

    await update_graph_requirement_files(graph['_id'], requirement_files)