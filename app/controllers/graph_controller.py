from fastapi import APIRouter, HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from app.services import read_graph_by_repository_id, read_repository_by_owner_name
from app.models import RepositoryModel
from app.utils import json_encoder
from .generate_controller import extract_graph

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
    repository_id = await read_repository_by_owner_name(repository_json['owner'], repository_json['name'], '_')
    if not repository_id:
        await extract_graph(repository_json)
    else:
        # TODO: Hacer un método que actualize el grafo existente en la base de datos
        pass
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=json_encoder({'message': 'created'}))