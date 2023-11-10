from typing import Any

from univers.versions import MavenVersion, PypiVersion, SemverVersion

from app.utils import mean, weighted_mean


async def relate_cves(
    version: Any,
    cpe_matches: list[dict[str, Any]],
    package_manager: str,
    package_name: str,
    artifact_id: str | None = None,
) -> dict[str, Any]:
    impacts: list[float] = []
    version["cves"] = []
    version_type = await get_version_type(package_manager)
    for raw_cpe_match in cpe_matches:
        for configuration in raw_cpe_match["configurations"]:
            for node in configuration["nodes"]:
                for cpe_match in node["cpeMatch"]:
                    cpe_parts = cpe_match["criteria"].split(":")
                    if cpe_parts[4] in (package_name, artifact_id):
                        version_keys = (
                            "versionStartIncluding",
                            "versionEndIncluding",
                            "versionStartExcluding",
                            "versionEndExcluding",
                        )
                        if not any(key in cpe_match for key in version_keys):
                            cpe_version = cpe_parts[5]
                            if "*" in cpe_version or "-" in cpe_version:
                                version["cves"].append(raw_cpe_match["id"])
                                impacts.append(raw_cpe_match["impact_score"][0])
                            else:
                                try:
                                    if version_type(version["name"]) == version_type(
                                        cpe_version
                                    ):
                                        version["cves"].append(raw_cpe_match["id"])
                                        impacts.append(raw_cpe_match["impact_score"][0])
                                except Exception as _:
                                    continue
                        else:
                            check = True
                            try:
                                if "versionStartIncluding" in cpe_match:
                                    check = check and version_type(
                                        version["name"]
                                    ) >= version_type(
                                        cpe_match["versionStartIncluding"]
                                    )
                                if "versionEndIncluding" in cpe_match:
                                    check = check and version_type(
                                        version["name"]
                                    ) <= version_type(cpe_match["versionEndIncluding"])
                                if "versionStartExcluding" in cpe_match:
                                    check = check and version_type(
                                        version["name"]
                                    ) > version_type(cpe_match["versionStartExcluding"])
                                if "versionEndExcluding" in cpe_match:
                                    check = check and version_type(
                                        version["name"]
                                    ) < version_type(cpe_match["versionEndExcluding"])
                            except Exception as _:
                                continue
                            if check:
                                version["cves"].append(raw_cpe_match["id"])
                                impacts.append(raw_cpe_match["impact_score"][0])
    version["mean"] = await mean(impacts)
    version["weighted_mean"] = await weighted_mean(impacts)
    return version


async def get_version_type(package_manager: str):
    match package_manager:
        case "PIP":
            return PypiVersion
        case "NPM":
            return SemverVersion
        case "MVN":
            return MavenVersion
