from app.config import settings
from app.utils.ctc_parser import parse_constraints
from app.utils.get_session import get_session
from app.utils.managers import managers

headers = {
    'Accept': 'application/vnd.github.hawkgirl-preview+json',
    'Authorization': f'Bearer {settings.GIT_GRAPHQL_API_KEY}'
}

all_packages = {}

async def get_repo_data(owner: str, name: str, end_cursor: str = '') -> dict[list, list] | list:
    query = '{repository(owner: \"' + owner + '\", name: \"' + name + '\")'
    query += '{dependencyGraphManifests{nodes{filename dependencies(after: \"' + end_cursor + '\"){pageInfo {hasNextPage endCursor}'
    query += 'nodes{packageName requirements}}}}}}'

    session = await get_session()
    response = session.post('https://api.github.com/graphql', json={'query': query}, headers = headers, timeout = 50).json()

    page_info = await json_reader(response)

    if not page_info['hasNextPage'] and end_cursor != '':
        return []

    await get_repo_data(owner, name, page_info['endCursor'])
    return all_packages

async def json_reader(response) -> tuple:
    for node in response['data']['repository']['dependencyGraphManifests']['nodes']:
        file = node['filename']
        page_info = node['dependencies']['pageInfo']
        if file not in managers:
            continue

        if file not in all_packages.keys():
            all_packages[file] = [managers[file], []]
        for node in node['dependencies']['nodes']:
            req = await parse_constraints(node['requirements'])
            all_packages[file][1].append([node['packageName'], req])

    return page_info