from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.utils import json_encoder

router = APIRouter()

@router.get("/health")
def health_check():
    return JSONResponse(
        status_code=status.HTTP_200_OK, content=json_encoder({"status": "healthy"})
    )
