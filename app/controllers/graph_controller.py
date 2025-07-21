from datetime import datetime, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, status
from fastapi.responses import JSONResponse

from app.apis import (
    get_last_commit_date_github,
)
from app.schemas import (
    GetPackageStatusRequest,
    GetRepositoriesRequest,
    GetVersionStatusRequest,
    InitPackageRequest,
    InitRepositoryRequest,
    InitVersionRequest
)
from app.services import (
    read_package_by_name,
    read_package_status_by_name,
    read_version_status_by_package_and_name,
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
async def get_repositories(get_repositories_request: GetRepositoriesRequest = Depends()) -> JSONResponse:
    repositories = await read_repositories_by_user_id(get_repositories_request.user_id)
    return JSONResponse(status_code=status.HTTP_200_OK, content=json_encoder(repositories))


@router.post("/graph/package/init", dependencies=[Depends(JWTBearer())], tags=["graph"])
async def init_package(init_package_request: InitPackageRequest) -> JSONResponse:
    package = await read_package_by_name(init_package_request.node_type.value, init_package_request.name)
    if not package:
        await create_package(init_package_request)
    elif package["moment"] < datetime.now() - timedelta(days=10):
        await search_new_versions(package, init_package_request.node_type.value)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=json_encoder({"message": "initializing"}),
    )


@router.post("/graph/repository/init", dependencies=[Depends(JWTBearer())], tags=["graph"])
async def init_repository(init_graph_request: InitRepositoryRequest, background_tasks: BackgroundTasks) -> JSONResponse:
    last_repository_update = await read_repositories_update(
        init_graph_request.owner, init_graph_request.name
    )
    if last_repository_update["is_complete"]:
        last_commit_date = await get_last_commit_date_github(
            init_graph_request.owner, init_graph_request.name
        )
        if not last_commit_date:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=json_encoder({"message": "no_repo"}),
            )
        await init_repository_graph(init_graph_request, last_repository_update, last_commit_date)
        # background_tasks.add_task(init_repository_graph, repository, last_repository_update, last_commit_date)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=json_encoder({"message": "init_graph"}),
    )
