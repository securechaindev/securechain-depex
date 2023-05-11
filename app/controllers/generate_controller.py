from typing import Any

from app.apis import (
    get_repo_data
)

from app.services import (
    create_repository
)

from .managers.pypi_generate_controller import pypi_extract_graph
from .managers.npm_generate_controller import npm_extract_graph


async def extract_graph(repository: dict[str, Any]) -> None:

    repository_id = await create_repository(repository)

    files = await get_repo_data(repository['owner'], repository['name'])

    for name, file in files.items():

        match file['manager']:
            case 'PIP':
                await pypi_extract_graph(name, file, repository_id)
            case 'NPM':
                await npm_extract_graph(name, file, repository_id)
            case _:
                continue