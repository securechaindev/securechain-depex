from fastapi import APIRouter, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from app.services import read_graph_by_repository_id, read_repositories, read_repositories_moment
from app.models import RepositoryModel
from app.utils import json_encoder
from app.apis import get_repo_data, get_last_commit_date
from .managers.pip_generate_controller import pip_extract_graph
from .managers.npm_generate_controller import npm_extract_graph
from .managers.mvn_generate_controller import mvn_extract_graph

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
    last_repository_moment = await read_repositories_moment(repository_json['owner'], repository_json['name'])
    last_commit_date = await get_last_commit_date(repository_json['owner'], repository_json['name'])
    if not last_repository_moment or last_repository_moment < last_commit_date:
        repository_ids = await read_repositories(repository_json['owner'], repository_json['name'])
        files = await get_repo_data(repository_json['owner'], repository_json['name'])
        for package_manager, repository_id in repository_ids.items():
            if not repository_id:
                for name, file in files.items():
                    if file['package_manager'] == package_manager:
                        match file['package_manager']:
                            case 'PIP':
                                await pip_extract_graph(name, file, repository_json)
                            case 'NPM':
                                await npm_extract_graph(name, file, repository_json)
                            case 'MVN':
                                await mvn_extract_graph(name, file, repository_json)
                            case _:
                                continue
            else:
                # TODO: Hacer un método que actualize el grafo existente en la base de datos
                pass
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=json_encoder({'message': 'created'}))