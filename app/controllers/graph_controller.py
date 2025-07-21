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


# TODO: Hacer una llamada para devolver la información de un paquete
@router.get("/graph/package/status", tags=["graph"])
async def get_package_status(get_package_status_request: GetPackageStatusRequest = Depends()) -> JSONResponse:
    package = await read_package_status_by_name(get_package_status_request.node_type.value, get_package_status_request.name)
    if not package:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=json_encoder({"message": "package_not_found"}),
        )
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=json_encoder(package),
    )


# TODO: Hacer una llamada para ver el estado de una versión de un paquete
@router.get("/graph/version/status", tags=["graph"])
async def get_version_status(get_version_status_request: GetVersionStatusRequest = Depends()) -> JSONResponse:
    package = await read_version_status_by_package_and_name(
        get_version_status_request.node_type.value,
        get_version_status_request.package_name,
        get_version_status_request.name
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


# TODO: Hacer una llamada para que se inicialice una versión de un paquete
@router.post("/graph/version/init", dependencies=[Depends(JWTBearer())], tags=["graph"])
async def init_version(init_version_request: InitVersionRequest) -> JSONResponse:
    pass


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
        # background_tasks.add_task(init_repository_graph, init_graph_request, last_repository_update, last_commit_date)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=json_encoder({"message": "init_graph"}),
    )
