from app.services.cve_service import read_cpe_matches_by_package_name
from app.services.version_service import update_versions_cves_by_constraints


async def extract_cves(package: dict) -> None:
    cpe_matches = await read_cpe_matches_by_package_name(package['name'])
    await relate_cve(cpe_matches, package)

async def relate_cve(cpe_matches: list, package: dict) -> None:
    for raw_cpe_match in cpe_matches:
        cpe_match = raw_cpe_match['configurations']['nodes']['cpeMatch']
        if (
            'versionStartIncluding' not in cpe_match and
            'versionEndIncluding' not in cpe_match  and
            'versionStartExcluding' not in cpe_match  and
            'versionEndExcluding' not in cpe_match 
        ):
            version = cpe_match['criteria'].split(':')[5]
            if '*' in version:
                await update_versions_cves_by_constraints([], package['_id'], raw_cpe_match['_id'])
            else:
                await update_versions_cves_by_constraints([['=', version]], package['_id'], raw_cpe_match['_id'])
        else:
            ctcs = []

            if 'versionStartIncluding' in cpe_match: ctcs.append(['>=', cpe_match['versionStartIncluding']])
            if 'versionEndIncluding' in cpe_match: ctcs.append(['<=', cpe_match['versionEndIncluding']])
            if 'versionStartExcluding' in cpe_match: ctcs.append(['>', cpe_match['versionStartExcluding']])
            if 'versionEndExcluding' in cpe_match: ctcs.append(['<', cpe_match['versionEndExcluding']])

            await update_versions_cves_by_constraints(ctcs, package['_id'], raw_cpe_match['_id'])