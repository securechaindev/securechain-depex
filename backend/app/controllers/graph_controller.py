from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, status
from fastapi.responses import JSONResponse
from pytz import UTC

from app.apis import (
    get_last_commit_date_github,
)
from app.models.graphs import InitPackageRequest, InitRepositoryRequest
from app.services import (
    create_repository,
    create_user_repository_rel,
    delete_requirement_file,
    delete_requirement_file_rel,
    read_package_by_name,
    read_packages_by_requirement_file,
    read_repositories,
    read_repositories_by_user_id,
    read_repositories_update,
    read_requirement_files_by_repository,
    update_repository_is_complete,
    update_repository_moment,
    update_repository_users,
    update_requirement_file_moment,
    update_requirement_rel_constraints,
)
from app.utils import JWTBearer, json_encoder, repo_analyzer

from .managers import (
    cargo_create_package,
    cargo_search_new_versions,
    maven_create_package,
    maven_create_requirement_file,
    maven_generate_packages,
    maven_search_new_versions,
    npm_create_package,
    npm_create_requirement_file,
    npm_generate_packages,
    npm_search_new_versions,
    nuget_create_package,
    nuget_search_new_versions,
    pypi_create_package,
    pypi_create_requirement_file,
    pypi_generate_packages,
    pypi_search_new_versions,
    rubygems_create_package,
    rubygems_search_new_versions,
)

router = APIRouter()


@router.get("/graph/repositories/{user_id}", dependencies=[Depends(JWTBearer())], tags=["graph"])
async def get_repositories(user_id: str) -> JSONResponse:
    repositories = await read_repositories_by_user_id(user_id)
    return JSONResponse(status_code=status.HTTP_200_OK, content=json_encoder(repositories))


# dependencies=[Depends(JWTBearer())], tags=["graph"]
@router.post("/graph/package/init")
async def init_package(init_package_request: InitPackageRequest) -> JSONResponse:
    init_package_request.name = init_package_request.name.lower()
    package = await read_package_by_name(init_package_request.node_type.value, init_package_request.name)
    if not package:
        await create_package(init_package_request)
    elif package["moment"] < datetime.now() - timedelta(days=10):
        await search_new_versions(package, init_package_request.node_type.value)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=json_encoder({"message": "initializing"}),
    )


async def create_package(init_package_request: InitPackageRequest) -> None:
    match init_package_request.node_type.value:
        case "CargoPackage":
            await cargo_create_package(init_package_request.name)
        case "MavenPackage":
            group_id, artifact_id = init_package_request.name.split(":")
            await maven_create_package(group_id, artifact_id)
        case "NPMPackage":
            await npm_create_package(init_package_request.name)
        case "NuGetPackage":
            await nuget_create_package(init_package_request.name)
        case "PyPIPackage":
            await pypi_create_package(init_package_request.name)
        case "RubyGemsPackage":
            await rubygems_create_package(init_package_request.name)


async def search_new_versions(package: dict[str, Any], node_type: str) -> None:
    match node_type:
        case "CargoPackage":
            await cargo_search_new_versions(package)
        case "MavenPackage":
            await maven_search_new_versions(package)
        case "NPMPackage":
            await npm_search_new_versions(package)
        case "NuGetPackage":
            await nuget_search_new_versions(package)
        case "PyPIPackage":
            await pypi_search_new_versions(package)
        case "RubyGemsPackage":
            await rubygems_search_new_versions(package)


# dependencies=[Depends(JWTBearer())], tags=["graph"]
@router.post("/graph/repository/init")
async def init_repository(init_graph_request: InitRepositoryRequest, background_tasks: BackgroundTasks) -> JSONResponse:
    repository = {
        "owner": init_graph_request.owner,
        "name": init_graph_request.name,
        "moment": datetime.now(),
        "add_extras": False,
        "is_complete": False,
        "user_id": init_graph_request.user_id
    }
    last_repository_update = await read_repositories_update(
        repository["owner"], repository["name"]
    )
    if last_repository_update["is_complete"]:
        last_commit_date = await get_last_commit_date_github(
            repository["owner"], repository["name"]
        )
        if not last_commit_date:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=json_encoder({"message": "no_repo"}),
            )
        await init_repository_graph(repository, last_repository_update, last_commit_date, init_graph_request.user_id)
        # background_tasks.add_task(init_repository_graph, repository, last_repository_update, last_commit_date, InitGraphRequest.user_id)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=json_encoder({"message": "init_graph"}),
    )


