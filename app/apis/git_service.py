from requests import post

from app.config import settings

from app.utils.ctc_parser import parse_constraints
from app.utils.managers import managers


headers = {
    'Accept': 'application/vnd.github.hawkgirl-preview+json',
    'Authorization': f'Bearer {settings.GIT_GRAPHQL_API_KEY}',
}

endpoint = 'https://api.github.com/graphql'

async def get_repo_data(owner: str, name: str) -> dict[list, list]:
    query = "{repository(owner: \"" + owner + "\", name: \"" + name + "\")"
    query += "{dependencyGraphManifests{nodes{filename dependencies{nodes{packageName requirements}}}}}}"

    response = post(endpoint, json={'query': query}, headers = headers, timeout = 25).json()

    return await json_reader(response)

async def json_reader(data) -> dict[list, list]: 
    files = {}

    for node in data['data']['repository']['dependencyGraphManifests']['nodes']:
        file = node['filename']

        if file not in managers:
            continue

        data = []

        for node in node['dependencies']['nodes']:
            req = await parse_constraints(node['requirements'])
            data.append([node['packageName'], req])

        files[file] = [managers[file], data]

    return files