from typing import Any

from app.services import read_vulnerabilities_by_package_and_version

from .metrics import mean, weighted_mean


async def attribute_vulnerabilities(
    package_name: str, version: Any
) -> dict[str, Any]:
    vulnerabilities = await read_vulnerabilities_by_package_and_version(package_name, version["name"])
    impacts: list[float] = []
    version["vulnerabilities"] = []
    for vuln in vulnerabilities:
        version["vulnerabilities"].append(vuln["id"])
        if "severity" in vuln:
            for severity in vuln["severity"]:
                if severity["type"] == "CVSS_V3":
                    impacts.append(severity["base_score"])
    version["mean"] = await mean(impacts)
    version["weighted_mean"] = await weighted_mean(impacts)
    return version
