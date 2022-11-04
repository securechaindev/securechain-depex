from app.config import settings
from app.utils.ctc_parser import parse_constraints
from app.utils.get_session import get_session
from app.utils.managers import managers

headers = {
    'Accept': 'application/vnd.github.hawkgirl-preview+json',
    'Authorization': f'Bearer {settings.GIT_GRAPHQL_API_KEY}'
}

async def get_repo_data(owner: str, name: str, all_packages: dict = {}, end_cursor: str = None) -> dict[list, list] | list:
    if not end_cursor:
        query = '{repository(owner: \"' + owner + '\", name: \"' + name + '\")'
        query += '{dependencyGraphManifests{nodes{filename dependencies{pageInfo {hasNextPage endCursor} nodes{packageName requirements}}}}}}'
    else:
        query = '{repository(owner: \"' + owner + '\", name: \"' + name + '\")'
        query += '{dependencyGraphManifests{nodes{filename dependencies(after: \"' + end_cursor + '\"){pageInfo {hasNextPage endCursor}'
        query += 'nodes{packageName requirements}}}}}}'

    session = await get_session()
    response = session.post('https://api.github.com/graphql', json={'query': query}, headers = headers, timeout = 50).json()

    page_info, all_packages = await json_reader(response, all_packages)

    if not page_info['hasNextPage']:
        return all_packages

    await get_repo_data(owner, name, all_packages, page_info['endCursor'])

async def json_reader(response, all_packages: dict) -> tuple:
    page_info = {'hasNextPage': None}

    for node in response['data']['repository']['dependencyGraphManifests']['nodes']:
        file = node['filename']
        page_info = node['dependencies']['pageInfo']
        if file not in managers:
            continue

        if file not in all_packages:
            all_packages[file] = [managers[file], []]
        for node in node['dependencies']['nodes']:
            req = await parse_constraints(node['requirements'])
            all_packages[file][1].append([node['packageName'], req])

    return (page_info, all_packages)