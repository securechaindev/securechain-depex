from asyncio import TimeoutError, sleep
from json import JSONDecodeError
from typing import Any

from aiohttp import ClientConnectorError, ContentTypeError

from app.cache import get_cache, set_cache
from app.http_session import get_session
from app.logger import logger
from app.utils.others import order_versions


async def get_rubygems_versions(package_name: str) -> list[dict[str, Any]]:
    response = await get_cache(package_name)
    if response:
        versions = response
    else:
        url = f"https://rubygems.org/api/v1/versions/{package_name}.json"
        session = await get_session()
        while True:
            try:
                logger.info(f"RubyGems - {url}")
                async with session.get(url) as resp:
                    response = await resp.json()
                    break
            except (ClientConnectorError, TimeoutError):
                await sleep(5)
            except (JSONDecodeError, ContentTypeError):
                return []
        raw_versions = [version.get("number") for version in response]
        versions = await order_versions("RubyGemsPackage", raw_versions)
        await set_cache(package_name, versions)
    return versions


async def get_rubygems_version(package_name: str, version_name: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    url = f"https://rubygems.org/api/v1/versions/{package_name}.json"
    session = await get_session()
    while True:
        try:
            logger.info(f"RubyGems - {url}")
            async with session.get(url) as resp:
                response = await resp.json()
                break
        except (ClientConnectorError, TimeoutError):
            await sleep(5)
        except (JSONDecodeError, ContentTypeError):
            return {}
    raw_versions = [version.get("number") for version in response]
    versions = await order_versions("RubyGemsPackage", raw_versions)
    index = next((i for i, d in enumerate(versions) if d.get("name") == version_name), None)
    if index is not None:
        return versions[index], versions[index + 1:]
    else:
        raise ValueError(f"Version {version_name} not found for package {package_name}")


async def get_rubygems_requirement(package_name: str, version_name: str) -> dict[str, list[str] | str]:
    key = f"requirement:{package_name}:{version_name}"
    response = await get_cache(key)
    if response:
        require_packages = response
    else:
        url = f"https://rubygems.org/api/v2/rubygems/{package_name}/versions/{version_name}.json"
        session = await get_session()
        while True:
            try:
                logger.info(f"RubyGems - {url}")
                async with session.get(url) as resp:
                    response = await resp.json()
                    break
            except (ClientConnectorError, TimeoutError):
                await sleep(5)
            except (JSONDecodeError, ContentTypeError):
                return {}
        require_packages: dict[str, Any] = {
            dep.get("name"): dep.get("requirements") for dep in response.get("dependencies", {}).get("runtime", []) or []
        }
        await set_cache(key, require_packages)
    return require_packages
