from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from flamapy.metamodels.smt_metamodel.operations import (
    FilterConfigs,
    # MinimizeImpact,
    MaximizeImpact,
    ValidModel,
    NumberOfProducts
)
from app.controllers.minimize import MinimizeImpact
from app.controllers.graph_to_smt2 import GraphToSMT

from app.services import (
    read_data_for_smt_transform,
    read_graph_for_info_operation,
    read_releases_by_counts,
)
from app.utils import get_manager, json_encoder
import time
router = APIRouter()


@router.post(
    "/operation/file/file_info/{requirement_file_id}",
    summary="Summarizes file information",
    response_description="Return file information",
)
async def file_info(requirement_file_id: str, file_name: str) -> JSONResponse:
    """
    Summarizes file information regarding its dependencies, edges and vulnerabilities:

    - **requirement_file_id**: the id of a requirement file
    - **file_name**: name of requirement file belonging to a graph
    """
    package_manager = await get_manager(file_name)
    graph_info = await read_graph_for_info_operation(
        requirement_file_id, package_manager
    )
    return JSONResponse(
        status_code=status.HTTP_200_OK, content=json_encoder(graph_info)
    )


@router.post(
    "/operation/file/valid_file/{requirement_file_id}",
    summary="Validates model satisfiability",
    response_description="Return True if valid, False if not",
)
async def valid_file(requirement_file_id: str, file_name: str, max_level: int) -> JSONResponse:
    """
    Summarizes requirement file graph information regarding its dependencies,
    edges and vulnerabilities:

    - **requirement_file_id**: the id of a requirement file
    - **file_name**: name of requirement file belonging to a graph
    - **max_level**: the depth of the graph to be analysed
    """
    package_manager = await get_manager(file_name)
    graph_data = await read_data_for_smt_transform(
        requirement_file_id, package_manager, max_level
    )
    smt_transform = GraphToSMT(graph_data, file_name, package_manager, "mean")
    smt_transform.transform()
    smt_model = smt_transform.destination_model
    operation = ValidModel()
    operation.execute(smt_model)
    result = {"is_valid": operation.get_result()}
    return JSONResponse(status_code=status.HTTP_200_OK, content=json_encoder(result))


@router.post(
    "/operation/file/number_of_configurations/{requirement_file_id}",
    summary="Count the number of configurations",
    response_description="Return the number of configurations.",
)
async def number_of_configurations(
    requirement_file_id: str, file_name: str, max_level: int
) -> JSONResponse:
    """
    Count the number of configurations of a file. Recommendatory to not use in massive graphs:

    - **requirement_file_id**: the id of a requirement file
    - **file_name**: name of requirement file belonging to graph
    - **max_level**: the depth of the graph to be analysed
    """
    package_manager = await get_manager(file_name)
    graph_data = await read_data_for_smt_transform(
        requirement_file_id, package_manager, max_level
    )
    smt_transform = GraphToSMT(graph_data, file_name, package_manager, "mean")
    smt_transform.transform()
    smt_model = smt_transform.destination_model
    operation = NumberOfProducts()
    operation.execute(smt_model)
    result = {"number_of_products": operation.get_result()}
    return JSONResponse(status_code=status.HTTP_200_OK, content=json_encoder(result))


@router.post(
    "/operation/file/minimize_impact/{requirement_file_id}",
    summary="Minimize impact of a graph",
    response_description="Return a list of configurations",
)
async def minimize_impact(
    requirement_file_id: str, agregator: str, file_name: str, limit: int, max_level: int
) -> JSONResponse:
    """
    Return a list of configurations of a file ordered with the minimun posible impact:

    - **requirement_file_id**: the id of a requirement file
    - **agregator**: agregator function to build the smt model ('mean' or 'weighted_mean')
    - **file_name**: name of requirement file belonging to graph
    - **limit**: the number of configurations to return
    - **max_level**: the depth of the graph to be analysed
    """
    package_manager = await get_manager(file_name)
    begin = time.time()
    graph_data = await read_data_for_smt_transform(
        requirement_file_id, package_manager, max_level
    )
    print("Tiempo de Extracción: " + str(time.time()-begin))
    begin = time.time()
    smt_transform = GraphToSMT(graph_data, file_name, package_manager, agregator)
    smt_transform.transform()
    print("Tiempo de Transformación: " + str(time.time()-begin))
    begin = time.time()
    operation = MinimizeImpact(limit)
    operation.execute(smt_transform.destination_model)
    print("Tiempo de Ejecución de la Operación: " + str(time.time()-begin))
    result = await read_releases_by_counts(operation.get_result(), package_manager)
    return JSONResponse(
        status_code=status.HTTP_200_OK, content=json_encoder({"result": result})
    )


@router.post(
    "/operation/file/maximize_impact/{requirement_file_id}",
    summary="Maximize impact of a graph",
    response_description="Return a list of configurations",
)
async def maximize_impact(
    requirement_file_id: str, agregator: str, file_name: str, limit: int, max_level: int
) -> JSONResponse:
    """
    Return a list of configurations of a file ordered with the maximun posible impact:

    - **requirement_file_id**: the id of a requirement file
    - **agregator**: agregator function to build the smt model ('mean' or 'weighted_mean')
    - **file_name**: name of requirement file belonging to graph
    - **limit**: the number of configurations to return
    - **max_level**: the depth of the graph to be analysed
    """
    package_manager = await get_manager(file_name)
    graph_data = await read_data_for_smt_transform(
        requirement_file_id, package_manager, max_level
    )
    smt_transform = GraphToSMT(graph_data, file_name, package_manager, agregator)
    smt_transform.transform()
    smt_model = smt_transform.destination_model
    operation = MaximizeImpact(limit)
    operation.execute(smt_model)
    result = await read_releases_by_counts(operation.get_result(), package_manager)
    return JSONResponse(
        status_code=status.HTTP_200_OK, content=json_encoder({"result": result})
    )


@router.post(
    "/operation/file/filter_configs/{requirement_file_id}",
    summary="Filter configurations of a graph",
    response_description="Return a list of configurations",
)
async def filter_configs(
    requirement_file_id: str,
    agregator: str,
    file_name: str,
    max_threshold: float,
    min_threshold: float,
    limit: int,
    max_level: int,
) -> JSONResponse:
    """
    Return a list of configurations of a file between a max and min impact:

    - **requirement_file_id**: the id of a requirement file
    - **agregator**: agregator function to build the smt model ('mean' or 'weighted_mean')
    - **file_name**: name of requirement file belonging to graph
    - **max_threshold**: max impact threshold
    - **min_threshold**: min impact threshold
    - **limit**: the number of configurations to return
    - **max_level**: the depth of the graph to be analysed
    """
    package_manager = await get_manager(file_name)
    graph_data = await read_data_for_smt_transform(
        requirement_file_id, package_manager, max_level
    )
    smt_transform = GraphToSMT(graph_data, file_name, package_manager, agregator)
    smt_transform.transform()
    smt_model = smt_transform.destination_model
    operation = FilterConfigs(max_threshold, min_threshold, limit)
    operation.execute(smt_model)
    result = await read_releases_by_counts(operation.get_result(), package_manager)
    return JSONResponse(
        status_code=status.HTTP_200_OK, content=json_encoder({"result": result})
    )
