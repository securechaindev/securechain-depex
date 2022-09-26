from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError, ValidationError

from json import loads

from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from app.router import api_router

from app.utils.json_encoder import JSONEncoder


description = 'A simple backend for dependency extraction'

app = FastAPI(
    title = "Depex",
    description = description,
    version = "0.1.0",
    contact = {
        "name": "Antonio Germán Márquez Trujillo",
        "url": "https://github.com/GermanMT",
        "email": "amtrujillo@us.es",
    },
    license_info = {
        "name": "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "url": "https://www.gnu.org/licenses/gpl-3.0.html",
    },
)

@app.exception_handler(RequestValidationError)
@app.exception_handler(ValidationError)
async def validation_exception_handler(_ , exc):
    exc_json = loads(exc.json())
    response = {'message': []}
    for error in exc_json:
        response['message'].append(error['loc'][-1]+f": {error['msg']}")
    
    return JSONResponse(content = JSONEncoder().encode(response), status_code = 422)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins = [],
    allow_credentials = True,
    allow_methods = ['*'],
    allow_headers = ['*']
)

app.include_router(api_router)