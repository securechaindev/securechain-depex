from fastapi import APIRouter

from app.controllers import (
    config_operation_controller,
    file_operation_controller,
    graph_controller,
    health_controller,
    package_operation_controller,
)

api_router = APIRouter()
api_router.include_router(health_controller.router, tags=["Secure Chain Depex Health"])
api_router.include_router(graph_controller.router, tags=["Secure Chain Depex - Graph"])
api_router.include_router(package_operation_controller.router, tags=["Secure Chain Depex - Operation/Package"])
api_router.include_router(file_operation_controller.router, tags=["Secure Chain Depex - Operation/File"])
api_router.include_router(config_operation_controller.router, tags=["Secure Chain Depex - Operation/Config"])
