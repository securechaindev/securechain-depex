from typing import Annotated

from fastapi import APIRouter, Body, Depends, status
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
from app.utils import JWTBearer, json_encoder

router = APIRouter()

@router.post("/operation/file/file_info", dependencies=[Depends(JWTBearer())], tags=["operation/file"])
async def file_info(
    FileInfoRequest: Annotated[FileInfoRequest, Body()]
) -> JSONResponse:
    graph_info = await read_graph_for_info_operation(jsonable_encoder(FileInfoRequest))
    return JSONResponse(
        status_code=status.HTTP_200_OK, content=json_encoder(graph_info)
    )


@router.post("/operation/file/valid_file", dependencies=[Depends(JWTBearer())], tags=["operation/file"])
async def valid_file(
    valid_file_request: Annotated[ValidFileRequest, Body()]
) -> JSONResponse:
    print(jsonable_encoder(valid_file_request))
    graph_data = await read_data_for_smt_transform(jsonable_encoder(valid_file_request))
    smt_id = f"{valid_file_request.requirement_file_id}-{valid_file_request.max_level}"
    if graph_data["name"] is not None:
        smt_transform = GraphToSMT(graph_data, valid_file_request.manager, "mean")
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


@router.post("/operation/file/minimize_impact", dependencies=[Depends(JWTBearer())], tags=["operation/file"])
async def minimize_impact(
    MinMaxImpactRequest: Annotated[MinMaxImpactRequest, Body()]
) -> JSONResponse:
    graph_data = await read_data_for_smt_transform(jsonable_encoder(MinMaxImpactRequest))
    smt_id = f"{MinMaxImpactRequest.requirement_file_id}-{MinMaxImpactRequest.max_level}"
    if graph_data["name"] is not None:
        smt_transform = GraphToSMT(graph_data, MinMaxImpactRequest.manager, MinMaxImpactRequest.agregator)
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
        result = operation.get_result()
        if not isinstance(result, str):
            result = await read_releases_by_counts(operation.get_result(), MinMaxImpactRequest.manager)
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


@router.post("/operation/file/maximize_impact", dependencies=[Depends(JWTBearer())], tags=["operation/file"])
async def maximize_impact(
    MinMaxImpactRequest: Annotated[MinMaxImpactRequest, Body()]
) -> JSONResponse:
    graph_data = await read_data_for_smt_transform(jsonable_encoder(MinMaxImpactRequest))
    smt_id = f"{MinMaxImpactRequest.requirement_file_id}-{MinMaxImpactRequest.max_level}"
    if graph_data["name"] is not None:
        smt_transform = GraphToSMT(graph_data, MinMaxImpactRequest.manager, MinMaxImpactRequest.agregator)
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
        result = operation.get_result()
        if not isinstance(result, str):
            result = await read_releases_by_counts(operation.get_result(), MinMaxImpactRequest.manager)
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


@router.post("/operation/file/filter_configs", dependencies=[Depends(JWTBearer())], tags=["operation/file"])
async def filter_configs(
    FilterConfigsRequest: Annotated[FilterConfigsRequest, Body()]
) -> JSONResponse:
    graph_data = await read_data_for_smt_transform(jsonable_encoder(FilterConfigsRequest))
    smt_id = f"{FilterConfigsRequest.requirement_file_id}-{FilterConfigsRequest.max_level}"
    if graph_data["name"] is not None:
        smt_transform = GraphToSMT(graph_data, FilterConfigsRequest.manager, FilterConfigsRequest.agregator)
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
        result = operation.get_result()
        if not isinstance(result, str):
            result = await read_releases_by_counts(operation.get_result(), FilterConfigsRequest.manager)
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
