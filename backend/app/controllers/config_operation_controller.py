from fastapi import APIRouter, Body, status
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
from app.utils import json_encoder

router = APIRouter()

@router.post(
    "/operation/config/valid_config",
    summary="Validates a configuration",
    response_description="Return True if valid, False if not",
)
async def valid_config(
    ValidConfigRequest: Annotated[ValidConfigRequest, Body()]
) -> JSONResponse:
    """
    Validates a configuration satisfiability into a graph by the constraints over dependencies:

    - **requirement_file_id**: the id of a requirement file
    - **max_level**: the depth of the graph to be analysed
    - **package_manager**: package manager of the requirement file
    - **agregator**: agregator function to build the smt model
    - **config**: configuration containing the name of the dependency and the version to be chosen
    """
    graph_data = await read_data_for_smt_transform(jsonable_encoder(ValidConfigRequest))
    smt_id = f"{ValidConfigRequest.requirement_file_id}-{ValidConfigRequest.max_level}"
    if graph_data["name"] is not None:
        smt_transform = GraphToSMT(graph_data, ValidConfigRequest.package_manager, ValidConfigRequest.agregator)
        smt_text = await read_smt_text(smt_id)
        if smt_text is not None and smt_text["moment"].replace(tzinfo=UTC) > graph_data[
            "moment"
        ].replace(tzinfo=UTC):
            smt_transform.convert(smt_text["text"])
        else:
            model_text = smt_transform.transform()
            await replace_smt_text(smt_id, model_text)
        smt_model = smt_transform.destination_model
        operation = ValidConfig(await read_counts_by_releases(ValidConfigRequest.config, ValidConfigRequest.package_manager))
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


@router.post(
    "/operation/config/complete_config",
    summary="Complete a configuration",
    response_description="Return a configuration of versions",
)
async def complete_config(
    CompleteConfigRequest: Annotated[CompleteConfigRequest, Body()]
) -> JSONResponse:
    """
    Complete a partial configuration with the minimun posible impact:

    - **requirement_file_id**: the id of a requirement file
    - **max_level**: the depth of the graph to be analysed
    - **package_manager**: package manager of the requirement file
    - **agregator**: agregator function to build the smt model
    - **config**: partial configuration containing the name and the version of each dependency
    """
    graph_data = await read_data_for_smt_transform(jsonable_encoder(CompleteConfigRequest))
    smt_id = f"{CompleteConfigRequest.requirement_file_id}-{CompleteConfigRequest.max_level}"
    if graph_data["name"] is not None:
        smt_transform = GraphToSMT(graph_data, CompleteConfigRequest.package_manager, CompleteConfigRequest.agregator)
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
            await read_counts_by_releases(CompleteConfigRequest.config, CompleteConfigRequest.package_manager)
        )
        operation.execute(smt_model)
        result = await read_releases_by_counts(operation.get_result(), CompleteConfigRequest.package_manager)
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


@router.post(
    "/operation/config/config_by_impact",
    summary="Get a configuration by impact operation",
    response_description="Return a configuration of versions",
)
async def config_by_impact(
    ConfigByImpactRequest: Annotated[ConfigByImpactRequest, Body()]
) -> JSONResponse:
    """
    Return a configuration witn an impact as close as possible to the given impact:

    - **requirement_file_id**: the id of a requirement file
    - **max_level**: the depth of the graph to be analysed
    - **impact**: impact floating number between 0.0 and 10.0
    - **package_manager**: package manager of the requirement file
    - **agregator**: agregator function to build the smt model
    """
    graph_data = await read_data_for_smt_transform(jsonable_encoder(ConfigByImpactRequest))
    smt_id = f"{ConfigByImpactRequest.requirement_file_id}-{ConfigByImpactRequest.max_level}"
    if graph_data["name"] is not None:
        smt_transform = GraphToSMT(graph_data, ConfigByImpactRequest.package_manager, ConfigByImpactRequest.agregator)
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
        result = await read_releases_by_counts(operation.get_result(), ConfigByImpactRequest.package_manager)
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
