from requests import get

from dateutil.parser import parse

from app.utils.ctc_parser import parse_constraints
from app.utils.get_first_pos import get_first_position


async def get_all_versions(pkg_name: str) -> list:
    url = f'https://pypi.python.org/pypi/{pkg_name}/json'
    response = get(url, timeout = 25).json()

    if 'releases' in response:
        versions = []
        releases = response['releases']

        for release in releases:
            release_date = None
            for item in releases[release]:
                release_date = parse(item['upload_time_iso_8601'])

            if release.replace('.', '').isdigit():
                versions.append({'release': release, 'release_date': release_date, 'package_edges': []})

        return versions

    return []

async def requires_packages(pkg_name: str, version_dist: str) -> dict:
    url = f'https://pypi.python.org/pypi/{pkg_name}/{version_dist}/json'
    response = get(url, timeout = 25).json()['info']['requires_dist']

    if response:
        require_packages = {}

        for dist in response:
            data = dist.split(';')

            if len(data) > 1:
                if 'extra' in data[1]:
                    continue

            data = data[0].replace('(', '').replace(')', '').replace(' ', '')

            pos = await get_first_position(data)

            dist = data[:pos]
            raw_ctcs = data[pos:]

            require_packages[dist] = await parse_constraints(raw_ctcs)

        return require_packages

    return {}