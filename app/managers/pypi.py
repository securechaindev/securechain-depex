from requests import get


def get_all_versions(pkg_name: str) -> list[dict[str, str]]:
    url = f'https://pypi.python.org/pypi/{pkg_name}/json'
    releases = get(url).json()['releases']
    versions = list()

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
    dists = dict()

    for dist in requires_dist:
        dist, raw_ctcs = dist.split(' ')[0:2]
        ctcs = list()

        for ctc in raw_ctcs.split(','):
            raw_ctc = ctc.replace('(', '').replace(')', '')

            pos: int = 0
            for char in raw_ctc:
                if char.isdigit():
                    pos = raw_ctc.index(char)
                    break

            version = raw_ctc[:pos]
            op = raw_ctc[pos:]

            op = 'Any' if op.__eq__(';') else op

            ctcs.append(f'{version} {op}')

        dists[dist] = ctcs

    return dists
