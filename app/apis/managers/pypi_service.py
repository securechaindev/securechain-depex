from typing import Any

from time import sleep

from dateutil.parser import parse

from app.utils import get_first_position

from requests import get


async def get_all_pypi_versions(pkg_name: str) -> list[dict[str, Any]]:
    while True:
        try:
            response = get(f'https://pypi.python.org/pypi/{pkg_name}/json').json()
            break
        except:
            # Actualmente la API JSON de PyPI no nos permite hacer llamadas para obtener toda
            # la información. Esto hace que tenga que hacer una llamada por cada versión, si
            # se satura la api tendremos que esperar a que vuelva a haber respueta.
            # TODO: En las nuevas actualizaciones de la API JSON se debería resolver esto,
            # estar atento a nuevas versiones.
            sleep(5)

    if 'releases' in response:
        versions = []
        releases = response['releases']

        for release in releases:
            release_date = None
            for item in releases[release]:
                release_date = parse(item['upload_time_iso_8601'])

            versions.append({
                'name': release,
                'release_date': release_date
            })

        return versions

    return []


async def requires_pypi_packages(pkg_name: str, version_dist: str) -> dict[str, list[str] | str]:
    while True:
        try:
            response = get(
                f'https://pypi.python.org/pypi/{pkg_name}/{version_dist}/json'
            ).json()['info']['requires_dist']
            break
        except:
            # Actualmente la API JSON de PyPI no nos permite hacer llamadas para obtener toda
            # la información. Esto hace que tenga que hacer una llamada por cada versión, si
            # se satura la api tendremos que esperar a que vuelva a haber respueta.
            # TODO: En las nuevas actualizaciones de la API JSON se debería resolver esto,
            # estar atento a nuevas versiones.
            sleep(5)

    if response:
        require_packages: dict[str, Any] = {}

        for dist in response:
            data = dist.split(';')

            # TODO: En el futuro sería interesante construir el grafo teniendo en cuenta la version 
            # de python
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

            # Eliminamos que se puedan requerir extras
            # TODO: En el futuro sería interesante construir el grafo teniendo en cuenta los extras
            if '[' in data[0]:
                pos_1 = await get_first_position(data[0], ['['])
                pos_2 = await get_first_position(data[0], [']']) + 1
                data[0] = data[0][:pos_1] + data[0][pos_2:]

            data = data[0].replace('(', '').replace(')', '').replace(' ', '').replace("'", '')

            pos = await get_first_position(data, ['<', '>', '=', '!', '~'])

            dist = data[:pos]
            ctcs = data[pos:]
            if not ctcs:
                ctcs = 'any'

            if (
                dist in require_packages and
                isinstance(require_packages[dist], dict) and
                isinstance(ctcs, list)
            ):
                for ctc in ctcs:
                    if ctc not in require_packages[dist]:
                        require_packages[dist].append(ctcs)
            else:
                if '.' not in ctcs and ctcs != '':
                    continue
                require_packages[dist] = ctcs

        return require_packages

    return {}