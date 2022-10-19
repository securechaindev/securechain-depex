from datetime import datetime, timedelta

from fastapi import APIRouter, BackgroundTasks, Body, HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.apis.git_service import get_repo_data
from app.controllers.generate_controller import (generate_package_edge,
                                                 no_exist_package,
                                                 search_new_versions)
from app.models.graph_model import GraphModel
from app.services.graph_service import (create_graph, read_graph,
                                        update_graph_is_completed,
                                        update_graph_requirement_files)
from app.services.package_service import read_package_by_name
from app.services.requirement_file_service import create_requirement_file
from app.utils.json_encoder import JSONencoder

router = APIRouter()

@router.get('/graph/{graph_id}', response_description = 'Get graph', response_model = GraphModel)
async def read_graph_data(graph_id: str):
    try:
        graph = await read_graph(graph_id)
        return JSONResponse(status_code = status.HTTP_200_OK, content = JSONencoder().encode(graph))
    except HTTPException as error:
        return JSONResponse(status_code = error.status_code, content = JSONencoder().encode({'message': error.detail}))

@router.post('/graph', response_description = 'Init graph', response_model = GraphModel)
async def init_graph(background_tasks: BackgroundTasks, graph: GraphModel = Body(...)):
    graph_json = jsonable_encoder(graph)
    try:
        new_graph = await create_graph(graph_json)
        background_tasks.add_task(generate_graph, new_graph)
        # await generate_graph(new_graph)
        return JSONResponse(status_code = status.HTTP_201_CREATED, content = JSONencoder().encode(new_graph))
    except HTTPException as error:
        return JSONResponse(status_code = error.status_code, content = JSONencoder().encode({'message': error.detail}))

async def generate_graph(graph: dict) -> None:
    files = await get_repo_data(graph['owner'], graph['name'])

    for file in files.items():
        req_file = {'name': file[0], 'manager': file[1][0], 'package_edges': []}

        new_req_file = await create_requirement_file(req_file)

        await update_graph_requirement_files(graph['_id'], new_req_file['_id'])

        for dependencie in file[1][1]:

            package = await read_package_by_name(dependencie[0])

            if package is not None:

                now = datetime.now()
                if package['moment'] < now - timedelta(days = 10):
                    await search_new_versions(package)

                await generate_package_edge(package, dependencie[1], 'depex', new_req_file['_id'], 'req_file')

            else:

                await no_exist_package(dependencie[0],  dependencie[1], 'depex', new_req_file['_id'], 'req_file')

    await update_graph_is_completed(graph['_id'])