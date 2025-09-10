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
    create_user_repository_rel,
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

@router.get(
    "/graph/repositories/{user_id}",
    summary="Get User Repositories",
    description="Retrieve a list of repositories for a specific user.",
    response_description="List of user repositories.",
    dependencies=[Depends(JWTBearer())],
    tags=["Secure Chain Depex - Graph"]
)
@limiter.limit("25/minute")
async def get_repositories(request: Request, get_repositories_request: GetRepositoriesRequest = Depends()) -> JSONResponse:
    repositories = await read_repositories_by_user_id(get_repositories_request.user_id)
    return JSONResponse(status_code=status.HTTP_200_OK, content= await json_encoder({
        "repositories": repositories,
        "detail": "get_repositories_success",
    }))


@router.get(
    "/graph/package/status",
    summary="Get Package Status",
    description="Retrieve the status of a specific package.",
    response_description="Package status.",
    tags=["Secure Chain Depex - Graph"]
)
@limiter.limit("25/minute")
async def get_package_status(request: Request, get_package_status_request: GetPackageStatusRequest = Depends()) -> JSONResponse:
    package = await read_package_status_by_name(get_package_status_request.node_type.value, get_package_status_request.package_name)
    if not package:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content= await json_encoder(
                {
                    "detail": "package_not_found",
                }
            ),
        )
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content= await json_encoder({
            "package": package,
            "detail": "get_package_status_success",
        })
    )


@router.get(
    "/graph/version/status",
    summary="Get Version Status",
    description="Retrieve the status of a specific version.",
    response_description="Version status.",
    tags=["Secure Chain Depex - Graph"]
)
@limiter.limit("25/minute")
async def get_version_status(request: Request, get_version_status_request: GetVersionStatusRequest = Depends()) -> JSONResponse:
    version = await read_version_status_by_package_and_name(
        get_version_status_request.node_type.value,
        get_version_status_request.package_name,
        get_version_status_request.version_name
    )
    if not version:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content= await json_encoder(
                {
                    "detail": "version_not_found",
                }
            ),
        )
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content= await json_encoder({
            "version": version,
            "detail": "get_version_status_success",
        }),
    )


@router.post(
    "/graph/version/init",
    summary="Initialize Version",
    description="Initialize a specific version.",
    response_description="Version initialization status.",
    dependencies=[Depends(JWTBearer())],
    tags=["Secure Chain Depex - Graph"]
)
@limiter.limit("25/minute")
async def init_version(request: Request, init_version_request: InitVersionRequest, background_tasks: BackgroundTasks) -> JSONResponse:
    exists = await exists_version(init_version_request.node_type.value, init_version_request.package_name, init_version_request.version_name)
    if not exists:
        exists = await exists_package(init_version_request.node_type.value, init_version_request.package_name)
        if exists:
            background_tasks.add_task(create_version, init_version_request)
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content= await json_encoder(
                    {
                        "detail": "version_initializing",
                    }
                ),
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content= await json_encoder(
                    {
                        "detail": "package_not_found",
                    }
                ),
            )
    else:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content= await json_encoder(
                {
                    "detail": "version_already_exists",
                }
            ),
        )


@router.post(
    "/graph/package/init",
    summary="Initialize Package",
    description="Initialize a specific package.",
    response_description="Package initialization status.",
    dependencies=[Depends(JWTBearer())],
    tags=["Secure Chain Depex - Graph"]
)
@limiter.limit("25/minute")
async def init_package(request: Request, init_package_request: InitPackageRequest, background_tasks: BackgroundTasks) -> JSONResponse:
    package = await read_package_by_name(init_package_request.node_type.value, init_package_request.package_name)
    if not package:
        background_tasks.add_task(create_package, init_package_request)
    elif package["moment"] < datetime.now() - timedelta(days=10):
        background_tasks.add_task(search_new_versions, package, init_package_request.node_type.value)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content= await json_encoder(
            {
                "detail": "package_initializing",
            }
        ),
    )


@router.post(
    "/graph/repository/init",
    summary="Initialize Repository",
    description="Initialize a specific repository.",
    response_description="Repository initialization status.",
    dependencies=[Depends(JWTBearer())],
    tags=["Secure Chain Depex - Graph"]
)
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
                content= await json_encoder(
                    {
                        "detail": "no_repo",
                    }
                ),
            )
        background_tasks.add_task(init_repository_graph, init_graph_request, last_repository_update, last_commit_date)
    else:
        await create_user_repository_rel(
            last_repository_update["id"], init_graph_request.user_id
        )
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content= await json_encoder(
            {
                "detail": "init_repo",
            }
        ),
    )
