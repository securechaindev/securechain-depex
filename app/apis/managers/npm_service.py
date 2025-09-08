from asyncio import TimeoutError, sleep
from json import JSONDecodeError
from typing import Any

from aiohttp import ClientConnectorError, ContentTypeError

from app.cache import get_cache, set_cache
from app.http_session import get_session
from app.logger import logger
from app.utils.others import looks_like_repo, normalize_repo_url, order_versions


async def get_npm_versions(package_name: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str, str]:
    response = await get_cache(package_name)
    if response:
        versions, requirements, repository_url = response
    else:
        url = f"https://registry.npmjs.org/{package_name}"
        session = await get_session()
        while True:
            try:
                logger.info(f"NPM - {url}")
                async with session.get(url) as resp:
                    response = await resp.json()
                    break
            except (ClientConnectorError, TimeoutError):
                await sleep(5)
            except (JSONDecodeError, ContentTypeError):
                return [], []
        time_map = response.get("time", {})
        raw_url = None
        repository_url= None
        repository = response.get("repository")
        if isinstance(repository, dict):
            raw_url = repository.get("url")
        elif isinstance(repository, str):
            raw_url = repository
        norm_url = await normalize_repo_url(raw_url)
        if norm_url and await looks_like_repo(norm_url):
            repository_url = norm_url
            vendor = norm_url.split("/")[-2]
        raw_versions = []
        for version in response.get("versions", {}).keys():
            release_date = time_map.get(version)
            raw_versions.append({
                "name": version,
                "release_date": release_date
            })
        versions = await order_versions("NPMPackage", raw_versions)
        requirements = [v.get("dependencies", {}) for v in response.get("versions", {}).values()]
        await set_cache(package_name, (versions, requirements, repository_url))
    return versions, requirements, repository_url, vendor


async def get_npm_version(package_name: str, version_name: str) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    url = f"https://registry.npmjs.org/{package_name}"
    session = await get_session()
    while True:
        try:
            logger.info(f"NPM - {url}")
            async with session.get(url) as resp:
                response = await resp.json()
                break
        except (ClientConnectorError, TimeoutError):
            await sleep(5)
        except (JSONDecodeError, ContentTypeError):
            return {}, [], {}
    time_map = response.get("time", {})
    raw_versions = []
    for version in response.get("versions", {}).keys():
        release_date = time_map.get(version)
        raw_versions.append({
            "name": version,
            "release_date": release_date
        })
    versions = await order_versions("NPMPackage", raw_versions)
    index = next((i for i, d in enumerate(versions) if d.get("name") == version_name), None)
    if index is not None:
        dependencies = response.get("versions", {}).get(version_name, {}).get("dependencies", {}) or {}
        return versions[index], versions[index + 1:], dependencies
    else:
        raise ValueError(f"Version {version_name} not found for package {package_name}")
