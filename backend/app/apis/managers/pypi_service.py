from asyncio import TimeoutError, sleep
from json import JSONDecodeError
from typing import Any

from aiohttp import ClientConnectorError, ClientSession

from app.logger import logger
from app.utils import get_first_position, parse_pypi_constraints


# TODO: En las nuevas actualizaciones de la API JSON se debería devolver la info de forma diferente, estar atento a nuevas versiones.
async def get_pypi_versions(name: str) -> list[dict[str, Any]]:
    api_url = f"https://pypi.python.org/pypi/{name}/json"
    async with ClientSession() as session:
        while True:
            try:
                logger.info(f"PyPI - {api_url}")
                async with session.get(api_url) as response:
                    response = await response.json()
                    break
            except (ClientConnectorError, TimeoutError):
                await sleep(5)
            except JSONDecodeError:
                return []
    versions: list[dict[str, Any]] = []
    for count, version in enumerate(response.get("releases", {})):
        versions.append(
            {"name": version, "count": count}
        )
    return versions


async def get_pypi_requires(
    name: str, version: str
) -> dict[str, list[str] | str]:
    api_url = f"https://pypi.python.org/pypi/{name}/{version}/json"
    async with ClientSession() as session:
        while True:
            try:
                logger.info(f"PyPI - {api_url}")
                async with session.get(api_url) as response:
                    response = await response.json()
                    break
            except (ClientConnectorError, TimeoutError):
                await sleep(5)
            except JSONDecodeError:
                return {}
    require_packages: dict[str, Any] = {}
    for dependency in response.get("info", {}).get("requires_dist", []) or []:
        data = dependency.split(";")
        if "python-version" in data[0]:
            continue
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
        require_packages[data[:pos].lower()] = await parse_pypi_constraints(
            data[pos:]
        )
    return require_packages
