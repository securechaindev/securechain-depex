from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from flamapy.metamodels.smt_metamodel.transformations import NetworkToSMT
from flamapy.metamodels.smt_metamodel.operations import (
    ValidConfig,
    CompleteConfig,
    ConfigByImpact
)

from app.services import (
    get_release_by_values,
    get_count_by_values
)
from app.utils import json_encoder

from .serialize_controller import serialize_graph

router = APIRouter()


@router.post(
    '/operation/config/valid_config/{graph_id}',
    summary='Validates a configuration',
    response_description='Return True if valid, False if not'
)
async def valid_config(
    graph_id: str,
    agregator: str,
    file_name: str,
    config: dict[str, str]
) -> JSONResponse:
    '''
    Validates a configuration satisfiability into a graph by the constraints over dependencies:

    - **graph_id**: the id of a graph
    - **agregator**: agregator function to build the smt model
    - **file_name**: name of requirement file belonging to graph
    - **config**: configuration containing the name of the dependency and the version to be chosen
    '''
    dependency_graph = await serialize_graph(graph_id)
    smt_transform = NetworkToSMT(dependency_graph, agregator)
    smt_transform.transform()
    smt_model = smt_transform.destination_model
    operation = ValidConfig(file_name, await get_count_by_values(config))
    operation.execute(smt_model)
    result = {'is_valid': operation.get_result()}
    return JSONResponse(status_code=status.HTTP_200_OK, content=json_encoder(result))


@router.post(
    '/operation/complete_config/{graph_id}',
    response_description='Complete configuration operation'
)
async def complete_config(
    graph_id: str,
    agregator: str,
    file_name: str,
    config: dict[str, str]
) -> JSONResponse:
    dependency_graph = await serialize_graph(graph_id)
    smt_transform = NetworkToSMT(dependency_graph, agregator)
    smt_transform.transform()
    smt_model = smt_transform.destination_model
    operation = CompleteConfig(file_name, await get_count_by_values(config))
    operation.execute(smt_model)
    result = await get_release_by_values(operation.get_result())
    return JSONResponse(status_code=status.HTTP_200_OK, content=json_encoder({'result': result}))


@router.post(
    '/operation/config_by_impact/{graph_id}',
    response_description='Get a configuration by impact operation'
)
async def config_by_impact(
    graph_id: str,
    agregator: str,
    file_name: str,
    impact: float
) -> JSONResponse:
    dependency_graph = await serialize_graph(graph_id)
    smt_transform = NetworkToSMT(dependency_graph, agregator)
    smt_transform.transform()
    smt_model = smt_transform.destination_model
    operation = ConfigByImpact(file_name, impact)
    operation.execute(smt_model)
    result = await get_release_by_values(operation.get_result())
    return JSONResponse(status_code=status.HTTP_200_OK, content=json_encoder({'result': result}))