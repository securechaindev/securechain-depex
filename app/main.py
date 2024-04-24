from contextlib import asynccontextmanager
from time import sleep
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, Request
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import Response

from app.controllers import nvd_update
from app.router import api_router
from app.services import create_indexes

DESCRIPTION = """
A backend for dependency graph building, atribution of vulnerabilities and reasoning
over it.
"""


@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    while True:
        try:
            await create_indexes()
            await nvd_update()
            scheduler = AsyncIOScheduler()
            scheduler.add_job(nvd_update, "interval", seconds=7200)
            scheduler.start()
            break
        except Exception as _:
            sleep(5)
    yield
    scheduler.shutdown()


app = FastAPI(
    title="Depex",
    description=DESCRIPTION,
    version="0.6.2",
    contact={
        "name": "Antonio Germán Márquez Trujillo",
        "url": "https://github.com/GermanMT",
        "email": "amtrujillo@us.es",
    },
    license_info={
        "name": "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "url": "https://www.gnu.org/licenses/gpl-3.0.html",
    },
    lifespan=lifespan,
)


@app.exception_handler(HTTPException)
async def custom_http_exception_handler(
    request: Request, exc: HTTPException
) -> Response:
    return await http_exception_handler(request, exc)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> Response:
    return await request_validation_exception_handler(request, exc)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
