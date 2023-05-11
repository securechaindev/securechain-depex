from typing import Any

from time import sleep

from requests import get


async def get_all_npm_versions(pkg_name: str) -> list[dict[str, Any]]:
    while True:
        try:
            response = get(f'https://registry.npmjs.org/{pkg_name}').json()
            break
        except:
            sleep(5)

    if 'versions' in response:
        versions = []
        releases = response['versions']

        for release in releases:

            versions.append({
                'name': release,
                'release_date': None,
                'require_packages': releases[release]['dependencies'] if 'dependencies' in releases[release] else {}
            })

        return versions

    return []