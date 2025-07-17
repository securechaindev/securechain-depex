from fastapi import APIRouter

from app.controllers import (
    config_operation_controller,
    file_operation_controller,
    graph_controller,
    health_controller,
)

api_router = APIRouter()
api_router.include_router(health_controller.router, tags=["health"])
api_router.include_router(graph_controller.router, tags=["graph"])
api_router.include_router(file_operation_controller.router, tags=["operation/file"])
api_router.include_router(config_operation_controller.router, tags=["operation/config"])
