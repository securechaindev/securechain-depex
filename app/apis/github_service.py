from asyncio import TimeoutError, sleep
from datetime import datetime

from aiohttp import ClientConnectorError, ClientSession

from app.config import settings
from app.exceptions import InvalidRepositoryException

headers_github = {
    "Accept": "application/vnd.github.hawkgirl-preview+json",
    "Authorization": f"Bearer {settings.GITHUB_GRAPHQL_API_KEY}",
}


async def get_last_commit_date_github(owner: str, name: str) -> datetime | bool:
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
                    "https://api.github.com/graphql",
                    json={"query": query},
                    headers=headers_github,
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
