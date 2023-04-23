from typing import Any

from packaging.version import parse

from app.services import add_impacts_and_cves


async def relate_cves(version: dict[str, Any], cpe_matches: list[dict[str, Any]]) -> None:
    impacts: list[float] = []
    cves: list[str] = []
    for raw_cpe_match in cpe_matches:
        cpe_match: dict[str, Any] = raw_cpe_match['configurations']['nodes']['cpeMatch']
        if (
            'versionStartIncluding' not in cpe_match and
            'versionEndIncluding' not in cpe_match and
            'versionStartExcluding' not in cpe_match and
            'versionEndExcluding' not in cpe_match 
        ):
            cpe_version = cpe_match['criteria'].split(':')[5]
            if '*' in cpe_version or '-' in cpe_version:
                cves.append(raw_cpe_match['id'])
                impacts.append(await get_impact(raw_cpe_match))
            else:
                if parse(version['name']) == parse(cpe_version):
                    cves.append(raw_cpe_match['id'])
                    impacts.append(await get_impact(raw_cpe_match))
        else:
            check = True

            if 'versionStartIncluding' in cpe_match:
                check = parse(version['name']) >= parse(cpe_match['versionStartIncluding'])
            if 'versionEndIncluding' in cpe_match:
                check = parse(version['name']) <= parse(cpe_match['versionEndIncluding'])
            if 'versionStartExcluding' in cpe_match:
                check = parse(version['name']) > parse(cpe_match['versionStartExcluding'])
            if 'versionEndExcluding' in cpe_match:
                check = parse(version['name']) < parse(cpe_match['versionEndExcluding'])

            if check:
                cves.append(raw_cpe_match['id'])
                impacts.append(await get_impact(raw_cpe_match))
    await add_impacts_and_cves(impacts, cves, version['id'])


async def get_impact(cve: dict[str, Any]) -> float:
    for key, value in cve['metrics'].items():
        match key:
            case 'cvssMetricV31':
                return float(value[0]['impactScore'])
            case 'cvssMetricV30':
                return float(value[0]['impactScore'])
            case 'cvssMetricV2':
                return float(value[0]['impactScore'])
    return 0.