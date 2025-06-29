from asyncio import TimeoutError, sleep
from json import JSONDecodeError
from typing import Any

from aiohttp import ClientConnectorError, ContentTypeError

from app.cache import get_cache, set_cache
from app.http_session import get_session
from app.logger import logger


async def get_npm_versions(
    name: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    response = await get_cache(name)
    if response:
        versions, all_require_packages = response
    else:
        url = f"https://registry.npmjs.org/{name}"
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
        versions = [{"name": version, "count": count} for count, version in enumerate(response.get("versions", {}).keys())]
        all_require_packages = [data.get("dependencies", {}) for data in response.get("versions", {}).values()]
        await set_cache(name, (versions, all_require_packages))
    return versions, all_require_packages
