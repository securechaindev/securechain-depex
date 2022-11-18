from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from flamapy.metamodels.dn_metamodel.operations import NetworkInfo

from app.controllers.network_to_smt import NetworkToSMT
from app.controllers.operations import (FilterConfigs, MaximizeImpact,
                                        MinimizeImpact, NumberOfProducts,
                                        ValidModel)
from app.controllers.serialize_controller import serialize_network
from app.utils.json_encoder import JSONencoder
from app.services.version_service import get_release_by_values

router = APIRouter()

@router.post('/operation/network_info/{network_id}', response_description = 'Network info operation')
async def network_info(network_id: str):
    dependency_network = await serialize_network(network_id)
    operation = NetworkInfo()
    operation.execute(dependency_network)
    return JSONResponse(status_code = status.HTTP_200_OK, content = JSONencoder().encode(operation.get_result()))

@router.post('/operation/valid_model/{network_id}', response_description = 'Valid model operation')
async def valid_model(network_id: str):
    dependency_network = await serialize_network(network_id)
    smt_transform = NetworkToSMT(dependency_network, 'mean')
    smt_transform.transform()
    smt_model = smt_transform.destination_model
    operation = ValidModel()
    operation.execute(smt_model)
    result = {'is_valid': operation.get_result()}
    return JSONResponse(status_code = status.HTTP_200_OK, content = JSONencoder().encode(result))

@router.post('/operation/number_of_products/{network_id}', response_description = 'Number of products operation')
async def number_of_products(network_id: str):
    dependency_network = await serialize_network(network_id)
    smt_transform = NetworkToSMT(dependency_network, 'mean')
    smt_transform.transform()
    smt_model = smt_transform.destination_model
    operation = NumberOfProducts()
    operation.execute(smt_model)
    result = {'number_of_products': operation.get_result()}
    return JSONResponse(status_code = status.HTTP_200_OK, content = JSONencoder().encode(result))

@router.post('/operation/minimize_impact/{network_id}', response_description = 'Minimize impact operation')
async def minimize_impact(network_id: str, op_configs: dict = {'limit': 10}):
    dependency_network = await serialize_network(network_id)
    smt_transform = NetworkToSMT(dependency_network, 'mean')
    smt_transform.transform()
    smt_model = smt_transform.destination_model
    operation = MinimizeImpact(**op_configs)
    operation.execute(smt_model)
    result = await get_release_by_values(operation.get_result())
    return JSONResponse(status_code = status.HTTP_200_OK, content = JSONencoder().encode(result))

@router.post('/operation/maximize_impact/{network_id}', response_description = 'Maximize impact operation')
async def maximize_impact(network_id: str, op_configs: dict = {'limit': 10}):
    dependency_network = await serialize_network(network_id)
    smt_transform = NetworkToSMT(dependency_network, 'mean')
    smt_transform.transform()
    smt_model = smt_transform.destination_model
    operation = MaximizeImpact(**op_configs)
    operation.execute(smt_model)
    result = await get_release_by_values(operation.get_result())
    return JSONResponse(status_code = status.HTTP_200_OK, content = JSONencoder().encode(result))

@router.post('/operation/filter_configs/{network_id}', response_description = 'Filter configs operation')
async def filter_configs(network_id: str, op_configs: dict = {'max_threshold': 10., 'min_threshold': 0., 'limit': 10}):
    dependency_network = await serialize_network(network_id)
    smt_transform = NetworkToSMT(dependency_network, 'mean')
    smt_transform.transform()
    smt_model = smt_transform.destination_model
    operation = FilterConfigs(**op_configs)
    operation.execute(smt_model)
    result = await get_release_by_values(operation.get_result())
    return JSONResponse(status_code = status.HTTP_200_OK, content = JSONencoder().encode(result))