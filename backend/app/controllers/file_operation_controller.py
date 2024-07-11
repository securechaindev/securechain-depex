from typing import Annotated

from fastapi import APIRouter, Body, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from flamapy.metamodels.smt_metamodel.operations import (
    FilterConfigs,
    MaximizeImpact,
    MinimizeImpact,
    ValidModel,
)
from flamapy.metamodels.smt_metamodel.transformations import GraphToSMT
from pytz import UTC

from app.models import (
    FileInfoRequest,
    FilterConfigsRequest,
    MinMaxImpactRequest,
    ValidFileRequest,
)
from app.services import (
    read_data_for_smt_transform,
    read_graph_for_info_operation,
    read_releases_by_counts,
    read_smt_text,
    replace_smt_text,
)
from app.utils import json_encoder

router = APIRouter()

@router.post(
    "/operation/file/file_info",
    summary="Summarizes file information",
    response_description="Return file information",
)
async def file_info(
    FileInfoRequest: Annotated[FileInfoRequest, Body()]
) -> JSONResponse:
    """
    Summarizes file information regarding its dependencies, edges and vulnerabilities:

    - **requirement_file_id**: the id of a requirement file
    - **max_level**: the depth of the graph to be analysed
    - **package_manager**: package manager of the requirement file
    """
    graph_info = await read_graph_for_info_operation(jsonable_encoder(FileInfoRequest))
    return JSONResponse(
        status_code=status.HTTP_200_OK, content=json_encoder(graph_info)
    )


@router.post(
    "/operation/file/valid_file",
    summary="Validates model satisfiability",
    response_description="Return True if valid, False if not",
)
async def valid_file(
    valid_file_request: Annotated[ValidFileRequest, Body()]
) -> JSONResponse:
    """
    Summarizes requirement file graph information regarding its dependencies,
    edges and vulnerabilities:

    - **requirement_file_id**: the id of a requirement file
    - **max_level**: the depth of the graph to be analysed
    - **package_manager**: package manager of the requirement file
    """
    print(jsonable_encoder(valid_file_request))
    graph_data = await read_data_for_smt_transform(jsonable_encoder(valid_file_request))
    smt_id = f"{valid_file_request.requirement_file_id}-{valid_file_request.max_level}"
    if graph_data["name"] is not None:
        smt_transform = GraphToSMT(graph_data, valid_file_request.package_manager, "mean")
        smt_text = await read_smt_text(smt_id)
        if smt_text is not None and smt_text["moment"].replace(tzinfo=UTC) > graph_data[
            "moment"
        ].replace(tzinfo=UTC):
            smt_transform.convert(smt_text["text"])
        else:
            model_text = smt_transform.transform()
            await replace_smt_text(smt_id, model_text)
        operation = ValidModel()
        operation.execute(smt_transform.destination_model)
        result = {"is_valid": operation.get_result(), "message": "success"}
        return JSONResponse(
            status_code=status.HTTP_200_OK, content=json_encoder(result)
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=json_encoder(
                {"message": "no_dependencies"}
            ),
        )


@router.post(
    "/operation/file/minimize_impact",
    summary="Minimize impact of a graph",
    response_description="Return a list of configurations",
)
async def minimize_impact(
    MinMaxImpactRequest: Annotated[MinMaxImpactRequest, Body()]
) -> JSONResponse:
    """
    Return a list of configurations of a file ordered with the minimun posible impact:

    - **requirement_file_id**: the id of a requirement file
    - **limit**: the number of configurations to return
    - **max_level**: the depth of the graph to be analysed
    - **package_manager**: package manager of the requirement file
    - **agregator**: agregator function to build the smt model
    """
    graph_data = await read_data_for_smt_transform(jsonable_encoder(MinMaxImpactRequest))
    smt_id = f"{MinMaxImpactRequest.requirement_file_id}-{MinMaxImpactRequest.max_level}"
    if graph_data["name"] is not None:
        smt_transform = GraphToSMT(graph_data, MinMaxImpactRequest.package_manager, MinMaxImpactRequest.agregator)
        smt_text = await read_smt_text(smt_id)
        if smt_text is not None and smt_text["moment"].replace(tzinfo=UTC) > graph_data[
            "moment"
        ].replace(tzinfo=UTC):
            smt_transform.convert(smt_text["text"])
        else:
            model_text = smt_transform.transform()
            await replace_smt_text(smt_id, model_text)
        operation = MinimizeImpact(MinMaxImpactRequest.limit)
        operation.execute(smt_transform.destination_model)
        result = await read_releases_by_counts(operation.get_result(), MinMaxImpactRequest.package_manager)
        return JSONResponse(
            status_code=status.HTTP_200_OK, content=json_encoder({"result": result, "message": "success"})
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=json_encoder(
                {"message": "no_dependencies"}
            ),
        )


