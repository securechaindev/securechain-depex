from fastapi import APIRouter, Path, Query, status
from fastapi.responses import JSONResponse
from flamapy.metamodels.smt_metamodel.operations import (
    FilterConfigs,
    MaximizeImpact,
    MinimizeImpact,
    NumberOfProducts,
    ValidModel,
)
from flamapy.metamodels.smt_metamodel.transformations import GraphToSMT
from typing_extensions import Annotated

from app.models import Agregator, PackageManager
from app.services import (
    read_data_for_smt_transform,
    read_graph_for_info_operation,
    read_releases_by_counts,
)
from app.utils import json_encoder

router = APIRouter()

@router.post(
    "/operation/file/file_info/{requirement_file_id}",
    summary="Summarizes file information",
    response_description="Return file information",
)
async def file_info(
    requirement_file_id: Annotated[str, Path(pattern="^4:[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}:[0-9]+$")],
    max_level: Annotated[int, Query(ge=-1)],
    package_manager: PackageManager
) -> JSONResponse:
    """
    Summarizes file information regarding its dependencies, edges and vulnerabilities:

    - **requirement_file_id**: the id of a requirement file
    - **max_level**: the depth of the graph to be analysed
    - **package_manager**: package manager of the requirement file
    """
    graph_info = await read_graph_for_info_operation(
        requirement_file_id, package_manager, max_level
    )
    return JSONResponse(
        status_code=status.HTTP_200_OK, content=json_encoder(graph_info)
    )


@router.post(
    "/operation/file/valid_file/{requirement_file_id}",
    summary="Validates model satisfiability",
    response_description="Return True if valid, False if not",
)
async def valid_file(
    requirement_file_id: Annotated[str, Path(pattern="^4:[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}:[0-9]+$")],
    max_level: Annotated[int, Query(ge=-1)],
    package_manager: PackageManager
) -> JSONResponse:
    """
    Summarizes requirement file graph information regarding its dependencies,
    edges and vulnerabilities:

    - **requirement_file_id**: the id of a requirement file
    - **max_level**: the depth of the graph to be analysed
    - **package_manager**: package manager of the requirement file
    """
    graph_data = await read_data_for_smt_transform(
        requirement_file_id, package_manager, max_level
    )
    if graph_data["name"] is not None:
        smt_transform = GraphToSMT(graph_data, package_manager, "mean")
        smt_transform.transform()
        smt_model = smt_transform.destination_model
        operation = ValidModel()
        operation.execute(smt_model)
        result = {"is_valid": operation.get_result()}
        return JSONResponse(status_code=status.HTTP_200_OK, content=json_encoder(result))
    else:
        return JSONResponse(status_code=status.HTTP_200_OK, content=json_encoder({"message": "The requirement file don't have dependencies"}))


@router.post(
    "/operation/file/number_of_configurations/{requirement_file_id}",
    summary="Count the number of configurations",
    response_description="Return the number of configurations.",
)
async def number_of_configurations(
    requirement_file_id: Annotated[str, Path(pattern="^4:[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}:[0-9]+$")],
    max_level: Annotated[int, Query(ge=-1)],
    package_manager: PackageManager
) -> JSONResponse:
    """
    Count the number of configurations of a file. Recommendatory to not use in massive graphs:

    - **requirement_file_id**: the id of a requirement file
    - **max_level**: the depth of the graph to be analysed
    - **package_manager**: package manager of the requirement file
    """
    graph_data = await read_data_for_smt_transform(
        requirement_file_id, package_manager, max_level
    )
    if graph_data["name"] is not None:
        smt_transform = GraphToSMT(graph_data, package_manager, "mean")
        smt_transform.transform()
        smt_model = smt_transform.destination_model
        operation = NumberOfProducts()
        operation.execute(smt_model)
        result = {"number_of_products": operation.get_result()}
        return JSONResponse(status_code=status.HTTP_200_OK, content=json_encoder(result))
    else:
        return JSONResponse(status_code=status.HTTP_200_OK, content=json_encoder({"message": "The requirement file don't have dependencies"}))


