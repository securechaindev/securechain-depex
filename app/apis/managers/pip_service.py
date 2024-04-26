from json import JSONDecodeError
from time import sleep
from typing import Any

from dateutil.parser import parse
from requests import ConnectionError, ConnectTimeout, get

from app.utils import get_first_position, parse_pip_constraints


# TODO: En las nuevas actualizaciones de la API JSON se debería devolver la info de forma diferente, estar atento a nuevas versiones.
async def get_all_pip_versions(pkg_name: str) -> list[dict[str, Any]]:
    while True:
        try:
            response = get(f"https://pypi.python.org/pypi/{pkg_name}/json").json()
            break
        except (ConnectTimeout, ConnectionError):
            sleep(5)
        except JSONDecodeError:
            print("Error en el paquete: ", pkg_name)
            return []
    if "releases" in response:
        versions: list[dict[str, Any]] = []
        raw_versions = response["releases"]
        for count, version in enumerate(raw_versions):
            release_date = None
            for item in raw_versions[version]:
                release_date = parse(item["upload_time_iso_8601"])
            versions.append(
                {"name": version, "release_date": release_date, "count": count}
            )
        return versions
    return []


async def requires_pip_packages(
    pkg_name: str, version_dist: str
) -> dict[str, list[str] | str]:
    while True:
        try:
            response = get(
                f"https://pypi.python.org/pypi/{pkg_name}/{version_dist}/json"
            ).json()["info"]["requires_dist"]
            break
        except (ConnectTimeout, ConnectionError):
            sleep(5)
    if response:
        require_packages: dict[str, Any] = {}
        for dependency in response:
            data = dependency.split(";")
            # TODO: En el futuro sería interesante construir el grafo teniendo en cuenta la version
            # de python
            if len(data) > 1:
                if "extra" in data[1]:
                    continue
                python_version = (
                    '== "3.9"' in data[1]
                    or '<= "3.9"' in data[1]
                    or '>= "3.9"' in data[1]
                    or '>= "3"' in data[1]
                    or '<= "3"' in data[1]
                    or '>= "2' in data[1]
                    or '> "2' in data[1]
                )
                if "python_version" in data[1] and not python_version:
                    continue
            # INFO: Eliminamos que se puedan requerir extras
            # TODO: En el futuro sería interesante construir el grafo teniendo en cuenta los extras
            # Ejemplo, selenium:4.1.1 -> urllib3[secure, socks] == 1.26
            if "[" in data[0]:
                pos_1 = await get_first_position(data[0], ["["])
                pos_2 = await get_first_position(data[0], ["]"]) + 1
                data[0] = data[0][:pos_1] + data[0][pos_2:]
            data = (
                data[0]
                .replace("(", "")
                .replace(")", "")
                .replace(" ", "")
                .replace("'", "")
            )
            pos = await get_first_position(data, ["<", ">", "=", "!", "~"])
            require_packages[data[:pos].lower()] = await parse_pip_constraints(
                data[pos:]
            )
        return require_packages
    return {}
