from typing import Annotated

from fastapi import APIRouter, Body, Depends, Request, status
from fastapi.responses import JSONResponse
from pytz import UTC

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
    SMTModel,
    ValidConfigOperation,
)
from app.limiter import limiter
from app.schemas import (
    CompleteConfigRequest,
    ConfigByImpactRequest,
    ValidConfigRequest,
)
from app.services import RequirementFileService, SMTService, VersionService
from app.utils import JSONEncoder

router = APIRouter()

@router.post(
    "/operation/config/valid_config",
    summary="Validate a Configuration",
    description="Validate the configuration based on a requirement file and maximum level.",
    response_description="Returns the result of the validation.",
    dependencies=[Depends(get_jwt_bearer())],
    tags=["Secure Chain Depex - Operation/Config"]
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
        result = await ValidConfigOperation.execute(smt_model, config)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=json_encoder.encode(
                {
                    "result": result,
                    "detail": "operation_success",
                }
            ),
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=json_encoder.encode(
                {
                    "detail": "no_dependencies",
                }
            ),
        )


@router.post(
    "/operation/config/complete_config",
    summary="Complete a Configuration",
    description="Complete the configuration based on a requirement file and maximum level.",
    response_description="Returns the result of the completion.",
    dependencies=[Depends(get_jwt_bearer())],
    tags=["Secure Chain Depex - Operation/Config"]
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
                    "result": result,
                    "detail": "operation_success",
                }
            ),
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=json_encoder.encode(
                {
                    "detail": "no_dependencies",
                }
            ),
        )


@router.post(
    "/operation/config/config_by_impact",
    summary="Complete a Configuration by Impact",
    description="Complete the configuration based on a requirement file, maximum level, and impact.",
    response_description="Returns the result of the completion by impact.",
    dependencies=[Depends(get_jwt_bearer())],
    tags=["Secure Chain Depex - Operation/Config"]
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
                    "result": result,
                    "detail": "operation_success",
                }
            ),
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=json_encoder.encode(
                {
                    "detail": "no_dependencies",
                }
            ),
        )
