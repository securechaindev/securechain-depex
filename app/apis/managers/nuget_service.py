from asyncio import TimeoutError, sleep
from json import JSONDecodeError
from typing import Any

from aiohttp import ClientConnectorError, ContentTypeError

from app.cache import get_cache, set_cache
from app.http_session import get_session
from app.logger import logger
from app.utils.others import looks_like_repo, normalize_repo_url, order_versions


async def fetch_page_versions(url: str) -> list[dict[str, Any]]:
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

async def get_nuget_versions(package_name: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    response = await get_cache(package_name)
    if response:
        versions, requirements, repository_url = response
    else:
        url = f"https://api.nuget.org/v3/registration5-gz-semver2/{package_name}/index.json"
        session = await get_session()
        while True:
            try:
                logger.info(f"NuGet - {url}")
                async with session.get(url) as resp:
                    response = await resp.json()
                    break
            except (ClientConnectorError, TimeoutError):
                await sleep(5)
            except (JSONDecodeError, ContentTypeError):
                return [], []
        raw_versions = []
        requirements = []
        repository_url = None
        vendor = None
        for item in response.get("items", []) or []:
            subitems = item.get("items") or await fetch_page_versions(item.get("@id")) if "@id" in item else []
            for version_item in subitems:
                catalog_entry = version_item.get("catalogEntry", {})
                name = catalog_entry.get("version")
                release_date = catalog_entry.get("published")
                raw_url = catalog_entry.get("repositoryUrl")
                norm_url = await normalize_repo_url(raw_url)
                if norm_url and await looks_like_repo(norm_url):
                    repository_url = norm_url 
                    vendor = norm_url.split("/")[-2]
                raw_versions.append({
                    "name": name,
                    "release_date": release_date
                })
                dependencies = {
                    dep.get("id"): dep.get("range")
                    for group in catalog_entry.get("dependencyGroups", [])
                    if "targetFramework" not in group
                    for dep in group.get("dependencies", [])
                }
                requirements.append(dependencies)

        versions = await order_versions("NuGetPackage", raw_versions)
        await set_cache(package_name, (versions, requirements, repository_url))
    return versions, requirements, repository_url, vendor


async def get_nuget_version(package_name: str, version_name: str) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    url = f"https://api.nuget.org/v3/registration5-gz-semver2/{package_name}/index.json"
    session = await get_session()
    while True:
        try:
            logger.info(f"NuGet - {url}")
            async with session.get(url) as resp:
                response = await resp.json()
                break
        except (ClientConnectorError, TimeoutError):
            await sleep(5)
        except (JSONDecodeError, ContentTypeError):
            return {}, [], {}
    raw_versions = []
    requirements = []
    for item in response.get("items", []) or []:
        subitems = item.get("items") or await fetch_page_versions(item.get("@id")) if "@id" in item else []
        for version_item in subitems:
            catalog_entry = version_item.get("catalogEntry", {})
            name = catalog_entry.get("version")
            release_date = catalog_entry.get("published")
            raw_versions.append({
                "name": name,
                "release_date": release_date
            })
            dependencies = {
                dep.get("id"): dep.get("range")
                for group in catalog_entry.get("dependencyGroups", [])
                if "targetFramework" not in group
                for dep in group.get("dependencies", [])
            }
            requirements.append(dependencies)
    versions = await order_versions("NuGetPackage", raw_versions)
    index = next((i for i, d in enumerate(versions) if d.get("name") == version_name), None)
    if index is not None:
        return versions[index], versions[index + 1:], requirements[index]
    else:
        raise ValueError(f"Version {version_name} not found for package {package_name}")
