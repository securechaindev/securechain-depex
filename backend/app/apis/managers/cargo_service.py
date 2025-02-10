from asyncio import TimeoutError, sleep
from json import JSONDecodeError
from typing import Any

from aiohttp import ClientConnectorError, ClientSession

from app.logger import logger


async def get_cargo_versions(name: str) -> list[dict[str, Any]]:
    api_url = f"https://crates.io/api/v1/crates/{name}"
    async with ClientSession() as session:
        while True:
            try:
                logger.info(f"CARGO - {api_url}")
                async with session.get(api_url) as response:
                    response = await response.json()
                    break
            except (ClientConnectorError, TimeoutError):
                await sleep(5)
    versions: list[dict[str, Any]] = []
    for count, version in enumerate(response.get("versions", [])):
        versions.append(
            {"name": version.get("num"), "count": count}
        )
    return versions


async def get_cargo_requires(
    name: str, version: str
) -> dict[str, list[str] | str]:
    api_url = f"https://crates.io/api/v1/crates/{name}/{version}/dependencies"
    async with ClientSession() as session:
        while True:
            try:
                logger.info(f"CARGO - {api_url}")
                async with session.get(api_url) as response:
                    response = await response.json()
                    break
            except (ClientConnectorError, TimeoutError):
                await sleep(5)
            except JSONDecodeError:
                return {}
    require_packages: dict[str, Any] = {}
    for dependency in response.get("dependencies", []):
        require_packages[dependency.get("crate_id")] = dependency.get("req")
    return require_packages
