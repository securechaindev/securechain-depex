from datetime import datetime
from glob import glob
from json import JSONDecodeError, dumps, load
from os import makedirs, system
from os.path import exists, isdir
from typing import Any
from zipfile import ZipFile

from fastapi import APIRouter, Path, Query, status
from fastapi.responses import FileResponse, JSONResponse
from git import GitCommandError, Repo
from regex import findall, search
from typing_extensions import Annotated

from app.controllers import init_mvn_package, init_npm_package, init_pypi_package
from app.services import (
    read_cve_by_id,
    read_cve_ids_by_version_and_package,
    read_cwes_by_cve_id,
    read_exploits_by_cve_id,
)
from app.utils import json_encoder

router = APIRouter()

@router.post(
    "/vex/van/{owner}/{name}",
    summary="Create boths VEX and VAN files by repository id and SBOM file",
    response_description="Return a zip with a VEX and a VAN file",
)
async def create_vex_van(
    owner: Annotated[str, Path(min_length=1)],
    name: Annotated[str, Path(min_length=1)],
    sbom_path: Annotated[str, Query(min_lengt=1)]
) -> JSONResponse | FileResponse:
    """
    Return boths VEX and VAN files by a given owner, name and a SBOM path:

    - **owner**: the owner of a repository
    - **name**: the name of a repository
    - **sbom_path**: the path to the sbom file in repository
    """
    carpeta_descarga = await download_repository(owner, name)
    result = await generate_vex_van(carpeta_descarga, owner, sbom_path)
    if isinstance(result, JSONResponse):
        system("rm -rf " + carpeta_descarga)
        return result
    else:
        vex, van, s_path = result
    with ZipFile("vex_van.zip", "w") as myzip:
        myzip.writestr("vex.json", dumps(vex, indent=2))
        myzip.writestr("van.json", dumps(van, indent=2))
        myzip.write(s_path, arcname=s_path.split("/")[-1])
    system("rm -rf " + carpeta_descarga)
    return FileResponse(path="vex_van.zip", filename="vex_van.zip", status_code=status.HTTP_200_OK)


async def download_repository(owner: str, name: str) -> str:
    carpeta_descarga = "repositories/" + name
    system("rm -rf " + carpeta_descarga)
    makedirs(carpeta_descarga)
    for branch in ("main", "master"):
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


async def generate_vex_van(
    carpeta_descarga: str,
    owner: str,
    sbom_path: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str] | JSONResponse:
    paths = await get_files_path(carpeta_descarga)
    s_path = ""
    timestamp = str(datetime.now())
    with open("app/templates/van_template.json", encoding="utf-8") as van_file:
        van = load(van_file)
    van["timestamp"] = timestamp
    with open("app/templates/vex_template.json", encoding="utf-8") as vex_file:
        vex = load(vex_file)
    vex["author"] = owner
    vex["timestamp"] = timestamp
    vex["last_updated"] = timestamp
    vex["tooling"] = "https://github.com/GermanMT/depex"
    for branch in ("main", "master"):
        if exists(f"{carpeta_descarga}/{branch}/{sbom_path}"):
            s_path = f"{carpeta_descarga}/{branch}/{sbom_path}"
            with open(f"{carpeta_descarga}/{branch}/{sbom_path}", encoding="utf-8") as sbom_file:
                try:
                    sbom_json = load(sbom_file)
                except JSONDecodeError:
                    return JSONResponse(
                        status_code=status.HTTP_200_OK,
                        content=json_encoder(
                            {"message": "The sbom file is not correctly constructed"}
                        ),
                    )
                if "components" in sbom_json and isinstance(sbom_json["components"], list):
                    for component in sbom_json["components"]:
                        if "name" in component:
                            if "group" in component:
                                component_name = f"{component["group"]}\\{component["name"]}"
                            else:
                                component_name = component["name"]
                            if "purl" in component and "version" in component:
                                package_manager = component["purl"].split(":")[1].split("/")[0]
                                if package_manager in ("npm", "maven", "pypi"):
                                    package_manager = await parse_package_manager(package_manager)
                                    result = await init_package(component, package_manager)
                                    if isinstance(result, JSONResponse):
                                        system("rm -rf " + carpeta_descarga)
                                        return result
                                    else:
                                        component_name = result
                                    cve_ids = await read_cve_ids_by_version_and_package(
                                        component["version"], component_name, package_manager
                                    )
                                    for cve_id in cve_ids:
                                        vex["statements"].append(
                                            await generate_statement(cve_id, timestamp, package_manager)
                                        )
                                        van["statements_assisting_information"].append(
                                            await generate_statement_info(cve_id, paths, component_name, component["version"])
                                        )
    van["statements_assisting_information"] = sorted(van["statements_assisting_information"], key=lambda d: d['priority'], reverse=True)
    if not s_path:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=json_encoder(
                {"message": "The repository don't have main or master branch"}
            ),
        )
    return vex, van, s_path


async def get_files_path(directory_path: str) -> list[str]:
    files = []
    for branch in ("/main", "/master"):
        paths = glob(directory_path + branch + "/**", recursive=True)
        for _path in paths:
            if not isdir(_path) and ".py" in _path:
                files.append(_path)
    return files


async def parse_package_manager(package_manager: str) -> str:
    if package_manager == "npm":
        return "NPM"
    elif package_manager == "maven":
        return "MVN"
    elif package_manager == "pypi":
        return "PIP"


