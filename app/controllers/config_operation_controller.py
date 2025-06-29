from typing import Annotated

from fastapi import APIRouter, Body, Depends, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from app.utils.smt.operations import (
    CompleteConfig,
    ConfigByImpact,
    ValidConfig,
)
from app.utils.smt.model import SMTModel
from pytz import UTC

from app.schemas.operations import (
    CompleteConfigRequest,
    ConfigByImpactRequest,
    ValidConfigRequest,
)
from app.services import (
    read_counts_by_releases,
    read_data_for_smt_transform,
    read_releases_by_counts,
    read_smt_text,
    replace_smt_text,
)
from app.utils import JWTBearer, json_encoder

router = APIRouter()

@router.post("/operation/config/valid_config", dependencies=[Depends(JWTBearer())], tags=["operation/config"])
async def valid_config(
    valid_config_request: Annotated[ValidConfigRequest, Body()]
) -> JSONResponse:
    graph_data = await read_data_for_smt_transform(jsonable_encoder(valid_config_request))
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
        smt_model = smt_model.destination_model
        operation = ValidConfig(await read_counts_by_releases(valid_config_request.config, valid_config_request.node_type.value))
        operation.execute(smt_model)
        result = {"is_valid": operation.get_result(), "message": "success"}
        return JSONResponse(
            status_code=status.HTTP_200_OK, content=json_encoder(result)
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=json_encoder(
                {"message": "no_dependencies"}
            ),
        )


@router.post("/operation/config/complete_config", dependencies=[Depends(JWTBearer())], tags=["operation/config"])
async def complete_config(
    complete_config_request: Annotated[CompleteConfigRequest, Body()]
) -> JSONResponse:
    graph_data = await read_data_for_smt_transform(jsonable_encoder(complete_config_request))
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
            await read_counts_by_releases(complete_config_request.config, complete_config_request.node_type.value)
        )
        operation.execute(smt_model)
        result = operation.get_result()
        if not isinstance(result, str):
            result = await read_releases_by_counts(operation.get_result(), complete_config_request.node_type.value)
        return JSONResponse(
            status_code=status.HTTP_200_OK, content=json_encoder({"result": result, "message": "success"})
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=json_encoder(
                {"message": "no_dependencies"}
            ),
        )


@router.post("/operation/config/config_by_impact", dependencies=[Depends(JWTBearer())], tags=["operation/config"])
async def config_by_impact(
    config_by_impact_request: Annotated[ConfigByImpactRequest, Body()]
) -> JSONResponse:
    graph_data = await read_data_for_smt_transform(jsonable_encoder(config_by_impact_request))
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
            result = await read_releases_by_counts(operation.get_result(), config_by_impact_request.node_type.value)
        return JSONResponse(
            status_code=status.HTTP_200_OK, content=json_encoder({"result": result, "message": "success"})
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=json_encoder(
                {"message": "no_dependencies"}
            ),
        )
