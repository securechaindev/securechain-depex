from typing import Any

from app.apis import (
    get_repo_data
)

from app.services import (
    create_repositories
)

from .managers.pip_generate_controller import pip_extract_graph
from .managers.npm_generate_controller import npm_extract_graph
from .managers.mvn_generate_controller import mvn_extract_graph

import time


async def extract_graph(repository: dict[str, Any]) -> None:

    begin = time.time()

    files = await get_repo_data(repository['owner'], repository['name'])

    repository_ids = await create_repositories(repository)

    for name, file in files.items():

        match file['manager']:
            case 'PIP':
                await pip_extract_graph(name, file, repository_ids)
            case 'NPM':
                await npm_extract_graph(name, file, repository_ids)
            case 'MVN':
                await mvn_extract_graph(name, file, repository_ids)
            case _:
                continue
    
    print('El grafo se ha construido en ' + str(time.time() - begin) + ' segundos.')