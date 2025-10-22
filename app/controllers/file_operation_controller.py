from typing import Annotated

from fastapi import APIRouter, Body, Depends, Request, status
from fastapi.responses import JSONResponse
from pytz import UTC

from app.dependencies import (
    get_json_encoder,
    get_jwt_bearer,
    get_operation_service,
    get_requirement_file_service,
    get_smt_service,
)
from app.domain.smt import (
    FilterConfigsOperation,
    MaximizeImpactOperation,
    MinimizeImpactOperation,
    SMTModel,
    ValidGraphOperation,
)
from app.limiter import limiter
from app.schemas import (
    FileInfoRequest,
    FilterConfigsRequest,
    MinMaxImpactRequest,
    ValidGraphRequest,
)
from app.services import OperationService, RequirementFileService, SMTService
from app.utils import JSONEncoder, VersionFilter

router = APIRouter()

@router.post(
    "/operation/file/file_info",
    summary="Get Requirement File Information",
    description="Retrieve information about dependnecy graph of a specific requirement file.",
    response_description="Requirement File information.",
    dependencies=[Depends(get_jwt_bearer())],
    tags=["Secure Chain Depex - Operation/File"]
)
@limiter.limit("5/minute")
async def requirement_file_info(
    request: Request,
    file_info_request: Annotated[FileInfoRequest, Body()],
    requirement_file_service: RequirementFileService = Depends(get_requirement_file_service),
    operation_service: OperationService = Depends(get_operation_service),
    json_encoder: JSONEncoder = Depends(get_json_encoder),
) -> JSONResponse:
    operation_result_id = f"{file_info_request.node_type.value}:{file_info_request.requirement_file_id}:{file_info_request.max_depth}"
    operation_result = await operation_service.read_operation_result(operation_result_id)
    req_file_moment = await requirement_file_service.read_requirement_file_moment(file_info_request.requirement_file_id)
    if operation_result is not None and operation_result["moment"].replace(tzinfo=UTC) > req_file_moment.replace(tzinfo=UTC):
        result = operation_result["result"]
    else:
        result = await requirement_file_service.read_graph_for_req_file_info_operation(
            file_info_request.node_type.value,
            file_info_request.requirement_file_id,
            file_info_request.max_depth
        )
        if result["total_direct_dependencies"] != 0:
            for direct_package in result["direct_dependencies"]:
                direct_package["versions"] = await VersionFilter.filter_versions(
                    file_info_request.node_type.value,
                    direct_package["versions"],
                    direct_package["package_constraints"]
                )
            for _, indirect_packages in result["indirect_dependencies_by_depth"].items():
                for indirect_package in indirect_packages:
                    indirect_package["versions"] = await VersionFilter.filter_versions(
                        file_info_request.node_type.value,
                        indirect_package["versions"],
                        indirect_package["package_constraints"]
                    )
        else:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content= await json_encoder.encode(
                    {
                        "detail": "no_dependencies",
                    }
                ),
            )
        await operation_service.replace_operation_result(operation_result_id, result)
    return JSONResponse(
        status_code=status.HTTP_200_OK, content= await json_encoder.encode(
            {
                "result": result,
                "detail": "file_info_success",
            }
        )
    )


@router.post(
    "/operation/file/valid_graph",
    summary="Validate Requirement File Graph",
    description="Validate the graph of a requirement file up to a specified level.",
    response_description="Validation result of the requirement file graph.",
    dependencies=[Depends(get_jwt_bearer())],
    tags=["Secure Chain Depex - Operation/File"]
)
@limiter.limit("5/minute")
async def valid_graph(
    request: Request,
    valid_graph_request: Annotated[ValidGraphRequest, Body()],
    requirement_file_service: RequirementFileService = Depends(get_requirement_file_service),
    smt_service: SMTService = Depends(get_smt_service),
    json_encoder: JSONEncoder = Depends(get_json_encoder),
) -> JSONResponse:
    graph_data = await requirement_file_service.read_data_for_smt_transform(valid_graph_request.requirement_file_id, valid_graph_request.max_depth)
    smt_text_id = f"{valid_graph_request.requirement_file_id}:{valid_graph_request.max_depth}"
    if graph_data["name"] is not None:
        smt_model = SMTModel(graph_data, valid_graph_request.node_type.value, "mean")
        smt_text = await smt_service.read_smt_text(smt_text_id)
        if smt_text is not None and smt_text["moment"].replace(tzinfo=UTC) > graph_data["moment"].replace(tzinfo=UTC):
            await smt_model.convert(smt_text["text"])
        else:
            model_text = await smt_model.transform()
            await smt_service.replace_smt_text(smt_text_id, model_text)
        result = await ValidGraphOperation.execute(smt_model)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=await json_encoder.encode(
                {
                    "result": result,
                    "detail": "operation_success",
                }
            ),
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content= await json_encoder.encode(
                {
                    "detail": "no_dependencies",
                }
            ),
        )


