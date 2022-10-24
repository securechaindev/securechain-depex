from fastapi import APIRouter

from app.controllers import graph_controller, serialize_controller

api_router = APIRouter()
api_router.include_router(graph_controller.router, tags = ['graph'])
api_router.include_router(serialize_controller.router, tags = ['serialize'])