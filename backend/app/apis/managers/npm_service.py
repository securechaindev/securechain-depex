from asyncio import TimeoutError, sleep
from json import JSONDecodeError
from typing import Any

from aiohttp import ClientConnectorError, ClientSession

from app.logger import logger


async def get_all_npm_versions(pkg_name: str) -> Any:
    async with ClientSession() as session:
        while True:
            try:
                logger.info(f"NPM - https://registry.npmjs.org/{pkg_name}")
                async with session.get(f"https://registry.npmjs.org/{pkg_name}") as response:
                    response = await response.json()
                    break
            except (ClientConnectorError, TimeoutError):
                await sleep(5)
            except JSONDecodeError:
                return {}
    if "versions" in response:
        versions = []
        all_require_packages = []
        raw_versions = response["versions"]
        for count, version in enumerate(raw_versions):
            versions.append(
                {
                    "name": version,
                    "release_date": None,
                    "count": count,
                }
            )
            all_require_packages.append(
                raw_versions[version]["dependencies"]
                if "dependencies" in raw_versions[version]
                else {}
            )
        return (versions, all_require_packages)
    return ([], [])
