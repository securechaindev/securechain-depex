from app.apis.nvd_service import get_cves

from app.controllers.version_controller import update_versions_cves_by_constraints

from dateutil.parser import parse

from app.services.cve_service import (
    create_cve,
    read_cve_by_cve_id
)


async def extract_cves(package: dict) -> None:
    raw_cves = get_cves(package['name'])

    for raw_cve in raw_cves['vulnerabilities']:
        raw_cve = raw_cve['cve']
        cve = await read_cve_by_cve_id(raw_cve['id'])
        if cve:
            cpe_matches = await get_cpe_matches(package['name'], cve)
        else:
            raw_cve['published'] = parse(raw_cve['published'])
            raw_cve['lastModified'] = parse(raw_cve['lastModified'])

            cve = await create_cve(raw_cve)

            cpe_matches = await get_cpe_matches(package['name'], cve)
        await relate_cve(cve, cpe_matches, package)

async def get_cpe_matches(package_name: str, cve: dict) -> list:
    cpe_matches = []
    for configuration in cve['configurations']:
        for node in configuration['nodes']:
            for cpe_match in node['cpeMatch']:
                if package_name in cpe_match['criteria']:
                    cpe_matches.append(cpe_match)
    return cpe_matches

async def relate_cve(cve: dict, cpe_matches: list, package: dict) -> None:
    for cpe_match in cpe_matches:
        if (
            'versionStartIncluding' not in cpe_match and
            'versionEndIncluding' not in cpe_match  and
            'versionStartExcluding' not in cpe_match  and
            'versionEndExcluding' not in cpe_match 
        ):
            version = cpe_match['criteria'].split(':')[5]
            if '*' in version:
                await update_versions_cves_by_constraints([], package['_id'], cve['_id'])
            else:
                await update_versions_cves_by_constraints([['=', version]], package['_id'], cve['_id'])
        else:
            ctcs = []

            if 'versionStartIncluding' in cpe_match: ctcs.append(['>=', cpe_match['versionStartIncluding']])
            if 'versionEndIncluding' in cpe_match: ctcs.append(['<=', cpe_match['versionEndIncluding']])
            if 'versionStartExcluding' in cpe_match: ctcs.append(['>', cpe_match['versionStartExcluding']])
            if 'versionEndExcluding' in cpe_match: ctcs.append(['<', cpe_match['versionEndExcluding']])

            await update_versions_cves_by_constraints(ctcs, package['_id'], cve['_id'])