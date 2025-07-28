from typing import Annotated

from fastapi import APIRouter, Body, Depends, Request, status
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
    read_releases_by_serial_numbers,
    read_requirement_file_moment,
    read_smt_text,
    replace_smt_text,
    read_smt_result,
    replace_smt_result,
)
from app.utils import (
    FilterConfigs,
    JWTBearer,
    MaximizeImpact,
    MinimizeImpact,
    SMTModel,
    ValidGraph,
    json_encoder,
    filter_versions,
)

router = APIRouter()

@router.post("/operation/file/file_info", dependencies=[Depends(JWTBearer())], tags=["operation/file"])
@limiter.limit("5/minute")
async def file_info(
    request: Request,
    file_info_request: Annotated[FileInfoRequest, Body()]
) -> JSONResponse:
    smt_result_id = f"{file_info_request.node_type.value}:{file_info_request.requirement_file_id}:{file_info_request.max_level}"
    smt_result = await read_smt_result(smt_result_id)
    req_file_moment = await read_requirement_file_moment(file_info_request.requirement_file_id)
    if smt_result is not None and smt_result["moment"].replace(tzinfo=UTC) > req_file_moment.replace(tzinfo=UTC):
        result = smt_result["result"]
    else:
        result = await read_graph_for_info_operation(
            file_info_request.node_type.value,
            file_info_request.requirement_file_id,
            file_info_request.max_level
        )
        for direct_package in result["direct_dependencies"]:
            direct_package["versions"] = await filter_versions(
                file_info_request.node_type.value,
                direct_package["versions"],
                direct_package["package_constraints"]
            )
        for _, indirect_packages in result["indirect_dependencies_by_depth"].items():
            for indirect_package in indirect_packages:
                indirect_package["versions"] = await filter_versions(
                    file_info_request.node_type.value,
                    indirect_package["versions"],
                    indirect_package["package_constraints"]
                )
        result = await filter_versions(file_info_request.node_type.value,result)
        await replace_smt_result(smt_result_id, result)
    return JSONResponse(
        status_code=status.HTTP_200_OK, content=json_encoder({
            "result": result,
            "code": "success",
            "message": "File information retrieved successfully"
        })
    )


@router.post("/operation/file/valid_graph", dependencies=[Depends(JWTBearer())], tags=["operation/file"])
@limiter.limit("5/minute")
async def valid_graph(
    request: Request,
    valid_graph_request: Annotated[ValidGraphRequest, Body()]
) -> JSONResponse:
    graph_data = await read_data_for_smt_transform(valid_graph_request.requirement_file_id, valid_graph_request.max_level)
    smt_text_id = f"{valid_graph_request.requirement_file_id}-{valid_graph_request.max_level}"
    if graph_data["name"] is not None:
        smt_model = SMTModel(graph_data, valid_graph_request.node_type.value, "mean")
        smt_text = await read_smt_text(smt_text_id)
        if smt_text is not None and smt_text["moment"].replace(tzinfo=UTC) > graph_data["moment"].replace(tzinfo=UTC):
            smt_model.convert(smt_text["text"])
        else:
            model_text = smt_model.transform()
            await replace_smt_text(smt_text_id, model_text)
        operation = ValidGraph()
        operation.execute(smt_model)
        return JSONResponse(
            status_code=status.HTTP_200_OK, content=json_encoder({
                "result": operation.get_result(),
                "code": "success",
                "message": "Operation Valid Graph executed successfully"
            })
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=json_encoder(
                {
                    "code": "no_dependencies",
                    "message": "No dependencies found for the provided requirement file ID and max level"
                }
            ),
        )


