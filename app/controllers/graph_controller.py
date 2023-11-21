from datetime import datetime
from typing import Any

from fastapi import APIRouter, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pytz import timezone

from app.apis import get_last_commit_date_github, get_repo_data, get_all_versions
from app.models import RepositoryModel, PackageModel
from app.services import (
    create_repository,
    create_package_and_versions,
    delete_requirement_file,
    delete_requirement_file_rel,
    read_graphs_by_owner_name_for_sigma,
    read_packages_by_requirement_file,
    read_repositories,
    read_repositories_moment,
    read_requirement_files_by_repository,
    update_repository_is_complete,
    update_repository_moment,
    update_requirement_rel_constraints,
)
from app.utils import json_encoder

from .managers.mvn_generate_controller import mvn_extract_graph, mvn_extract_package
from .managers.npm_generate_controller import npm_extract_graph, npm_extract_package
from .managers.pip_generate_controller import pip_extract_graph, pip_extract_package

router = APIRouter()


@router.get(
    "/graph/{owner}/{name}",
    summary="Get each package manager graph by the owner and name of a repository",
    response_description="Return a graph",
)
async def get_graphs(owner: str, name: str) -> JSONResponse:
    """
    Get each package manager graph by the owner and name of a repository:

    - **owner**: the owner of a repository
    - **name**: the name of a repository
    """
    # TODO: Hacer un servicio que devuelva todos los grafos por owner y name para mostrarlos en el FrontEnd
    # TODO: Añadir a Neo4J owner y name como un índice
    # TODO: Cambiar en los servicios la palabra relationships por edges
    graphs = await read_graphs_by_owner_name_for_sigma(owner, name)
    return JSONResponse(status_code=status.HTTP_200_OK, content=json_encoder(graphs))


@router.post(
    "/pypi/package/init", summary="Init a PyPI package", response_description="Initialize a PyPI package"
)
async def init_pypi_package(package_name: str) -> JSONResponse:
    """
    Starts graph extraction from a Python Package Index (PyPI) package:

    - **package_name**: the name of the package as it appears in PyPI
    """
    all_versions = get_all_versions("PIP", package_name=package_name)
    await create_package_and_versions({"name": package_name, "moment": datetime.now()}, all_versions, "PIP")
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=json_encoder({"message": "initializing"}),
    )

@router.post(
    "/npm/package/init", summary="Init a NPM package", response_description="Initialize a NPM package"
)
async def init_npm_package(package_name: str) -> JSONResponse:
    """
    Starts graph extraction from a Node Package Manager (NPM) package:

    - **package_name**: the name of the package as it appears in NPM
    """
    all_versions = get_all_versions("NPM", package_name=package_name)
    await create_package_and_versions({"name": package_name, "moment": datetime.now()}, all_versions, "NPM")
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=json_encoder({"message": "initializing"}),
    )


@router.post(
    "/mvn/package/init", summary="Init a Maven Central package", response_description="Initialize a Maven Central package"
)
async def init_mvn_package(group_id: str, artifact_id: str) -> JSONResponse:
    """
    Starts graph extraction from a Maven Central package:

    - **group_id**: the group_id of the package as it appears in Maven Central
    - **artifact_id**: the artifact_id of the package as it appears in Maven Central
    """
    all_versions = get_all_versions("MVN", package_artifact_id=artifact_id ,package_group_id=group_id)
    await create_package_and_versions({"name": artifact_id, "group_id": group_id, "moment": datetime.now()}, all_versions, "MVN")
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=json_encoder({"message": "initializing"}),
    )


@router.post(
    "/graph/init", summary="Init a graph", response_description="Initialize a graph"
)
async def init_graph(owner: str, name: str) -> JSONResponse:
    """
    Starts graph extraction from a GitHub repository:

    - **owner**: the owner of a repository
    - **name**: the name of a repository
    """
    repository = {
        "owner": owner,
        "name": name,
        "moment": datetime.now(timezone("Europe/Madrid")),
        "add_extras": False,
        "is_complete": False,
    }
    last_repository = await read_repositories_moment(
        repository["owner"], repository["name"]
    )
    if last_repository["is_complete"]:
        last_commit_date = await get_last_commit_date_github(
            repository["owner"], repository["name"]
        )
        if (
            not last_repository["moment"]
            or last_repository["moment"] < last_commit_date
        ):
            repository_ids = await read_repositories(
                repository["owner"], repository["name"]
            )
            raw_requirement_files = await get_repo_data(
                repository["owner"], repository["name"]
            )
            for package_manager, repository_id in repository_ids.items():
                if not repository_id:
                    repository_id = await create_repository(
                        repository, package_manager
                    )
                    await extract_repository(
                        raw_requirement_files, repository_id, package_manager
                    )
                else:
                    await update_repository_is_complete(
                        repository_id, False, package_manager
                    )
                    await replace_repository(
                        raw_requirement_files, repository_id, package_manager
                    )
                await update_repository_is_complete(
                    repository_id, True, package_manager
                )
        else:
            # TODO: Devolver el grafo actual de la misma forma que en get_graphs
            pass
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=json_encoder({"message": "initializing"}),
    )


async def extract_repository(
    raw_requirement_files: dict[str, Any], repository_id: str, package_manager: str
) -> None:
    for name, file in raw_requirement_files.items():
        if file["package_manager"] == package_manager:
            await select_manager(package_manager, name, file, repository_id)


async def replace_repository(
    raw_requirement_files: dict[str, Any], repository_id: str, package_manager: str
) -> None:
    requirement_files = await read_requirement_files_by_repository(
        repository_id, package_manager
    )
    for file_name, requirement_file_id in requirement_files.items():
        if file_name not in raw_requirement_files:
            await delete_requirement_file(repository_id, file_name, package_manager)
        else:
            packages = await read_packages_by_requirement_file(
                requirement_file_id, package_manager
            )
            for package, constraints in packages.items():
                keys = raw_requirement_files[file_name]["dependencies"].keys()
                if package in keys:
                    if (
                        constraints
                        != raw_requirement_files[file_name]["dependencies"][package]
                    ):
                        await update_requirement_rel_constraints(
                            requirement_file_id,
                            package,
                            raw_requirement_files[file_name]["dependencies"][package],
                            package_manager,
                        )
                        raw_requirement_files[file_name]["dependencies"].pop(package)
                    else:
                        await delete_requirement_file_rel(
                            requirement_file_id, package, package_manager
                        )
                if raw_requirement_files[file_name]["dependencies"]:
                    for package, constraints in raw_requirement_files[file_name][
                        "dependencies"
                    ].items():
                        match package_manager:
                            case "PIP":
                                await pip_extract_package(
                                    package, constraints, requirement_file_id
                                )
                            case "NPM":
                                await npm_extract_package(
                                    package, constraints, requirement_file_id
                                )
                            case "MVN":
                                await mvn_extract_package(
                                    package, constraints, requirement_file_id
                                )
                raw_requirement_files.pop(file_name)
        if raw_requirement_files:
            for name, file in raw_requirement_files.items():
                if file["package_manager"] == package_manager:
                    await select_manager(package_manager, name, file, repository_id)
        await update_repository_moment(repository_id, package_manager)


async def select_manager(
    package_manager: str, name: str, file: dict[str, Any], repository_id: str
) -> None:
    match package_manager:
        case "PIP":
            await pip_extract_graph(name, file, repository_id)
        case "NPM":
            await npm_extract_graph(name, file, repository_id)
        case "MVN":
            await mvn_extract_graph(name, file, repository_id)
