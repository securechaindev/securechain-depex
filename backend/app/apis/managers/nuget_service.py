from asyncio import TimeoutError, sleep
from json import JSONDecodeError
from typing import Any

from aiohttp import ClientConnectorError, ClientSession

# from app.logger import logger


async def get_all_nuget_versions(pkg_name: str) -> Any:
    async with ClientSession() as session:
        while True:
            try:
                # logger.info(f"NUGET - https://api.nuget.org/v3/registration5-gz-semver2/{pkg_name}/index.json")
                async with session.get(f"https://api.nuget.org/v3/registration5-gz-semver2/{pkg_name}/index.json") as response:
                    response = await response.json()
                    break
            except (ClientConnectorError, TimeoutError):
                await sleep(5)
            except JSONDecodeError:
                return {}
    if "items" in response and "items" in response["items"][0]:
        versions = []
        all_require_packages = []
        raw_versions = response["items"][0]["items"]
        for count, raw_version in enumerate(raw_versions):
            versions.append(
                {
                    "name": raw_version["catalogEntry"]["version"],
                    "release_date": None,
                    "count": count,
                }
            )
            ctcs = {}
            if "dependencyGroups" in raw_version["catalogEntry"]:
                for dependencyGroup in raw_version["catalogEntry"]["dependencyGroups"]:
                    if "dependencies" in dependencyGroup and "targetFramework" not in dependencyGroup:
                        for dependency in dependencyGroup["dependencies"]:
                            ctcs[dependency["id"]] = dependency["range"]
            all_require_packages.append(ctcs)
        return (versions, all_require_packages)
    return ([], [])
