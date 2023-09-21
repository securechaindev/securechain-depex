from typing import Any
from time import sleep
from requests import post, ConnectTimeout, ConnectionError
from app.config import settings
from app.utils import get_manager, parse_pip_constraints
from dateutil.parser import parse
from datetime import datetime

headers = {
    'Accept': 'application/vnd.github.hawkgirl-preview+json',
    'Authorization': f'Bearer {settings.GIT_GRAPHQL_API_KEY}'
}

async def get_repo_data(owner: str, name: str, all_packages: dict[str, Any] | None = None, end_cursor: str | None = None) -> dict[str, Any]:
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
    while True:
        try:
            response = post(
                'https://api.github.com/graphql',
                json={'query': query},
                headers=headers
            ).json()
            break
        except (ConnectTimeout, ConnectionError):
            sleep(5)
    page_info, all_packages = await json_reader(response, all_packages)
    if not page_info['hasNextPage']:
        return all_packages
    return await get_repo_data(owner, name, all_packages, page_info['endCursor'])


async def json_reader(response: Any, all_packages: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    page_info = {'hasNextPage': None}
    for node in response['data']['repository']['dependencyGraphManifests']['nodes']:
        requirement_file_name = node['filename']
        if requirement_file_name == 'package-lock.json':
            continue
        page_info = node['dependencies']['pageInfo']
        requirement_file_manager = await get_manager(requirement_file_name)
        if not requirement_file_manager:
            continue
        if requirement_file_name not in all_packages:
            all_packages[requirement_file_name] = {'package_manager': requirement_file_manager, 'dependencies': {}}
        for node in node['dependencies']['nodes']:
            if requirement_file_manager == 'MVN':
                if '=' in node['requirements']:
                    node['requirements'] = '[' + node['requirements'].replace('=', '').replace(' ', '') + ']'
            if requirement_file_manager == 'PIP':
                node['requirements'] = await parse_pip_constraints(node['requirements'])
            all_packages[requirement_file_name]['dependencies'].update({node['packageName']: node['requirements']})
    return (page_info, all_packages)


async def get_last_commit_date(owner: str, name: str) -> datetime:
    query = '''
    {
        repository(owner: "%s", name: "%s") {
            defaultBranchRef {
                target {
                    ... on Commit {
                        history(first: 1) {
                            edges {
                                node {
                                    author {
                                    date
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    ''' % (owner, name)
    while True:
        try:
            response = post(
                'https://api.github.com/graphql',
                json={'query': query},
                headers=headers
            ).json()
            break
        except (ConnectTimeout, ConnectionError):
            sleep(5)
    return parse(response["data"]["repository"]["defaultBranchRef"]["target"]["history"]["edges"][0]["node"]["author"]["date"])