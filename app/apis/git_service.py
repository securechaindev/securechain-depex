from typing import Any

from app.config import settings
from app.utils import parse_constraints
from app.utils import get_session
from app.utils import managers

headers = {
    'Accept': 'application/vnd.github.hawkgirl-preview+json',
    'Authorization': f'Bearer {settings.GIT_GRAPHQL_API_KEY}'
}


async def get_repo_data(
    owner: str,
    name: str,
    all_packages: dict[str, Any] | None = None,
    end_cursor: str | None = None
) -> dict[str, Any]:
    if not all_packages:
        all_packages = {}
    if not end_cursor:
        query = '{repository(owner: \"' + owner + '\", name: \"' + name + '\")'
        query += '{dependencyGraphManifests{nodes{filename dependencies{pageInfo {'
        query += 'hasNextPage endCursor} nodes{packageName requirements}}}}}}'
    else:
        query = '{repository(owner: \"' + owner + '\", name: \"' + name + '\")'
        query += '{dependencyGraphManifests{nodes{filename dependencies(after: \"'
        query += end_cursor + '\"){pageInfo {hasNextPage endCursor}'
        query += 'nodes{packageName requirements}}}}}}'

    session = await get_session()
    response = session.post(
        'https://api.github.com/graphql',
        json={'query': query},
        headers=headers,
        timeout=50
    ).json()

    page_info, all_packages = await json_reader(response, all_packages)

    if not page_info['hasNextPage']:
        return all_packages

    return await get_repo_data(owner, name, all_packages, page_info['endCursor'])


async def json_reader(
    response: Any,
    all_packages: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    page_info = {'hasNextPage': None}

    for node in response['data']['repository']['dependencyGraphManifests']['nodes']:
        file = node['filename']
        page_info = node['dependencies']['pageInfo']
        if file not in managers:
            continue

        if file not in all_packages:
            all_packages[file] = {'manager': managers[file], 'dependencies': {}}
        for node in node['dependencies']['nodes']:
            req = await parse_constraints(node['requirements'], managers[file])
            all_packages[file]['dependencies'].update({node['packageName']: req})

    return (page_info, all_packages)