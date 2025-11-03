from typing import Annotated

from fastapi import APIRouter, Body, Depends, Request, status
from fastapi.responses import JSONResponse
from pytz import UTC

from app.constants import ResponseCode, ResponseMessage
from app.dependencies import (
    get_json_encoder,
    get_jwt_bearer,
    get_requirement_file_service,
    get_smt_service,
    get_version_service,
)
from app.domain.smt import (
    CompleteConfigOperation,
    ConfigByImpactOperation,
    FilterConfigsOperation,
    MaximizeImpactOperation,
    MinimizeImpactOperation,
    SMTModel,
    ValidConfigOperation,
    ValidGraphOperation,
)
from app.limiter import limiter
from app.schemas import (
    CompleteConfigRequest,
    ConfigByImpactRequest,
    FilterConfigsRequest,
    MinMaxImpactRequest,
    ValidConfigRequest,
    ValidGraphRequest,
)
from app.services import RequirementFileService, SMTService, VersionService
from app.utils import JSONEncoder

router = APIRouter()

@router.post(
    "/operation/smt/valid_graph",
    summary="Validate Requirement File Graph",
    description="Validate the graph of a requirement file up to a specified level.",
    response_description="Validation result of the requirement file graph.",
    dependencies=[Depends(get_jwt_bearer())],
    tags=["Secure Chain Depex - Operation/SMT"]
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
            smt_model.convert(smt_text["text"])
        else:
            model_text = smt_model.transform()
            await smt_service.replace_smt_text(smt_text_id, model_text)
        result = ValidGraphOperation.execute(smt_model)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=json_encoder.encode(
                {
                    "code": ResponseCode.OPERATION_SUCCESS,
                    "message": ResponseMessage.GRAPH_VALIDATION_SUCCESS,
                    "result": result
                }
            ),
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=json_encoder.encode(
                {
                    "code": ResponseCode.NO_DEPENDENCIES,
                    "message": ResponseMessage.NO_DEPENDENCIES_TO_VALIDATE,
                }
            ),
        )


@router.post(
    "/operation/smt/minimize_impact",
    summary="Minimize Impact of Requirement File",
    description="Get the minimized impact and configuration of a specific requirement file.",
    response_description="Minimized Impact Configuration.",
    dependencies=[Depends(get_jwt_bearer())],
    tags=["Secure Chain Depex - Operation/SMT"]
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
            smt_model.convert(smt_text["text"])
        else:
            model_text = smt_model.transform()
            await smt_service.replace_smt_text(smt_text_id, model_text)
        result = await MinimizeImpactOperation.execute(smt_model, min_max_impact_request.limit)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=json_encoder.encode(
                {
                    "code": ResponseCode.OPERATION_SUCCESS,
                    "message": ResponseMessage.IMPACT_MINIMIZATION_SUCCESS,
                    "result": result
                }
            ),
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=json_encoder.encode(
                {
                    "code": ResponseCode.NO_DEPENDENCIES,
                    "message": ResponseMessage.NO_DEPENDENCIES_TO_MINIMIZE,
                }
            ),
        )


@router.post(
    "/operation/smt/maximize_impact",
    summary="Maximize Impact of Requirement File",
    description="Get the maximized impact and configuration of a specific requirement file.",
    response_description="Maximized Impact Configuration.",
    dependencies=[Depends(get_jwt_bearer())],
    tags=["Secure Chain Depex - Operation/SMT"]
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
            smt_model.convert(smt_text["text"])
        else:
            model_text = smt_model.transform()
            await smt_service.replace_smt_text(smt_text_id, model_text)
        result = await MaximizeImpactOperation.execute(smt_model, min_max_impact_request.limit)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=json_encoder.encode(
                {
                    "code": ResponseCode.OPERATION_SUCCESS,
                    "message": ResponseMessage.IMPACT_MAXIMIZATION_SUCCESS,
                    "result": result
                }
            ),
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=json_encoder.encode(
                {
                    "code": ResponseCode.NO_DEPENDENCIES,
                    "message": ResponseMessage.NO_DEPENDENCIES_TO_MAXIMIZE,
                }
            ),
        )


@router.post(
    "/operation/smt/filter_configs",
    summary="Filter Configurations of Requirement File",
    description="Get the filtered configurations of a specific requirement file.",
    response_description="Filtered Configurations.",
    dependencies=[Depends(get_jwt_bearer())],
    tags=["Secure Chain Depex - Operation/SMT"]
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
            smt_model.convert(smt_text["text"])
        else:
            model_text = smt_model.transform()
            await smt_service.replace_smt_text(smt_text_id, model_text)
        result = await FilterConfigsOperation.execute(
            smt_model,
            filter_configs_request.max_threshold,
            filter_configs_request.min_threshold,
            filter_configs_request.limit,
        )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=json_encoder.encode(
                {
                    "code": ResponseCode.OPERATION_SUCCESS,
                    "message": ResponseMessage.CONFIG_FILTERING_SUCCESS,
                    "result": result
                }
            ),
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=json_encoder.encode(
                {
                    "code": ResponseCode.NO_DEPENDENCIES,
                    "message": ResponseMessage.NO_DEPENDENCIES_TO_FILTER,
                }
            ),
        )

