from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

from app.limiter import limiter
from app.utils import json_encoder

router = APIRouter()

@router.get(
    "/health",
    summary="Health Check",
    description="Check the status of the API.",
    response_description="API status.",
    tags=["Secure Chain Depex Health"]
)
@limiter.limit("25/minute")
async def health_check(request: Request):
    return JSONResponse(
        status_code=status.HTTP_200_OK, content= await json_encoder(
            {
                "detail": "healthy",
            }
        )
    )