@router.post(
    "/operation/file/maximize_impact",
    summary="Maximize impact of a graph",
    response_description="Return a list of configurations",
)
async def maximize_impact(
    MinMaxImpactRequest: Annotated[MinMaxImpactRequest, Body()]
) -> JSONResponse:
    """
    Return a list of configurations of a file ordered with the maximun posible impact:

    - **requirement_file_id**: the id of a requirement file
    - **limit**: the number of configurations to return
    - **max_level**: the depth of the graph to be analysed
    - **package_manager**: package manager of the requirement file
    - **agregator**: agregator function to build the smt model
    """
    graph_data = await read_data_for_smt_transform(jsonable_encoder(MinMaxImpactRequest))
    smt_id = f"{MinMaxImpactRequest.requirement_file_id}-{MinMaxImpactRequest.max_level}"
    if graph_data["name"] is not None:
        smt_transform = GraphToSMT(graph_data, MinMaxImpactRequest.package_manager, MinMaxImpactRequest.agregator)
        smt_text = await read_smt_text(smt_id)
        if smt_text is not None and smt_text["moment"].replace(tzinfo=UTC) > graph_data[
            "moment"
        ].replace(tzinfo=UTC):
            smt_transform.convert(smt_text["text"])
        else:
            model_text = smt_transform.transform()
            await replace_smt_text(smt_id, model_text)
        operation = MaximizeImpact(MinMaxImpactRequest.limit)
        operation.execute(smt_transform.destination_model)
        result = await read_releases_by_counts(operation.get_result(), MinMaxImpactRequest.package_manager)
        return JSONResponse(
            status_code=status.HTTP_200_OK, content=json_encoder({"result": result, "message": "success"})
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=json_encoder(
                {"message": "no_dependencies"}
            ),
        )


@router.post(
    "/operation/file/filter_configs",
    summary="Filter configurations of a graph",
    response_description="Return a list of configurations",
)
async def filter_configs(
    FilterConfigsRequest: Annotated[FilterConfigsRequest, Body()]
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
    graph_data = await read_data_for_smt_transform(jsonable_encoder(FilterConfigsRequest))
    smt_id = f"{FilterConfigsRequest.requirement_file_id}-{FilterConfigsRequest.max_level}"
    if graph_data["name"] is not None:
        smt_transform = GraphToSMT(graph_data, FilterConfigsRequest.package_manager, FilterConfigsRequest.agregator)
        smt_text = await read_smt_text(smt_id)
        if smt_text is not None and smt_text["moment"].replace(tzinfo=UTC) > graph_data[
            "moment"
        ].replace(tzinfo=UTC):
            smt_transform.convert(smt_text["text"])
        else:
            model_text = smt_transform.transform()
            await replace_smt_text(smt_id, model_text)
        operation = FilterConfigs(FilterConfigsRequest.max_threshold, FilterConfigsRequest.min_threshold, FilterConfigsRequest.limit)
        operation.execute(smt_transform.destination_model)
        result = await read_releases_by_counts(operation.get_result(), FilterConfigsRequest.package_manager)
        return JSONResponse(
            status_code=status.HTTP_200_OK, content=json_encoder({"result": result, "message": "success"})
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=json_encoder(
                {"message": "no_dependencies"}
            ),
        )
