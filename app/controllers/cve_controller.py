from bson import ObjectId

from app.apis.nvd_service import get_cves

from app.controllers.version_controller import filter_versions_db

from dateutil.parser import parse

from app.services.cve_service import (
    create_cve,
    read_cve_by_cve_id
)
from app.services.version_service import update_version_cves


async def extract_cves(package: dict) -> None:
    raw_cves = get_cves(package['name'])

    for raw_cve in raw_cves['vulnerabilities']:
        raw_cve = raw_cve['cve']
        cve = await read_cve_by_cve_id(raw_cve['id'])
        if cve:
            await relate_cve(package, cve)
        else:
            raw_cve['published'] = parse(raw_cve['published'])
            raw_cve['lastModified'] = parse(raw_cve['lastModified'])

            cve = await create_cve(raw_cve)

            await relate_cve(package, cve)

async def relate_cve(package: dict, cve: dict) -> None:
    for configuration in cve['configurations']:
        for node in configuration['nodes']:
            for cpe_match in node['cpeMatch']:
                if package['name'] in cpe_match['criteria']:
                    await process_cve(package, cve, cpe_match)

async def process_cve(package: dict, cve: dict, cpe_match: dict) -> None:
    if (
        'versionStartIncluding' in cpe_match and
        'versionEndIncluding' in cpe_match  and
        'versionStartExcluding' in cpe_match  and
        'versionEndExcluding' in cpe_match 
    ):
        version = cpe_match['criteria'].split(':')[5]
        if '*' in version:
            await update_versions(package['versions'], cve['_id'])
        else:
            filtered_versions = await filter_versions_db([['='], version], package['versions'])
            await update_versions(filtered_versions, cve['_id'])
    else:
        ctcs = []

        if 'versionStartIncluding' in cpe_match: ctcs.append(['>=', cpe_match['versionStartIncluding']])
        if 'versionEndIncluding' in cpe_match: ctcs.append(['<=', cpe_match['versionEndIncluding']])
        if 'versionStartExcluding' in cpe_match: ctcs.append(['>', cpe_match['versionStartExcluding']])
        if 'versionEndExcluding' in cpe_match: ctcs.append(['<', cpe_match['versionEndExcluding']])

        filtered_versions = await filter_versions_db(ctcs, package['versions'])
        await update_versions(filtered_versions, cve['_id'])

async def update_versions(version_ids: list[ObjectId], cve_id: ObjectId) -> None:
    for version_id in version_ids:
        await update_version_cves(version_id, cve_id)