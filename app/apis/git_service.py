from requests import post

from functools import lru_cache

from app.config import Settings

from app.utils.ctc_parser import parse_constraints


@lru_cache()
def get_settings():
    return Settings()


settings: Settings = get_settings()

headers = {
    'Accept': 'application/vnd.github.hawkgirl-preview+json',
    'Authorization': f'Bearer {settings.GIT_GRAPHQL_API_KEY}',
}

endpoint = 'https://api.github.com/graphql'

async def get_repo_data(owner: str, name: str, manager: str) -> dict[str, list[str]]:
    query = '''
        {
            repository(owner: \"%s\", name: \"%s\")
            {
                dependencyGraphManifests
                {
                    nodes
                    {
                        filename
                        dependencies
                        {
                            nodes
                            {
                                packageName
                                requirements
                                packageManager
                            }
                        }
                    }
                }
            }
        }''' % (owner, name)

    response = post(endpoint, json={'query': query}, headers = headers, timeout = 25)

    return await json_reader(response.json(), manager)

async def json_reader(data, manager: str) -> dict[str, list[str]]: 
    files = {}

    for node in data['data']['repository']['dependencyGraphManifests']['nodes']:
        file = node['filename']

        if '.yml' in file:
            continue
        
        data = []

        for node in node['dependencies']['nodes']:
            if node['packageManager'] == manager:
                req = parse_constraints(node['requirements'])
                data.append([node['packageName'], req, node['packageManager']])

        files[file] = data

    return files