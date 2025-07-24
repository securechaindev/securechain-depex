from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

from app.limiter import limiter
from app.utils import json_encoder

router = APIRouter()

@router.get("/health")
@limiter.limit("25/minute")
def health_check(request: Request):
    return JSONResponse(
        status_code=status.HTTP_200_OK, content=json_encoder(
            {
                "code": "healthy",
                "message": "Service is running",
            }
        )
    )
