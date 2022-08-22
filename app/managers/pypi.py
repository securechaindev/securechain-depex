from requests import get


def get_all_versions(pkg_name: str) -> list[dict[str, str]]:
    url = f'https://pypi.python.org/pypi/{pkg_name}/json'
    response = get(url).json()
    versions: list[dict] = []

    if 'releases' in response:
        releases = response['releases']
        versions = []

        for release in releases:
            release_date = None
            for item in releases[release]:
                release_date = item['upload_time']

            aux = release.replace('.', '')

            if aux.isdigit():
                versions.append({
                    'release': release,
                    'release_date': release_date
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

def requires_dists_ver(pkg_name, version_dist):
    url = f'https://pypi.python.org/pypi/{pkg_name}/{version_dist}/json'
    requires_dist = get(url).json()['info']['requires_dist']
    dists: dict = {}

    if requires_dist:

        for dist in requires_dist:
            data = dist.split(';')[0]

            data = data.replace('(', '').replace(')', '').replace(' ', '')

            pos: int = [data.index(char) for char in data if char in ('<', '>', '=', '!', '|', '^', '~')]

            pos = pos[0] if pos else len(data)

            dist = data[:pos]
            raw_ctcs = data[pos:]

            if raw_ctcs:

                ctcs = []

                for ctc in raw_ctcs.split(','):

                    pos: int = [ctc.index(char) for char in ctc if char.isdigit()][0]

                    ctcs.append(f'{ctc[:pos]} {ctc[pos:]}')

                dists[dist] = ctcs

            else:

                dists[dist] = ['Any']

    return dists