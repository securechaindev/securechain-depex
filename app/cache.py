from aiocache import SimpleMemoryCache

cache = SimpleMemoryCache()

async def get_cache(url: str):
    return await cache.get(url)


async def set_cache(url: str, response: str):
    await cache.set(url, response, ttl=600)