@router.post("/operation/file/minimize_impact", dependencies=[Depends(JWTBearer())], tags=["operation/file"])
@limiter.limit("5/minute")
async def minimize_impact(
    request: Request,
    min_max_impact_request: Annotated[MinMaxImpactRequest, Body()]
) -> JSONResponse:
    graph_data = await read_data_for_smt_transform(min_max_impact_request.requirement_file_id, min_max_impact_request.max_level)
    smt_text_id = f"{min_max_impact_request.requirement_file_id}-{min_max_impact_request.max_level}"
    if graph_data["name"] is not None:
        smt_model = SMTModel(graph_data, min_max_impact_request.node_type.value, min_max_impact_request.agregator)
        smt_text = await read_smt_text(smt_text_id)
        if smt_text is not None and smt_text["moment"].replace(tzinfo=UTC) > graph_data["moment"].replace(tzinfo=UTC):
            smt_model.convert(smt_text["text"])
        else:
            model_text = smt_model.transform()
            await replace_smt_text(smt_text_id, model_text)
        operation = MinimizeImpact(min_max_impact_request.limit)
        operation.execute(smt_model)
        result = operation.get_result()
        if not isinstance(result, str):
            result = await read_releases_by_serial_numbers(min_max_impact_request.node_type.value, operation.get_result())
        return JSONResponse(
            status_code=status.HTTP_200_OK, content=json_encoder(
                {
                    "result": result,
                    "code": "success",
                    "message": "Operation Minimize Impact executed successfully"
                }
            )
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=json_encoder(
                {
                    "code": "no_dependencies",
                    "message": "No dependencies found for the provided requirement file ID and max level"
                }
            ),
        )


@router.post("/operation/file/maximize_impact", dependencies=[Depends(JWTBearer())], tags=["operation/file"])
@limiter.limit("5/minute")
async def maximize_impact(
    request: Request,
    min_max_impact_request: Annotated[MinMaxImpactRequest, Body()]
) -> JSONResponse:
    graph_data = await read_data_for_smt_transform(min_max_impact_request.requirement_file_id, min_max_impact_request.max_level)
    smt_text_id = f"{min_max_impact_request.requirement_file_id}-{min_max_impact_request.max_level}"
    if graph_data["name"] is not None:
        smt_model = SMTModel(graph_data, min_max_impact_request.node_type.value, min_max_impact_request.agregator)
        smt_text = await read_smt_text(smt_text_id)
        if smt_text is not None and smt_text["moment"].replace(tzinfo=UTC) > graph_data["moment"].replace(tzinfo=UTC):
            smt_model.convert(smt_text["text"])
        else:
            model_text = smt_model.transform()
            await replace_smt_text(smt_text_id, model_text)
        operation = MaximizeImpact(min_max_impact_request.limit)
        operation.execute(smt_model)
        result = operation.get_result()
        if not isinstance(result, str):
            result = await read_releases_by_serial_numbers(min_max_impact_request.node_type.value, operation.get_result())
        return JSONResponse(
            status_code=status.HTTP_200_OK, content=json_encoder(
                {
                    "result": result,
                    "code": "success",
                    "message": "Operation Maximize Impact executed successfully"
                }
            )
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=json_encoder(
                {
                    "code": "no_dependencies",
                    "message": "No dependencies found for the provided requirement file ID and max level"
                }
            ),
        )


@router.post("/operation/file/filter_configs", dependencies=[Depends(JWTBearer())], tags=["operation/file"])
@limiter.limit("5/minute")
async def filter_configs(
    request: Request,
    filter_configs_request: Annotated[FilterConfigsRequest, Body()]
) -> JSONResponse:
    graph_data = await read_data_for_smt_transform(filter_configs_request.requirement_file_id, filter_configs_request.max_level)
    smt_text_id = f"{filter_configs_request.requirement_file_id}-{filter_configs_request.max_level}"
    if graph_data["name"] is not None:
        smt_model = SMTModel(graph_data, filter_configs_request.node_type.value, filter_configs_request.agregator)
        smt_text = await read_smt_text(smt_text_id)
        if smt_text is not None and smt_text["moment"].replace(tzinfo=UTC) > graph_data["moment"].replace(tzinfo=UTC):
            smt_model.convert(smt_text["text"])
        else:
            model_text = smt_model.transform()
            await replace_smt_text(smt_text_id, model_text)
        operation = FilterConfigs(filter_configs_request.max_threshold, filter_configs_request.min_threshold, filter_configs_request.limit)
        operation.execute(smt_model)
        result = operation.get_result()
        if not isinstance(result, str):
            result = await read_releases_by_serial_numbers(filter_configs_request.node_type.value, operation.get_result())
        return JSONResponse(
            status_code=status.HTTP_200_OK, content=json_encoder(
                {
                    "result": result,
                    "code": "success",
                    "message": "Operation Filter Configs executed successfully"
                }
            )
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=json_encoder(
                {
                    "code": "no_dependencies",
                    "message": "No dependencies found for the provided requirement file ID and max level"
                }
            ),
        )
