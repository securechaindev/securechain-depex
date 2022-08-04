from fastapi import APIRouter

from app.controllers import graph_controller

api_router = APIRouter()
api_router.include_router(graph_controller.router, tags=["graph"])
