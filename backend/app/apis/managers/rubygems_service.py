from asyncio import TimeoutError, sleep
from json import JSONDecodeError
from typing import Any

from aiohttp import ClientConnectorError, ClientSession

from app.logger import logger


async def get_rubygems_versions(name: str) -> list[dict[str, Any]]:
    api_url = f"https://rubygems.org/api/v1/versions/{name}.json"
    async with ClientSession() as session:
        while True:
            try:
                logger.info(f"RUBYGEMS - {api_url}")
                async with session.get(api_url) as response:
                    response = await response.json()
                    break
            except (ClientConnectorError, TimeoutError):
                await sleep(5)
    versions: list[dict[str, Any]] = []
    for count, version in enumerate(response):
        versions.append(
            {"name": version.get("number"), "count": count}
        )
    return versions


async def get_rubygems_requires(
    name: str, version: str
) -> dict[str, list[str] | str]:
    api_url = f"https://rubygems.org/api/v2/rubygems/{name}/versions/{version}.json"
    async with ClientSession() as session:
        while True:
            try:
                logger.info(f"RUBYGEMS - {api_url}")
                async with session.get(api_url) as response:
                    response = await response.json()
                    break
            except (ClientConnectorError, TimeoutError):
                await sleep(5)
            except JSONDecodeError:
                return {}
    require_packages: dict[str, Any] = {}
    for dependency in response.get("dependencies", {}).get("runtime", {}) or []:
        require_packages[dependency.get("name")] = dependency.get("requirements")
    return require_packages
