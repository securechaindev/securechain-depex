from fastapi import APIRouter, BackgroundTasks, Depends, Request, status
from fastapi.responses import JSONResponse

from app.apis import GitHubService
from app.constants import ResponseCode, ResponseMessage
from app.dependencies import (
    get_dual_auth_bearer,
    get_github_service,
    get_json_encoder,
    get_package_service,
    get_redis_queue,
    get_repository_service,
)
from app.domain import RepositoryInitializer
from app.limiter import limiter
from app.schemas import (
    GetPackageStatusRequest,
    GetVersionStatusRequest,
    InitPackageRequest,
    InitRepositoryRequest,
    PackageMessageSchema,
)
from app.services import PackageService, RepositoryService
from app.utils import JSONEncoder, RedisQueue

router = APIRouter()

@router.get(
    "/graph/repositories",
    summary="Get User Repositories",
    description="Retrieve a list of repositories for the authenticated user.",
    response_description="List of user repositories.",
    tags=["Secure Chain Depex - Graph"]
)
@limiter.limit("25/minute")
async def get_repositories(
    request: Request,
    payload: dict = Depends(get_dual_auth_bearer()),
    repository_service: RepositoryService = Depends(get_repository_service),
    json_encoder: JSONEncoder = Depends(get_json_encoder),
) -> JSONResponse:
    user_id = payload.get("user_id")
    repositories = await repository_service.read_repositories_by_user_id(user_id)
    return JSONResponse(status_code=status.HTTP_200_OK, content=json_encoder.encode({
        "code": ResponseCode.GET_REPOSITORIES_SUCCESS,
        "message": ResponseMessage.REPOSITORIES_RETRIEVED_SUCCESS,
        "data": repositories
    }))


@router.get(
    "/graph/package/status",
    summary="Get Package Status",
    description="Retrieve the status of a specific package.",
    response_description="Package status.",
    dependencies=[Depends(get_dual_auth_bearer())],
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
            content=json_encoder.encode(
                {
                    "code": ResponseCode.PACKAGE_NOT_FOUND,
                    "message": ResponseMessage.PACKAGE_NOT_FOUND,
                }
            ),
        )
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=json_encoder.encode({
            "code": ResponseCode.GET_PACKAGE_STATUS_SUCCESS,
            "message": ResponseMessage.PACKAGE_STATUS_RETRIEVED_SUCCESS,
            "data": package
        })
    )


@router.get(
    "/graph/version/status",
    summary="Get Version Status",
    description="Retrieve the status of a specific version.",
    response_description="Version status.",
    dependencies=[Depends(get_dual_auth_bearer())],
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
            content=json_encoder.encode(
                {
                    "code": ResponseCode.VERSION_NOT_FOUND,
                    "message": ResponseMessage.VERSION_NOT_FOUND,
                }
            ),
        )
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=json_encoder.encode({
            "code": ResponseCode.GET_VERSION_STATUS_SUCCESS,
            "message": ResponseMessage.VERSION_STATUS_RETRIEVED_SUCCESS,
            "data": version
        }),
    )


@router.post(
    "/graph/package/init",
    summary="Initialize Package",
    description="Queue a package for extraction and analysis. The package will be processed asynchronously by Dagster.",
    response_description="Package queuing status.",
    dependencies=[Depends(get_dual_auth_bearer())],
    tags=["Secure Chain Depex - Graph"]
)
@limiter.limit("25/minute")
async def init_package(
    request: Request,
    init_package_request: InitPackageRequest,
    redis_queue: RedisQueue = Depends(get_redis_queue),
    json_encoder: JSONEncoder = Depends(get_json_encoder),
) -> JSONResponse:
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

    redis_queue.add_package_message(message)

    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content=json_encoder.encode({
            "code": ResponseCode.PACKAGE_QUEUED_FOR_PROCESSING,
            "message": ResponseMessage.PACKAGE_QUEUED,
        }),
    )


@router.post(
    "/graph/repository/init",
    summary="Initialize Repository",
    description="Initialize a repository by creating it in the graph and queuing its packages for extraction.",
    response_description="Repository initialization status.",
    tags=["Secure Chain Depex - Graph"]
)
@limiter.limit("25/minute")
async def init_repository(
    request: Request,
    init_repository_request: InitRepositoryRequest,
    background_tasks: BackgroundTasks,
    payload: dict = Depends(get_dual_auth_bearer()),
    repository_service: RepositoryService = Depends(get_repository_service),
    github_service: GitHubService = Depends(get_github_service),
    json_encoder: JSONEncoder = Depends(get_json_encoder),
) -> JSONResponse:
    user_id = payload.get("user_id")

    last_commit_date = await github_service.get_last_commit_date(
        init_repository_request.owner,
        init_repository_request.name
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
            user_id,
            repository,
            last_commit_date,
        )

        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content=json_encoder.encode({
                "code": ResponseCode.REPOSITORY_QUEUED_FOR_PROCESSING,
                "message": ResponseMessage.REPOSITORY_QUEUED,
                "data": {
                    "repository": f"{init_repository_request.owner}/{init_repository_request.name}"
                }
            }),
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=json_encoder.encode({
                "code": ResponseCode.REPOSITORY_PROCESSING_IN_PROGRESS,
                "message": ResponseMessage.REPOSITORY_PROCESSING,
                "data": {
                    "repository_id": repository["id"]
                }
            }),
        )
