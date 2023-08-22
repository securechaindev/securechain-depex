from fastapi import APIRouter
from app.controllers import (
    graph_controller,
    file_operation_controller,
    config_operation_controller,
    test_report_controller
)

api_router = APIRouter()
api_router.include_router(graph_controller.router, tags=['graph'])
api_router.include_router(file_operation_controller.router, tags=['operation/file'])
api_router.include_router(config_operation_controller.router, tags=['operation/config'])
api_router.include_router(test_report_controller.router, tags=['test_report'])