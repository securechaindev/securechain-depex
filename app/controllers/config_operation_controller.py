from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from flamapy.metamodels.smt_metamodel.operations import (
    ValidConfig,
    CompleteConfig,
    ConfigByImpact
)

from app.controllers.transform import GraphToSMT

from app.services import (
    read_data_for_smt_transform,
    get_counts_by_releases,
    get_releases_by_counts
)

from app.utils import json_encoder, get_manager

router = APIRouter()


@router.post(
    '/operation/config/valid_config/{requirement_file_id}',
    summary='Validates a configuration',
    response_description='Return True if valid, False if not'
)
async def valid_config(
    requirement_file_id: str,
    agregator: str,
    file_name: str,
    config: dict[str, str]
) -> JSONResponse:
    '''
    Validates a configuration satisfiability into a graph by the constraints over dependencies:

    - **requirement_file_id**: the id of a requirement file
    - **agregator**: agregator function to build the smt model ('mean' or 'weighted_mean')
    - **file_name**: name of requirement file belonging to graph
    - **config**: configuration containing the name of the dependency and the version to be chosen
    '''
    package_manager = await get_manager(file_name)
    graph_data = await read_data_for_smt_transform(requirement_file_id, package_manager)
    smt_transform = GraphToSMT(graph_data, file_name, package_manager, agregator)
    smt_transform.transform()
    smt_model = smt_transform.destination_model
    operation = ValidConfig(await get_counts_by_releases(config, package_manager))
    operation.execute(smt_model)
    result = {'is_valid': operation.get_result()}
    return JSONResponse(status_code=status.HTTP_200_OK, content=json_encoder(result))


@router.post(
    '/operation/config/complete_config/{requirement_file_id}',
    summary='Complete a configuration',
    response_description='Return a configuration of versions'
)
async def complete_config(
    requirement_file_id: str,
    agregator: str,
    file_name: str,
    config: dict[str, str]
) -> JSONResponse:
    '''
    Complete a partial configuration with the minimun posible impact:

    - **requirement_file_id**: the id of a requirement file
    - **agregator**: agregator function to build the smt model ('mean' or 'weighted_mean')
    - **file_name**: name of requirement file belonging to graph
    - **config**: partial configuration containing the name and the version of each dependency
    '''
    package_manager = await get_manager(file_name)
    graph_data = await read_data_for_smt_transform(requirement_file_id, package_manager)
    smt_transform = GraphToSMT(graph_data, file_name, package_manager, agregator)
    smt_transform.transform()
    smt_model = smt_transform.destination_model
    operation = CompleteConfig(await get_counts_by_releases(config, package_manager))
    operation.execute(smt_model)
    result = await get_releases_by_counts(operation.get_result(), package_manager)
    return JSONResponse(status_code=status.HTTP_200_OK, content=json_encoder({'result': result}))


@router.post(
    '/operation/config/config_by_impact/{graph_id}',
    summary='Get a configuration by impact operation',
    response_description='Return a configuration of versions'
)
async def config_by_impact(
    requirement_file_id: str,
    agregator: str,
    file_name: str,
    impact: float
) -> JSONResponse:
    '''
    Return a configuration witn an impact as close as possible to the given impact:

    - **requirement_file_id**: the id of a requirement file
    - **agregator**: agregator function to build the smt model ('mean' or 'weighted_mean')
    - **file_name**: name of requirement file belonging to graph
    - **impact**: impact number between 0 and 10
    '''
    package_manager = await get_manager(file_name)
    graph_data = await read_data_for_smt_transform(requirement_file_id, package_manager)
    smt_transform = GraphToSMT(graph_data, file_name, package_manager, agregator)
    smt_transform.transform()
    smt_model = smt_transform.destination_model
    operation = ConfigByImpact(impact)
    operation.execute(smt_model)
    result = await get_releases_by_counts(operation.get_result(), package_manager)
    return JSONResponse(status_code=status.HTTP_200_OK, content=json_encoder({'result': result}))