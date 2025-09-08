from asyncio import TimeoutError, sleep
from json import JSONDecodeError
from typing import Any

from aiohttp import ClientConnectorError, ContentTypeError

from app.cache import get_cache, set_cache
from app.http_session import get_session
from app.logger import logger
from app.utils.others import looks_like_repo, normalize_repo_url, order_versions


async def get_cargo_url_vendor(response: dict[str, Any]) -> tuple[str, str]:
    raw_url = response.get("crate", {}).get("repository")
    norm_url = await normalize_repo_url(raw_url)
    if norm_url and await looks_like_repo(norm_url):
        vendor = norm_url.split("/")[-2]
        return norm_url, vendor
    return "", ""


async def get_cargo_versions(package_name: str) -> tuple[list[dict[str, Any]], str, str]:
    response = await get_cache(package_name)
    if response:
        versions, repository_url, vendor = response
    else:
        url = f"https://crates.io/api/v1/crates/{package_name}"
        session = await get_session()
        while True:
            try:
                logger.info(f"Cargo - {url}")
                async with session.get(url) as resp:
                    response = await resp.json()
                    break
            except (ClientConnectorError, TimeoutError):
                await sleep(5)
            except (JSONDecodeError, ContentTypeError):
                return []
        raw_versions = response.get("versions", [])
        versions_list = []
        for v in raw_versions:
            ver = v.get("num")
            created_at = v.get("created_at")
            versions_list.append({
                "name": ver,
                "release_date": created_at
            })
        versions = await order_versions("CargoPackage", versions_list)
        repository_url, vendor = await get_cargo_url_vendor(response)
        await set_cache(package_name, (versions, repository_url, vendor))
    return versions, repository_url, vendor


async def get_cargo_version(package_name: str, version_name: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    url = f"https://crates.io/api/v1/crates/{package_name}"
    session = await get_session()
    while True:
        try:
            logger.info(f"Cargo - {url}")
            async with session.get(url) as resp:
                response = await resp.json()
                break
        except (ClientConnectorError, TimeoutError):
            await sleep(5)
        except (JSONDecodeError, ContentTypeError):
            return {}, []
    raw_versions = response.get("versions", [])
    versions_list = []
    for v in raw_versions:
        ver = v.get("num")
        created_at = v.get("created_at")
        versions_list.append({
            "name": ver,
            "release_date": created_at
        })
    versions = await order_versions("CargoPackage", versions_list)
    index = next((i for i, d in enumerate(versions) if d.get("name") == version_name), None)
    if index is not None:
        return versions[index], versions[index + 1:]
    else:
        raise ValueError(f"Version {version_name} not found for package {package_name}")


async def get_cargo_package(package_name: str, version_name: str) -> dict[str, Any]:
    key = f"requirement:{package_name}:{version_name}"
    response = await get_cache(key)
    if response:
        requirement = response
    else:
        url = f"https://crates.io/api/v1/crates/{package_name}/{version_name}/dependencies"
        session = await get_session()
        while True:
            try:
                logger.info(f"Cargo - {url}")
                async with session.get(url) as resp:
                    response = await resp.json()
                    break
            except (ClientConnectorError, TimeoutError):
                await sleep(5)
            except (JSONDecodeError, ContentTypeError):
                return {}
        requirement: dict[str, Any] = {dep.get("crate_id"): dep.get("req") for dep in response.get("dependencies", []) or []}
        await set_cache(key, requirement)
    return requirement