@router.post(
    "/operation/file/minimize_impact",
    summary="Minimize Impact of Requirement File",
    description="Get the minimized impact and configuration of a specific requirement file.",
    response_description="Minimized Impact Configuration.",
    dependencies=[Depends(get_jwt_bearer())],
    tags=["Secure Chain Depex - Operation/File"]
)
@limiter.limit("5/minute")
async def minimize_impact(
    request: Request,
    min_max_impact_request: Annotated[MinMaxImpactRequest, Body()],
    requirement_file_service: RequirementFileService = Depends(get_requirement_file_service),
    smt_service: SMTService = Depends(get_smt_service),
    json_encoder: JSONEncoder = Depends(get_json_encoder),
) -> JSONResponse:
    graph_data = await requirement_file_service.read_data_for_smt_transform(min_max_impact_request.requirement_file_id, min_max_impact_request.max_depth)
    smt_text_id = f"{min_max_impact_request.requirement_file_id}:{min_max_impact_request.max_depth}"
    if graph_data["name"] is not None:
        smt_model = SMTModel(graph_data, min_max_impact_request.node_type.value, min_max_impact_request.aggregator)
        smt_text = await smt_service.read_smt_text(smt_text_id)
        if smt_text is not None and smt_text["moment"].replace(tzinfo=UTC) > graph_data["moment"].replace(tzinfo=UTC):
            await smt_model.convert(smt_text["text"])
        else:
            model_text = await smt_model.transform()
            await smt_service.replace_smt_text(smt_text_id, model_text)
        result = await MinimizeImpactOperation.execute(smt_model, min_max_impact_request.limit)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=await json_encoder.encode(
                {
                    "result": result,
                    "detail": "operation_success",
                }
            ),
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content= await json_encoder.encode(
                {
                    "detail": "no_dependencies",
                }
            ),
        )


@router.post(
    "/operation/file/maximize_impact",
    summary="Maximize Impact of Requirement File",
    description="Get the maximized impact and configuration of a specific requirement file.",
    response_description="Maximized Impact Configuration.",
    dependencies=[Depends(get_jwt_bearer())],
    tags=["Secure Chain Depex - Operation/File"]
)
@limiter.limit("5/minute")
async def maximize_impact(
    request: Request,
    min_max_impact_request: Annotated[MinMaxImpactRequest, Body()],
    requirement_file_service: RequirementFileService = Depends(get_requirement_file_service),
    smt_service: SMTService = Depends(get_smt_service),
    json_encoder: JSONEncoder = Depends(get_json_encoder),
) -> JSONResponse:
    graph_data = await requirement_file_service.read_data_for_smt_transform(min_max_impact_request.requirement_file_id, min_max_impact_request.max_depth)
    smt_text_id = f"{min_max_impact_request.requirement_file_id}:{min_max_impact_request.max_depth}"
    if graph_data["name"] is not None:
        smt_model = SMTModel(graph_data, min_max_impact_request.node_type.value, min_max_impact_request.aggregator)
        smt_text = await smt_service.read_smt_text(smt_text_id)
        if smt_text is not None and smt_text["moment"].replace(tzinfo=UTC) > graph_data["moment"].replace(tzinfo=UTC):
            await smt_model.convert(smt_text["text"])
        else:
            model_text = await smt_model.transform()
            await smt_service.replace_smt_text(smt_text_id, model_text)
        result = await MaximizeImpactOperation.execute(smt_model, min_max_impact_request.limit)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=await json_encoder.encode(
                {
                    "result": result,
                    "detail": "operation_success",
                }
            ),
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content= await json_encoder.encode(
                {
                    "detail": "no_dependencies",
                }
            ),
        )


@router.post(
    "/operation/file/filter_configs",
    summary="Filter Configurations of Requirement File",
    description="Get the filtered configurations of a specific requirement file.",
    response_description="Filtered Configurations.",
    dependencies=[Depends(get_jwt_bearer())],
    tags=["Secure Chain Depex - Operation/File"]
)
@limiter.limit("5/minute")
async def filter_configs(
    request: Request,
    filter_configs_request: Annotated[FilterConfigsRequest, Body()],
    requirement_file_service: RequirementFileService = Depends(get_requirement_file_service),
    smt_service: SMTService = Depends(get_smt_service),
    json_encoder: JSONEncoder = Depends(get_json_encoder),
) -> JSONResponse:
    graph_data = await requirement_file_service.read_data_for_smt_transform(filter_configs_request.requirement_file_id, filter_configs_request.max_depth)
    smt_text_id = f"{filter_configs_request.requirement_file_id}:{filter_configs_request.max_depth}"
    if graph_data["name"] is not None:
        smt_model = SMTModel(graph_data, filter_configs_request.node_type.value, filter_configs_request.aggregator)
        smt_text = await smt_service.read_smt_text(smt_text_id)
        if smt_text is not None and smt_text["moment"].replace(tzinfo=UTC) > graph_data["moment"].replace(tzinfo=UTC):
            await smt_model.convert(smt_text["text"])
        else:
            model_text = await smt_model.transform()
            await smt_service.replace_smt_text(smt_text_id, model_text)
        result = await FilterConfigsOperation.execute(
            smt_model,
            filter_configs_request.max_threshold,
            filter_configs_request.min_threshold,
            filter_configs_request.limit,
        )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=await json_encoder.encode(
                {
                    "result": result,
                    "detail": "operation_success",
                }
            ),
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content= await json_encoder.encode(
                {
                    "detail": "no_dependencies",
                }
            ),
        )
