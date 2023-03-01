from fastapi import APIRouter

from app.controllers import (
    graph_controller,
    graph_operation_controller,
    config_operation_controller
)

api_router = APIRouter()
api_router.include_router(graph_controller.router, tags=['graph'])
api_router.include_router(graph_operation_controller.router, tags=['operation/graph'])
api_router.include_router(config_operation_controller.router, tags=['operation/config'])