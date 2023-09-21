from typing import Any
from pytz import timezone
from datetime import datetime
from fastapi import APIRouter, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from app.services import (
    create_repository,
    read_graph_by_repository_id,
    read_repositories,
    read_repositories_moment,
    read_requirement_files_by_repository,
    delete_requirement_file,
    read_packages_by_requirement_file,
    update_requirement_rel_constraints,
    delete_requirement_file_rel,
    update_repository_moment
)
from app.models import RepositoryModel
from app.utils import json_encoder
from app.apis import get_repo_data, get_last_commit_date
from .managers.pip_generate_controller import pip_extract_graph, pip_exist_package
from .managers.npm_generate_controller import npm_extract_graph, npm_exist_package
from .managers.mvn_generate_controller import mvn_extract_graph, mvn_exist_package

router = APIRouter()

@router.get(
    '/graph/{repository_id}',
    summary='Get a graph by a repository id',
    response_description='Return a graph'
)
async def get_graph(repository_id: str) -> JSONResponse:
    '''
    Return a graph by a given repository id. If attribute is_complete is True
    the graph is wholly built:

    - **repository_id**: the id of a repository
    '''
    graph = await read_graph_by_repository_id(repository_id, '_')
    return JSONResponse(status_code=status.HTTP_200_OK, content=graph)


@router.post(
    '/graph/init',
    summary='Init a graph',
    response_description='Initialize a graph'
)
async def init_graph(repository: RepositoryModel) -> JSONResponse:
    '''
    Starts graph extraction in its initial state, i.e., not complete:

    - **repository**: a json containing the owner and the name of a repository
    '''
    repository_json = jsonable_encoder(repository)
    repository_json['moment'] = datetime.now(timezone('Europe/Madrid'))
    last_repository_moment = await read_repositories_moment(repository_json['owner'], repository_json['name'])
    last_commit_date = await get_last_commit_date(repository_json['owner'], repository_json['name'])
    if not last_repository_moment or last_repository_moment < last_commit_date:
        repository_ids = await read_repositories(repository_json['owner'], repository_json['name'])
        files = await get_repo_data(repository_json['owner'], repository_json['name'])
        for package_manager, repository_id in repository_ids.items():
            if not repository_id:
                for name, file in files.items():
                    if file['package_manager'] == package_manager:
                        await select_manager(package_manager, name, file, repository_json=repository_json)
            else:
                requirement_files = await read_requirement_files_by_repository(repository_id, package_manager)
                for file_name, requirement_file_id in requirement_files.items():
                    if file_name not in files:
                        await delete_requirement_file(repository_id, file_name, package_manager)
                    else:
                        packages = await read_packages_by_requirement_file(requirement_file_id, package_manager)
                        for package, constraints in packages.items():
                            keys = files[file_name]['dependencies'].keys()
                            if package in keys:
                                if constraints != files[file_name]['dependencies'][package]:
                                    await update_requirement_rel_constraints(requirement_file_id, package, files[file_name]['dependencies'][package], package_manager)
                                files[file_name]['dependencies'].pop(package)
                            else:
                                await delete_requirement_file_rel(requirement_file_id, package, package_manager)
                        if files[file_name]['dependencies']:
                            for package, constraints in files[file_name]['dependencies'].items():
                                match package_manager:
                                    case 'PIP':
                                        await pip_exist_package(package, constraints, requirement_file_id)
                                    case 'NPM':
                                        await npm_exist_package(package, constraints, requirement_file_id)
                                    case 'MVN':
                                        await mvn_exist_package(package, constraints, requirement_file_id)
                        files.pop(file_name)
                if files:
                    for name, file in files.items():
                        if file['package_manager'] == package_manager:
                            await select_manager(package_manager, name, file, repository_id=repository_id)
                await update_repository_moment(repository_id, package_manager)
    return JSONResponse(status_code=status.HTTP_200_OK, content=json_encoder({'message': 'created'}))


async def select_manager(package_manager: str, name: str, file: dict[str, Any], repository_json: dict[str, Any] | None = None, repository_id: str | None = None) -> None:
    if not repository_id:
        repository_id = await create_repository(repository_json, package_manager)
    match package_manager:
        case 'PIP':
            await pip_extract_graph(name, file, repository_id)
        # case 'NPM':
        #     await npm_extract_graph(name, file, repository_json, repository_id)
        # case 'MVN':
        #     await mvn_extract_graph(name, file, repository_json, repository_id)