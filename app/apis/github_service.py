from asyncio import sleep
from datetime import datetime

from aiohttp import ClientConnectorError, ClientSession

from app.exceptions import InvalidRepositoryException
from app.settings import settings


class GitHubService:
    def __init__(self):
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
        async with ClientSession() as session:
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
            raise InvalidRepositoryException()

        date_str = (
            repo["defaultBranchRef"]
            .get("target", {})
            .get("committedDate")
        )
        if not date_str:
            raise InvalidRepositoryException()

        return datetime.fromisoformat(date_str)
