from datetime import datetime
from time import sleep

from dateutil.parser import parse
from requests import ConnectionError, ConnectTimeout, post

from app.config import settings

headers_gitlab = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {settings.GITLAB_GRAPHQL_API_KEY}",
}


async def get_last_commit_date_gitlab(owner: str, name: str) -> datetime:
    query = f"""
    {{
        project(fullPath: "{owner}/{name}") {{
            lastActivityAt
        }}
    }}
    """
    while True:
        try:
            response = post(
                "https://gitlab.com/api/graphql",
                json={"query": query},
                headers=headers_gitlab,
            ).json()
            break
        except (ConnectTimeout, ConnectionError):
            sleep(5)
    return parse(response["data"]["project"]["lastActivityAt"])
