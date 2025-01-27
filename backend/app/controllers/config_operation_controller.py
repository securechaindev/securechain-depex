from fastapi import APIRouter, Body, Depends, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from flamapy.metamodels.smt_metamodel.operations import (
    CompleteConfig,
    ConfigByImpact,
    ValidConfig,
)
from flamapy.metamodels.smt_metamodel.transformations import GraphToSMT
from pytz import UTC
from typing_extensions import Annotated

from app.models import CompleteConfigRequest, ConfigByImpactRequest, ValidConfigRequest
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
    ValidConfigRequest: Annotated[ValidConfigRequest, Body()]
) -> JSONResponse:
    graph_data = await read_data_for_smt_transform(jsonable_encoder(ValidConfigRequest))
    smt_id = f"{ValidConfigRequest.requirement_file_id}-{ValidConfigRequest.max_level}"
    if graph_data["name"] is not None:
        smt_transform = GraphToSMT(graph_data, ValidConfigRequest.manager, ValidConfigRequest.agregator)
        smt_text = await read_smt_text(smt_id)
        if smt_text is not None and smt_text["moment"].replace(tzinfo=UTC) > graph_data[
            "moment"
        ].replace(tzinfo=UTC):
            smt_transform.convert(smt_text["text"])
        else:
            model_text = smt_transform.transform()
            await replace_smt_text(smt_id, model_text)
        smt_model = smt_transform.destination_model
        operation = ValidConfig(await read_counts_by_releases(ValidConfigRequest.config, ValidConfigRequest.manager))
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
    CompleteConfigRequest: Annotated[CompleteConfigRequest, Body()]
) -> JSONResponse:
    graph_data = await read_data_for_smt_transform(jsonable_encoder(CompleteConfigRequest))
    smt_id = f"{CompleteConfigRequest.requirement_file_id}-{CompleteConfigRequest.max_level}"
    if graph_data["name"] is not None:
        smt_transform = GraphToSMT(graph_data, CompleteConfigRequest.manager, CompleteConfigRequest.agregator)
        smt_text = await read_smt_text(smt_id)
        if smt_text is not None and smt_text["moment"].replace(tzinfo=UTC) > graph_data[
            "moment"
        ].replace(tzinfo=UTC):
            smt_transform.convert(smt_text["text"])
        else:
            model_text = smt_transform.transform()
            await replace_smt_text(smt_id, model_text)
        smt_model = smt_transform.destination_model
        operation = CompleteConfig(
            await read_counts_by_releases(CompleteConfigRequest.config, CompleteConfigRequest.manager)
        )
        operation.execute(smt_model)
        result = operation.get_result()
        if not isinstance(result, str):
            result = await read_releases_by_counts(operation.get_result(), CompleteConfigRequest.manager)
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
    ConfigByImpactRequest: Annotated[ConfigByImpactRequest, Body()]
) -> JSONResponse:
    graph_data = await read_data_for_smt_transform(jsonable_encoder(ConfigByImpactRequest))
    smt_id = f"{ConfigByImpactRequest.requirement_file_id}-{ConfigByImpactRequest.max_level}"
    if graph_data["name"] is not None:
        smt_transform = GraphToSMT(graph_data, ConfigByImpactRequest.manager, ConfigByImpactRequest.agregator)
        smt_text = await read_smt_text(smt_id)
        if smt_text is not None and smt_text["moment"].replace(tzinfo=UTC) > graph_data[
            "moment"
        ].replace(tzinfo=UTC):
            smt_transform.convert(smt_text["text"])
        else:
            model_text = smt_transform.transform()
            await replace_smt_text(smt_id, model_text)
        smt_model = smt_transform.destination_model
        operation = ConfigByImpact(ConfigByImpactRequest.impact)
        operation.execute(smt_model)
        result = operation.get_result()
        if not isinstance(result, str):
            result = await read_releases_by_counts(operation.get_result(), ConfigByImpactRequest.manager)
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
