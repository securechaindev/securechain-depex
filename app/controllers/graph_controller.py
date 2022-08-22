from fastapi import APIRouter, Body, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from app.models.graph_model import GraphModel

from app.services.graph_service import add_graph
from app.services.package_service import add_package, get_package_by_name_in_graph
from app.services.version_service import add_version
from app.services.package_edge_service import add_package_edge

from app.utils.json_encoder import JSONEncoder
from app.utils.ctc_parser import parse_constraints
from app.utils.filter import filter_versions

from app.managers.pypi import requires_dist, requires_dists_ver


router = APIRouter()

@router.post("/graph", response_description="Init graph", response_model = GraphModel)
async def init_graph(graph: GraphModel = Body(...)):
    graph_json = jsonable_encoder(graph)

    new_graph = await add_graph(graph_json)
    graph_id = new_graph['_id']

    req_dist = requires_dist(graph_json['name'])

    for dist in req_dist.items():
        dist, raw_constraints = dist

        package = {
            'name': dist,
            'graph': graph_id,
            'versions': []
        }

        constraints = parse_constraints(raw_constraints)
        
        versions = filter_versions(dist, constraints)

        for version in versions:

            version = await generate_graph(package['name'], version, graph_id)

            new_version = await add_version(version)
 
            package['versions'].append(new_version['_id'])

        await add_package(package)

    return JSONResponse(status_code = status.HTTP_201_CREATED, content = JSONEncoder().encode(new_graph))

async def generate_graph(package, parent_version, graph_id):
    req_dists = requires_dists_ver(package, parent_version['release'])

    if req_dists:

        parent_version['package_edges'] = []

        for req_dist in req_dists.items():
            package_edge = {}

            dist, raw_constraints = req_dist

            constraints = parse_constraints(raw_constraints)
            package_edge['constraints'] = constraints

            package = await get_package_by_name_in_graph(dist, graph_id)
            exist = package is not None
            
            if exist:
                package_edge['package'] = package['_id']
                new_package_edge = await add_package_edge(package_edge)
                parent_version['package_edges'].append(new_package_edge['_id'])
                continue


            package = {
                'name': dist,
                'graph': graph_id,
                'versions': []
            }

            versions = filter_versions(dist, constraints)

            for version in versions:

                version = await generate_graph(package['name'], version, graph_id)

                new_version = await add_version(version)
    
                package['versions'].append(new_version['_id'])

            new_package = await add_package(package)

            package_edge['package'] = new_package['_id']
            new_package_edge = await add_package_edge(package_edge)
            parent_version['package_edges'].append(new_package_edge['_id'])
    
    return parent_version