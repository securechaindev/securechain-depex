from fastapi import APIRouter

from app.controllers import network_controller, operation_controller

api_router = APIRouter()
api_router.include_router(network_controller.router, tags=['network'])
api_router.include_router(operation_controller.router, tags=['operation'])