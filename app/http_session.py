from aiohttp import ClientSession

session: ClientSession | None = None

async def get_session() -> ClientSession:
    global session
    if session is None or session.closed:
        session = ClientSession()
    return session

async def close_session():
    global session
    if session and not session.closed:
        await session.close()
