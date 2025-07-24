from datetime import datetime, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, Request, status
from fastapi.responses import JSONResponse

from app.apis import get_last_commit_date_github
from app.limiter import limiter
from app.schemas import (
    GetPackageStatusRequest,
    GetRepositoriesRequest,
    GetVersionStatusRequest,
    InitPackageRequest,
    InitRepositoryRequest,
    InitVersionRequest,
)
from app.services import (
    exists_package,
    exists_version,
    read_package_by_name,
    read_package_status_by_name,
    read_repositories_by_user_id,
    read_repositories_update,
    read_version_status_by_package_and_name,
)
from app.utils import (
    JWTBearer,
    create_package,
    create_version,
    init_repository_graph,
    json_encoder,
    search_new_versions,
)

router = APIRouter()

@router.get("/graph/repositories/{user_id}", dependencies=[Depends(JWTBearer())], tags=["graph"])
@limiter.limit("25/minute")
async def get_repositories(request: Request, get_repositories_request: GetRepositoriesRequest = Depends()) -> JSONResponse:
    repositories = await read_repositories_by_user_id(get_repositories_request.user_id)
    return JSONResponse(status_code=status.HTTP_200_OK, content=json_encoder(repositories))


@router.get("/graph/package/status", tags=["graph"])
@limiter.limit("25/minute")
async def get_package_status(request: Request, get_package_status_request: GetPackageStatusRequest = Depends()) -> JSONResponse:
    package = await read_package_status_by_name(get_package_status_request.node_type.value, get_package_status_request.package_name)
    if not package:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=json_encoder({"message": "package_not_found"}),
        )
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=json_encoder(package),
    )


@router.get("/graph/version/status", tags=["graph"])
@limiter.limit("25/minute")
async def get_version_status(request: Request, get_version_status_request: GetVersionStatusRequest = Depends()) -> JSONResponse:
    package = await read_version_status_by_package_and_name(
        get_version_status_request.node_type.value,
        get_version_status_request.package_name,
        get_version_status_request.version_name
    )
    if not package:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=json_encoder({"message": "version_not_found"}),
        )
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=json_encoder(package),
    )


@router.post("/graph/version/init", dependencies=[Depends(JWTBearer())], tags=["graph"])
@limiter.limit("25/minute")
async def init_version(request: Request, init_version_request: InitVersionRequest) -> JSONResponse:
    exists = await exists_version(init_version_request.node_type.value, init_version_request.package_name, init_version_request.version_name)
    if not exists:
        exists = await exists_package(init_version_request.node_type.value, init_version_request.package_name)
        if exists:
            await create_version(init_version_request)
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=json_encoder({"message": "initializing"}),
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=json_encoder({"message": "package_not_found"}),
            )
    else:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=json_encoder({"message": "version_already_exists"}),
        )


@router.post("/graph/package/init", dependencies=[Depends(JWTBearer())], tags=["graph"])
@limiter.limit("25/minute")
async def init_package(request: Request, init_package_request: InitPackageRequest) -> JSONResponse:
    package = await read_package_by_name(init_package_request.node_type.value, init_package_request.package_name)
    if not package:
        await create_package(init_package_request)
    elif package["moment"] < datetime.now() - timedelta(days=10):
        await search_new_versions(package, init_package_request.node_type.value)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=json_encoder({"message": "initializing"}),
    )


@router.post("/graph/repository/init", dependencies=[Depends(JWTBearer())], tags=["graph"])
@limiter.limit("25/minute")
async def init_repository(request: Request, init_graph_request: InitRepositoryRequest, background_tasks: BackgroundTasks) -> JSONResponse:
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
        # background_tasks.add_task(init_repository_graph, init_graph_request, last_repository_update, last_commit_date)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=json_encoder({"message": "init_graph"}),
    )
