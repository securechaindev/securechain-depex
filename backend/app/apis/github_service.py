from asyncio import TimeoutError, sleep
from datetime import datetime

from aiohttp import ClientConnectorError, ClientSession
from dateutil.parser import parse

from app.config import settings

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
                        history(first: 1) {{
                            edges {{
                                node {{
                                    author {{
                                    date
                                    }}
                                }}
                            }}
                        }}
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
    if response["data"]["repository"]:
        if "defaultBranchRef" in response["data"]["repository"]:
            return parse(
                response["data"]["repository"]["defaultBranchRef"]["target"]["history"][
                    "edges"
                ][0]["node"]["author"]["date"]
            )
    else:
        return False
