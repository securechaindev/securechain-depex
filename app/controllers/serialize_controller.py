import time

from bson import ObjectId
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from flamapy.metamodels.dn_metamodel.models import (DependencyNetwork, Package,
                                                    RequirementFile, Version)
from flamapy.metamodels.dn_metamodel.operations import NetworkInfo
from flamapy.metamodels.dn_metamodel.transformations import SerializeNetwork

from app.services.package_edge_service import read_package_edge_by_id
from app.services.serialize_service import aggregate_network_by_id
from app.utils.json_encoder import JSONencoder

router = APIRouter()
all_package_edges: list[dict] = []
all_package_edges_ids: list[ObjectId] = []

@router.get('/serialize/{network_id}', response_description = 'Serialize network')
async def serialize_network(network_id: str):
    try:
        begin = time.time()
        network = await aggregate_network_by_id(network_id)
        requirement_files = network['requirement_files']
        del network['_id']
        network['requirement_files'] = []
        serializer = SerializeNetwork(source_model = network)
        serializer.transform()
        await read_requirement_files(requirement_files, serializer.destination_model)
        end = time.time()
        print('Extraer y Serializar: ' + str(end - begin))
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

async def read_requirement_files(requirement_files: list[dict], dn_model: DependencyNetwork) -> None:
    for requirement_file in requirement_files:
        if not requirement_file['package_edges']:
            continue
        package_edges = requirement_file['package_edges']
        del requirement_file['package_edges']
        del requirement_file['_id']
        requirement_file['packages'] = []
        requirement_file = RequirementFile(**requirement_file)
        dn_model.requirement_files.append(requirement_file)
        await read_packages(package_edges, requirement_file)
        all_package_edges.clear()
        all_package_edges_ids.clear()

async def read_packages(package_egdes: list[dict], parent: RequirementFile | Version) -> None:
    for package_edge in package_egdes:
        package = Package(**{'name': package_edge['package_name'], 'versions': []})
        parent.packages.append(package)
        await read_versions(package_edge['versions'], package)

async def read_versions(versions: list[dict], package: Package) -> None:
    for version in versions:
        if '_id' not in version:
            continue
        package_edges = await search_package_edge(version['package_edges'])
        del version['package_edges']
        del version['_id']
        version['packages'] = []
        version = Version(**version)
        package.versions.append(version)
        await read_packages(package_edges, version)

async def search_package_edge(package_edge_ids: list[ObjectId]):
    package_edges = []
    for package_edge_id in package_edge_ids:
        if package_edge_id not in all_package_edges_ids:
            package_edge = await read_package_edge_by_id(package_edge_id, 'pypi')
            all_package_edges.append(package_edge)
            all_package_edges_ids.append(package_edge_id)
            package_edges.append(package_edge)
            continue
        for package_edge in all_package_edges:
            if package_edge['_id'] == package_edge_id:
                package_edges.append(package_edge)
                break
    return package_edges