@router.post(
    "/operation/file/minimize_impact/{requirement_file_id}",
    summary="Minimize impact of a graph",
    response_description="Return a list of configurations",
)
async def minimize_impact(
    requirement_file_id: Annotated[str, Path(pattern="^4:[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}:[0-9]+$")],
    limit: Annotated[int, Query(ge=1)],
    max_level: Annotated[int, Query(ge=-1)],
    package_manager: PackageManager,
    agregator: Agregator
) -> JSONResponse:
    """
    Return a list of configurations of a file ordered with the minimun posible impact:

    - **requirement_file_id**: the id of a requirement file
    - **limit**: the number of configurations to return
    - **max_level**: the depth of the graph to be analysed
    - **package_manager**: package manager of the requirement file
    - **agregator**: agregator function to build the smt model
    """
    graph_data = await read_data_for_smt_transform(
        requirement_file_id, package_manager, max_level
    )
    if graph_data["name"] is not None:
        smt_transform = GraphToSMT(graph_data, package_manager, agregator)
        smt_transform.transform()
        operation = MinimizeImpact(limit)
        operation.execute(smt_transform.destination_model)
        result = await read_releases_by_counts(operation.get_result(), package_manager)
        return JSONResponse(
            status_code=status.HTTP_200_OK, content=json_encoder({"result": result})
        )
    else:
        return JSONResponse(status_code=status.HTTP_200_OK, content=json_encoder({"message": "The requirement file don't have dependencies"}))


@router.post(
    "/operation/file/maximize_impact/{requirement_file_id}",
    summary="Maximize impact of a graph",
    response_description="Return a list of configurations",
)
async def maximize_impact(
    requirement_file_id: Annotated[str, Path(pattern="^4:[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}:[0-9]+$")],
    limit: Annotated[int, Query(ge=1)],
    max_level: Annotated[int, Query(ge=-1)],
    package_manager: PackageManager,
    agregator: Agregator
) -> JSONResponse:
    """
    Return a list of configurations of a file ordered with the maximun posible impact:

    - **requirement_file_id**: the id of a requirement file
    - **limit**: the number of configurations to return
    - **max_level**: the depth of the graph to be analysed
    - **package_manager**: package manager of the requirement file
    - **agregator**: agregator function to build the smt model
    """
    graph_data = await read_data_for_smt_transform(
        requirement_file_id, package_manager, max_level
    )
    if graph_data["name"] is not None:
        smt_transform = GraphToSMT(graph_data, package_manager, agregator)
        smt_transform.transform()
        smt_model = smt_transform.destination_model
        operation = MaximizeImpact(limit)
        operation.execute(smt_model)
        result = await read_releases_by_counts(operation.get_result(), package_manager)
        return JSONResponse(
            status_code=status.HTTP_200_OK, content=json_encoder({"result": result})
        )
    else:
        return JSONResponse(status_code=status.HTTP_200_OK, content=json_encoder({"message": "The requirement file don't have dependencies"}))


@router.post(
    "/operation/file/filter_configs/{requirement_file_id}",
    summary="Filter configurations of a graph",
    response_description="Return a list of configurations",
)
async def filter_configs(
    requirement_file_id: Annotated[str, Path(pattern="^4:[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}:[0-9]+$")],
    max_threshold: Annotated[float, Query(ge=0, le=10)],
    min_threshold: Annotated[float, Query(ge=0, le=10)],
    limit: Annotated[int, Query(ge=1)],
    max_level: Annotated[int, Query(ge=-1)],
    package_manager: PackageManager,
    agregator: Agregator
) -> JSONResponse:
    """
    Return a list of configurations of a file between a max and min impact:

    - **requirement_file_id**: the id of a requirement file
    - **max_threshold**: max impact floating threshold between 0.0 and 10.0
    - **min_threshold**: min impact floating threshold between 0.0 and 10.0
    - **limit**: the number of configurations to return
    - **max_level**: the depth of the graph to be analysed
    - **package_manager**: package manager of the requirement file
    - **agregator**: agregator function to build the smt model
    """
    graph_data = await read_data_for_smt_transform(
        requirement_file_id, package_manager, max_level
    )
    if graph_data["name"] is not None:
        smt_transform = GraphToSMT(graph_data, package_manager, agregator)
        smt_transform.transform()
        smt_model = smt_transform.destination_model
        operation = FilterConfigs(max_threshold, min_threshold, limit)
        operation.execute(smt_model)
        result = await read_releases_by_counts(operation.get_result(), package_manager)
        return JSONResponse(
            status_code=status.HTTP_200_OK, content=json_encoder({"result": result})
        )
    else:
        return JSONResponse(status_code=status.HTTP_200_OK, content=json_encoder({"message": "The requirement file don't have dependencies"}))
