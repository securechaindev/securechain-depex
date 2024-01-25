from fastapi import APIRouter, status, Path, Query
from fastapi.responses import JSONResponse
from flamapy.metamodels.smt_metamodel.operations import (
    CompleteConfig,
    ConfigByImpact,
    ValidConfig,
)
from flamapy.metamodels.smt_metamodel.transformations import GraphToSMT
from app.services import (
    read_counts_by_releases,
    read_data_for_smt_transform,
    read_releases_by_counts,
)
from app.models import PackageManager, Agregator
from app.utils import json_encoder
from typing_extensions import Annotated

router = APIRouter()


@router.post(
    "/operation/config/valid_config/{requirement_file_id}",
    summary="Validates a configuration",
    response_description="Return True if valid, False if not",
)
async def valid_config(
    requirement_file_id: Annotated[str, Path(pattern="^4:[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}:[0-9]+$")],
    max_level: Annotated[int, Query(ge=-1)],
    package_manager: PackageManager,
    agregator: Agregator,
    config: dict[str, str]
) -> JSONResponse:
    """
    Validates a configuration satisfiability into a graph by the constraints over dependencies:

    - **requirement_file_id**: the id of a requirement file
    - **max_level**: the depth of the graph to be analysed
    - **package_manager**: package manager of the requirement file
    - **agregator**: agregator function to build the smt model
    - **config**: configuration containing the name of the dependency and the version to be chosen
    """
    graph_data = await read_data_for_smt_transform(
        requirement_file_id, package_manager, max_level
    )
    if graph_data["name"] is not None:
        smt_transform = GraphToSMT(graph_data, package_manager, agregator)
        smt_transform.transform()
        smt_model = smt_transform.destination_model
        operation = ValidConfig(await read_counts_by_releases(config, package_manager))
        operation.execute(smt_model)
        result = {"is_valid": operation.get_result()}
        return JSONResponse(status_code=status.HTTP_200_OK, content=json_encoder(result))
    else:
        return JSONResponse(status_code=status.HTTP_200_OK, content=json_encoder({"message": "The requirement file don't have dependencies"}))


@router.post(
    "/operation/config/complete_config/{requirement_file_id}",
    summary="Complete a configuration",
    response_description="Return a configuration of versions",
)
async def complete_config(
    requirement_file_id: Annotated[str, Path(pattern="^4:[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}:[0-9]+$")],
    max_level: Annotated[int, Query(ge=-1)],
    package_manager: PackageManager,
    agregator: Agregator,
    config: dict[str, str]
) -> JSONResponse:
    """
    Complete a partial configuration with the minimun posible impact:

    - **requirement_file_id**: the id of a requirement file
    - **max_level**: the depth of the graph to be analysed
    - **package_manager**: package manager of the requirement file
    - **agregator**: agregator function to build the smt model
    - **config**: partial configuration containing the name and the version of each dependency
    """
    graph_data = await read_data_for_smt_transform(
        requirement_file_id, package_manager, max_level
    )
    if graph_data["name"] is not None:
        smt_transform = GraphToSMT(graph_data, package_manager, agregator)
        smt_transform.transform()
        smt_model = smt_transform.destination_model
        operation = CompleteConfig(await read_counts_by_releases(config, package_manager))
        operation.execute(smt_model)
        result = await read_releases_by_counts(operation.get_result(), package_manager)
        return JSONResponse(
            status_code=status.HTTP_200_OK, content=json_encoder({"result": result})
        )
    else:
        return JSONResponse(status_code=status.HTTP_200_OK, content=json_encoder({"message": "The requirement file don't have dependencies"}))


@router.post(
    "/operation/config/config_by_impact/{graph_id}",
    summary="Get a configuration by impact operation",
    response_description="Return a configuration of versions",
)
async def config_by_impact(
    requirement_file_id: Annotated[str, Path(pattern="^4:[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}:[0-9]+$")],
    max_level: Annotated[int, Query(ge=-1)],
    impact: Annotated[float, Query(ge=0, le=10)],
    package_manager: PackageManager,
    agregator: Agregator
) -> JSONResponse:
    """
    Return a configuration witn an impact as close as possible to the given impact:

    - **requirement_file_id**: the id of a requirement file
    - **max_level**: the depth of the graph to be analysed
    - **impact**: impact floating number between 0.0 and 10.0
    - **package_manager**: package manager of the requirement file
    - **agregator**: agregator function to build the smt model
    """
    graph_data = await read_data_for_smt_transform(
        requirement_file_id, package_manager, max_level
    )
    if graph_data["name"] is not None:
        smt_transform = GraphToSMT(graph_data, package_manager, agregator)
        smt_transform.transform()
        smt_model = smt_transform.destination_model
        operation = ConfigByImpact(impact)
        operation.execute(smt_model)
        result = await read_releases_by_counts(operation.get_result(), package_manager)
        return JSONResponse(
            status_code=status.HTTP_200_OK, content=json_encoder({"result": result})
        )
    else:
        return JSONResponse(status_code=status.HTTP_200_OK, content=json_encoder({"message": "The requirement file don't have dependencies"}))
