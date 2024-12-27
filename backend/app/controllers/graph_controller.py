from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, status
from fastapi.responses import JSONResponse
from pytz import UTC

from app.apis import get_last_commit_date_github
from app.models import InitGraphRequest
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

from .managers.mvn_generate_controller import (
    mvn_create_package,
    mvn_create_requirement_file,
    mvn_generate_packages,
    mvn_search_new_versions,
)
from .managers.npm_generate_controller import (
    npm_create_package,
    npm_create_requirement_file,
    npm_generate_packages,
    npm_search_new_versions,
)
from .managers.pip_generate_controller import (
    pip_create_package,
    pip_create_requirement_file,
    pip_generate_packages,
    pip_search_new_versions,
)

router = APIRouter()


@router.get("/graph/repositories/{user_id}", dependencies=[Depends(JWTBearer())], tags=["graph"])
async def get_repositories(user_id: str) -> JSONResponse:
    repositories = await read_repositories_by_user_id(user_id)
    return JSONResponse(status_code=status.HTTP_200_OK, content=json_encoder(repositories))

# dependencies=[Depends(JWTBearer())], tags=["graph"]
@router.post("/graph/pypi/package/init")
async def init_pypi_package(package_name: str) -> JSONResponse:
    package = await read_package_by_name(package_name, "PIP")
    if not package:
        await pip_create_package(package_name)
    elif package["moment"] < datetime.now() - timedelta(days=10):
        await pip_search_new_versions(package)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=json_encoder({"message": "Initializing graph"}),
    )


# dependencies=[Depends(JWTBearer())], tags=["graph"]
@router.post("/graph/npm/package/init")
async def init_npm_package(package_name: str) -> JSONResponse:
    package = await read_package_by_name(package_name, "NPM")
    if not package:
        await npm_create_package(package_name)
    elif package["moment"] < datetime.now() - timedelta(days=10):
        await npm_search_new_versions(package)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=json_encoder({"message": "initializing"}),
    )


@router.post("/graph/mvn/package/init", dependencies=[Depends(JWTBearer())], tags=["graph"])
async def init_mvn_package(group_id: str, artifact_id: str) -> JSONResponse:
    package = await read_package_by_name(artifact_id, "MVN")
    if not package:
        await mvn_create_package(group_id, artifact_id)
    elif package["moment"] < datetime.now() - timedelta(days=10):
        await mvn_search_new_versions(package)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=json_encoder({"message": "initializing"}),
    )


@router.post("/graph/init", dependencies=[Depends(JWTBearer())], tags=["graph"])
async def init_graph(InitGraphRequest: InitGraphRequest, background_tasks: BackgroundTasks) -> JSONResponse:
    repository = {
        "owner": InitGraphRequest.owner,
        "name": InitGraphRequest.name,
        "moment": datetime.now(),
        "add_extras": False,
        "is_complete": False,
        "user_id": InitGraphRequest.user_id
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
        background_tasks.add_task(init_graph_background, repository, last_repository_update, last_commit_date, InitGraphRequest.user_id)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=json_encoder({"message": "init_graph"}),
    )


async def init_graph_background(repository: dict[str, Any], last_repository_update: dict[str, datetime | bool], last_commit_date: datetime, user_id: str):
    if last_commit_date is not None and (
        not last_repository_update["moment"]
        or last_repository_update["moment"].replace(tzinfo=UTC)
        < last_commit_date.replace(tzinfo=UTC)
    ):
        repository_ids = await read_repositories(
            repository["owner"], repository["name"]
        )
        raw_requirement_files = await repo_analyzer(
            repository["owner"], repository["name"]
        )
        for package_manager, repository_id in repository_ids.items():
            if not repository_id:
                repository_id = await create_repository(repository, package_manager)
                await extract_repository(
                    raw_requirement_files, repository_id, package_manager
                )
            else:
                await create_user_repository_rel(
                    repository_id, user_id, package_manager
                )
                await update_repository_is_complete(
                    repository_id, False, package_manager
                )
                await replace_repository(
                    raw_requirement_files, repository_id, package_manager
                )
            await update_repository_is_complete(
                repository_id, True, package_manager
            )
    await update_repository_users(last_repository_update["id"], user_id)


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
            keys = raw_requirement_files[file_name]["dependencies"].keys()
            for group_package, constraints in packages.items():
                if package_manager == "MVN":
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
                            package_manager,
                        )
                else:
                    await delete_requirement_file_rel(
                        requirement_file_id, package, package_manager
                    )
                if package_manager == "MVN":
                    pop_key = (group_id, package)
                else:
                    pop_key = package
                raw_requirement_files[file_name]["dependencies"].pop(pop_key)
            if raw_requirement_files[file_name]["dependencies"]:
                match package_manager:
                    case "PIP":
                        await pip_generate_packages(
                            raw_requirement_files[file_name]["dependencies"],
                            requirement_file_id,
                        )
                    case "NPM":
                        await npm_generate_packages(
                            raw_requirement_files[file_name]["dependencies"],
                            requirement_file_id,
                        )
                    case "MVN":
                        await mvn_generate_packages(
                            raw_requirement_files[file_name]["dependencies"],
                            requirement_file_id,
                        )
            await update_requirement_file_moment(requirement_file_id, package_manager)
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
            await pip_create_requirement_file(name, file, repository_id)
        case "NPM":
            await npm_create_requirement_file(name, file, repository_id)
        case "MVN":
            await mvn_create_requirement_file(name, file, repository_id)
