from asyncio import TimeoutError, sleep
from json import JSONDecodeError
from typing import Any, Dict, List

from aiohttp import ClientConnectorError, ClientSession

from app.logger import logger


async def fetch_page_versions(url: str) -> List[Dict[str, Any]]:
    async with ClientSession() as session:
        while True:
            try:
                async with session.get(url) as response:
                    page_data = await response.json()
                    return page_data.get("items", [])
            except (ClientConnectorError, TimeoutError):
                await sleep(5)
            except JSONDecodeError:
                return []


async def get_nuget_versions(name: str) -> Any:
    api_url = f"https://api.nuget.org/v3/registration5-gz-semver2/{name}/index.json"
    async with ClientSession() as session:
        while True:
            try:
                logger.info(f"NUGET - {api_url}")
                async with session.get(api_url) as response:
                    response = await response.json()
                    break
            except (ClientConnectorError, TimeoutError):
                await sleep(5)
            except JSONDecodeError:
                return {}
    items = response.get("items", [])
    versions = []
    all_require_packages = []
    for item in items:
        if "items" in item:
            for version_item in item["items"]:
                catalog_entry = version_item.get("catalogEntry", {})
                versions.append(
                    {
                        "name": catalog_entry.get("version"),
                        "release_date": catalog_entry.get("published"),
                        "authors": catalog_entry.get("authors"),
                        "description": catalog_entry.get("description"),
                        "vulnerabilities": catalog_entry.get("vulnerabilities", []),
                    }
                )
                dependency_groups = catalog_entry.get("dependencyGroups", [])
                dependencies = {
                    dependency["id"]: dependency["range"]
                    for group in dependency_groups
                    if "dependencies" in group and "targetFramework" not in group
                    for dependency in group["dependencies"]
                }
                all_require_packages.append(dependencies)
        elif "@id" in item:
            page_url = item["@id"]
            page_versions = await fetch_page_versions(page_url)
            for version_item in page_versions:
                catalog_entry = version_item.get("catalogEntry", {})
                versions.append(
                    {
                        "name": catalog_entry.get("version"),
                        "release_date": catalog_entry.get("published"),
                        "authors": catalog_entry.get("authors"),
                        "description": catalog_entry.get("description"),
                        "vulnerabilities": catalog_entry.get("vulnerabilities", []),
                    }
                )
                dependency_groups = catalog_entry.get("dependencyGroups", [])
                dependencies = {
                    dependency["id"]: dependency["range"]
                    for group in dependency_groups
                    if "dependencies" in group and "targetFramework" not in group
                    for dependency in group["dependencies"]
                }
                all_require_packages.append(dependencies)
    return (versions, all_require_packages)
