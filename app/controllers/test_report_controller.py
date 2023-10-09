from typing import Any
from os import system, makedirs
from os.path import isdir, exists
from glob import glob
from git import Repo, GitCommandError
from re import findall, search
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from app.services import (
    read_cve_ids_by_version_and_package,
    read_cve_impact_by_cve_id,
    read_exploits_by_cve_id,
    read_repository_by_id
)
from app.utils import json_encoder, get_manager

router = APIRouter()

@router.post(
    '/test_report/{repository_id}',
    summary='Create a test report by repository id and configuration',
    response_description='Return a test report'
)
async def create_test_report(repository_id: str, configuration: dict[str, str | int | float], file_name: str) -> JSONResponse:
    '''
    Return a test report by a given repository id and a configuration:

    - **repository_id**: the id of a repository
    - **configuration**: a valid configuration for a file of the repository
    '''
    package_manager = await get_manager(file_name)
    repository = await read_repository_by_id(repository_id, package_manager)
    carpeta_descarga = await download_repository(repository['owner'], repository['name'])
    paths = await get_files_path('repositories/' + repository['name'])
    raw_report = await get_raw_report(configuration, package_manager)
    test_report: dict[str, list[Any]] = {'tests': []}
    number = 0
    for dependency in raw_report:
        if dependency['impact'] != 0:
            for cve in dependency['cves']:
                if cve['exploits']:
                    for exploit in cve['exploits']:
                        tests, number = await create_tests(number, paths, dependency, cve, exploit['id'])
                        test_report['tests'].extend(tests)
                else:
                    tests, number = await create_tests(number, paths, dependency, cve)
                    test_report['tests'].extend(tests)

    system('rm -rf ' + carpeta_descarga)
    return JSONResponse(status_code=status.HTTP_200_OK, content=json_encoder(test_report))


async def create_tests(number: int, paths: list[str], dependency, cve, exploit_id: str = None) -> list[dict[str, Any]]:
    tests = []
    for _path in paths:
        if await is_imported(_path, dependency['name']):
            number += 1
            tests.append({
                f'test{number}': {
                    'dependency': dependency['name'],
                    'version': dependency['version'],
                    'dep_impact': dependency['impact'],
                    'file_dir': _path,
                    'dep_artifacts': await get_used_artifacts(_path, dependency['name']),
                    'vulnerability': cve['id'],
                    'vuln_impact': cve['vuln_impact'],
                    'exploit': 'https://www.exploit-db.com/exploits/' + exploit_id if exploit_id else None,
                    'payload': 'https://www.exploit-db.com/download/' + exploit_id if exploit_id else None,
                    'automatable': bool(exploit_id)
                }
            })
    return (tests, number)


async def get_raw_report(configuration: dict[str, str | int], package_manager: str) -> list[dict[str, int]]:
    raw_report = []
    aux = {}
    for dependency in configuration:
        if 'CVSS' in dependency:
            aux[dependency.replace('CVSS', '')] = configuration[dependency]
    for dependency, version in configuration.items():
        if version != -1 and all(key not in dependency for key in ('CVSS', 'func_obj')):
            cves = []
            cve_ids = await read_cve_ids_by_version_and_package(version, dependency, package_manager)
            for cve_id in cve_ids:
                impact = await read_cve_impact_by_cve_id(cve_id)
                exploits = await read_exploits_by_cve_id(cve_id)
                cves.append(
                    {
                        'id': cve_id,
                        'vuln_impact': impact['impact_score'][0],
                        'exploits': exploits
                    }
                )
            raw_report.append(
                    {
                    'name': dependency,
                    'version': version,
                    'impact': aux[dependency],
                    'cves': cves
                    }
                )
    return raw_report


async def download_repository(owner:str, name: str) -> str:
    carpeta_descarga = 'repositories/' + name
    branches = ['main', 'master']
    makedirs(carpeta_descarga)
    for branch in branches:
        branch_dir = carpeta_descarga + "/" + branch
        if not exists(branch_dir):
            makedirs(branch_dir)
        try:
            Repo.clone_from(f'https://github.com/{owner}/{name}.git', branch_dir, branch=branch)
        except GitCommandError:
            continue
    return carpeta_descarga


async def is_imported(file_path: str, dependency: str) -> int:
    with open(file_path, 'r', encoding='utf-8') as file:
        code = file.read()
        return search(rf'from\s+{dependency}', code) or search(rf'import\s+{dependency}', code)


async def get_files_path(directory_path: str) -> list[str]:
    branches = ['/main', '/master']
    files = []
    for branch in branches:
        paths = glob(directory_path + branch + '/**', recursive=True)
        for _path in paths:
            if not isdir(_path) and '.py' in _path:
                files.append(_path)
    return files
    

async def get_used_artifacts(filename: str, dependency: str) -> dict[str, list[int]]:
    with open(filename, 'r', encoding='utf-8') as file:
        used_artifacts: dict[str, list[int]] = {}
        code = file.read()
        current_line = 1
        imported_artifacts = []
        for linea in code.split('\n'):
            if search(rf'from\s+{dependency}', linea):
                line_imports = findall(rf'from\s+{dependency}\.[^\(\)\s:]+\s+import\s+\w+(?:\s*,\s*\w+)*', linea)
                line_imports.extend(findall(rf'from\s+{dependency}\s+import\s+\w+(?:\s*,\s*\w+)*', linea))
                for line_import in line_imports:
                    artifacs = line_import.split('import')[1].strip().split(',')
                    imported_artifacts.extend(artifacs)
                    for artifact in artifacs:
                        used_artifacts.setdefault(artifact, []).append(current_line)
                current_line += 1
                continue
            if search(rf'{dependency}\.[^\(\)\s:]+', linea):
                for artifact in findall(rf'{dependency}\.[^\(\)\s:]+', linea):
                    artifact = artifact.replace(f'{dependency}.', '')
                    used_artifacts.setdefault(artifact, []).append(current_line)
            for imported_artifact in imported_artifacts:
                if search(rf'{imported_artifact}[.(]', linea):
                    used_artifacts[imported_artifact].append(current_line)
            current_line += 1
        return used_artifacts