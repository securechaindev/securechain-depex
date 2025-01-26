from glob import glob
from os import makedirs, system
from os.path import exists, isdir

from git import GitCommandError, Repo

from .files.package_json_analyzer import analyze_package_json
from .files.pom_xml_analyzer import analyze_pom_xml
from .files.pyproject_toml_analyzer import analyze_pyproject_toml
from .files.requirements_txt_analyzer import analyze_requirements_txt
from .files.setup_cfg_analyzer import analyze_setup_cfg
from .files.setup_py_analyzer import analyze_setup_py

pypi_files = ["pyproject.toml", "setup.cfg", "setup.py", "requirements.txt"]
npm_files = ["package.json"]
maven_files = ["pom.xml"]


async def repo_analyzer(owner: str, name: str) -> dict[str, dict[str, dict | str]]:
    requirement_files: dict[str, dict[str, dict | str]] = {}
    repository_path = await download_repository(owner, name)
    requirement_file_names = await get_req_files_names(repository_path)
    for requirement_file_name in requirement_file_names:
        if "pom.xml" in requirement_file_name:
            requirement_files = await analyze_pom_xml(
                requirement_files, repository_path, requirement_file_name
            )
        elif "package.json" in requirement_file_name:
            requirement_files = await analyze_package_json(
                requirement_files, repository_path, requirement_file_name
            )
        elif "pyproject.toml" in requirement_file_name:
            requirement_files = await analyze_pyproject_toml(
                requirement_files, repository_path, requirement_file_name
            )
        elif "setup.cfg" in requirement_file_name:
            requirement_files = await analyze_setup_cfg(
                requirement_files, repository_path, requirement_file_name
            )
        elif "setup.py" in requirement_file_name:
            requirement_files = await analyze_setup_py(
                requirement_files, repository_path, requirement_file_name
            )
        elif "requirements.txt" in requirement_file_name:
            requirement_files = await analyze_requirements_txt(
                requirement_files, repository_path, requirement_file_name
            )
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
                requirement_files.append(
                    _path.replace(directory_path, "").replace(directory_path, "")
                )
    return requirement_files


async def is_req_file(requirement_file_name: str) -> bool:
    if any(extension in requirement_file_name for extension in pypi_files):
        return True
    if any(extension in requirement_file_name for extension in npm_files):
        return True
    if any(extension in requirement_file_name for extension in maven_files):
        return True
    return False
