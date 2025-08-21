from glob import glob
from os import makedirs
from os.path import exists, isdir, join
from shutil import rmtree

from aiofiles import open

from app.http_session import get_session

from .requirement_files import (
    analyze_cargo_lock,
    analyze_cargo_toml,
    analyze_gemfile,
    analyze_gemfile_lock,
    analyze_package_json,
    analyze_package_lock_json,
    analyze_packages_config,
    analyze_pom_xml,
    analyze_pyproject_toml,
    analyze_requirements_txt,
    analyze_setup_cfg,
    analyze_setup_py,
)

pypi_files = ["pyproject.toml", "setup.cfg", "setup.py", "requirements.txt"]
npm_files = ["package.json", "package-lock.json"]
maven_files = ["pom.xml"]
nuget_files = ["packages.config"]
ruby_files = ["Gemfile", "Gemfile.lock"]
cargo_files = ["Cargo.toml", "Cargo.lock"]
all_files = set(pypi_files + npm_files + maven_files + nuget_files + ruby_files + cargo_files)

async def repo_analyzer(owner: str, name: str) -> dict[str, dict[str, dict | str]]:
    requirement_files: dict[str, dict[str, dict | str]] = {}
    repository_path = await download_repository(owner, name)
    requirement_file_names = await get_req_files_names(repository_path)
    for requirement_file_name in requirement_file_names:
        if "pom.xml" == requirement_file_name:
            requirement_files = await analyze_pom_xml(
                requirement_files, repository_path, requirement_file_name
            )
        elif "package.json" == requirement_file_name:
            requirement_files = await analyze_package_json(
                requirement_files, repository_path, requirement_file_name
            )
        elif "package-lock.json" == requirement_file_name:
            requirement_files = await analyze_package_lock_json(
                requirement_files, repository_path, requirement_file_name
            )
        elif "pyproject.toml" == requirement_file_name:
            requirement_files = await analyze_pyproject_toml(
                requirement_files, repository_path, requirement_file_name
            )
        elif "setup.cfg" == requirement_file_name:
            requirement_files = await analyze_setup_cfg(
                requirement_files, repository_path, requirement_file_name
            )
        elif "setup.py" == requirement_file_name:
            requirement_files = await analyze_setup_py(
                requirement_files, repository_path, requirement_file_name
            )
        elif "requirements.txt" in requirement_file_name:
            requirement_files = await analyze_requirements_txt(
                requirement_files, repository_path, requirement_file_name
            )
        elif "packages.config" == requirement_file_name:
            requirement_files = await analyze_packages_config(
                requirement_files, repository_path, requirement_file_name
            )
        elif "Gemfile" == requirement_file_name:
            requirement_files = await analyze_gemfile(
                requirement_files, repository_path, requirement_file_name
            )
        elif "Gemfile.lock" == requirement_file_name:
            requirement_files = await analyze_gemfile_lock(
                requirement_files, repository_path, requirement_file_name
            )
        elif "Cargo.toml" == requirement_file_name:
            requirement_files = await analyze_cargo_toml(
                requirement_files, repository_path, requirement_file_name
            )
        elif "Cargo.lock" == requirement_file_name:
            requirement_files = await analyze_cargo_lock(
                requirement_files, repository_path, requirement_file_name
            )
    rmtree(repository_path)
    return requirement_files


async def download_repository(owner: str, name: str) -> str:
    repository_path = f"repositories/{owner}/{name}"
    if exists(repository_path):
        rmtree(repository_path)
    makedirs(repository_path)
    session = await get_session()
    url = f"https://api.github.com/repos/{owner}/{name}/contents"
    async with session.get(url) as resp:
        if resp.status != 200:
            return repository_path
        contents = await resp.json()
    for item in contents:
        if item["type"] == "file" and any(extension in item["name"] for extension in all_files):
            raw_url = item["download_url"]
            async with session.get(raw_url) as file_resp:
                if file_resp.status == 200:
                    file_content = await file_resp.text()
                    filepath = join(repository_path, item["name"])
                    async with open(filepath, "w") as f:
                            await f.write(file_content)
    return repository_path


async def get_req_files_names(directory_path: str) -> list[str]:
    requirement_files = []
    paths = glob(directory_path + "/**", recursive=True)
    for _path in paths:
        if not isdir(_path) and await is_req_file(_path):
            requirement_files.append(
                _path.replace(directory_path, "").replace(directory_path, "").replace("/", "")
            )
    return requirement_files


async def is_req_file(requirement_file_name: str) -> bool:
    if any(extension in requirement_file_name for extension in all_files):
        return True
    return False
