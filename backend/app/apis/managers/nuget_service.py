from asyncio import TimeoutError, sleep
from json import JSONDecodeError
from typing import Any, Dict, List, Tuple

from aiohttp import ClientConnectorError, ContentTypeError
from app.cache import get_cache, set_cache
from app.http_session import get_session
from app.logger import logger


async def fetch_page_versions(url: str) -> List[Dict[str, Any]]:
    session = await get_session()
    while True:
        response = await get_cache(url)
        if not response:
            try:
                async with session.get(url) as resp:
                    response = await resp.json()
                    await set_cache(url, response)
                    return response.get("items", [])
            except (ClientConnectorError, TimeoutError):
                await sleep(5)
            except (JSONDecodeError, ContentTypeError):
                return []

async def get_nuget_versions(
    name: str,
    constraints: str | None = None,
    parent_id: str | None = None,
    parent_version_name: str | None = None
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], str | None, str | None, str | None]:
    response = await get_cache(name)
    if response:
        versions, all_require_packages = response
    else:
        url = f"https://api.nuget.org/v3/registration5-gz-semver2/{name}/index.json"
        session = await get_session()
        while True:
            try:
                logger.info(f"NUGET - {url}")
                async with session.get(url) as resp:
                    response = await resp.json()
                    break
            except (ClientConnectorError, TimeoutError):
                await sleep(5)
            except (JSONDecodeError, ContentTypeError):
                return [], [], name, constraints, parent_id, parent_version_name
        versions = []
        all_require_packages = []
        count = 0
        for item in response.get("items", []) or []:
            if "items" in item:
                for version_item in item.get("items", []):
                    catalog_entry = version_item.get("catalogEntry", {})
                    versions.append({"name": catalog_entry.get("version"), "count": count})
                    count += 1
                    dependencies = {
                        dependency.get("id"): dependency.get("range")
                        for group in catalog_entry.get("dependencyGroups", [])
                        if "targetFramework" not in group
                        for dependency in group.get("dependencies", [])
                    }
                    all_require_packages.append(dependencies)
            elif "@id" in item:
                for version_item in await fetch_page_versions(item.get("@id")):
                    catalog_entry = version_item.get("catalogEntry", {})
                    versions.append({"name": catalog_entry.get("version"), "count": count})
                    count += 1
                    dependencies = {
                        dependency.get("id"): dependency.get("range")
                        for group in catalog_entry.get("dependencyGroups", [])
                        if "targetFramework" not in group
                        for dependency in group.get("dependencies", [])
                    }
                    all_require_packages.append(dependencies)
        await set_cache(name, (versions, all_require_packages))
    return versions, all_require_packages, name, constraints, parent_id, parent_version_name
