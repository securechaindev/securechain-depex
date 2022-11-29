from typing import Any

from datetime import datetime, timedelta

from fastapi import APIRouter, BackgroundTasks, Body, HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.apis.git_service import get_repo_data
from app.controllers.cve_controller import relate_cves
from app.controllers.generate_controller import (
    generate_package_edge,
    no_exist_package,
    search_new_versions
)
from app.models.network_model import NetworkModel
from app.services.network_service import (
    create_network, read_network_by_id,
    update_network_is_completed,
    update_network_requirement_files
)
from app.services.package_service import read_package_by_name
from app.services.requirement_file_service import create_requirement_file
from app.utils.json_encoder import json_encoder

router = APIRouter()


@router.get(
    '/network/{network_id}',
    response_description='Get network',
    response_model=NetworkModel
)
async def read_network_data(network_id: str) -> JSONResponse:
    try:
        network = await read_network_by_id(network_id)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=json_encoder(network)
        )
    except HTTPException as error:
        return JSONResponse(
            status_code=error.status_code,
            content=json_encoder({'message': error.detail})
        )


@router.post('/network', response_description='Init network', response_model=NetworkModel)
async def init_network(
    background_tasks: BackgroundTasks,
    network: NetworkModel = Body(...)
) -> JSONResponse:
    network_json = jsonable_encoder(network)
    try:
        new_network = await create_network(network_json)
        # background_tasks.add_task(generate_network, new_network)
        await generate_network(new_network)
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=json_encoder(new_network)
        )
    except HTTPException as error:
        return JSONResponse(
            status_code=error.status_code,
            content=json_encoder({'message': error.detail})
        )


async def generate_network(network: dict[str, Any]) -> None:
    files = await get_repo_data(network['owner'], network['name'])

    for file in files.items():
        if file[1][0] != 'PIP':
            continue

        req_file = {'name': file[0], 'manager': file[1][0], 'package_edges': []}

        new_req_file = await create_requirement_file(req_file)

        await update_network_requirement_files(network['_id'], new_req_file['_id'])

        for dependencie in file[1][1]:

            package = await read_package_by_name(dependencie[0])

            if package is not None:

                now = datetime.now()
                if package['moment'] < now - timedelta(days=10):
                    await search_new_versions(package)
                    await relate_cves(package['name'])

                await generate_package_edge(
                    package['name'],
                    dependencie[1],
                    'depex',
                    new_req_file['_id'],
                    'requirement_file'
                )

            else:

                print(dependencie[0])
                await no_exist_package(
                    dependencie[0],
                    dependencie[1],
                    'depex',
                    new_req_file['_id'],
                    'requirement_file'
                )

    await update_network_is_completed(network['_id'])