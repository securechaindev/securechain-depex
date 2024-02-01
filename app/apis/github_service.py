from datetime import datetime
from time import sleep

from dateutil.parser import parse
from requests import ConnectionError, ConnectTimeout, post

from app.config import settings

headers_github = {
    "Accept": "application/vnd.github.hawkgirl-preview+json",
    "Authorization": f"Bearer {settings.GITHUB_GRAPHQL_API_KEY}",
}


async def get_last_commit_date_github(owner: str, name: str) -> datetime:
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
    while True:
        try:
            response = post(
                "https://api.github.com/graphql",
                json={"query": query},
                headers=headers_github,
            ).json()
            break
        except (ConnectTimeout, ConnectionError):
            sleep(5)
    if "defaultBranchRef" in response["data"]["repository"]:
        return parse(
            response["data"]["repository"]["defaultBranchRef"]["target"]["history"][
                "edges"
            ][0]["node"]["author"]["date"]
        )
