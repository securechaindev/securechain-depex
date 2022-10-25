from bson import ObjectId
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from flamapy.metamodels.dn_metamodel.transformations import SerializeNetwork

from app.services.cve_service import read_cve_by_id
from app.services.network_service import read_network_by_id
from app.services.requirement_file_service import read_requirement_file_by_id
from app.services.package_edge_service import read_package_edge_by_id
from app.services.package_service import read_package_by_id
from app.services.version_service import read_version_by_id
from app.utils.json_encoder import JSONencoder

router = APIRouter()

@router.get('/serialize/{network_id}', response_description = 'Serialize network')
async def serialize_network(network_id: str):
    try:
        network = await read_network_by_id(network_id, {'_id': 0, 'owner': 1, 'name': 1, 'requirement_files': 1})
        network['requirement_files'] = await read_requirement_files(network['requirement_files'])
        serializer = SerializeNetwork(source_model = network)
        serializer.transform()
        print(serializer.destination_model)
        # TODO: Completar con la transformación a SMT
        return JSONResponse(status_code = status.HTTP_200_OK, content = JSONencoder().encode({}))
    except HTTPException as error:
        return JSONResponse(status_code = error.status_code, content = JSONencoder().encode({'message': error.detail}))
    
async def read_requirement_files(requirement_file_ids: list[ObjectId]) -> list[dict]:
    requirement_files = []
    for requirement_file_id in requirement_file_ids:
        requirement_file = await read_requirement_file_by_id(requirement_file_id, {'_id': 0})
        packages = await read_packages(requirement_file['package_edges'], 'depex')
        del requirement_file['package_edges']
        requirement_file['packages'] = packages
        requirement_files.append(requirement_file)
    return requirement_files

async def read_packages(package_egde_ids: list[ObjectId], db: str) -> list[dict]:
    packages = []
    for package_edge_id in package_egde_ids:
        package_edge = await read_package_edge_by_id(package_edge_id, db, {'_id': 0})
        package = await read_package_by_id(package_edge['package'], {'_id': 0, 'moment': 0})
        versions = await read_versions(package_edge['versions'])
        package['versions'] = versions
        packages.append(package)
    return packages

async def read_versions(version_ids: list[ObjectId]) -> list[dict]:
    versions = []
    for version_id in version_ids:
        version = await read_version_by_id(version_id, {'_id': 0, 'package': 0})
        version['packages'] = await read_packages(version['package_edges'], 'pypi')
        del version['package_edges']
        version['cves'] = await read_cves(version['cves'])
        versions.append(version)
    return versions

async def read_cves(cve_ids: list[ObjectId]) -> list[dict]:
    return [await read_cve_by_id(cve_id, {'_id': 0, 'id': 1, 'metrics': 1}) for cve_id in cve_ids]