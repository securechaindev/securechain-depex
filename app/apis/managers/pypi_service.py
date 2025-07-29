from asyncio import TimeoutError, sleep
from json import JSONDecodeError
from typing import Any

from aiohttp import ClientConnectorError, ContentTypeError

from app.cache import get_cache, set_cache
from app.http_session import get_session
from app.logger import logger
from app.utils.others import (
    get_first_position,
    order_versions,
    parse_pypi_constraints,
)


# TODO: En las nuevas actualizaciones de la API JSON se debería devolver la info de forma diferente, estar atento a nuevas versiones.
async def get_pypi_versions(package_name: str) -> list[dict[str, Any]]:
    response = await get_cache(package_name)
    if response:
        versions = response
    else:
        url = f"https://pypi.python.org/pypi/{package_name}/json"
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
                return []
        raw_versions = list(response.get("releases", {}))
        versions = await order_versions("PyPIPackage", raw_versions)
        await set_cache(package_name, versions)
    return versions


async def get_pypi_version(package_name: str, version_name: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    url = f"https://pypi.python.org/pypi/{package_name}/json"
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
            return {}
    versions = await order_versions("PyPIPackage", response.get("releases", {}).keys())
    index = next((i for i, d in enumerate(versions) if d.get("name") == version_name), None)
    if index is not None:
        return versions[index], versions[index + 1:]
    else:
        raise ValueError(f"Version {version_name} not found for package {package_name}")


async def get_pypi_requirement(package_name: str, version_name: str) -> dict[str, list[str] | str]:
    key = f"requirement:{package_name}:{version_name}"
    response = await get_cache(key)
    if response:
        require_packages = response
    else:
        url = f"https://pypi.python.org/pypi/{package_name}/{version_name}/json"
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
                return {}
        require_packages: dict[str, Any] = {}
        for dependency in response.get("info", {}).get("requires_dist", []) or []:
            data = dependency.split(";")
            if "python-version" in data[0]:
                continue
            if len(data) > 1 and "extra" in data[1]:
                continue
            if len(data) > 1:
                python_version = any(sub in data[1] for sub in ['== "3.10"', '<= "3.10"', '>= "3.10"', '>= "3"', '<= "3"', '>= "2', '> "2'])
                if "python_version" in data[1] and not python_version:
                    continue
            if "[" in data[0]:
                pos_1 = await get_first_position(data[0], ["["])
                pos_2 = await get_first_position(data[0], ["]"]) + 1
                data[0] = data[0][:pos_1] + data[0][pos_2:]
            data = data[0].replace("(", "").replace(")", "").replace(" ", "").replace("'", "")
            pos = await get_first_position(data, ["<", ">", "=", "!", "~"])
            require_packages[data[:pos].lower()] = await parse_pypi_constraints(data[pos:])
        await set_cache(key, require_packages)
    return require_packages
