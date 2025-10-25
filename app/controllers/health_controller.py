from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse

from app.dependencies import get_json_encoder
from app.limiter import limiter
from app.utils import JSONEncoder

router = APIRouter()

@router.get(
    "/health",
    summary="Health Check",
    description="Check the status of the API.",
    response_description="API status.",
    tags=["Secure Chain Depex Health"]
)
@limiter.limit("25/minute")
async def health_check(
    request: Request,
    json_encoder: JSONEncoder = Depends(get_json_encoder),
):
    return JSONResponse(
        status_code=status.HTTP_200_OK, content=json_encoder.encode(
            {
                "detail": "healthy",
            }
        )
    )
