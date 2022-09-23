from fastapi import FastAPI

from starlette.middleware.cors import CORSMiddleware

from app.router import api_router


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

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins = [],
    allow_credentials = True,
    allow_methods = ['*'],
    allow_headers = ['*']
)

app.include_router(api_router)