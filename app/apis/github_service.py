from asyncio import sleep
from datetime import datetime

from aiohttp import ClientConnectorError

from app.exceptions import DateNotFoundException, InvalidRepositoryException
from app.http_session import HTTPSessionManager
from app.settings import settings


class GitHubService:
    def __init__(self, http_session: HTTPSessionManager):
        self.http_session = http_session
        self.headers = {
            "Accept": "application/vnd.github.hawkgirl-preview+json",
            "Authorization": f"Bearer {settings.GITHUB_GRAPHQL_API_KEY}",
        }
        self.api_url = "https://api.github.com/graphql"

    async def get_last_commit_date(self, owner: str, name: str) -> datetime:
        query = f"""
        {{
            repository(owner: "{owner}", name: "{name}") {{
                defaultBranchRef {{
                    target {{
                        ... on Commit {{
                            committedDate
                        }}
                    }}
                }}
            }}
        }}
        """
        session = await self.http_session.get_session()
        while True:
            try:
                async with session.post(
                    self.api_url,
                    json={"query": query},
                    headers=self.headers,
                ) as response:
                    response = await response.json()
                    break
            except (ClientConnectorError, TimeoutError):
                await sleep(5)

        repo = response.get("data", {}).get("repository")
        if not repo or not repo.get("defaultBranchRef"):
            raise InvalidRepositoryException(owner, name)

        date_str = (
            repo["defaultBranchRef"]
            .get("target", {})
            .get("committedDate")
        )
        if not date_str:
            raise DateNotFoundException(owner, name)

        return datetime.fromisoformat(date_str)
