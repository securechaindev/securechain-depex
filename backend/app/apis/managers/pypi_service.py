from asyncio import TimeoutError, sleep
from json import JSONDecodeError
from typing import Any

from aiohttp import ClientConnectorError, ContentTypeError
from app.cache import get_cache, set_cache
from app.http_session import get_session
from app.logger import logger
from app.utils import get_first_position, parse_pypi_constraints


# TODO: En las nuevas actualizaciones de la API JSON se debería devolver la info de forma diferente, estar atento a nuevas versiones.
async def get_pypi_versions(
    name: str,
    constraints: str | None = None,
    parent_id: str | None = None,
    parent_version_name: str | None = None
) -> tuple[list[dict[str, Any]], str | None, str | None, str | None]:
    response = await get_cache(name)
    if response:
        versions = response
    else:
        url = f"https://pypi.python.org/pypi/{name}/json"
        session = await get_session()
        while True:
            try:
                logger.info(f"PyPI - {url}")
                async with session.get(url) as resp:
                    response = await resp.json()
                    break
            except (ClientConnectorError, TimeoutError):
                await sleep(5)
            except (JSONDecodeError, ContentTypeError):
                return [], name, constraints, parent_id, parent_version_name
        versions = [{"name": version, "count": count} for count, version in enumerate(response.get("releases", {}))]
        await set_cache(name, versions)
    return versions, name, constraints, parent_id, parent_version_name


async def get_pypi_requires(
    version_id: str,
    version: str,
    name: str
) -> tuple[dict[str, list[str] | str], str, str]:
    key = f"{name}:{version}"
    response = await get_cache(key)
    if response:
        require_packages = response
    else:
        url = f"https://pypi.python.org/pypi/{name}/{version}/json"
        session = await get_session()
        while True:
            try:
                logger.info(f"PyPI - {url}")
                async with session.get(url) as resp:
                    response = await resp.json()
                    break
            except (ClientConnectorError, TimeoutError):
                await set_cache(url, "error")
                await sleep(5)
            except (JSONDecodeError, ContentTypeError):
                await set_cache(url, "error")
                return {}, version_id, name
        require_packages: dict[str, Any] = {}
        for dependency in response.get("info", {}).get("requires_dist", []) or []:
            data = dependency.split(";")
            # TODO: En el futuro sería interesante construir el grafo teniendo en cuenta la version
            # de python
            if "python-version" in data[0]:
                continue
            if len(data) > 1 and "extra" in data[1]:
                continue
            if len(data) > 1:
                python_version = any(sub in data[1] for sub in ['== "3.9"', '<= "3.9"', '>= "3.9"', '>= "3"', '<= "3"', '>= "2', '> "2'])
                if "python_version" in data[1] and not python_version:
                    continue
            # INFO: Eliminamos que se puedan requerir extras
            # TODO: En el futuro sería interesante construir el grafo teniendo en cuenta los extras
            # Ejemplo, selenium:4.1.1 -> urllib3[secure, socks] == 1.26
            if "[" in data[0]:
                pos_1 = await get_first_position(data[0], ["["])
                pos_2 = await get_first_position(data[0], ["]"]) + 1
                data[0] = data[0][:pos_1] + data[0][pos_2:]
            data = data[0].replace("(", "").replace(")", "").replace(" ", "").replace("'", "")
            pos = await get_first_position(data, ["<", ">", "=", "!", "~"])
            require_packages[data[:pos].lower()] = await parse_pypi_constraints(data[pos:])
        await set_cache(key, require_packages)
    return require_packages, version_id, name
