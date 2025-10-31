from aiohttp import ClientSession

from app.settings import settings


class HTTPSessionManager:
    def __init__(self):
        self.session: ClientSession | None = None

    async def get_session(self) -> ClientSession:
        if self.session is None or self.session.closed:
            headers = {}
            headers["Authorization"] = f"token {settings.GITHUB_GRAPHQL_API_KEY}"
            self.session = ClientSession(headers=headers)
        return self.session

    async def close(self) -> None:
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None