@router.post(
    "/operation/smt/valid_config",
    summary="Validate a Configuration",
    description="Validate the configuration based on a requirement file and maximum level.",
    response_description="Returns the result of the validation.",
    dependencies=[Depends(get_jwt_bearer())],
    tags=["Secure Chain Depex - Operation/SMT"]
)
@limiter.limit("5/minute")
async def valid_config(
    request: Request,
    valid_config_request: Annotated[ValidConfigRequest, Body()],
    requirement_file_service: RequirementFileService = Depends(get_requirement_file_service),
    version_service: VersionService = Depends(get_version_service),
    smt_service: SMTService = Depends(get_smt_service),
    json_encoder: JSONEncoder = Depends(get_json_encoder),
) -> JSONResponse:
    graph_data = await requirement_file_service.read_data_for_smt_transform(valid_config_request.requirement_file_id, valid_config_request.max_depth)
    smt_text_id = f"{valid_config_request.requirement_file_id}:{valid_config_request.max_depth}"
    if graph_data["name"] is not None:
        smt_model = SMTModel(graph_data, valid_config_request.node_type.value, valid_config_request.aggregator)
        smt_text = await smt_service.read_smt_text(smt_text_id)
        if smt_text is not None and smt_text["moment"].replace(tzinfo=UTC) > graph_data["moment"].replace(tzinfo=UTC):
            smt_model.convert(smt_text["text"])
        else:
            model_text = smt_model.transform()
            await smt_service.replace_smt_text(smt_text_id, model_text)
        config = await version_service.read_serial_numbers_by_releases(valid_config_request.node_type.value, valid_config_request.config)
        result = ValidConfigOperation.execute(smt_model, config)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=json_encoder.encode(
                {
                    "code": ResponseCode.OPERATION_SUCCESS,
                    "message": ResponseMessage.CONFIG_VALIDATION_SUCCESS,
                    "result": result
                }
            ),
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=json_encoder.encode(
                {
                    "code": ResponseCode.NO_DEPENDENCIES,
                    "message": ResponseMessage.NO_DEPENDENCIES_TO_VALIDATE,
                }
            ),
        )


@router.post(
    "/operation/smt/complete_config",
    summary="Complete a Configuration",
    description="Complete the configuration based on a requirement file and maximum level.",
    response_description="Returns the result of the completion.",
    dependencies=[Depends(get_jwt_bearer())],
    tags=["Secure Chain Depex - Operation/SMT"]
)
@limiter.limit("5/minute")
async def complete_config(
    request: Request,
    complete_config_request: Annotated[CompleteConfigRequest, Body()],
    requirement_file_service: RequirementFileService = Depends(get_requirement_file_service),
    version_service: VersionService = Depends(get_version_service),
    smt_service: SMTService = Depends(get_smt_service),
    json_encoder: JSONEncoder = Depends(get_json_encoder),
) -> JSONResponse:
    graph_data = await requirement_file_service.read_data_for_smt_transform(complete_config_request.requirement_file_id, complete_config_request.max_depth)
    smt_text_id = f"{complete_config_request.requirement_file_id}:{complete_config_request.max_depth}"
    if graph_data["name"] is not None:
        smt_model = SMTModel(graph_data, complete_config_request.node_type.value, complete_config_request.aggregator)
        smt_text = await smt_service.read_smt_text(smt_text_id)
        if smt_text is not None and smt_text["moment"].replace(tzinfo=UTC) > graph_data["moment"].replace(tzinfo=UTC):
            smt_model.convert(smt_text["text"])
        else:
            model_text = smt_model.transform()
            await smt_service.replace_smt_text(smt_text_id, model_text)
        config = await version_service.read_serial_numbers_by_releases(complete_config_request.node_type.value, complete_config_request.config)
        result = await CompleteConfigOperation.execute(smt_model, config)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=json_encoder.encode(
                {
                    "code": ResponseCode.OPERATION_SUCCESS,
                    "message": ResponseMessage.CONFIG_COMPLETION_SUCCESS,
                    "result": result
                }
            ),
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=json_encoder.encode(
                {
                    "code": ResponseCode.NO_DEPENDENCIES,
                    "message": ResponseMessage.NO_DEPENDENCIES_TO_COMPLETE,
                }
            ),
        )


@router.post(
    "/operation/smt/config_by_impact",
    summary="Complete a Configuration by Impact",
    description="Complete the configuration based on a requirement file, maximum level, and impact.",
    response_description="Returns the result of the completion by impact.",
    dependencies=[Depends(get_jwt_bearer())],
    tags=["Secure Chain Depex - Operation/SMT"]
)
@limiter.limit("5/minute")
async def config_by_impact(
    request: Request,
    config_by_impact_request: Annotated[ConfigByImpactRequest, Body()],
    requirement_file_service: RequirementFileService = Depends(get_requirement_file_service),
    smt_service: SMTService = Depends(get_smt_service),
    json_encoder: JSONEncoder = Depends(get_json_encoder),
) -> JSONResponse:
    graph_data = await requirement_file_service.read_data_for_smt_transform(config_by_impact_request.requirement_file_id, config_by_impact_request.max_depth)
    smt_text_id = f"{config_by_impact_request.requirement_file_id}:{config_by_impact_request.max_depth}"
    if graph_data["name"] is not None:
        smt_model = SMTModel(graph_data, config_by_impact_request.node_type.value, config_by_impact_request.aggregator)
        smt_text = await smt_service.read_smt_text(smt_text_id)
        if smt_text is not None and smt_text["moment"].replace(tzinfo=UTC) > graph_data["moment"].replace(tzinfo=UTC):
            smt_model.convert(smt_text["text"])
        else:
            model_text = smt_model.transform()
            await smt_service.replace_smt_text(smt_text_id, model_text)
        result = await ConfigByImpactOperation.execute(smt_model, config_by_impact_request.impact)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=json_encoder.encode(
                {
                    "code": ResponseCode.OPERATION_SUCCESS,
                    "message": ResponseMessage.CONFIG_BY_IMPACT_SUCCESS,
                    "result": result
                }
            ),
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=json_encoder.encode(
                {
                    "code": ResponseCode.NO_DEPENDENCIES,
                    "message": ResponseMessage.NO_DEPENDENCIES_TO_PROCESS,
                }
            ),
        )
