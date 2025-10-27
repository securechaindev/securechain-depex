from fastapi import APIRouter

from app.controllers import (
    graph_controller,
    health_controller,
    smt_operation_controller,
    ssc_operation_controller,
)

api_router = APIRouter()
api_router.include_router(health_controller.router, tags=["Secure Chain Depex Health"])
api_router.include_router(graph_controller.router, tags=["Secure Chain Depex - Graph"])
api_router.include_router(ssc_operation_controller.router, tags=["Secure Chain Depex - Operation/SSC"])
api_router.include_router(smt_operation_controller.router, tags=["Secure Chain Depex - Operation/SMT"])
