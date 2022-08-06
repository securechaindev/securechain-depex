from fastapi import APIRouter, Body, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from app.models.graph_model import GraphModel

from app.services.graph_service import add_graph
from app.services.package_service import add_package
from app.services.version_package import add_version

from app.utils.json_encoder import JSONEncoder
from app.utils.ctc_parser import parse_constraints
from app.utils.filter import filter_versions

from app.managers.pypi import requires_dist


router = APIRouter()

@router.post("/graph", response_description="Generate graph", response_model = GraphModel)
async def generate_graph(graph: GraphModel = Body(...)):
    graph_json = jsonable_encoder(graph)
    graph_json['packages'] = list()
    req_dist = requires_dist(graph_json['name'])

    for dist in req_dist:

        package = {
            'name': dist,
            'versions': list()
        }

        constraints = parse_constraints(req_dist[dist])
        
        versions = filter_versions(dist, constraints)

        for version in versions:
            version = version

            new_version = await add_version(version)
 
            package['versions'].append(new_version['_id'])

        new_package = await add_package(package)

        graph_json['packages'].append(new_package['_id'])

    new_graph = await add_graph(graph_json)

    return JSONResponse(status_code = status.HTTP_201_CREATED, content = JSONEncoder().encode(new_graph))