async def init_repository_graph(repository: dict[str, Any], last_repository_update: dict[str, datetime | bool], last_commit_date: datetime, user_id: str) -> None:
    if last_commit_date is not None and (
        not last_repository_update["moment"]
        or last_repository_update["moment"].replace(tzinfo=UTC)
        < last_commit_date.replace(tzinfo=UTC)
    ):
        repository_id = await read_repositories(
            repository["owner"], repository["name"]
        )
        raw_requirement_files = await repo_analyzer(
            repository["owner"], repository["name"]
        )
        if not repository_id:
            repository_id = await create_repository(repository)
            await extract_repository(
                raw_requirement_files, repository_id
            )
        else:
            await create_user_repository_rel(
                repository_id, user_id
            )
            await update_repository_is_complete(
                repository_id, False
            )
            await replace_repository(
                raw_requirement_files, repository_id
            )
        await update_repository_is_complete(
            repository_id, True
        )
    await update_repository_users(last_repository_update["id"], user_id)


async def extract_repository(
    raw_requirement_files: dict[str, Any], repository_id: str
) -> None:
    for name, file in raw_requirement_files.items():
        await select_manager(name, file, repository_id)


async def replace_repository(
    raw_requirement_files: dict[str, Any], repository_id: str, manager: str
) -> None:
    requirement_files = await read_requirement_files_by_repository(
        repository_id, manager
    )
    for file_name, requirement_file_id in requirement_files.items():
        if file_name not in raw_requirement_files:
            await delete_requirement_file(repository_id, file_name, manager)
        else:
            packages = await read_packages_by_requirement_file(
                requirement_file_id, manager
            )
            keys = raw_requirement_files[file_name]["dependencies"].keys()
            for group_package, constraints in packages.items():
                if manager == "maven":
                    group_id, package = group_package.split(":")
                else:
                    package = group_package
                if package in keys:
                    if (
                        constraints
                        != raw_requirement_files[file_name]["dependencies"][package]
                    ):
                        await update_requirement_rel_constraints(
                            requirement_file_id,
                            package,
                            raw_requirement_files[file_name]["dependencies"][package],
                            manager,
                        )
                else:
                    await delete_requirement_file_rel(
                        requirement_file_id, package, manager
                    )
                if manager == "maven":
                    pop_key = (group_id, package)
                else:
                    pop_key = package
                raw_requirement_files[file_name]["dependencies"].pop(pop_key)
            if raw_requirement_files[file_name]["dependencies"]:
                match manager:
                    case "pypi":
                        await pypi_generate_packages(
                            raw_requirement_files[file_name]["dependencies"],
                            requirement_file_id,
                        )
                    case "npm":
                        await npm_generate_packages(
                            raw_requirement_files[file_name]["dependencies"],
                            requirement_file_id,
                        )
                    case "maven":
                        await maven_generate_packages(
                            raw_requirement_files[file_name]["dependencies"],
                            requirement_file_id,
                        )
            await update_requirement_file_moment(requirement_file_id, manager)
        raw_requirement_files.pop(file_name)
    if raw_requirement_files:
        for name, file in raw_requirement_files.items():
            if file["manager"] == manager:
                await select_manager(manager, name, file, repository_id)
    await update_repository_moment(repository_id, manager)


async def select_manager(
    name: str, file: dict[str, Any], repository_id: str
) -> None:
    match file["manager"]:
        case "PyPI":
            await pypi_create_requirement_file(name, file, repository_id)
        case "NPM":
            await npm_create_requirement_file(name, file, repository_id)
        case "Maven":
            await maven_create_requirement_file(name, file, repository_id)
