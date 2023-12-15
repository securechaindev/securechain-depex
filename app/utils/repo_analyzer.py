from git import GitCommandError, Repo
from os import makedirs, system
from os.path import exists, isdir
from glob import glob
from typing import Any

from .files.pom_xml_analyzer import analyze_pom_xml
from .files.package_json_analyzer import analyze_package_json
from .managers import get_manager
from .parse_pip_constraints import parse_pip_constraints

from time import sleep
from requests import ConnectionError, ConnectTimeout, post

from app.config import settings

headers_github = {
    "Accept": "application/vnd.github.hawkgirl-preview+json",
    "Authorization": f"Bearer {settings.GITHUB_GRAPHQL_API_KEY}",
}

pip_files = ["pyproject.toml"]
npm_files = ["package.json"]
mvn_files = ["pom.xml"]


async def repo_analyzer(owner: str, name: str, manager: str) -> dict[str, dict[str, dict|str]]:
    if manager == "PIP":
        return await get_repo_data(owner, name)
    else:
        requirement_files: dict[str, dict[str, dict|str]] = {}
        repository_path = await download_repository(owner, name)
        requirement_file_names = await get_req_files_names(repository_path)
        for requirement_file_name in requirement_file_names:
            if "pom.xml" in requirement_file_name:
                requirement_files = await analyze_pom_xml(requirement_files, repository_path, requirement_file_name)
            elif "package.json" in requirement_file_name:
                requirement_files = await analyze_package_json(requirement_files, repository_path, requirement_file_name)
        system("rm -rf " + repository_path)
        return requirement_files


async def download_repository(owner: str, name: str) -> str:
    repository_path = "repositories/" + name
    branches = ["main", "master"]
    makedirs(repository_path)
    for branch in branches:
        branch_dir = repository_path + "/" + branch
        if not exists(branch_dir):
            makedirs(branch_dir)
        try:
            Repo.clone_from(
                f"https://github.com/{owner}/{name}.git", branch_dir, branch=branch
            )
        except GitCommandError:
            continue
    return repository_path


async def get_req_files_names(directory_path: str) -> list[str]:
    branches = ["/main", "/master"]
    requirement_files = []
    for branch in branches:
        paths = glob(directory_path + branch + "/**", recursive=True)
        for _path in paths:
            if not isdir(_path) and await is_req_file(_path):
                requirement_files.append(_path.replace(directory_path, "").replace(directory_path, ""))
    return requirement_files


async def is_req_file(requirement_file_name: str) -> bool:
    if any(extension in requirement_file_name for extension in pip_files):
        return True
    if any(extension in requirement_file_name for extension in npm_files):
        return True
    if any(extension in requirement_file_name for extension in mvn_files):
        return True
    return False

async def get_repo_data(
    owner: str,
    name: str,
    all_packages: dict[str, Any] | None = None,
    end_cursor: str | None = None,
) -> dict[str, Any]:
    if not all_packages:
        all_packages = {}
    if not end_cursor:
        query = f"""
        {{
            repository(owner: "{owner}", name: "{name}") {{
                dependencyGraphManifests {{
                    nodes {{
                        filename
                        dependencies {{
                            pageInfo {{
                                hasNextPage
                                endCursor
                            }}
                            nodes {{
                                packageName
                                requirements
                            }}
                        }}
                    }}
                }}
            }}
        }}
        """
    else:
        query = f"""
        {{
            repository(owner: "{owner}", name: "{name}") {{
                dependencyGraphManifests {{
                    nodes {{
                        filename
                        dependencies (after: "{end_cursor}") {{
                            pageInfo {{
                                hasNextPage
                                endCursor
                            }}
                            nodes {{
                                packageName
                                requirements
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