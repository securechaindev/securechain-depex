from typing import Any

from dateutil.parser import parse

from app.utils.ctc_parser import parse_constraints
from app.utils.get_first_pos import get_first_position
from app.utils.get_session import get_session


async def get_all_versions(pkg_name: str) -> list[dict[str, Any]]:
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
                    'mayor': int(xyzd[0]),
                    'minor': int(xyzd[1]) if len(xyzd) >= 2 else 0,
                    'patch': int(xyzd[2]) if len(xyzd) >= 3 else 0,
                    'build_number': int(xyzd[3]) if len(xyzd) >= 4 else 0,
                    'release_date': release_date,
                    'package_edges': [],
                    'cves': []
                })

        return versions

    return []


async def requires_packages(pkg_name: str, version_dist: str) -> dict[str, dict[str, str] | str]:
    session = await get_session()
    response = session.get(
        f'https://pypi.python.org/pypi/{pkg_name}/{version_dist}/json'
    ).json()['info']['requires_dist']

    if response:
        require_packages: dict[str, Any] = {}

        for dist in response:
            data = dist.split(';')

            # TODO: En el futuro sería interesante construir el grado teniendo en cuenta los extras
            # TODO: En el futuro sería interesante construir 
            # el grado teniendo en cuenta la version de python
            if len(data) > 1:
                if 'extra' in data[1]:
                    continue
                python_version = (
                    '== \"3.9\"' in data[1] or
                    '<= \"3.9\"' in data[1] or
                    '>= \"3.9\"' in data[1] or
                    '>= \"3\"' in data[1] or
                    '<= \"3\"' in data[1] or
                    '>= \"2' in data[1] or
                    '> \"2' in data[1]
                )
                if 'python_version' in data[1] and not python_version:
                    continue

            # TODO: Eliminamos que se puedan requerir extras
            if '[' in data[0]:
                pos_1 = await get_first_position(data[0], ['['])
                pos_2 = await get_first_position(data[0], [']']) + 1
                data[0] = data[0][:pos_1] + data[0][pos_2:]

            data = data[0].replace('(', '').replace(')', '').replace(' ', '').replace("'", '')

            pos = await get_first_position(data, ['<', '>', '=', '!', '~'])

            dist = data[:pos]
            raw_ctcs = data[pos:]
            ctcs = await parse_constraints(raw_ctcs, 'PIP')

            if dist in require_packages:
                if isinstance(require_packages[dist], dict):
                    if isinstance(ctcs, dict):
                        require_packages[dist].update(ctcs)
            else:
                if '.' not in raw_ctcs and raw_ctcs != '':
                    continue
                require_packages[dist] = ctcs

        return require_packages

    return {}