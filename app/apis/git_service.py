from app.config import settings
from app.utils.ctc_parser import parse_constraints
from app.utils.get_session import get_session
from app.utils.managers import managers

headers = {
    'Accept': 'application/vnd.github.hawkgirl-preview+json',
    'Authorization': f'Bearer {settings.GIT_GRAPHQL_API_KEY}'
}

all_packages = []

async def get_repo_data(owner: str, name: str, end_cursor: str = '') -> dict[list, list] | list:
    query = '{repository(owner: \"' + owner + '\", name: \"' + name + '\")'
    query += '{dependencyGraphManifests{nodes{filename dependencies(after: \"' + end_cursor + '\"){pageInfo {hasNextPage endCursor}'
    query += 'nodes{packageName requirements}}}}}}'

    session = await get_session()
    response = session.post('https://api.github.com/graphql', json={'query': query}, headers = headers, timeout = 50).json()

    packages, page_info, file = await json_reader(response)

    if not page_info['hasNextPage'] and end_cursor != '':
        return []

    all_packages.extend(packages)
    await get_repo_data(owner, name, page_info['endCursor'])
    return {file: [managers[file], all_packages]}

async def json_reader(response) -> tuple:
    packages = []

    for node in response['data']['repository']['dependencyGraphManifests']['nodes']:
        file = node['filename']

        page_info = node['dependencies']['pageInfo']

        for node in node['dependencies']['nodes']:
            req = await parse_constraints(node['requirements'])
            packages.append([node['packageName'], req])

    return (packages, page_info, file)