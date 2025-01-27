from typing import Any

from univers.versions import MavenVersion, PypiVersion, SemverVersion

from app.utils import mean, weighted_mean


async def attribute_cves(
    version: Any, cpe_product: dict[str, Any], manager: str
) -> dict[str, Any]:
    impacts: list[float] = []
    version["cves"] = []
    version_keys = (
        "versionStartIncluding",
        "versionEndIncluding",
        "versionStartExcluding",
        "versionEndExcluding",
    )
    version_type = await get_version_type(manager)
    if cpe_product:
        for cve in cpe_product["cves"]:
            if not any(key in cve for key in version_keys):
                if "*" in cve["version"] or "-" in cve["version"]:
                    if cve["id"] not in version["cves"]:
                        version["cves"].append(cve["id"])
                        impacts.append(cve["impact_score"])
                else:
                    try:
                        if version_type(version["name"]) == version_type(
                            cve["version"]
                        ):
                            if cve["id"] not in version["cves"]:
                                version["cves"].append(cve["id"])
                                impacts.append(cve["impact_score"])
                    except Exception as _:
                        continue
            else:
                check = True
                try:
                    if "versionStartIncluding" in cve:
                        check = check and version_type(version["name"]) >= version_type(
                            cve["versionStartIncluding"]
                        )
                    if "versionEndIncluding" in cve:
                        check = check and version_type(version["name"]) <= version_type(
                            cve["versionEndIncluding"]
                        )
                    if "versionStartExcluding" in cve:
                        check = check and version_type(version["name"]) > version_type(
                            cve["versionStartExcluding"]
                        )
                    if "versionEndExcluding" in cve:
                        check = check and version_type(version["name"]) < version_type(
                            cve["versionEndExcluding"]
                        )
                except Exception as _:
                    continue
                if check:
                    if cve["id"] not in version["cves"]:
                        version["cves"].append(cve["id"])
                        impacts.append(cve["impact_score"])
    version["mean"] = await mean(impacts)
    version["weighted_mean"] = await weighted_mean(impacts)
    return version


async def get_version_type(manager: str):
    match manager:
        case "pypi":
            return PypiVersion
        case "npm":
            return SemverVersion
        case "maven":
            return MavenVersion
