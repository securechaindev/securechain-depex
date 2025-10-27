from aiohttp import ClientSession


class HTTPSessionManager:
    def __init__(self):
        self._session: ClientSession | None = None

    async def get_session(self) -> ClientSession:
        if self._session is None or self._session.closed:
            self._session = ClientSession()
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
