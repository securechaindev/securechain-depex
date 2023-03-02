from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from flamapy.metamodels.dn_metamodel.operations import NetworkInfo
from flamapy.metamodels.smt_metamodel.transformations import NetworkToSMT
from flamapy.metamodels.smt_metamodel.operations import (
    ValidModel,
    NumberOfProducts,
    MaximizeImpact,
    MinimizeImpact,
    FilterConfigs
)

from app.services import get_release_by_count_many

from app.utils import json_encoder

from .serialize_controller import serialize_graph

router = APIRouter()


@router.post(
    '/operation/graph/graph_info/{graph_id}',
    summary='Summarizes graph information',
    response_description='Return graph information'
)
async def graph_info(graph_id: str) -> JSONResponse:
    '''
    Summarizes graph information regarding its dependencies, edges and vulnerabilities:

    - **graph_id**: the id of a graph
    '''
    dependency_graph = await serialize_graph(graph_id)
    # Modificar esta operacion para que devuelva edges como nombre y no constraints
    operation = NetworkInfo()
    operation.execute(dependency_graph)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=json_encoder(operation.get_result())
    )


@router.post(
    '/operation/graph/valid_model/{graph_id}',
    summary='Validates model satisfiability',
    response_description='Return True if valid, False if not'
)
async def valid_file(
    graph_id: str,
    agregator: str,
    file_name: str
) -> JSONResponse:
    '''
    Summarizes graph information regarding its dependencies, edges and vulnerabilities:

    - **graph_id**: the id of a graph
    - **agregator**: agregator function to build the smt model
    - **file_name**: name of requirement file belonging to graph
    '''
    dependency_graph = await serialize_graph(graph_id)
    smt_transform = NetworkToSMT(dependency_graph, agregator)
    smt_transform.transform()
    smt_model = smt_transform.destination_model
    operation = ValidModel(file_name)
    operation.execute(smt_model)
    result = {'is_valid': operation.get_result()}
    return JSONResponse(status_code=status.HTTP_200_OK, content=json_encoder(result))


@router.post(
    '/operation/graph/number_of_products/{graph_id}',
    summary='Count the number of configurations',
    response_description='Return the number of products.'
)
async def number_of_products(
    graph_id: str,
    agregator: str,
    file_name: str
) -> JSONResponse:
    '''
    Count the number of configurations of a graph. Recommendatory to not use in massive graphs:

    - **graph_id**: the id of a graph
    - **agregator**: agregator function to build the smt model
    - **file_name**: name of requirement file belonging to graph
    '''
    dependency_graph = await serialize_graph(graph_id)
    smt_transform = NetworkToSMT(dependency_graph, agregator)
    smt_transform.transform()
    smt_model = smt_transform.destination_model
    operation = NumberOfProducts(file_name)
    operation.execute(smt_model)
    result = {'number_of_products': operation.get_result()}
    return JSONResponse(status_code=status.HTTP_200_OK, content=json_encoder(result))


@router.post(
    '/operation/graph/minimize_impact/{graph_id}',
    summary='Minimize impact of a graph',
    response_description='Return a list of configurations'
)
async def minimize_impact(
    graph_id: str,
    agregator: str,
    file_name: str,
    limit: int
) -> JSONResponse:
    '''
    Return a list of configurations ordered with the minimun posible impact:

    - **graph_id**: the id of a graph
    - **agregator**: agregator function to build the smt model
    - **file_name**: name of requirement file belonging to graph
    - **limit**: the number of configurations to return
    '''
    dependency_graph = await serialize_graph(graph_id)
    smt_transform = NetworkToSMT(dependency_graph, agregator)
    smt_transform.transform()
    smt_model = smt_transform.destination_model
    operation = MinimizeImpact(file_name, limit)
    operation.execute(smt_model)
    result = await get_release_by_count_many(operation.get_result())
    return JSONResponse(status_code=status.HTTP_200_OK, content=json_encoder({'result': result}))


@router.post(
    '/operation/graph/maximize_impact/{graph_id}',
    summary='Maximize impact of a graph',
    response_description='Return a list of configurations'
)
async def maximize_impact(
    graph_id: str,
    agregator: str,
    file_name: str,
    limit: int
) -> JSONResponse:
    '''
    Return a list of configurations ordered with the maximun posible impact:

    - **graph_id**: the id of a graph
    - **agregator**: agregator function to build the smt model
    - **file_name**: name of requirement file belonging to graph
    - **limit**: the number of configurations to return
    '''
    dependency_graph = await serialize_graph(graph_id)
    smt_transform = NetworkToSMT(dependency_graph, agregator)
    smt_transform.transform()
    smt_model = smt_transform.destination_model
    operation = MaximizeImpact(file_name, limit)
    operation.execute(smt_model)
    result = await get_release_by_count_many(operation.get_result())
    return JSONResponse(status_code=status.HTTP_200_OK, content=json_encoder({'result': result}))


@router.post(
    '/operation/graph/filter_configs/{graph_id}',
    summary='Filter configurations of a graph',
    response_description='Return a list of configurations'
)
async def filter_configs(
    graph_id: str,
    agregator: str,
    file_name: str,
    max_threshold: float,
    min_threshold: float,
    limit: int
) -> JSONResponse:
    '''
    Return a list of configurations between a max and min impact:

    - **graph_id**: the id of a graph
    - **agregator**: agregator function to build the smt model
    - **file_name**: name of requirement file belonging to graph
    - **max_threshold**: max impact threshold
    - **min_threshold**: min impact threshold
    - **limit**: the number of configurations to return
    '''
    dependency_graph = await serialize_graph(graph_id)
    smt_transform = NetworkToSMT(dependency_graph, agregator)
    smt_transform.transform()
    smt_model = smt_transform.destination_model
    operation = FilterConfigs(file_name, max_threshold, min_threshold, limit)
    operation.execute(smt_model)
    result = await get_release_by_count_many(operation.get_result())
    return JSONResponse(status_code=status.HTTP_200_OK, content=json_encoder({'result': result}))