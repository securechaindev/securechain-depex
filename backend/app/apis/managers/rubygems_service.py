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
    if response:
        versions: list[dict[str, Any]] = []
        for count, version in enumerate(response):
            versions.append(
                {"name": version["number"], "count": count}
            )
        return versions
    return []


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
    if response and "dependencies" in response and "runtime" in response["dependencies"]:
        require_packages: dict[str, Any] = {}
        for dependency in response["dependencies"]["runtime"]:
            require_packages[dependency["name"]] = dependency["requirements"]
        return require_packages
    return {}
