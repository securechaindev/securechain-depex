from fastapi import APIRouter, HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.services import create_repository, read_graph_by_repository_id
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
    try:
        graph = await read_graph_by_repository_id(repository_id)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=graph
        )
    except HTTPException as error:
        return JSONResponse(
            status_code=error.status_code,
            content=json_encoder({'message': error.detail})
        )


@router.post(
    '/graph/init',
    summary='Init a graph',
)
async def init_graph(
    repository: RepositoryModel
) -> JSONResponse:
    '''
    Starts graph extraction in its initial state, i.e., not complete:

    - **repository**: a json containing the owner and the name of a repository
    '''
    repository_json = jsonable_encoder(repository)
    try:
        await create_repository(repository_json)
        await extract_graph(repository_json)
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=json_encoder({'message': 'created'})
        )
    except HTTPException as error:
        return JSONResponse(
            status_code=error.status_code,
            content=json_encoder({'message': error.detail})
        )