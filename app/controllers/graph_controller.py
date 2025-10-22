from fastapi import APIRouter, BackgroundTasks, Depends, Request, status
from fastapi.responses import JSONResponse

from app.apis import get_last_commit_date_github
from app.dependencies import (
    get_json_encoder,
    get_jwt_bearer,
    get_package_service,
    get_repository_service,
)
from app.domain import RepositoryInitializer
from app.exceptions import InvalidRepositoryException
from app.limiter import limiter
from app.schemas import (
    GetPackageStatusRequest,
    GetRepositoriesRequest,
    GetVersionStatusRequest,
    InitPackageRequest,
    InitRepositoryRequest,
    PackageMessageSchema,
)
from app.services import PackageService, RepositoryService
from app.utils import JSONEncoder, RedisQueue

router = APIRouter()

@router.get(
    "/graph/repositories/{user_id}",
    summary="Get User Repositories",
    description="Retrieve a list of repositories for a specific user.",
    response_description="List of user repositories.",
    dependencies=[Depends(get_jwt_bearer())],
    tags=["Secure Chain Depex - Graph"]
)
@limiter.limit("25/minute")
async def get_repositories(
    request: Request,
    get_repositories_request: GetRepositoriesRequest = Depends(),
    repository_service: RepositoryService = Depends(get_repository_service),
    json_encoder: JSONEncoder = Depends(get_json_encoder),
) -> JSONResponse:
    repositories = await repository_service.read_repositories_by_user_id(get_repositories_request.user_id)
    return JSONResponse(status_code=status.HTTP_200_OK, content= await json_encoder.encode({
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
async def get_package_status(
    request: Request,
    get_package_status_request: GetPackageStatusRequest = Depends(),
    package_service: PackageService = Depends(get_package_service),
    json_encoder: JSONEncoder = Depends(get_json_encoder),
) -> JSONResponse:
    package = await package_service.read_package_status_by_name(get_package_status_request.node_type.value, get_package_status_request.package_name)
    if not package:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content= await json_encoder.encode(
                {
                    "detail": "package_not_found",
                }
            ),
        )
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content= await json_encoder.encode({
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
async def get_version_status(
    request: Request,
    get_version_status_request: GetVersionStatusRequest = Depends(),
    package_service: PackageService = Depends(get_package_service),
    json_encoder: JSONEncoder = Depends(get_json_encoder),
) -> JSONResponse:
    version = await package_service.read_version_status_by_package_and_name(
        get_version_status_request.node_type.value,
        get_version_status_request.package_name,
        get_version_status_request.version_name
    )
    if not version:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content= await json_encoder.encode(
                {
                    "detail": "version_not_found",
                }
            ),
        )
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content= await json_encoder.encode({
            "version": version,
            "detail": "get_version_status_success",
        }),
    )


@router.post(
    "/graph/package/init",
    summary="Initialize Package",
    description="Queue a package for extraction and analysis. The package will be processed asynchronously by Dagster.",
    response_description="Package queuing status.",
    dependencies=[Depends(get_jwt_bearer())],
    tags=["Secure Chain Depex - Graph"]
)
@limiter.limit("25/minute")
async def init_package(
    request: Request,
    init_package_request: InitPackageRequest,
    json_encoder: JSONEncoder = Depends(get_json_encoder),
) -> JSONResponse:
    try:
        message = PackageMessageSchema(
            node_type=init_package_request.node_type.value,
            package=init_package_request.package_name,
            vendor=init_package_request.vendor,
            repository_url=init_package_request.repository_url,
            constraints=init_package_request.constraints,
            parent_id=init_package_request.parent_id,
            parent_version=init_package_request.parent_version,
            refresh=init_package_request.refresh,
        )

        redis_queue = RedisQueue.from_env()
        msg_id = redis_queue.add_package_message(message)

        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content=await json_encoder.encode({
                "detail": "package_queued_for_processing",
                "message_id": msg_id,
                "package": init_package_request.package_name,
            }),
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=await json_encoder.encode({
                "detail": "error_queuing_package",
                "error": str(e),
            }),
        )


@router.post(
    "/graph/repository/init",
    summary="Initialize Repository",
    description="Initialize a repository by creating it in the graph and queuing its packages for extraction.",
    response_description="Repository initialization status.",
    dependencies=[Depends(get_jwt_bearer())],
    tags=["Secure Chain Depex - Graph"]
)
@limiter.limit("25/minute")
async def init_repository(
    request: Request,
    init_repository_request: InitRepositoryRequest,
    background_tasks: BackgroundTasks,
    repository_service: RepositoryService = Depends(get_repository_service),
    json_encoder: JSONEncoder = Depends(get_json_encoder),
) -> JSONResponse:
    try:
        try:
            last_commit_date = await get_last_commit_date_github(
                init_repository_request.owner,
                init_repository_request.name
            )
        except InvalidRepositoryException:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=await json_encoder.encode({
                    "detail": "repository_not_found_on_github",
                }),
            )

        repository = await repository_service.read_repository_by_owner_and_name(
            init_repository_request.owner,
            init_repository_request.name
        )

        if repository is None or repository["is_complete"]:
            background_tasks.add_task(
                RepositoryInitializer().init_repository,
                init_repository_request.owner,
                init_repository_request.name,
                init_repository_request.user_id,
                repository,
                last_commit_date,
            )

            return JSONResponse(
                status_code=status.HTTP_202_ACCEPTED,
                content=await json_encoder.encode({
                    "detail": "repository_queued_for_processing",
                    "repository": f"{init_repository_request.owner}/{init_repository_request.name}",
                }),
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content=await json_encoder.encode({
                    "detail": "repository_processing_in_progress",
                    "repository_id": repository["id"],
                }),
            )

    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=await json_encoder.encode({
                "detail": "error_initializing_repository",
                "error": str(e),
            }),
        )
