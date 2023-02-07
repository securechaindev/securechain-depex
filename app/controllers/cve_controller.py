from app.services import (
    read_cpe_matches_by_package_name,
    update_versions_cves_by_constraints
)
from app.utils import sanitize_version


async def relate_cves(package_name: str) -> None:
    cpe_matches = await read_cpe_matches_by_package_name(package_name)
    for raw_cpe_match in cpe_matches:
        cpe_match = raw_cpe_match['configurations']['nodes']['cpeMatch']
        del raw_cpe_match['configurations']
        if (
            'versionStartIncluding' not in cpe_match and
            'versionEndIncluding' not in cpe_match and
            'versionStartExcluding' not in cpe_match and
            'versionEndExcluding' not in cpe_match 
        ):
            version = cpe_match['criteria'].split(':')[5]
            if '*' in version:
                await update_versions_cves_by_constraints('any', package_name, raw_cpe_match)
            else:
                await update_versions_cves_by_constraints(
                    {'=': await sanitize_version(version)},
                    package_name,
                    raw_cpe_match
                )
        else:
            ctcs = {}

            if 'versionStartIncluding' in cpe_match:
                ctcs['>='] = await sanitize_version(cpe_match['versionStartIncluding'])
            if 'versionEndIncluding' in cpe_match:
                ctcs['<='] = await sanitize_version(cpe_match['versionEndIncluding'])
            if 'versionStartExcluding' in cpe_match:
                ctcs['>'] = await sanitize_version(cpe_match['versionStartExcluding'])
            if 'versionEndExcluding' in cpe_match:
                ctcs['<'] = await sanitize_version(cpe_match['versionEndExcluding'])

            await update_versions_cves_by_constraints(ctcs, package_name, raw_cpe_match)