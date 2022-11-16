from json import loads

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError, ValidationError
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from app.controllers.update_db_controller import db_updater
from app.router import api_router
from app.services.dbs.indexes import create_indexes
from app.utils.json_encoder import JSONEncoder

DESCRIPTION = 'A simple backend for dependency extraction'

app = FastAPI(
    title='Depex',
    description=DESCRIPTION,
    version='0.3.0',
    contact={
        'name': 'Antonio Germán Márquez Trujillo',
        'url': 'https://github.com/GermanMT',
        'email': 'amtrujillo@us.es',
    },
    license_info={
        'name': 'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'url': 'https://www.gnu.org/licenses/gpl-3.0.html',
    },
)


@app.on_event("startup")
async def startup_event():
    await create_indexes()
    await db_updater()


@app.exception_handler(RequestValidationError)
@app.exception_handler(ValidationError)
async def validation_exception_handler(_, exc):
    exc_json = loads(exc.json())
    response = {'message': []}
    for error in exc_json:
        response['message'].append(error['loc'][-1] + f": {error['msg']}")

    return JSONResponse(content=JSONEncoder().encode(response), status_code=422)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)

app.include_router(api_router)