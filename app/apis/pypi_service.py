from requests import get

from dateutil.parser import parse

from app.utils.ctc_parser import parse_constraints


def get_all_versions(pkg_name: str) -> list[dict]:
    url = f'https://pypi.python.org/pypi/{pkg_name}/json'
    response = get(url, timeout = 25).json()
    versions: list[dict] = []

    if 'releases' in response:
        releases = response['releases']
        versions = []

        for release in releases:
            release_date = None
            for item in releases[release]:
                release_date = item['upload_time_iso_8601']

            aux = release.replace('.', '')

            if aux.isdigit():
                versions.append({
                    'release': release,
                    'release_date': parse(release_date) if release_date else None,
                    'package_edges': []
                })

    return versions

def requires_packages(pkg_name, version_dist):
    url = f'https://pypi.python.org/pypi/{pkg_name}/{version_dist}/json'
    response = get(url, timeout = 25).json()['info']['requires_dist']
    require_packages: dict = {}

    if response:

        for dist in response:
            data = dist.split(';')

            if len(data) > 1:
                if 'extra' in data[1]:
                    continue

            data = data[0].replace('(', '').replace(')', '').replace(' ', '')

            pos: int = [data.index(char) for char in data if char in ('<', '>', '=', '!', '|', '^', '~')]

            pos = pos[0] if pos else len(data)

            dist = data[:pos]
            raw_ctcs = data[pos:]

            require_packages[dist] = parse_constraints(raw_ctcs)

    return require_packages