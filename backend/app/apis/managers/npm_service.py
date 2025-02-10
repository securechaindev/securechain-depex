from asyncio import TimeoutError, sleep
from json import JSONDecodeError
from typing import Any

from aiohttp import ClientConnectorError, ClientSession

from app.logger import logger


async def get_npm_versions(name: str) -> Any:
    api_url = f"https://registry.npmjs.org/{name}"
    async with ClientSession() as session:
        while True:
            try:
                logger.info(f"NPM - {api_url}")
                async with session.get(api_url) as response:
                    response = await response.json()
                    break
            except (ClientConnectorError, TimeoutError):
                await sleep(5)
            except JSONDecodeError:
                return {}
    versions = []
    all_require_packages = []
    for count, (version, data) in enumerate(response.get("versions", {}).items()):
        versions.append({"name": version, "count": count})
        all_require_packages.append(data.get("dependencies"))
    return (versions, all_require_packages)
