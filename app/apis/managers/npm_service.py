from asyncio import TimeoutError, sleep
from json import JSONDecodeError
from typing import Any

from aiohttp import ClientConnectorError, ContentTypeError

from app.cache import get_cache, set_cache
from app.http_session import get_session
from app.logger import logger
from app.utils.others import order_versions


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
        raw_versions = list(response.get("versions", {}).keys())
        versions = await order_versions("NPMPackage", raw_versions)
        requirements = [data.get("dependencies", {}) for data in response.get("versions", {}).values()]
        await set_cache(package_name, (versions, requirements))
    return versions, requirements


async def get_npm_version(package_name: str, version_name: str) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
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
    versions = await order_versions("NPMPackage", response.get("versions", {}).keys())
    index = next((i for i, d in enumerate(versions) if d.get("name") == version_name), None)
    if index is not None:
        return versions[index], versions[index + 1:], response.get("versions", {})[version_name].get("dependencies", {})
    else:
        raise ValueError(f"Version {version_name} not found for package {package_name}")
