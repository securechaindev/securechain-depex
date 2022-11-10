from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from flamapy.metamodels.dn_metamodel.operations import NetworkInfo

from app.controllers.serialize_controller import serialize_network
from app.utils.json_encoder import JSONencoder

router = APIRouter()

@router.get('/operation/network_info/{network_id}', response_description = 'Network info operation')
async def network_info(network_id: str):
    dependency_network = await serialize_network(network_id)
    operation = NetworkInfo()
    operation.execute(dependency_network)
    return JSONResponse(status_code = status.HTTP_200_OK, content = JSONencoder().encode(operation.get_result()))