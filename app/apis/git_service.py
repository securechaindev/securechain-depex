from requests import post

from app.config import settings

from app.utils.ctc_parser import parse_constraints
from app.utils.managers import managers


headers = {
    'Accept': 'application/vnd.github.hawkgirl-preview+json',
    'Authorization': f'Bearer {settings.GIT_GRAPHQL_API_KEY}'
}

async def get_repo_data(owner: str, name: str) -> dict[list, list]:
    query = '{repository(owner: \"' + owner + '\", name: \"' + name + '\")'
    query += '{dependencyGraphManifests{nodes{filename dependencies{nodes{packageName requirements}}}}}}'

    response = post('https://api.github.com/graphql', json={'query': query}, headers = headers, timeout = 50).json()

    return await json_reader(response)

async def json_reader(response) -> dict[list, list]: 
    files = {}

    for node in response['data']['repository']['dependencyGraphManifests']['nodes']:
        file = node['filename']

        if file not in managers:
            continue

        packages = []

        for node in node['dependencies']['nodes']:
            req = await parse_constraints(node['requirements'])
            packages.append([node['packageName'], req])

        files[file] = [managers[file], packages]

    return files