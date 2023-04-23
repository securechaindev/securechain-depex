from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from flamapy.metamodels.smt_metamodel.transformations import GraphToSMT
from flamapy.metamodels.smt_metamodel.operations import (
    ValidModel,
    NumberOfProducts,
    MinimizeImpact,
    MaximizeImpact,
    FilterConfigs
)

from app.services import read_data_for_smt_transform, get_releases_by_counts

from app.utils import json_encoder

router = APIRouter()


# @router.post(
#     '/operation/graph/graph_info/{graph_id}',
#     summary='Summarizes graph information',
#     response_description='Return graph information'
# )
# async def graph_info(graph_id: str) -> JSONResponse:
#     '''
#     Summarizes graph information regarding its dependencies, edges and vulnerabilities:

#     - **graph_id**: the id of a graph
#     '''
#     dependency_graph = await serialize_graph(graph_id)
#     # Modificar esta operacion para que devuelva edges como nombre y no constraints
#     operation = NetworkInfo()
#     operation.execute(dependency_graph)
#     return JSONResponse(
#         status_code=status.HTTP_200_OK,
#         content=json_encoder(operation.get_result())
#     )


@router.post(
    '/operation/graph/valid_file/{requirement_file_id}',
    summary='Validates model satisfiability',
    response_description='Return True if valid, False if not'
)
async def valid_file(
    requirement_file_id: str,
    file_name: str
) -> JSONResponse:
    '''
    Summarizes requirement file graph information regarding its dependencies,
    edges and vulnerabilities:

    - **requirement_file_id**: the id of a requirement file
    - **file_name**: name of requirement file belonging to a graph
    '''
    graph_data = await read_data_for_smt_transform(requirement_file_id)
    smt_transform = GraphToSMT(graph_data, file_name, 'mean')
    smt_transform.transform()
    smt_model = smt_transform.destination_model
    operation = ValidModel()
    operation.execute(smt_model)
    result = {'is_valid': operation.get_result()}
    return JSONResponse(status_code=status.HTTP_200_OK, content=json_encoder(result))


@router.post(
    '/operation/graph/number_of_configurations/{requirement_file_id}',
    summary='Count the number of configurations',
    response_description='Return the number of configurations.'
)
async def number_of_configurations(
    requirement_file_id: str,
    file_name: str
) -> JSONResponse:
    '''
    Count the number of configurations of a graph. Recommendatory to not use in massive graphs:

    - **requirement_file_id**: the id of a requirement file
    - **file_name**: name of requirement file belonging to graph
    '''
    graph_data = await read_data_for_smt_transform(requirement_file_id)
    smt_transform = GraphToSMT(graph_data, file_name, 'mean')
    smt_transform.transform()
    smt_model = smt_transform.destination_model
    operation = NumberOfProducts()
    operation.execute(smt_model)
    result = {'number_of_products': operation.get_result()}
    return JSONResponse(status_code=status.HTTP_200_OK, content=json_encoder(result))


@router.post(
    '/operation/graph/minimize_impact/{requirement_file_id}',
    summary='Minimize impact of a graph',
    response_description='Return a list of configurations'
)
async def minimize_impact(
    requirement_file_id: str,
    agregator: str,
    file_name: str,
    limit: int
) -> JSONResponse:
    '''
    Return a list of configurations ordered with the minimun posible impact:

    - **requirement_file_id**: the id of a requirement file
    - **agregator**: agregator function to build the smt model ('mean' or 'weighted_mean')
    - **file_name**: name of requirement file belonging to graph
    - **limit**: the number of configurations to return
    '''
    graph_data = await read_data_for_smt_transform(requirement_file_id)
    smt_transform = GraphToSMT(graph_data, file_name, agregator)
    smt_transform.transform()
    smt_model = smt_transform.destination_model
    operation = MinimizeImpact(limit)
    operation.execute(smt_model)
    result = await get_releases_by_counts(operation.get_result())
    return JSONResponse(status_code=status.HTTP_200_OK, content=json_encoder({'result': result}))


@router.post(
    '/operation/graph/maximize_impact/{requirement_file_id}',
    summary='Maximize impact of a graph',
    response_description='Return a list of configurations'
)
async def maximize_impact(
    requirement_file_id: str,
    agregator: str,
    file_name: str,
    limit: int
) -> JSONResponse:
    '''
    Return a list of configurations ordered with the maximun posible impact:

    - **requirement_file_id**: the id of a requirement file
    - **agregator**: agregator function to build the smt model ('mean' or 'weighted_mean')
    - **file_name**: name of requirement file belonging to graph
    - **limit**: the number of configurations to return
    '''
    graph_data = await read_data_for_smt_transform(requirement_file_id)
    smt_transform = GraphToSMT(graph_data, file_name, agregator)
    smt_transform.transform()
    smt_model = smt_transform.destination_model
    operation = MaximizeImpact(limit)
    operation.execute(smt_model)
    result = await get_releases_by_counts(operation.get_result())
    return JSONResponse(status_code=status.HTTP_200_OK, content=json_encoder({'result': result}))


@router.post(
    '/operation/graph/filter_configs/{requirement_file_id}',
    summary='Filter configurations of a graph',
    response_description='Return a list of configurations'
)
async def filter_configs(
    requirement_file_id: str,
    agregator: str,
    file_name: str,
    max_threshold: float,
    min_threshold: float,
    limit: int
) -> JSONResponse:
    '''
    Return a list of configurations between a max and min impact:

    - **requirement_file_id**: the id of a requirement file
    - **agregator**: agregator function to build the smt model ('mean' or 'weighted_mean')
    - **file_name**: name of requirement file belonging to graph
    - **max_threshold**: max impact threshold
    - **min_threshold**: min impact threshold
    - **limit**: the number of configurations to return
    '''
    graph_data = await read_data_for_smt_transform(requirement_file_id)
    smt_transform = GraphToSMT(graph_data, file_name, agregator)
    smt_transform.transform()
    smt_model = smt_transform.destination_model
    operation = FilterConfigs(max_threshold, min_threshold, limit)
    operation.execute(smt_model)
    result = await get_releases_by_counts(operation.get_result())
    return JSONResponse(status_code=status.HTTP_200_OK, content=json_encoder({'result': result}))