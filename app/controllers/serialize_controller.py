from bson import ObjectId
from copy import copy
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from app.controllers.SerializeNetwork import SerializeNetwork
from app.controllers.operation import NetworkInfo

from app.services.cve_service import read_cve_by_id
from app.services.serialize_service import aggregate_network_by_id
from app.services.package_edge_service import read_package_edge_by_id
from app.utils.json_encoder import JSONencoder

import time

router = APIRouter()
all_package_edges = []
all_package_edges_ids = []

@router.get('/serialize/{network_id}', response_description = 'Serialize network')
async def serialize_network(network_id: str):
    try:
        begin = time.time()
        network = await aggregate_network_by_id(ObjectId(network_id))
        del network['_id']
        await read_requirement_files(network['requirement_files'])
        end = time.time()
        print('Extraer: ' + str(end - begin))
        begin = time.time()
        serializer = SerializeNetwork(source_model = network)
        serializer.transform()
        end = time.time()
        print('Serializar: ' + str(end - begin))
        begin = time.time()
        operation = NetworkInfo()
        operation.execute(serializer.destination_model)
        end = time.time()
        print('Operacion: ' + str(end - begin))
        print(operation.get_result())
        # TODO: Completar con la transformación a SMT
        return JSONResponse(status_code = status.HTTP_200_OK, content = JSONencoder().encode(operation.get_result()))
    except HTTPException as error:
        return JSONResponse(status_code = error.status_code, content = JSONencoder().encode({'message': error.detail}))
    
async def read_requirement_files(requirement_files: list[dict]) -> None:
    for requirement_file in requirement_files:
        requirement_file['packages'] = await read_packages(requirement_file['package_edges'])
        del requirement_file['_id']
        del requirement_file['package_edges']
    all_package_edges.clear()
    all_package_edges_ids.clear()

async def read_packages(package_egdes: list[dict]) -> list[dict]:
    packages = []
    for package_edge in package_egdes:
        package = {'name': package_edge['package_name']}
        versions = await read_versions(package_edge['versions'])
        package['versions'] = versions
        packages.append(package)
    return packages

async def read_versions(raw_versions: list[dict]) -> list[dict]:
    versions = []
    for raw_version in raw_versions:
        if '_id' not in raw_version:
            continue
        package_edges = await search_package_edge(raw_version['package_edges'])
        version = copy(raw_version)
        version['packages'] = await read_packages(package_edges)
        del version['package_edges']
        del version['_id']
        versions.append(version)
    return versions

async def search_package_edge(package_edges_ids: list[ObjectId]):
    package_edges = []
    for id in package_edges_ids:
        if id not in all_package_edges_ids:
            package_edge = await read_package_edge_by_id(id, 'pypi')
            all_package_edges.append(package_edge)
            all_package_edges_ids.append(id)
            package_edges.append(package_edge)
            continue
        for package_edge in all_package_edges:
            if package_edge['_id'] == id:
                package_edges.append(package_edge)
                break
    return package_edges