async def init_package(component: dict[str, Any], package_manager: str) -> str:
    if "group" in component:
        match package_manager:
            case "PIP":
                component_name = component["name"]
                await init_pypi_package(component_name)
            case "NPM":
                component_name = f"{component["group"]}\\{component["name"]}"
                await init_npm_package(component_name)
            case "MVN":
                component_name = f"{component["group"]}:{component["name"]}"
                await init_mvn_package(component["group"], component["name"])
    else:
        component_name = component["name"]
        match package_manager:
            case "PIP":
                await init_pypi_package(component_name)
            case "NPM":
                await init_npm_package(component_name)
            case "MVN":
                if ":" not in component_name:
                    return JSONResponse(
                        status_code=status.HTTP_200_OK,
                        content=json_encoder(
                            {"message": "A maven dependency component is not well built, there is needed a group attribute or name atribute follow the pattern <group_id>:<artifact_id>"}
                        ),
                    )
                group_id, artifact_id = component_name.split(":")
                await init_mvn_package(group_id, artifact_id)
    return component_name

async def generate_statement(cve_id: str, timestamp: str, package_manager: str) -> dict[str, Any]:
    statement_temp = open("app/templates/statement_template.json", encoding="utf-8")
    statement = load(statement_temp)
    statement_temp.close()
    cve = await read_cve_by_id(cve_id)
    statement["vulnerability"]["@id"] = f"https://nvd.nist.gov/vuln/detail/{cve["id"]}"
    statement["vulnerability"]["name"] = cve["id"]
    statement["vulnerability"]["description"] = cve["description"]
    statement["timestamp"] = timestamp
    statement["last_updated"] = timestamp
    statement["supplier"] = package_manager
    return statement


async def generate_statement_info(cve_id: str, paths: list[str],  name: str, version: str) -> dict[str, Any]:
    statement_info_temp = open("app/templates/statement_info_template.json", encoding="utf-8")
    statement_info = load(statement_info_temp)
    statement_info_temp.close()
    statement_info["affected_component"] = name
    statement_info["affected_component_version"] = version
    cve = await read_cve_by_id(cve_id)
    statement_info["vulnerability"]["@id"] = f"https://nvd.nist.gov/vuln/detail/{cve["id"]}"
    statement_info["vulnerability"]["name"] = cve["id"]
    statement_info["vulnerability"]["description"] = cve["description"]
    statement_info["vulnerability"]["cvss"]["vuln_impact"] = cve["vuln_impact"][0]
    statement_info["vulnerability"]["cvss"]["attack_vector"] = cve["attack_vector"][0]

    for cwe in await read_cwes_by_cve_id(cve_id):
        _cwe = {}
        _cwe["@id"] = f"https://cwe.mitre.org/data/definitions/{cwe["@ID"]}.html"
        _cwe["name"] = cwe["@ID"]
        _cwe["description"] = cwe["Extended_Description"] if "Extended_Description" in cwe else cwe["Description"]
        if "Background_Details" in cwe:
            _cwe["background_detail"] = cwe["Background_Details"]["Background_Detail"]
        if "Common_Consequences" in cwe:
            _cwe["consequences"] = cwe["Common_Consequences"]["Consequence"]
        if "Detection_Methods" in cwe:
            _cwe["detection_methods"] = cwe["Detection_Methods"]["Detection_Method"]
        if "Potential_Mitigations" in cwe:
            _cwe["potential_mitigations"] = cwe["Potential_Mitigations"]["Mitigation"]
        if "Demonstrative_Examples" in cwe:
            _cwe["demonstrative_examples"] = cwe["Demonstrative_Examples"]["Demonstrative_Example"]
        statement_info["vulnerability"]["cwes"].append(_cwe)

    for path in paths:
        if await is_imported(path, name):
            reacheable_code = {}
            reacheable_code["path_to_file"] = path.replace("repositories/", "")
            reacheable_code["used_artifacts"] = await get_used_artifacts(path, name, cve["description"])
            if reacheable_code["used_artifacts"]:
                statement_info["reachable_code"].append(reacheable_code)

    for exploit in await read_exploits_by_cve_id(cve_id):
        _exploit = {}
        _exploit["@id"] = exploit["href"] if exploit["href"] else "Unknown"
        _exploit["description"] = "" if exploit["type"] == "githubexploit" else exploit["description"]
        _exploit["payload"] = ""
        if exploit["type"] == "githubexploit":
            _exploit["payload"] = exploit["description"]
        else:
            if "sourceData" in exploit:
                _exploit["payload"] = exploit["sourceData"]
        statement_info["exploits"].append(_exploit)

    priority = cve["vuln_impact"][0]*0.7

    if not statement_info["reachable_code"]:
        del statement_info["reachable_code"]
    else:
        priority += 1

    if not statement_info["exploits"]:
        del statement_info["exploits"]
    else:
        priority += 1

    if not statement_info["vulnerability"]["cwes"]:
        del statement_info["vulnerability"]["cwes"]
    else:
        priority += 1

    statement_info["priority"] = priority

    return statement_info


async def is_imported(file_path: str, dependency: str) -> Any:
    with open(file_path, encoding="utf-8") as file:
        try:
            code = file.read()
            return search(rf"(from|import)\s+{dependency}", code)
        except Exception as _:
            return False


async def get_used_artifacts(filename: str, dependency: str, cve_description: str) -> dict[str, list[int]]:
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

        result = []
        for artifact_name, used_in_lines in used_artifacts.items():
            result.append({
                "artifact_name": artifact_name,
                "used_in_lines": used_in_lines
            })
        return result


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
