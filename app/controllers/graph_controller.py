from fastapi import APIRouter, Body, status, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from app.apis.git_service import get_repo_data

from app.controllers.generate_controller import exist_package, no_exist_package

from app.models.graph_model import GraphModel

from app.services.graph_service import read_graph, add_graph, update_graph_requirement_files, update_graph_is_completed
from app.services.package_service import get_package_by_name
from app.services.requirement_file_service import add_requirement_file, update_requirement_file

from app.utils.json_encoder import JSONEncoder


router = APIRouter()

@router.get('/graph/{graph_id}', response_description='Get graph', response_model = GraphModel)
async def get_graph(graph_id: str):
    new_graph = await read_graph(graph_id)

    return JSONResponse(status_code = status.HTTP_200_OK, content = JSONEncoder().encode(new_graph))

@router.post('/graph', response_description='Init graph', response_model = GraphModel)
async def init_graph(background_tasks: BackgroundTasks, graph: GraphModel = Body(...)):
    graph_json = jsonable_encoder(graph)

    new_graph = await add_graph(graph_json)

    background_tasks.add_task(generate_graph, new_graph)

    return JSONResponse(status_code = status.HTTP_201_CREATED, content = JSONEncoder().encode(new_graph))

async def generate_graph(graph: dict) -> None:
    files = await get_repo_data(graph['owner'], graph['name'])

    requirement_files = []

    for file in files.items():

        package_edges = []

        req_file = {'name': file[0], 'manager': file[1][0]}

        new_req_file = await add_requirement_file(req_file)

        requirement_files.append(new_req_file['_id'])

        for dependencie in file[1][1]:

            package_edge = {'constraints': dependencie[1]}

            package_name = dependencie[0]

            package = await get_package_by_name(package_name)

            if package is not None:

                package_edge_id = await exist_package(package, package_edge, 'depex')

            else:

                package_edge_id = await no_exist_package(package_name, package_edge, 'depex')

            package_edges.append(package_edge_id)

        await update_requirement_file(new_req_file['_id'], package_edges)

    await update_graph_requirement_files(graph['_id'], requirement_files)

    await update_graph_is_completed(graph['_id'])