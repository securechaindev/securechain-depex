from typing import Annotated

from fastapi import APIRouter, Body, Depends, Request, status
from fastapi.responses import JSONResponse
from pytz import UTC

from app.limiter import limiter
from app.schemas import (
    CompleteConfigRequest,
    ConfigByImpactRequest,
    ValidConfigRequest,
)
from app.services import (
    read_data_for_smt_transform,
    read_releases_by_serial_numbers,
    read_serial_numbers_by_releases,
    read_smt_text,
    replace_smt_text,
)
from app.utils import (
    CompleteConfig,
    ConfigByImpact,
    JWTBearer,
    SMTModel,
    ValidConfig,
    json_encoder,
)

router = APIRouter()

@router.post("/operation/config/valid_config", dependencies=[Depends(JWTBearer())], tags=["operation/config"])
@limiter.limit("5/minute")
async def valid_config(
    request: Request,
    valid_config_request: Annotated[ValidConfigRequest, Body()]
) -> JSONResponse:
    graph_data = await read_data_for_smt_transform(valid_config_request.requirement_file_id, valid_config_request.max_level)
    smt_id = f"{valid_config_request.requirement_file_id}-{valid_config_request.max_level}"
    if graph_data["name"] is not None:
        smt_model = SMTModel(graph_data, valid_config_request.node_type.value, valid_config_request.agregator)
        smt_text = await read_smt_text(smt_id)
        if smt_text is not None and smt_text["moment"].replace(tzinfo=UTC) > graph_data[
            "moment"
        ].replace(tzinfo=UTC):
            smt_model.convert(smt_text["text"])
        else:
            model_text = smt_model.transform()
            await replace_smt_text(smt_id, model_text)
        operation = ValidConfig(await read_serial_numbers_by_releases(valid_config_request.node_type.value, valid_config_request.config))
        operation.execute(smt_model)
        return JSONResponse(
            status_code=status.HTTP_200_OK, content=json_encoder(
                {
                    "result": operation.get_result(),
                    "code": "success",
                    "message": "Operation Valid Configuration executed successfully"
                }
            )
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=json_encoder(
                {
                    "code": "no_dependencies",
                    "message": "No dependencies found for the provided requirement file ID and max level"
                }
            ),
        )


@router.post("/operation/config/complete_config", dependencies=[Depends(JWTBearer())], tags=["operation/config"])
@limiter.limit("5/minute")
async def complete_config(
    request: Request,
    complete_config_request: Annotated[CompleteConfigRequest, Body()]
) -> JSONResponse:
    graph_data = await read_data_for_smt_transform(complete_config_request.requirement_file_id, complete_config_request.max_level)
    smt_id = f"{complete_config_request.requirement_file_id}-{complete_config_request.max_level}"
    if graph_data["name"] is not None:
        smt_model = SMTModel(graph_data, complete_config_request.node_type.value, complete_config_request.agregator)
        smt_text = await read_smt_text(smt_id)
        if smt_text is not None and smt_text["moment"].replace(tzinfo=UTC) > graph_data[
            "moment"
        ].replace(tzinfo=UTC):
            smt_model.convert(smt_text["text"])
        else:
            model_text = smt_model.transform()
            await replace_smt_text(smt_id, model_text)
        smt_model = smt_model
        operation = CompleteConfig(
            await read_serial_numbers_by_releases(complete_config_request.node_type.value, complete_config_request.config)
        )
        operation.execute(smt_model)
        result = operation.get_result()
        if not isinstance(result, str):
            result = await read_releases_by_serial_numbers(complete_config_request.node_type.value, operation.get_result())
        return JSONResponse(
            status_code=status.HTTP_200_OK, content=json_encoder(
                {
                    "result": result,
                    "code": "success",
                    "message": "Operation Complete Configuration executed successfully"
                }
            )
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=json_encoder(
                {
                    "code": "no_dependencies",
                    "message": "No dependencies found for the provided requirement file ID and max level"
                }
            ),
        )


@router.post("/operation/config/config_by_impact", dependencies=[Depends(JWTBearer())], tags=["operation/config"])
@limiter.limit("5/minute")
async def config_by_impact(
    request: Request,
    config_by_impact_request: Annotated[ConfigByImpactRequest, Body()]
) -> JSONResponse:
    graph_data = await read_data_for_smt_transform(config_by_impact_request.requirement_file_id, config_by_impact_request.max_level)
    smt_id = f"{config_by_impact_request.requirement_file_id}-{config_by_impact_request.max_level}"
    if graph_data["name"] is not None:
        smt_model = SMTModel(graph_data, config_by_impact_request.node_type.value, config_by_impact_request.agregator)
        smt_text = await read_smt_text(smt_id)
        if smt_text is not None and smt_text["moment"].replace(tzinfo=UTC) > graph_data[
            "moment"
        ].replace(tzinfo=UTC):
            smt_model.convert(smt_text["text"])
        else:
            model_text = smt_model.transform()
            await replace_smt_text(smt_id, model_text)
        smt_model = smt_model
        operation = ConfigByImpact(config_by_impact_request.impact)
        operation.execute(smt_model)
        result = operation.get_result()
        if not isinstance(result, str):
            result = await read_releases_by_serial_numbers(config_by_impact_request.node_type.value, operation.get_result())
        return JSONResponse(
            status_code=status.HTTP_200_OK, content=json_encoder(
                {
                    "result": result,
                    "code": "success",
                    "message": "Operation Config by Impact executed successfully"
                }
            )
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=json_encoder(
                {
                    "code": "no_dependencies",
                    "message": "No dependencies found for the provided requirement file ID and max level"
                }
            ),
        )
