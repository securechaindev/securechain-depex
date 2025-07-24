from asyncio import TimeoutError, sleep
from json import JSONDecodeError
from typing import Any

from aiohttp import ClientConnectorError, ContentTypeError

from app.cache import get_cache, set_cache
from app.http_session import get_session
from app.logger import logger
from app.utils.others import version_to_serial_number


async def get_npm_versions(package_name: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    response = await get_cache(package_name)
    if response:
        versions, requirements = response
    else:
        url = f"https://registry.npmjs.org/{package_name}"
        session = await get_session()
        while True:
            try:
                logger.info(f"NPM - {url}")
                async with session.get(url) as resp:
                    response = await resp.json()
                    break
            except (ClientConnectorError, TimeoutError):
                await sleep(5)
            except (JSONDecodeError, ContentTypeError):
                return [], []
        versions = [{"name": version, "serial_number": await version_to_serial_number(version)} for version in response.get("versions", {}).keys()]
        requirements = [data.get("dependencies", {}) for data in response.get("versions", {}).values()]
        await set_cache(package_name, (versions, requirements))
    return versions, requirements


async def get_npm_version(package_name: str, version_name: str) -> tuple[dict[str, Any], dict[str, Any]]:
    key = f"{package_name}:{version_name}"
    response = await get_cache(key)
    if response:
        version, requirement = response
    else:
        url = f"https://registry.npmjs.org/{package_name}"
        session = await get_session()
        while True:
            try:
                logger.info(f"NPM - {url}")
                async with session.get(url) as resp:
                    response = await resp.json()
                    break
            except (ClientConnectorError, TimeoutError):
                await sleep(5)
            except (JSONDecodeError, ContentTypeError):
                return [], []
        if version_name not in response.get("versions", {}).keys():
            raise ValueError(f"Version {version_name} not found for package {package_name}")
        version = {"name": version_name, "serial_number": await version_to_serial_number(version_name)}
        requirement = response.get("versions", {})[version_name].get("dependencies", {})
        await set_cache(key, (version, requirement))
    return version, requirement
