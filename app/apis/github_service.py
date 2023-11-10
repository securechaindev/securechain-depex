from datetime import datetime
from time import sleep
from typing import Any

from dateutil.parser import parse
from requests import ConnectionError, ConnectTimeout, post

from app.config import settings
from app.utils import get_manager, parse_pip_constraints

headers_github = {
    "Accept": "application/vnd.github.hawkgirl-preview+json",
    "Authorization": f"Bearer {settings.GITHUB_GRAPHQL_API_KEY}",
}


async def get_repo_data(
    owner: str,
    name: str,
    all_packages: dict[str, Any] | None = None,
    end_cursor: str | None = None,
) -> dict[str, Any]:
    if not all_packages:
        all_packages = {}
    if not end_cursor:
        query = '{repository(owner: "' + owner + '", name: "' + name + '")'
        query += "{dependencyGraphManifests{nodes{filename dependencies{pageInfo {"
        query += "hasNextPage endCursor} nodes{packageName requirements}}}}}}"
    else:
        query = '{repository(owner: "' + owner + '", name: "' + name + '")'
        query += '{dependencyGraphManifests{nodes{filename dependencies(after: "'
        query += end_cursor + '"){pageInfo {hasNextPage endCursor}'
        query += "nodes{packageName requirements}}}}}}"
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
    page_info, all_packages = await json_reader(response, all_packages)
    if not page_info["hasNextPage"]:
        return all_packages
    return await get_repo_data(owner, name, all_packages, page_info["endCursor"])


async def json_reader(
    response: Any, all_packages: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    page_info = {"hasNextPage": None}
    for file_node in response["data"]["repository"]["dependencyGraphManifests"][
        "nodes"
    ]:
        requirement_file_name = file_node["filename"]
        if requirement_file_name == "package-lock.json":
            continue
        page_info = file_node["dependencies"]["pageInfo"]
        requirement_file_manager = await get_manager(requirement_file_name)
        if not requirement_file_manager:
            continue
        if requirement_file_name not in all_packages:
            all_packages[requirement_file_name] = {
                "package_manager": requirement_file_manager,
                "dependencies": {},
            }
        for depependency_node in file_node["dependencies"]["nodes"]:
            if requirement_file_manager == "MVN":
                if "=" in depependency_node["requirements"]:
                    depependency_node["requirements"] = (
                        "["
                        + depependency_node["requirements"]
                        .replace("=", "")
                        .replace(" ", "")
                        + "]"
                    )
            if requirement_file_manager == "PIP":
                depependency_node["requirements"] = await parse_pip_constraints(
                    depependency_node["requirements"]
                )
            all_packages[requirement_file_name]["dependencies"].update(
                {depependency_node["packageName"]: depependency_node["requirements"]}
            )
    return (page_info, all_packages)


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
    return parse(
        response["data"]["repository"]["defaultBranchRef"]["target"]["history"][
            "edges"
        ][0]["node"]["author"]["date"]
    )
