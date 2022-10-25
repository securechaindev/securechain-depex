from dateutil.parser import parse

from app.utils.ctc_parser import parse_constraints
from app.utils.get_first_pos import get_first_position
from app.utils.get_session import get_session


async def get_all_versions(pkg_name: str) -> list:
    session = await get_session()
    response = session.get(f'https://pypi.python.org/pypi/{pkg_name}/json').json()

    if 'releases' in response:
        versions = []
        releases = response['releases']

        for release in releases:
            release_date = None
            for item in releases[release]:
                release_date = parse(item['upload_time_iso_8601'])

            if release.replace('.', '').isdigit():
                xyzd = release.split('.')
                versions.append({
                    'release': release,
                    'mayor': xyzd[0],
                    'minor': xyzd[1] if len(xyzd) >= 2 else '0',
                    'patch': xyzd[2] if len(xyzd) >= 3 else '0',
                    'build_number': xyzd[3] if len(xyzd) >= 4 else '0',
                    'release_date': release_date,
                    'package_edges': [],
                    'cves': []
                })

        return versions

    return []

async def requires_packages(pkg_name: str, version_dist: str) -> dict:
    session = await get_session()
    response = session.get(f'https://pypi.python.org/pypi/{pkg_name}/{version_dist}/json').json()['info']['requires_dist']

    if response:
        require_packages = {}

        for dist in response:
            data = dist.split(';')

            if len(data) > 1:
                if 'extra' in data[1]:
                    continue

            if 'dev' in data[0]:
                continue

            data = data[0].replace('(', '').replace(')', '').replace(' ', '').replace("'", '')

            pos = await get_first_position(data)

            dist = data[:pos]
            raw_ctcs = data[pos:]

            require_packages[dist] = await parse_constraints(raw_ctcs)

        return require_packages

    return {}