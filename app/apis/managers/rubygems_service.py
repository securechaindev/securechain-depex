from asyncio import TimeoutError, sleep
from json import JSONDecodeError
from typing import Any

from aiohttp import ClientConnectorError, ContentTypeError

from app.cache import get_cache, set_cache
from app.http_session import get_session
from app.logger import logger
from app.utils.others import version_to_serial_number


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
        versions = [{"name": version.get("number"), "serial_number": await version_to_serial_number(version)} for version in response]
        await set_cache(package_name, versions)
    return versions


async def get_rubygems_version(package_name: str, version_name: str) -> dict[str, Any]:
    key = f"version:{package_name}:{version_name}"
    response = await get_cache(key)
    if response:
        version = response
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
                await set_cache(url, "error")
                await sleep(5)
            except (JSONDecodeError, ContentTypeError):
                await set_cache(url, "error")
                return {}
        versions = [version.get("number") for version in response]
        if version_name in versions:
            version = {"name": version_name, "serial_number": await version_to_serial_number(version_name)}
            await set_cache(key, version)
        else:
            raise ValueError(f"Version {version_name} not found for package {package_name}")
    return version


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
