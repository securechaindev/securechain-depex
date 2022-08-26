from requests import get

from dateutil.parser import parse


def get_all_versions(pkg_name: str) -> list[dict]:
    url = f'https://pypi.python.org/pypi/{pkg_name}/json'
    response = get(url).json()
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

def requires_dist(pkg_name):
    url = f'https://pypi.python.org/pypi/{pkg_name}/json'
    requires_dist = get(url).json()['info']['requires_dist']
    dists = {}

    for dist in requires_dist:
        dist, raw_ctcs = dist.split(' ')[0:2]
        ctcs = []

        for ctc in raw_ctcs.split(','):
            raw_ctc = ctc.replace('(', '').replace(')', '')

            pos: int = 0
            for char in raw_ctc:
                if char.isdigit():
                    pos = raw_ctc.index(char)
                    break

            version = raw_ctc[:pos]
            op = raw_ctc[pos:]

            op = 'Any' if op == ';' else op

            ctcs.append(f'{version} {op}')

        dists[dist] = ctcs

    return dists

def requires_packages(pkg_name, version_dist):
    url = f'https://pypi.python.org/pypi/{pkg_name}/{version_dist}/json'
    response = get(url).json()['info']['requires_dist']
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

            if raw_ctcs:

                ctcs = []

                for ctc in raw_ctcs.split(','):

                    pos: int = [ctc.index(char) for char in ctc if char.isdigit()][0]

                    ctcs.append([ctc[:pos], ctc[pos:]])

                require_packages[dist] = ctcs

            else:

                require_packages[dist] = ['Any']

    return require_packages