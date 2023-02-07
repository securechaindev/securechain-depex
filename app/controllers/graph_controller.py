from typing import Any

from datetime import datetime, timedelta

from fastapi import APIRouter, BackgroundTasks, Body, HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.apis import get_repo_data
from app.models import GraphModel
from app.services import (
    create_graph,
    read_graph_by_id,
    update_graph_is_completed,
    update_graph_requirement_files,
    read_package_by_name,
    create_requirement_file
)
from app.utils import json_encoder

from .cve_controller import relate_cves
from .generate_controller import (
    generate_package_edge,
    no_exist_package,
    search_new_versions
)

router = APIRouter()


@router.get(
    '/graph/{graph_id}',
    response_description='Get graph',
    response_model=GraphModel
)
async def read_graph_data(graph_id: str) -> JSONResponse:
    try:
        graph = await read_graph_by_id(graph_id)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=json_encoder(graph)
        )
    except HTTPException as error:
        return JSONResponse(
            status_code=error.status_code,
            content=json_encoder({'message': error.detail})
        )


@router.post('/graph', response_description='Init graph', response_model=GraphModel)
async def init_graph(
    background_tasks: BackgroundTasks,
    graph: GraphModel = Body(...)
) -> JSONResponse:
    graph_json = jsonable_encoder(graph)
    try:
        new_graph = await create_graph(graph_json)
        background_tasks.add_task(generate_graph, new_graph)
        # await generate_graph(new_graph)
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=json_encoder(new_graph)
        )
    except HTTPException as error:
        return JSONResponse(
            status_code=error.status_code,
            content=json_encoder({'message': error.detail})
        )


async def generate_graph(graph: dict[str, Any]) -> None:
    files = await get_repo_data(graph['owner'], graph['name'])

    for name, file in files.items():
        if file['manager'] != 'PIP':
            continue

        req_file = {'name': name, 'manager': file['manager'], 'package_edges': []}

        new_req_file = await create_requirement_file(req_file)

        await update_graph_requirement_files(graph['_id'], new_req_file['_id'])

        for dependencie, constraints in file['dependencies'].items():

            package = await read_package_by_name(dependencie)

            if package is not None:

                now = datetime.now()
                if package['moment'] < now - timedelta(days=10):
                    await search_new_versions(package)
                    await relate_cves(package['name'])

                await generate_package_edge(
                    package['name'],
                    constraints,
                    'depex',
                    new_req_file['_id'],
                    'requirement_file'
                )

            else:

                print(dependencie)
                await no_exist_package(
                    dependencie,
                    constraints,
                    'depex',
                    new_req_file['_id'],
                    'requirement_file'
                )

    await update_graph_is_completed(graph['_id'])