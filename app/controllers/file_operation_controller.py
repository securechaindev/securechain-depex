from typing import Annotated

from fastapi import APIRouter, Body, Depends, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pytz import UTC

from app.limiter import limiter
from app.schemas import (
    FileInfoRequest,
    FilterConfigsRequest,
    MinMaxImpactRequest,
    ValidGraphRequest,
)
from app.services import (
    read_data_for_smt_transform,
    read_graph_for_info_operation,
    read_releases_by_counts,
    read_smt_text,
    replace_smt_text,
)
from app.utils import (
    FilterConfigs,
    JWTBearer,
    MaximizeImpact,
    MinimizeImpact,
    SMTModel,
    ValidGraph,
    json_encoder,
)

router = APIRouter()

@router.post("/operation/file/file_info", dependencies=[Depends(JWTBearer())], tags=["operation/file"])
@limiter.limit("25/minute")
async def file_info(
    file_info_request: Annotated[FileInfoRequest, Body()]
) -> JSONResponse:
    graph_info = await read_graph_for_info_operation(jsonable_encoder(file_info_request))
    return JSONResponse(
        status_code=status.HTTP_200_OK, content=json_encoder(graph_info)
    )


@router.post("/operation/file/valid_graph", dependencies=[Depends(JWTBearer())], tags=["operation/file"])
@limiter.limit("25/minute")
async def valid_graph(
    valid_graph_request: Annotated[ValidGraphRequest, Body()]
) -> JSONResponse:
    graph_data = await read_data_for_smt_transform(jsonable_encoder(valid_graph_request))
    smt_id = f"{valid_graph_request.requirement_file_id}-{valid_graph_request.max_level}"
    if graph_data["name"] is not None:
        smt_model = SMTModel(graph_data, valid_graph_request.node_type.value, "mean")
        smt_text = await read_smt_text(smt_id)
        if smt_text is not None and smt_text["moment"].replace(tzinfo=UTC) > graph_data[
            "moment"
        ].replace(tzinfo=UTC):
            smt_model.convert(smt_text["text"])
        else:
            model_text = smt_model.transform()
            await replace_smt_text(smt_id, model_text)
        operation = ValidGraph()
        operation.execute(smt_model)
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
@limiter.limit("25/minute")
async def minimize_impact(
    min_max_impact_request: Annotated[MinMaxImpactRequest, Body()]
) -> JSONResponse:
    graph_data = await read_data_for_smt_transform(jsonable_encoder(min_max_impact_request))
    smt_id = f"{min_max_impact_request.requirement_file_id}-{min_max_impact_request.max_level}"
    if graph_data["name"] is not None:
        smt_model = SMTModel(graph_data, min_max_impact_request.node_type.value, min_max_impact_request.agregator)
        smt_text = await read_smt_text(smt_id)
        if smt_text is not None and smt_text["moment"].replace(tzinfo=UTC) > graph_data[
            "moment"
        ].replace(tzinfo=UTC):
            smt_model.convert(smt_text["text"])
        else:
            model_text = smt_model.transform()
            await replace_smt_text(smt_id, model_text)
        operation = MinimizeImpact(min_max_impact_request.limit)
        operation.execute(smt_model)
        result = operation.get_result()
        if not isinstance(result, str):
            result = await read_releases_by_counts(operation.get_result(), min_max_impact_request.node_type.value)
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
@limiter.limit("25/minute")
async def maximize_impact(
    min_max_impact_request: Annotated[MinMaxImpactRequest, Body()]
) -> JSONResponse:
    graph_data = await read_data_for_smt_transform(jsonable_encoder(min_max_impact_request))
    smt_id = f"{min_max_impact_request.requirement_file_id}-{min_max_impact_request.max_level}"
    if graph_data["name"] is not None:
        smt_model = SMTModel(graph_data, min_max_impact_request.node_type.value, min_max_impact_request.agregator)
        smt_text = await read_smt_text(smt_id)
        if smt_text is not None and smt_text["moment"].replace(tzinfo=UTC) > graph_data[
            "moment"
        ].replace(tzinfo=UTC):
            smt_model.convert(smt_text["text"])
        else:
            model_text = smt_model.transform()
            await replace_smt_text(smt_id, model_text)
        operation = MaximizeImpact(min_max_impact_request.limit)
        operation.execute(smt_model)
        result = operation.get_result()
        if not isinstance(result, str):
            result = await read_releases_by_counts(operation.get_result(), min_max_impact_request.node_type.value)
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
@limiter.limit("25/minute")
async def filter_configs(
    filter_configs_request: Annotated[FilterConfigsRequest, Body()]
) -> JSONResponse:
    graph_data = await read_data_for_smt_transform(jsonable_encoder(filter_configs_request))
    smt_id = f"{filter_configs_request.requirement_file_id}-{filter_configs_request.max_level}"
    if graph_data["name"] is not None:
        smt_model = SMTModel(graph_data, filter_configs_request.node_type.value, filter_configs_request.agregator)
        smt_text = await read_smt_text(smt_id)
        if smt_text is not None and smt_text["moment"].replace(tzinfo=UTC) > graph_data[
            "moment"
        ].replace(tzinfo=UTC):
            smt_model.convert(smt_text["text"])
        else:
            model_text = smt_model.transform()
            await replace_smt_text(smt_id, model_text)
        operation = FilterConfigs(filter_configs_request.max_threshold, filter_configs_request.min_threshold, filter_configs_request.limit)
        operation.execute(smt_model)
        result = operation.get_result()
        if not isinstance(result, str):
            result = await read_releases_by_counts(operation.get_result(), filter_configs_request.node_type.value)
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
