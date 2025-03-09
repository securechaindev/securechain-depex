from asyncio import TimeoutError, sleep
from json import JSONDecodeError
from typing import Any

from aiohttp import ClientConnectorError, ContentTypeError
from app.cache import get_cache, set_cache
from app.http_session import get_session
from app.logger import logger


async def get_npm_versions(
    name: str,
    constraints: str | None = None,
    parent_id: str | None = None,
    parent_version_name: str | None = None
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str | None, str | None, str | None]:
    url = f"https://registry.npmjs.org/{name}"
    session = await get_session()
    while True:
        response = await get_cache(url)
        if not response:
            try:
                logger.info(f"NPM - {url}")
                async with session.get(url) as resp:
                    response = await resp.json()
                    await set_cache(url, response)
                    break
            except (ClientConnectorError, TimeoutError):
                await sleep(5)
            except (JSONDecodeError, ContentTypeError):
                return [], [], constraints, parent_id, parent_version_name
    versions = [{"name": version, "count": count} for count, version in enumerate(response.get("versions", {}).keys())]
    all_require_packages = [data.get("dependencies", {}) for data in response.get("versions", {}).values()]
    return versions, all_require_packages, constraints, parent_id, parent_version_name
