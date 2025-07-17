from datetime import datetime, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, status
from fastapi.responses import JSONResponse

from app.apis import (
    get_last_commit_date_github,
)
from app.schemas import InitPackageRequest, InitRepositoryRequest
from app.services import (
    read_package_by_name,
    read_repositories_by_user_id,
    read_repositories_update,
)
from app.utils import (
    JWTBearer,
    create_package,
    init_repository_graph,
    json_encoder,
    search_new_versions,
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
