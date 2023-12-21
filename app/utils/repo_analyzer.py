from git import GitCommandError, Repo
from os import makedirs, system
from os.path import exists, isdir
from glob import glob
from typing import Any

from .files.pom_xml_analyzer import analyze_pom_xml
from .files.package_json_analyzer import analyze_package_json

pip_files = ["pyproject.toml"]
npm_files = ["package.json"]
mvn_files = ["pom.xml"]


async def repo_analyzer(owner: str, name: str) -> dict[str, dict[str, dict|str]]:
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
