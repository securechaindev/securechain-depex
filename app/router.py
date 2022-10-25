from fastapi import APIRouter

from app.controllers import network_controller, serialize_controller

api_router = APIRouter()
api_router.include_router(network_controller.router, tags = ['network'])
api_router.include_router(serialize_controller.router, tags = ['serialize'])