from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from flamapy.metamodels.smt_metamodel.operations import (
    ValidModel,
    NumberOfProducts,
    MinimizeImpact,
    MaximizeImpact,
    FilterConfigs
)

from flamapy.metamodels.smt_metamodel.transformations import GraphToSMT
from app.services import (
    read_data_for_smt_transform,
    get_releases_by_counts,
    read_info
)
from app.utils import json_encoder, get_manager

router = APIRouter()

# TODO: Cambiar el nombre 'graph' por 'file' ya que nosotros lanzamos las operaciones sobre ficheros
# de requisitos, no sobre todo el grafo en su conjunto.

@router.post(
    '/operation/file/file_info/{requirement_file_id}',
    summary='Summarizes file information',
    response_description='Return file information'
)
async def file_info(requirement_file_id: str, file_name: str) -> JSONResponse:
    '''
    Summarizes file information regarding its dependencies, edges and vulnerabilities:

    - **file_id**: the id of a file
    '''
    package_manager = await get_manager(file_name)
    graph_info = await read_info(requirement_file_id, package_manager)
    return JSONResponse(status_code=status.HTTP_200_OK, content=json_encoder(graph_info))

@router.post(
    '/operation/file/valid_file/{requirement_file_id}',
    summary='Validates model satisfiability',
    response_description='Return True if valid, False if not'
)
async def valid_file(requirement_file_id: str, file_name: str) -> JSONResponse:
    '''
    Summarizes requirement file graph information regarding its dependencies,
    edges and vulnerabilities:

    - **requirement_file_id**: the id of a requirement file
    - **file_name**: name of requirement file belonging to a graph
    '''
    package_manager = await get_manager(file_name)
    graph_data = await read_data_for_smt_transform(requirement_file_id, package_manager)
    smt_transform = GraphToSMT(graph_data, file_name, package_manager, 'mean')
    smt_transform.transform()
    smt_model = smt_transform.destination_model
    operation = ValidModel()
    operation.execute(smt_model)
    result = {'is_valid': operation.get_result()}
    return JSONResponse(status_code=status.HTTP_200_OK, content=json_encoder(result))


@router.post(
    '/operation/file/number_of_configurations/{requirement_file_id}',
    summary='Count the number of configurations',
    response_description='Return the number of configurations.'
)
async def number_of_configurations(requirement_file_id: str, file_name: str) -> JSONResponse:
    '''
    Count the number of configurations of a file. Recommendatory to not use in massive graphs:

    - **requirement_file_id**: the id of a requirement file
    - **file_name**: name of requirement file belonging to graph
    '''
    package_manager = await get_manager(file_name)
    graph_data = await read_data_for_smt_transform(requirement_file_id, package_manager)
    smt_transform = GraphToSMT(graph_data, file_name, package_manager, 'mean')
    smt_transform.transform()
    smt_model = smt_transform.destination_model
    operation = NumberOfProducts()
    operation.execute(smt_model)
    result = {'number_of_products': operation.get_result()}
    return JSONResponse(status_code=status.HTTP_200_OK, content=json_encoder(result))


@router.post(
    '/operation/file/minimize_impact/{requirement_file_id}',
    summary='Minimize impact of a graph',
    response_description='Return a list of configurations'
)
async def minimize_impact(requirement_file_id: str, agregator: str, file_name: str, limit: int) -> JSONResponse:
    '''
    Return a list of configurations of a file ordered with the minimun posible impact:

    - **requirement_file_id**: the id of a requirement file
    - **agregator**: agregator function to build the smt model ('mean' or 'weighted_mean')
    - **file_name**: name of requirement file belonging to graph
    - **limit**: the number of configurations to return
    '''
    package_manager = await get_manager(file_name)
    graph_data = await read_data_for_smt_transform(requirement_file_id, package_manager)
    smt_transform = GraphToSMT(graph_data, file_name, package_manager, agregator)
    smt_transform.transform()
    smt_model = smt_transform.destination_model
    operation = MinimizeImpact(limit)
    operation.execute(smt_model)
    result = await get_releases_by_counts(operation.get_result(), package_manager)
    return JSONResponse(status_code=status.HTTP_200_OK, content=json_encoder({'result': result}))


@router.post(
    '/operation/file/maximize_impact/{requirement_file_id}',
    summary='Maximize impact of a graph',
    response_description='Return a list of configurations'
)
async def maximize_impact(requirement_file_id: str, agregator: str, file_name: str, limit: int) -> JSONResponse:
    '''
    Return a list of configurations of a file ordered with the maximun posible impact:

    - **requirement_file_id**: the id of a requirement file
    - **agregator**: agregator function to build the smt model ('mean' or 'weighted_mean')
    - **file_name**: name of requirement file belonging to graph
    - **limit**: the number of configurations to return
    '''
    package_manager = await get_manager(file_name)
    graph_data = await read_data_for_smt_transform(requirement_file_id, package_manager)
    smt_transform = GraphToSMT(graph_data, file_name, package_manager, agregator)
    smt_transform.transform()
    smt_model = smt_transform.destination_model
    operation = MaximizeImpact(limit)
    operation.execute(smt_model)
    result = await get_releases_by_counts(operation.get_result(), package_manager)
    return JSONResponse(status_code=status.HTTP_200_OK, content=json_encoder({'result': result}))


@router.post(
    '/operation/file/filter_configs/{requirement_file_id}',
    summary='Filter configurations of a graph',
    response_description='Return a list of configurations'
)
async def filter_configs(requirement_file_id: str, agregator: str, file_name: str, max_threshold: float, min_threshold: float, limit: int) -> JSONResponse:
    '''
    Return a list of configurations of a file between a max and min impact:

    - **requirement_file_id**: the id of a requirement file
    - **agregator**: agregator function to build the smt model ('mean' or 'weighted_mean')
    - **file_name**: name of requirement file belonging to graph
    - **max_threshold**: max impact threshold
    - **min_threshold**: min impact threshold
    - **limit**: the number of configurations to return
    '''
    package_manager = await get_manager(file_name)
    graph_data = await read_data_for_smt_transform(requirement_file_id, package_manager)
    smt_transform = GraphToSMT(graph_data, file_name, package_manager, agregator)
    smt_transform.transform()
    smt_model = smt_transform.destination_model
    operation = FilterConfigs(max_threshold, min_threshold, limit)
    operation.execute(smt_model)
    result = await get_releases_by_counts(operation.get_result(), package_manager)
    return JSONResponse(status_code=status.HTTP_200_OK, content=json_encoder({'result': result}))