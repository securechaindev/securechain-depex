from glob import glob
from os import makedirs, system
from os.path import exists, isdir
from typing import Any

from fastapi import APIRouter, Path, status
from fastapi.responses import JSONResponse
from git import GitCommandError, Repo
from regex import findall, search
from typing_extensions import Annotated

from app.models import PackageManager
from app.services import (
    read_cve_by_id,
    read_cve_ids_by_version_and_package,
    read_exploits_by_cve_id,
)
from app.utils import json_encoder

router = APIRouter()


@router.post(
    "/test_report/{owner}/{name}",
    summary="Create a test report by repository id and configuration",
    response_description="Return a test report",
)
async def create_test_report(
    owner: Annotated[str, Path(min_length=1)],
    name: Annotated[str, Path(min_length=1)],
    configuration: dict[str, str | int | float],
    package_manager: PackageManager,
) -> JSONResponse:
    """
    Return a test report by a given owner, name and a configuration of a repository:

    - **owner**: the owner of a repository
    - **name**: the name of a repository
    - **configuration**: a valid configuration for a file of the repository
    """
    carpeta_descarga = await download_repository(owner, name)
    paths = await get_files_path(carpeta_descarga)
    raw_report = await get_raw_report(configuration, package_manager)
    test_report: dict[str, list[Any]] = {"tests": []}
    number = 0
    for dependency in raw_report:
        for cve in dependency["cves"]:
            if cve["exploits"]:
                for exploit in cve["exploits"]:
                    tests, number = await create_tests(
                        number, paths, dependency, cve, exploit
                    )
                    test_report["tests"].extend(tests)
            else:
                tests, number = await create_tests(number, paths, dependency, cve)
                test_report["tests"].extend(tests)
    system("rm -rf " + carpeta_descarga)
    return JSONResponse(
        status_code=status.HTTP_200_OK, content=json_encoder(test_report)
    )


async def create_tests(
    number: int, paths: list[str], dependency, cve, exploit_id: str | None = None
) -> tuple[list[Any], int]:
    tests = []
    if dependency["name"] == "pycrypto":
        dependency["name"] = "Crypto"
    for _path in paths:
        dep_artifacts = await get_dep_artifacts(_path, dependency["name"], cve["description"])
        if await is_imported(_path, dependency["name"]) and dep_artifacts:
            number += 1
            tests.append(
                {
                    f"test{number}": {
                        "dependency": dependency["name"],
                        "version": dependency["version"],
                        "file_path": _path.replace("repositories/", ""),
                        "dep_artifacts": dep_artifacts,
                        "vulnerability": cve["id"],
                        "vuln_impact": cve["vuln_impact"],
                        "exploit": "https://www.exploit-db.com/exploits/" + exploit_id
                        if exploit_id
                        else None,
                        "payload": "https://www.exploit-db.com/download/" + exploit_id
                        if exploit_id
                        else None,
                        "automatable": bool(exploit_id),
                    }
                }
            )
    return (tests, number)


async def get_raw_report(
    configuration: dict[str, str | int | float], package_manager: str
) -> list[dict[str, Any]]:
    raw_report = []
    for dependency, version in configuration.items():
        if isinstance(version, str):
            cves = []
            cve_ids = await read_cve_ids_by_version_and_package(
                version, dependency, package_manager
            )
            if cve_ids:
                for cve_id in cve_ids:
                    cve = await read_cve_by_id(cve_id)
                    exploits = await read_exploits_by_cve_id(cve_id)
                    cves.append(
                        {
                            "id": cve_id,
                            "description": cve["description"],
                            "vuln_impact": cve["vuln_impact"][0],
                            "exploits": exploits,
                        }
                    )
                raw_report.append(
                    {
                        "name": dependency,
                        "version": version,
                        "cves": cves,
                    }
                )
    return raw_report


async def download_repository(owner: str, name: str) -> str:
    carpeta_descarga = "repositories/" + name
    system("rm -rf " + carpeta_descarga)
    branches = ["main", "master"]
    makedirs(carpeta_descarga)
    for branch in branches:
        branch_dir = carpeta_descarga + "/" + branch
        if not exists(branch_dir):
            makedirs(branch_dir)
        try:
            Repo.clone_from(
                f"https://github.com/{owner}/{name}.git", branch_dir, branch=branch
            )
        except GitCommandError:
            continue
    return carpeta_descarga


async def is_imported(file_path: str, dependency: str) -> Any:
    with open(file_path, encoding="utf-8") as file:
        try:
            code = file.read()
            return search(rf"(from|import)\s+{dependency}", code)
        except Exception as _:
            return False


async def get_files_path(directory_path: str) -> list[str]:
    branches = ["/main", "/master"]
    files = []
    for branch in branches:
        paths = glob(directory_path + branch + "/**", recursive=True)
        for _path in paths:
            if not isdir(_path) and ".py" in _path:
                files.append(_path)
    return files


async def get_child_artifacts(parent: str, code: str, cve_description: str) -> dict[str, list[int]]:
    used_artifacts: dict[str, list[int]] = {}
    for _ in findall(rf"{parent}\.[^\(\)\s:]+", code):
        for artifact in _.split(".")[1:]:
            if artifact.lower() in cve_description.lower():
                used_artifacts.setdefault(artifact.strip(), [])
    for _ in findall(rf"from\s+{parent}\.[^\(\)\s:]+\s+import\s+\w+(?:\s*,\s*\w+)*", code):
        for artifact in _.split("import")[1].split(","):
            if artifact.lower() in cve_description.lower():
                used_artifacts.setdefault(artifact.strip(), [])
    for _ in findall(rf"from\s+{parent}\s+import\s+\w+(?:\s*,\s*\w+)*", code):
        for artifact in _.split("import")[1].split(","):
            if artifact.lower() in cve_description.lower():
                used_artifacts.setdefault(artifact.strip(), [])
    aux = {}
    for artifact in used_artifacts:
        aux.update(await get_child_artifacts(artifact, code, cve_description))
    used_artifacts.update(aux)
    return used_artifacts


async def get_dep_artifacts(filename: str, dependency: str, cve_description: str) -> dict[str, list[int]]:
    with open(filename, encoding="utf-8") as file:
        code = file.read()
        current_line = 1
        used_artifacts = await get_child_artifacts(dependency, code, cve_description)
        for line in code.split("\n"):
            if "import" not in line:
                for artifact in used_artifacts:
                    if artifact in line:
                        used_artifacts.setdefault(artifact, []).append(current_line)
            current_line += 1
        for artifact in list(used_artifacts.keys()):
            if not used_artifacts[artifact]:
                del used_artifacts[artifact]
        return used_artifacts
